"""
Strategy: AI-powered employee matching.
Finds best-fit employees from the manager's team for a given requirement.
"""

import json
import re
from sqlalchemy.orm import Session

from app.llm.adapter_factory import get_llm_adapter
from app.repositories import allocation_repository, employee_repository


# Named constant — not an inline magic string
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


def find_best_matches(db: Session, requirement: str, manager_id: int) -> list[dict]:
    """
    1. Load manager's team.
    2. Parse requested hours from requirement text.
    3. Filter out employees without enough free capacity.
    4. If none qualify → return [] without calling LLM.
    5. Build structured employee summary.
    6. Call LLM.
    7. Parse and return ranked result list.
    """
    requested_hours = parse_requested_hours(requirement)
    team            = employee_repository.get_employees_by_manager(db, manager_id)
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
            f"- {emp.user.full_name}: {free_hours} hrs/week free, "
            f"Skills: {', '.join(skills) or 'none listed'}"
        )
    return "\n".join(lines)


def _parse_llm_response(response_text: str) -> list[dict]:
    """Parses the JSON array from the LLM response. Returns [] on parse failure."""
    try:
        return json.loads(response_text.strip())
    except (json.JSONDecodeError, ValueError):
        return []
