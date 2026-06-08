"""
Timesheet submission and history business rules.
All validation rules from BRD Section 5.1 are enforced here.
All thresholds use named constants — no magic numbers.
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.timesheet import Timesheet
from app.repositories import allocation_repository, timesheet_repository


def get_active_allocations_for_week(db: Session, employee_id: int, week_start: date) -> list:
    """Returns allocations the employee was active on during the given week."""
    week_end = week_start + timedelta(days=6)
    all_allocs = allocation_repository.get_active_allocations_for_employee(db, employee_id)
    return [
        a for a in all_allocs
        if a.from_date <= week_end and a.to_date >= week_start
    ]


def validate_timesheet_entry(
    db: Session,
    employee_id: int,
    project_id: int,
    week_start: date,
    hours_worked: int,
) -> None:
    """
    Raises ValueError with a clear message if any rule is violated.
    Rules (all from BRD Section 5.1):
      1. week_start must not be in the future
      2. Employee must be allocated to the project during that week
      3. hours_worked must be >= 0
      4. hours_worked must not exceed allocation% × max_weekly_hours / 100
      5. No duplicate submission for same employee + project + week
    """
    _assert_not_future_week(week_start)
    allocation = _get_allocation_for_entry(db, employee_id, project_id, week_start)
    _assert_hours_in_range(hours_worked, allocation)
    _assert_no_duplicate_submission(db, employee_id, project_id, week_start)


def submit_timesheet(
    db: Session,
    employee_id: int,
    week_start: date,
    entries: list[dict],
) -> None:
    """
    Validates each entry, validates total hours, then saves all rows and tags.
    Runs in a single transaction so all-or-nothing behaviour is maintained.
    """
    max_hours = _load_max_weekly_hours(db)

    for entry in entries:
        validate_timesheet_entry(
            db,
            employee_id,
            entry["project_id"],
            week_start,
            entry["hours_worked"],
        )

    total_hours = sum(e["hours_worked"] for e in entries)
    if total_hours > max_hours:
        raise ValueError(
            f"Total hours ({total_hours}) exceeds the maximum allowed per week ({max_hours})"
        )

    for entry in entries:
        _save_single_entry(db, employee_id, week_start, entry)


def get_timesheet_history(db: Session, employee_id: int) -> list[dict]:
    """
    Returns all past weeks. Each week has status SUBMITTED or MISSED.
    MISSED means the employee had an active allocation but did not submit.
    """
    submitted_rows = timesheet_repository.get_all_timesheets_for_employee(db, employee_id)
    missed_weeks   = get_missed_weeks(db, employee_id)

    # To group timesheet entries for the same week into a single history entry
    weeks_submitted = {}
    for row in submitted_rows:
        w_start = row.week_start
        weeks_submitted[w_start] = weeks_submitted.get(w_start, 0) + row.hours_worked

    history = []
    for w_start, hours in weeks_submitted.items():
        history.append({
            "week_start":   w_start,
            "hours_worked": hours,
            "status":       "SUBMITTED",
        })
        
    for missed_week in missed_weeks:
        # If the week is already in submitted list, don't flag as missed
        if missed_week not in weeks_submitted:
            history.append({
                "week_start":   missed_week,
                "hours_worked": 0,
                "status":       "MISSED",
            })

    return sorted(history, key=lambda x: x["week_start"], reverse=True)


def get_week_detail(db: Session, employee_id: int, week_start: date) -> dict:
    """Returns all timesheet rows for one week including activity tags."""
    rows = timesheet_repository.get_timesheets_for_week(db, employee_id, week_start)
    result = []
    for row in rows:
        tags = timesheet_repository.get_tags_for_timesheet(db, row.id)
        result.append({
            "project_id":   row.project_id,
            "project_name": row.project.name if row.project else f"Project {row.project_id}",
            "hours_worked": row.hours_worked,
            "tags":         [t.tag for t in tags],
        })
    return {"week_start": week_start, "entries": result}


def get_missed_weeks(db: Session, employee_id: int) -> list[date]:
    """
    Returns a list of past Mondays where the employee had an active allocation
    but did not submit a timesheet. Used for the ⚠ reminder on the employee menu.
    """
    missed = []
    today  = date.today()

    # Check the last 8 weeks to keep history manageable
    for weeks_ago in range(1, 9):
        week_start = _get_monday(today - timedelta(weeks=weeks_ago))
        allocations = get_active_allocations_for_week(db, employee_id, week_start)
        if not allocations:
            continue   # no allocation that week — skip, not a missed submission

        submissions = timesheet_repository.get_timesheets_for_week(db, employee_id, week_start)
        if not submissions:
            missed.append(week_start)

    return missed


# ── Private helpers ────────────────────────────────────────────────────────────

def _assert_not_future_week(week_start: date) -> None:
    today = date.today()
    if week_start > today:
        raise ValueError("Cannot submit a timesheet for a future week")


def _get_allocation_for_entry(db: Session, employee_id: int, project_id: int, week_start: date):
    week_end = week_start + timedelta(days=6)
    allocs   = allocation_repository.get_active_allocations_for_employee(db, employee_id)
    for alloc in allocs:
        if alloc.project_id == project_id and alloc.from_date <= week_end and alloc.to_date >= week_start:
            return alloc
    raise ValueError(f"You are not allocated to project ID {project_id} during the week of {week_start}")


def _assert_hours_in_range(hours_worked: int, allocation) -> None:
    if hours_worked < 0:
        raise ValueError("Hours worked cannot be negative")
    max_hours_for_project = _compute_max_project_hours(allocation)
    if hours_worked > max_hours_for_project:
        raise ValueError(
            f"Hours logged ({hours_worked}) exceeds the cap for this project. "
            f"Max is {max_hours_for_project} hrs ({allocation.utilisation_percent}% of weekly limit)."
        )


def _assert_no_duplicate_submission(
    db: Session,
    employee_id: int,
    project_id: int,
    week_start: date,
) -> None:
    existing = timesheet_repository.get_timesheet_for_week(db, employee_id, project_id, week_start)
    if existing is not None:
        raise ValueError(
            f"A timesheet for project ID {project_id} and week {week_start} has already been submitted"
        )


def _compute_max_project_hours(allocation) -> int:
    """Returns the maximum hours allowed for one project based on allocation %."""
    from app.core.config import settings
    return int(allocation.utilisation_percent * settings.DEFAULT_MAX_WEEKLY_HOURS / 100)


def _save_single_entry(db: Session, employee_id: int, week_start: date, entry: dict) -> None:
    timesheet = Timesheet(
        employee_id  = employee_id,
        project_id   = entry["project_id"],
        week_start   = week_start,
        hours_worked = entry["hours_worked"],
        status       = "SUBMITTED",
    )
    saved = timesheet_repository.save_timesheet(db, timesheet)
    timesheet_repository.save_tags(db, saved.id, entry.get("tags", []))


def _load_max_weekly_hours(db: Session) -> int:
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    return config.max_weekly_hours if config else settings.DEFAULT_MAX_WEEKLY_HOURS


def _get_monday(any_date: date) -> date:
    """Returns the Monday of the week containing any_date."""
    return any_date - timedelta(days=any_date.weekday())
