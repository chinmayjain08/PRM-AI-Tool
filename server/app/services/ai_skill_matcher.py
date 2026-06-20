"""
Strategy: AI-powered employee matching.
Finds best-fit employees from the manager's team for a given requirement.
"""

import json
import re
from sqlalchemy.orm import Session

from app.llm.adapter_factory import get_llm_adapter
from app.repositories import allocation_repository, employee_repository


SKILL_MATCH_PROMPT = """
You are a resource manager assistant. Based on the requirement below and the
list of available employees, rank the top matches from best to worst. For each,
provide a one-sentence reason (skills, availability, recent activity).

Project Requirement:
{requirement}

Available Employees:
{employee_summary}

Respond ONLY as a valid JSON array (no extra text):
[{{"name": "Full Name", "reason": "one sentence", "suggested_allocation_pct": 50}}]

Only use employees from the list. Do not invent names.
"""

TEAM_BUILDER_PROMPT = """
You are an advanced resource manager assistant. You have been given a request to staff a project team with multiple roles.
Based on the project requirements and the list of available employees, fill each role with the BEST available employee in one go.

CRITICAL RULES:
1. NEVER put the same person in two roles.
2. If multiple headcount for a role is requested (e.g., "2 QA Engineers"), treat each seat as a separate role to fill.
3. Fill as many seats as possible in "matches". For example, if 2 QA are requested but only 1 is available, put the 1 available QA in "matches", and put the 1 unfilled QA seat in "gaps".
4. If a role (or seat) cannot be filled, do NOT put "None" or "N/A" in matches. Instead, add it to the "gaps" list.
5. Be honest about gaps. Provide the exact role and precisely why it could not be filled (e.g., nobody has the skill, or someone has it but is fully allocated).

Project Requirement (Roles):
{requirement}

Available Employees (Bench & Allocated):
{employee_summary}

Respond ONLY as a valid JSON object matching this schema (no extra text, no markdown wrappers):
{{
    "matches": [
        {{"role": "Role Name", "name": "Full Name", "reason": "one sentence", "suggested_allocation_pct": 50}}
    ],
    "gaps": [
        {{"role": "Role Name", "reason": "Why the role could not be filled (nobody has skill OR allocated elsewhere)"}}
    ]
}}

Only use employees from the list. Do not invent names.
"""


def find_best_matches(db: Session, requirement: str, manager_id: int) -> list[dict]:
    """
    1. Load all active employees in the organization.
    2. Parse requested hours from requirement text.
    3. Filter out employees without enough free capacity.
    4. If none qualify → return [] without calling LLM.
    5. Build structured employee summary.
    6. Call LLM.
    7. Parse and return ranked result list.
    """
    requested_hours = parse_requested_hours(requirement)
    team            = employee_repository.get_all_employees(db, status_filter="BENCH", role_name_filter="RESOURCE")
    qualified       = _filter_by_capacity(db, team, requested_hours)

    if not qualified:
        return []

    employee_summary = _build_employee_summary(db, qualified)
    prompt           = SKILL_MATCH_PROMPT.format(
        requirement      = requirement,
        employee_summary = employee_summary,
    )

    llm      = get_llm_adapter(db)
    response = llm.complete(prompt)
    return _parse_llm_response(response)


def build_team(db: Session, requirement: str, manager_id: int) -> dict:
    """
    1. Load all active employees in the organization.
    2. Build structured employee summary containing ALL employees.
    3. Call LLM to find matches for ALL roles simultaneously.
    4. Parse and return {"matches": [...], "gaps": [...]}
    """
    team = employee_repository.get_all_employees(db, status_filter="BENCH", role_name_filter="RESOURCE")
    
    if not team:
        return {"matches": [], "gaps": []}

    employee_summary = _build_full_employee_summary(db, team)
    prompt           = TEAM_BUILDER_PROMPT.format(
        requirement      = requirement,
        employee_summary = employee_summary,
    )

    llm      = get_llm_adapter(db)
    response = llm.complete(prompt)
    
    response_dict = _parse_team_builder_response(response)
    
    # Augment matches, enforce uniqueness, and filter hallucinations
    if "matches" in response_dict:
        name_to_emp = {emp.employee.full_name: emp for emp in team}
        valid_matches = []
        assigned_names = set()
        
        for match in response_dict["matches"]:
            emp_name = match.get("name")
            role_name = match.get("role", "Unknown Role")
            
            if not emp_name or emp_name.lower() in ("none", "n/a", "null"):
                response_dict.setdefault("gaps", []).append({
                    "role": role_name,
                    "reason": match.get("reason", "Nobody has the skill available.")
                })
                continue
                
            if emp_name in assigned_names:
                response_dict.setdefault("gaps", []).append({
                    "role": role_name,
                    "reason": f"Candidate {emp_name} matched but was already assigned to another role in this request."
                })
                continue

            if emp_name in name_to_emp:
                free_hrs = _compute_free_hours(db, name_to_emp[emp_name])
                match["free_bandwidth_hrs"] = free_hrs
                assigned_names.add(emp_name)
                valid_matches.append(match)
            else:
                response_dict.setdefault("gaps", []).append({
                    "role": role_name,
                    "reason": f"LLM suggested an invalid or external employee: {emp_name}"
                })
                
        response_dict["matches"] = valid_matches
        
    # Deduplicate gaps by ROLE only to prevent duplicate reasons for the same missing role
    if "gaps" in response_dict:
        unique_gaps = []
        seen_roles = set()
        for gap in response_dict["gaps"]:
            role_name = gap.get("role", "Unknown Role").strip().lower()
            if role_name not in seen_roles:
                unique_gaps.append(gap)
                seen_roles.add(role_name)
        response_dict["gaps"] = unique_gaps

    return response_dict


