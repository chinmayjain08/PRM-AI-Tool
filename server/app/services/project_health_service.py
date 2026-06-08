"""
Computes project health status (ON_TRACK / ATTENTION / AT_RISK).
All thresholds use named constants from config — no magic numbers.
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import project_repository, allocation_repository, timesheet_repository


def compute_health_for_project(db: Session, project_id: int) -> str:
    """
    Returns "ON_TRACK", "ATTENTION", or "AT_RISK" for the given project.
    AT_RISK is checked first; if true, ATTENTION is skipped.
    """
    if _has_at_risk_conditions(db, project_id):
        return "AT_RISK"
    if _has_attention_conditions(db, project_id):
        return "ATTENTION"
    return "ON_TRACK"


def collect_risk_flags(db: Session, project_id: int) -> list[str]:
    """Returns a list of human-readable risk descriptions for the project."""
    flags     = []
    today     = date.today()
    project   = project_repository.get_project_by_id(db, project_id)
    milestones = project_repository.get_milestones_for_project(db, project_id)

    for milestone in milestones:
        if milestone.status != "DONE" and milestone.due_date and milestone.due_date < today:
            days_overdue = (today - milestone.due_date).days
            flags.append(f"{milestone.title} milestone is {days_overdue} day(s) overdue")

    for flag in _get_low_effort_flags(db, project_id):
        flags.append(flag)

    return flags


def update_all_project_health_statuses(db: Session) -> None:
    """Called by background scheduler. Updates health_status for every ACTIVE project."""
    active_projects = (
        db.query(project_repository.Project)
        .filter(project_repository.Project.status == "ACTIVE")
        .all()
    )
    for project in active_projects:
        new_status = compute_health_for_project(db, project.id)
        project_repository.update_project_fields(db, project.id, {"health_status": new_status})


def _has_at_risk_conditions(db: Session, project_id: int) -> bool:
    today      = date.today()
    milestones = project_repository.get_milestones_for_project(db, project_id)

    for milestone in milestones:
        if milestone.status != "DONE" and milestone.due_date and milestone.due_date < today:
            return True

    return bool(_get_low_effort_flags(db, project_id))


def _has_attention_conditions(db: Session, project_id: int) -> bool:
    today     = date.today()
    project   = project_repository.get_project_by_id(db, project_id)
    threshold = timedelta(days=settings.ATTENTION_DAYS_BEFORE_DEADLINE)

    if not project or not project.end_date:
        return False

    deadline_approaching = project.end_date - today <= threshold
    milestones           = project_repository.get_milestones_for_project(db, project_id)
    done_pts             = sum(m.story_points for m in milestones if m.status == "DONE")
    total_pts            = project.total_story_pts or 1   # avoid divide by zero
    below_half_done      = done_pts < (total_pts / 2)

    return deadline_approaching and below_half_done


def _get_low_effort_flags(db: Session, project_id: int) -> list[str]:
    """Returns flags for employees who logged less than the expected effort last week."""
    flags         = []
    last_monday   = _get_last_monday()
    allocations   = allocation_repository.get_all_allocations(db, project_id_filter=project_id)
    max_hours     = _load_max_weekly_hours(db)

    for allocation in allocations:
        expected_hours = (allocation.utilisation_percent * max_hours) / 100
        threshold      = expected_hours * (settings.LOW_EFFORT_THRESHOLD_PERCENT / 100)
        logged_hours   = timesheet_repository.get_hours_for_employee_week(
            db, allocation.employee_id, allocation.project_id, last_monday
        )
        if logged_hours < threshold:
            flags.append(
                f"Employee ID {allocation.employee_id} logged only {logged_hours}h "
                f"(expected \u2265 {threshold:.0f}h) last week"
            )
    return flags


def _get_last_monday() -> date:
    today  = date.today()
    offset = today.weekday()   # Monday = 0
    return today - timedelta(days=offset + 7)


def _load_max_weekly_hours(db: Session) -> int:
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    return config.max_weekly_hours if config else settings.DEFAULT_MAX_WEEKLY_HOURS
