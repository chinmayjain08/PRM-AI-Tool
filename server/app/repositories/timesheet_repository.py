from datetime import date
from sqlalchemy.orm import Session
from app.models.timesheet import Timesheet


def get_team_timesheets_for_week(db: Session, employee_ids: list[int], week_start: date) -> list[Timesheet]:
    return (
        db.query(Timesheet)
        .filter(Timesheet.employee_id.in_(employee_ids), Timesheet.week_start == week_start)
        .all()
    )


def get_hours_for_employee_week(
    db: Session,
    employee_id: int,
    project_id: int,
    week_start: date,
) -> int:
    row = (
        db.query(Timesheet)
        .filter(
            Timesheet.employee_id == employee_id,
            Timesheet.project_id  == project_id,
            Timesheet.week_start  == week_start,
        )
        .first()
    )
    return row.hours_worked if row else 0
