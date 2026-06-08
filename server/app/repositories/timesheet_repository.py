"""
All SQL for timesheet and timesheet_tag tables.
No business logic here.
"""

from datetime import date
from sqlalchemy.orm import Session
from app.models.timesheet import Timesheet, TimesheetTag


def get_timesheet_for_week(
    db: Session,
    employee_id: int,
    project_id: int,
    week_start: date,
) -> Timesheet | None:
    return (
        db.query(Timesheet)
        .filter(
            Timesheet.employee_id == employee_id,
            Timesheet.project_id  == project_id,
            Timesheet.week_start  == week_start,
        )
        .first()
    )


def get_all_timesheets_for_employee(db: Session, employee_id: int) -> list[Timesheet]:
    return (
        db.query(Timesheet)
        .filter(Timesheet.employee_id == employee_id)
        .order_by(Timesheet.week_start.desc())
        .all()
    )


def get_timesheets_for_week(db: Session, employee_id: int, week_start: date) -> list[Timesheet]:
    return (
        db.query(Timesheet)
        .filter(Timesheet.employee_id == employee_id, Timesheet.week_start == week_start)
        .all()
    )


def save_timesheet(db: Session, timesheet: Timesheet) -> Timesheet:
    db.add(timesheet)
    db.commit()
    db.refresh(timesheet)
    return timesheet


def save_tags(db: Session, timesheet_id: int, tags: list[str]) -> None:
    for tag_text in tags:
        tag = TimesheetTag(timesheet_id=timesheet_id, tag=tag_text)
        db.add(tag)
    db.commit()


def get_tags_for_timesheet(db: Session, timesheet_id: int) -> list[TimesheetTag]:
    return db.query(TimesheetTag).filter(TimesheetTag.timesheet_id == timesheet_id).all()


def get_hours_for_employee_week(
    db: Session,
    employee_id: int,
    project_id: int,
    week_start: date,
) -> int:
    """Returns logged hours for one employee/project/week. Returns 0 if not found."""
    row = get_timesheet_for_week(db, employee_id, project_id, week_start)
    return row.hours_worked if row else 0


def get_team_timesheets_for_week(
    db: Session,
    employee_ids: list[int],
    week_start: date,
) -> list[Timesheet]:
    return (
        db.query(Timesheet)
        .filter(Timesheet.employee_id.in_(employee_ids), Timesheet.week_start == week_start)
        .all()
    )
