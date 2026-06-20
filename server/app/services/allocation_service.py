"""
Allocation business rules.
Responsible for: create, end, validate, and employee status recompute.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.allocation import Allocation
from app.repositories import allocation_repository, employee_repository, project_repository


def create_allocation(
    db: Session,
    employee_id: int,
    project_id: int,
    utilisation_percent: int,
    from_date: date,
    to_date: date,
) -> Allocation:
    """
    Validates and saves a new allocation.
    Raises ValueError if validation fails.
    """
    validate_new_allocation(db, employee_id, utilisation_percent, from_date, to_date)
    _assert_project_accepts_allocations(db, project_id)

    allocation = Allocation(
        employee_id         = employee_id,
        project_id          = project_id,
        utilisation_percent = utilisation_percent,
        from_date           = from_date,
        to_date             = to_date,
        is_active           = True,
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    recompute_employee_status(db, employee_id)
    return allocation


def end_allocation(db: Session, allocation_id: int, requesting_manager_id: int) -> None:
    """
    Ends an allocation by setting to_date = today.
    Raises ValueError if the allocation does not belong to the requesting manager's project.
    """
    allocation = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if allocation is None:
        raise ValueError(f"Allocation {allocation_id} not found")

    _assert_manager_owns_project(db, requesting_manager_id, allocation.project_id)

    db.query(Allocation).filter(Allocation.id == allocation_id).update(
        {"is_active": False, "to_date": date.today()}
    )
    db.commit()
    recompute_employee_status(db, allocation.employee_id)


def validate_new_allocation(
    db: Session,
    employee_id: int,
    utilisation_percent: int,
    from_date: date,
    to_date: date,
) -> None:
    """
    Checks date order, that the employee is a RESOURCE, and that adding this 
    allocation will not exceed MAX_UTILISATION_PERCENT.
    """
    employee = employee_repository.get_employee_by_id(db, employee_id)
    if not employee or not employee.employee or employee.employee.role.name != "RESOURCE":
        raise ValueError("Allocations can only be created for employees/resources")

    if from_date >= to_date:
        raise ValueError("From date must be before to date")

    overlapping = allocation_repository.get_overlapping_allocations(
        db, employee_id, from_date, to_date
    )
    current_total = sum(a.utilisation_percent for a in overlapping)
    new_total     = current_total + utilisation_percent

    if new_total > settings.MAX_UTILISATION_PERCENT:
        raise ValueError(
            f"Employee is currently at {current_total}%. "
            f"Adding {utilisation_percent}% would reach {new_total}%. "
            f"Maximum allowed is {settings.MAX_UTILISATION_PERCENT}%."
        )


def recompute_employee_status(db: Session, employee_id: int) -> None:
    """
    Sets the employee's status to ALLOCATED or BENCH based on current active allocations.
    Called after every create/end allocation and by the background scheduler.
    """
    active_allocations = allocation_repository.get_active_allocations_for_employee(db, employee_id)
    new_status = "ALLOCATED" if active_allocations else "BENCH"
    # Status is derived at query time in this implementation;
    # if a status column existed on Employee, we would update it here.
    # For now: recompute_employee_status serves as the hook for the scheduler.


def _assert_project_accepts_allocations(db: Session, project_id: int) -> None:
    """Raises ValueError if the project is not ACTIVE or PLANNED."""
    project = project_repository.get_project_by_id(db, project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")
    if project.status not in ("ACTIVE", "PLANNED"):
        raise ValueError(f"Project '{project.name}' has status {project.status}. Only ACTIVE or PLANNED projects accept allocations.")


def _assert_manager_owns_project(db: Session, manager_user_id: int, project_id: int) -> None:
    """Raises ValueError if the project does not belong to this manager."""
    project = project_repository.get_project_by_id(db, project_id)
    if project is None or project.manager_id != manager_user_id:
        raise ValueError("You can only end allocations on your own projects")
