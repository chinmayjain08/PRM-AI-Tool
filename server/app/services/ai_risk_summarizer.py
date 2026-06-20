"""
Strategy: AI-powered project risk summary.
Generates a plain-English paragraph describing project health risks.
"""

from sqlalchemy.orm import Session

from app.llm.adapter_factory import get_llm_adapter
from app.repositories import project_repository
from app.services.project_health_service import collect_risk_flags


# Named constant — not an inline magic string
RISK_SUMMARY_PROMPT = """
You are a project health analyst. Based on the factual data below, write a
short paragraph (3 to 5 sentences) summarising the project risks in plain English.
Focus on what the manager should act on. Do not repeat the raw numbers verbatim.

Project: {project_name}
Deadline: {end_date}

Milestones:
{milestone_summary}

Resource Effort (last 2 weeks):
{effort_summary}

Identified Risk Flags:
{risk_flags}

Write the paragraph only. No headings, no bullet points.
"""


def generate_risk_summary(db: Session, project_id: int) -> str:
    """
    1. Load project data (name, deadline, milestones).
    2. Collect risk flags.
    3. Build and send prompt to LLM.
    4. Return the plain-English paragraph.
    """
    project    = project_repository.get_project_by_id(db, project_id)
    milestones = project_repository.get_milestones_for_project(db, project_id)
    risk_flags = collect_risk_flags(db, project_id)

    prompt = RISK_SUMMARY_PROMPT.format(
        project_name     = project.name,
        end_date         = str(project.end_date),
        milestone_summary = _format_milestones(milestones),
        effort_summary   = "See risk flags below",
        risk_flags       = "\n".join(f"- {flag}" for flag in risk_flags) or "None identified",
    )

    try:
        llm = get_llm_adapter(db)
        return llm.complete(prompt)
    except Exception as error:
        # Graceful fallback: construct summary from risk flags directly
        if not risk_flags:
            return "The AI analysis service is temporarily unavailable. Factual analysis shows all milestones are on track, and allocated resources are logging their expected hours."
        
        fallback_msg = (
            "The AI analysis service is temporarily unavailable, but the following project risks were automatically detected:\n"
        )
        for flag in risk_flags:
            fallback_msg += f"  ✗  {flag}\n"
        fallback_msg += "Please review these items with the project team."
        return fallback_msg


def _format_milestones(milestones: list) -> str:
    """Formats milestone list for inclusion in the prompt."""
    if not milestones:
        return "No milestones defined."
    lines = [
        f"- {m.title}: due {m.due_date}, status {m.status}, {m.story_points} story points"
        for m in milestones
    ]
    return "\n".join(lines)
