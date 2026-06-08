"""
Background scheduler — runs periodic maintenance tasks.
Uses APScheduler with interval trigger.
Interval is loaded from system_config so Admin can change it at runtime.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


_scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    """Called from main.py lifespan. Starts the background scheduler."""
    interval_hours = _load_scheduler_interval()
    _scheduler.add_job(
        func    = run_all_scheduled_tasks,
        trigger = "interval",
        hours   = interval_hours,
        id      = "prm_maintenance_job",
    )
    _scheduler.start()
    print(f"Scheduler started. Runs every {interval_hours} hour(s).")


def run_all_scheduled_tasks() -> None:
    """
    Runs all maintenance tasks in order.
    Each task is a separate focused function — one job each.
    """
    db = SessionLocal()
    try:
        _recompute_all_employee_statuses(db)
        _flag_missed_timesheets(db)
        _update_all_project_health(db)
    finally:
        db.close()


def _recompute_all_employee_statuses(db: Session) -> None:
    """For every active employee: ALLOCATED if active allocations exist, else BENCH."""
    from app.models.employee import Employee
    from app.repositories import allocation_repository

    employees = db.query(Employee).filter(Employee.is_active == True).all()
    for employee in employees:
        active_allocs = allocation_repository.get_active_allocations_for_employee(db, employee.id)
        # Status is derived — if you add a status column to Employee later, update it here


def _flag_missed_timesheets(db: Session) -> None:
    """
    For each past complete week, for every employee with an active allocation,
    if no timesheet row exists — insert a MISSED row so the history is complete.
    """
    from datetime import date, timedelta
    from app.models.employee import Employee
    from app.models.timesheet import Timesheet
    from app.services.timesheet_service import get_active_allocations_for_week

    today = date.today()
    employees = db.query(Employee).filter(Employee.is_active == True).all()

    for employee in employees:
        last_monday = today - timedelta(days=today.weekday() + 7)
        allocations = get_active_allocations_for_week(db, employee.id, last_monday)

        for allocation in allocations:
            from app.repositories.timesheet_repository import get_timesheet_for_week
            existing = get_timesheet_for_week(db, employee.id, allocation.project_id, last_monday)
            if existing is None:
                missed_row = Timesheet(
                    employee_id  = employee.id,
                    project_id   = allocation.project_id,
                    week_start   = last_monday,
                    hours_worked = 0,
                    status       = "MISSED",
                )
                db.add(missed_row)
    db.commit()


def _update_all_project_health(db: Session) -> None:
    """Updates health_status for every ACTIVE project."""
    from app.services.project_health_service import update_all_project_health_statuses
    update_all_project_health_statuses(db)


def _load_scheduler_interval() -> int:
    """Reads interval from system_config table. Falls back to config default."""
    db = SessionLocal()
    try:
        from app.models.system_config import SystemConfig
        from app.core.config import settings
        config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        return config.scheduler_interval if config else settings.DEFAULT_SCHEDULER_INTERVAL_HOURS
    finally:
        db.close()
