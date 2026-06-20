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
    """For every active employee profile: ALLOCATED if active allocations exist, else BENCH."""
    from app.models.employee import Employee, EmployeeProfile
    from app.repositories import allocation_repository

    profiles = (
        db.query(EmployeeProfile)
        .join(Employee)
        .filter(Employee.is_active == True)
        .all()
    )
    for profile in profiles:
        active_allocs = allocation_repository.get_active_allocations_for_employee(db, profile.id)
        # Status is derived — if you add a status column to Employee later, update it here


def _flag_missed_timesheets(db: Session) -> None:
    """
    For each past complete week, for every employee profile with an active allocation,
    if no timesheet row exists — insert a MISSED row so the history is complete.
    Escalates reminders and freezes accounts for missing timesheets.
    """
    from datetime import date, timedelta
    from app.models.employee import Employee, EmployeeProfile
    from app.models.timesheet import Timesheet
    from app.services.timesheet_service import get_active_allocations_for_week
    from app.models.enums import TimesheetStatus

    today = date.today()
    profiles = (
        db.query(EmployeeProfile)
        .join(Employee)
        .filter(Employee.is_active == True)
        .all()
    )

    for profile in profiles:
        last_monday = today - timedelta(days=today.weekday() + 7)
        allocations = get_active_allocations_for_week(db, profile.id, last_monday)

        for allocation in allocations:
            from app.repositories.timesheet_repository import get_timesheet_for_week
            from app.services.email_service import send_timesheet_reminder, send_account_frozen_notice
            
            existing = get_timesheet_for_week(db, profile.id, allocation.project_id, last_monday)
            if existing is None:
                missed_row = Timesheet(
                    employee_id  = profile.id,
                    project_id   = allocation.project_id,
                    week_start   = last_monday,
                    hours_worked = 0,
                    status       = TimesheetStatus.MISSED,
                    reminder_count = 1
                )
                db.add(missed_row)
                db.commit()
                # Send Reminder 1
                send_timesheet_reminder(profile.employee.email, profile.employee.full_name, 1)
            elif existing.status == TimesheetStatus.MISSED:
                if existing.reminder_count == 1:
                    existing.reminder_count = 2
                    db.commit()
                    # Send Reminder 2
                    send_timesheet_reminder(profile.employee.email, profile.employee.full_name, 2)
                elif existing.reminder_count == 2:
                    existing.reminder_count = 3
                    profile.timesheet_frozen = True
                    db.commit()
                    # Send Freeze Notice
                    mgr_email = profile.manager.employee.email if profile.manager else "admin@company.com"
                    send_account_frozen_notice(profile.employee.email, mgr_email, profile.employee.full_name)


def _update_all_project_health(db: Session) -> None:
    """Updates health_status for every ACTIVE project and sends At-Risk notices."""
    from app.services.project_health_service import compute_health_for_project
    from app.repositories import project_repository
    from app.models.enums import ProjectStatus, ProjectHealthStatus
    from app.services.ai_risk_summarizer import generate_risk_summary
    from app.services.ai_skill_matcher import find_best_matches
    from app.services.email_service import send_project_at_risk_notice
    
    active_projects = (
        db.query(project_repository.Project)
        .filter(project_repository.Project.status == ProjectStatus.ACTIVE)
        .all()
    )
    for project in active_projects:
        old_status = project.health_status
        new_status = compute_health_for_project(db, project.id)
        
        if old_status != new_status:
            project_repository.update_project_fields(db, project.id, {"health_status": new_status})
            
            if new_status == ProjectHealthStatus.AT_RISK:
                # Generate AI Summary and Suggest Help
                try:
                    risk_summary = generate_risk_summary(db, project.id)
                    requirement = f"We need an employee to help mitigate risks for the delayed project: {project.name}. Looking for someone with matching skills to the current project members."
                    suggested_help_data = find_best_matches(db, requirement, project.manager_id)
                    
                    help_lines = []
                    if suggested_help_data and "matches" in suggested_help_data:
                        for match in suggested_help_data["matches"]:
                            help_lines.append(f"- {match.get('name')} ({match.get('role')}): {match.get('reason')}")
                    suggested_help = "\n".join(help_lines) if help_lines else "No immediate suggestions available."
                    
                    project_details = f"Name: {project.name}\nManager ID: {project.manager_id}"
                    pm_email = project.manager.email if project.manager else "admin@company.com"
                    
                    send_project_at_risk_notice(pm_email, project_details, "AT_RISK", risk_summary, suggested_help)
                except Exception as e:
                    print(f"Error generating AT_RISK notice for project {project.id}: {e}")


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
