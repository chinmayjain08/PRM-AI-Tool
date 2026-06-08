"""
All database queries related to Employee records.
No business logic here — only SQL.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.models.employee import Employee


def get_all_employees(db: Session, status_filter: str = None, dept_filter: str = None) -> list[Employee]:
    query = db.query(Employee)
    if status_filter == "BENCH":
        query = query.filter(Employee.is_active == True)  # further filtered by allocation in service
    if dept_filter:
        query = query.filter(Employee.department == dept_filter)
    return query.order_by(Employee.id).all()


def get_employee_by_id(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employee_by_user_id(db: Session, user_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def create_employee(db: Session, user_id: int, department: str, joined_at: date) -> Employee:
    employee = Employee(user_id=user_id, department=department, joined_at=joined_at, is_active=True)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee_fields(db: Session, employee_id: int, fields: dict) -> Employee:
    db.query(Employee).filter(Employee.id == employee_id).update(fields)
    db.commit()
    return get_employee_by_id(db, employee_id)


def set_employee_active(db: Session, employee_id: int, is_active: bool) -> None:
    db.query(Employee).filter(Employee.id == employee_id).update({"is_active": is_active})
    db.commit()


def assign_manager(db: Session, employee_user_id: int, manager_user_id: int) -> None:
    db.query(Employee).filter(Employee.user_id == employee_user_id).update(
        {"manager_id": manager_user_id}
    )
    db.commit()
