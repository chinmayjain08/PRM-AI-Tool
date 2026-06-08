from datetime import date
from sqlalchemy.orm import Session
from app.models.allocation import Allocation


def get_all_allocations(
    db: Session,
    employee_id_filter: int = None,
    project_id_filter: int = None,
) -> list[Allocation]:
    query = db.query(Allocation).filter(Allocation.is_active == True)
    if employee_id_filter:
        query = query.filter(Allocation.employee_id == employee_id_filter)
    if project_id_filter:
        query = query.filter(Allocation.project_id == project_id_filter)
    return query.all()


def get_active_allocations_for_employee(db: Session, employee_id: int) -> list[Allocation]:
    return (
        db.query(Allocation)
        .filter(Allocation.employee_id == employee_id, Allocation.is_active == True)
        .all()
    )


def get_overlapping_allocations(
    db: Session,
    employee_id: int,
    from_date: date,
    to_date: date,
) -> list[Allocation]:
    """Returns active allocations for the employee that overlap with the given date range."""
    return (
        db.query(Allocation)
        .filter(
            Allocation.employee_id == employee_id,
            Allocation.is_active   == True,
            Allocation.from_date   <= to_date,
            Allocation.to_date     >= from_date,
        )
        .all()
    )


def end_all_allocations_for_employee(db: Session, employee_id: int, end_date: date) -> None:
    db.query(Allocation).filter(
        Allocation.employee_id == employee_id,
        Allocation.is_active   == True,
    ).update({"is_active": False, "to_date": end_date})
    db.commit()
