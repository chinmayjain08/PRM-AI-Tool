from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_employee
from app.models.user import User
from app.repositories import allocation_repository, employee_repository
from app.services import timesheet_service
from app.schemas.timesheet_schemas import TimesheetSubmission

router = APIRouter(dependencies=[Depends(require_employee)])


@router.get("/allocations")
def get_my_allocations(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_employee),
):
    """Returns the logged-in employee's own allocation history."""
    employee = employee_repository.get_employee_by_user_id(db, current_user.id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return allocation_repository.get_active_allocations_for_employee(db, employee.id)


@router.get("/active-allocations")
def get_active_allocations_for_week(
    week_start:   str    = None,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_employee),
):
    """Returns projects the employee should log time for during the given week."""
    employee = employee_repository.get_employee_by_user_id(db, current_user.id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    resolved_week = _resolve_week_start(week_start)
    return timesheet_service.get_active_allocations_for_week(db, employee.id, resolved_week)


@router.get("/timesheets")
def get_my_timesheet_history(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_employee),
):
    """Returns full timesheet history with SUBMITTED and MISSED weeks."""
    employee = employee_repository.get_employee_by_user_id(db, current_user.id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return timesheet_service.get_timesheet_history(db, employee.id)


@router.get("/timesheets/{week_start}")
def get_week_detail(
    week_start:   str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_employee),
):
    """Returns detailed timesheet for one week — project rows + hours + tags."""
    employee  = employee_repository.get_employee_by_user_id(db, current_user.id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    try:
        week_date = date.fromisoformat(week_start)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format YYYY-MM-DD")
    return timesheet_service.get_week_detail(db, employee.id, week_date)


@router.post("/timesheets", status_code=status.HTTP_201_CREATED)
def submit_timesheet(
    submission:   TimesheetSubmission,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_employee),
):
    """
    Submits timesheet entries for the given week.
    Body: { "week_start": "YYYY-MM-DD", "entries": [{"project_id", "hours_worked", "tags"}] }
    """
    employee = employee_repository.get_employee_by_user_id(db, current_user.id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")

    try:
        entries_dict = [
            {"project_id": e.project_id, "hours_worked": e.hours_worked, "tags": e.tags}
            for e in submission.entries
        ]
        timesheet_service.submit_timesheet(db, employee.id, submission.week_start, entries_dict)
        return {"message": "Timesheet submitted successfully. Status: SUBMITTED \u2713"}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/missed-weeks")
def get_missed_weeks(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_employee),
):
    """Returns list of past week_start dates where the employee missed a submission."""
    employee = employee_repository.get_employee_by_user_id(db, current_user.id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    missed   = timesheet_service.get_missed_weeks(db, employee.id)
    return {"missed_weeks": [str(w) for w in missed]}


# ── Private helper ─────────────────────────────────────────────────────────────

def _resolve_week_start(week_start_str: str | None) -> date:
    if week_start_str:
        return date.fromisoformat(week_start_str)
    today = date.today()
    return today - timedelta(days=today.weekday())   # last Monday
