"""
Employee management business rules.
Calls repositories for data — does not write SQL directly.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.repositories import employee_repository, allocation_repository, user_repository


def get_all_employees(db: Session, filters: dict) -> list:
    """Returns all employees. Each item includes current utilisation %."""
    employees = employee_repository.get_all_employees(
        db,
        status_filter=filters.get("status"),
        dept_filter=filters.get("department"),
    )
    enriched = [_enrich_with_utilisation(db, emp) for emp in employees]
    
    status_filter = filters.get("status")
    if status_filter == "BENCH":
        enriched = [e for e in enriched if e["current_utilisation_percent"] == 0]
    elif status_filter == "ALLOCATED":
        enriched = [e for e in enriched if e["current_utilisation_percent"] > 0]
        
    return enriched


def get_employee_detail(db: Session, employee_id: int) -> dict:
    """Returns full employee profile including skills and active allocations."""
    employee = employee_repository.get_employee_by_id(db, employee_id)
    if employee is None:
        raise ValueError(f"Employee with ID {employee_id} not found")
    return _enrich_with_utilisation(db, employee)


def deactivate_employee(db: Session, employee_id: int) -> None:
    """
    Deactivates the employee record, ends all active allocations today,
    and blocks the linked user account.
    All historical data is preserved (soft delete only).
    """
    employee = employee_repository.get_employee_by_id(db, employee_id)
    if employee is None:
        raise ValueError(f"Employee with ID {employee_id} not found")

    allocation_repository.end_all_allocations_for_employee(db, employee_id, date.today())
    employee_repository.set_employee_active(db, employee_id, False)
    user_repository.set_user_active_status(db, employee.user_id, False)


def _enrich_with_utilisation(db: Session, employee) -> dict:
    """Adds current_utilisation_percent to the employee data dict."""
    allocations   = allocation_repository.get_active_allocations_for_employee(db, employee.id)
    total_util    = sum(a.utilisation_percent for a in allocations)
    employee_dict = {c.name: getattr(employee, c.name) for c in employee.__table__.columns}
    employee_dict["current_utilisation_percent"] = total_util
    employee_dict["status"] = "ALLOCATED" if total_util > 0 else "BENCH"
    return employee_dict