def parse_requested_hours(requirement: str) -> int:
    """
    Extracts weekly hour commitment from natural language.
    Patterns handled: '10 hrs/week', '10 hours a week', 'ten hours per week'.
    Returns 0 if no specific hours found (treated as full-time request).
    """
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
    }
    text = requirement.lower()

    digit_match = re.search(r"(\d+)\s*(hrs?|hours?)\s*(a|per|/)\s*week", text)
    if digit_match:
        return int(digit_match.group(1))

    for word, value in number_words.items():
        if re.search(rf"\b{word}\b.*\b(hrs?|hours?)\b.*\bweek\b", text):
            return value

    return 0


def _filter_by_capacity(db: Session, team: list, requested_hours: int) -> list:
    """Removes employees who do not have enough free capacity."""
    qualified = []
    for employee in team:
        free_hours = _compute_free_hours(db, employee)
        if requested_hours > 0:
            if free_hours >= requested_hours:
                qualified.append(employee)
        else:
            if free_hours > 0:   # exclude fully booked employees
                qualified.append(employee)
    return qualified


def _compute_free_hours(db: Session, employee) -> int:
    """Returns the employee's available hours per week based on current utilisation."""
    from app.core.config import settings
    allocs     = allocation_repository.get_active_allocations_for_employee(db, employee.id)
    used_pct   = sum(a.utilisation_percent for a in allocs)
    free_pct   = max(0, 100 - used_pct)
    return int(free_pct * settings.DEFAULT_MAX_WEEKLY_HOURS / 100)


def _build_employee_summary(db: Session, employees: list) -> str:
    """Builds a readable text block describing each qualifying employee."""
    lines = []
    for emp in employees:
        free_hours = _compute_free_hours(db, emp)
        skills     = [es.skill.name for es in emp.skills]
        lines.append(
            f"- {emp.employee.full_name}: {free_hours} hrs/week free, "
            f"Skills: {', '.join(skills) or 'none listed'}"
        )
    return "\n".join(lines)


def _build_full_employee_summary(db: Session, employees: list) -> str:
    """Builds a readable text block describing each employee (bench & allocated) for team builder."""
    lines = []
    for emp in employees:
        free_hours = _compute_free_hours(db, emp)
        skills     = [es.skill.name for es in emp.skills]
        
        allocs = allocation_repository.get_active_allocations_for_employee(db, emp.id)
        if allocs:
            dates = [a.to_date for a in allocs if a.to_date]
            if dates:
                max_date = max(dates)
                alloc_info = f"Allocated until {max_date.isoformat()}"
            else:
                alloc_info = "Allocated indefinitely"
        else:
            alloc_info = "On bench"

        lines.append(
            f"- {emp.employee.full_name}: {free_hours} hrs/week free, "
            f"Skills: {', '.join(skills) or 'none listed'} | Status: {alloc_info}"
        )
    return "\n".join(lines)


def _parse_llm_response(response_text: str) -> list[dict]:
    """Parses the JSON array from the LLM response. Returns [] on parse failure."""
    try:
        return json.loads(response_text.strip())
    except (json.JSONDecodeError, ValueError):
        return []


def _parse_team_builder_response(response_text: str) -> dict:
    """Parses the JSON object from the LLM response."""
    try:
        import re
        match = re.search(r'\{.*\}', response_text.strip(), re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(response_text.strip())
    except (json.JSONDecodeError, ValueError):
        return {"matches": [], "gaps": []}
    except Exception:
        return {"matches": [], "gaps": []}
