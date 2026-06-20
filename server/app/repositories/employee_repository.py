"""
All database queries related to Employee accounts (credentials) and EmployeeProfile records.
No business logic here — only SQL.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.models.employee import Employee, EmployeeProfile
from app.models.role import Role


# ── Credentials / Account Queries ─────────────────────────────────────────────

def get_employee_by_username(db: Session, username: str) -> Employee | None:
    return db.query(Employee).filter(Employee.username == username).first()


def get_employee_account_by_id(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employee_by_email(db: Session, email: str) -> Employee | None:
    return db.query(Employee).filter(Employee.email == email).first()


def get_all_employee_accounts(db: Session) -> list[Employee]:
    return db.query(Employee).order_by(Employee.id).all()


def update_employee_password(db: Session, employee_id: int, new_hashed_password: str) -> None:
    db.query(Employee).filter(Employee.id == employee_id).update({"hashed_password": new_hashed_password})
    db.commit()


def set_employee_force_password_change(db: Session, employee_id: int, value: bool) -> None:
    db.query(Employee).filter(Employee.id == employee_id).update({"force_password_change": value})
    db.commit()


def set_employee_active_status(db: Session, employee_id: int, is_active: bool) -> None:
    db.query(Employee).filter(Employee.id == employee_id).update({"is_active": is_active})
    db.commit()


def save_new_employee(db: Session, employee: Employee) -> Employee:
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


# ── Profile Queries ───────────────────────────────────────────────────────────

def get_all_employees(db: Session, status_filter: str = None, dept_filter: str = None, role_name_filter: str = None) -> list[EmployeeProfile]:
    query = db.query(EmployeeProfile).join(Employee)
    if status_filter == "BENCH":
        query = query.filter(Employee.is_active == True)
    if dept_filter:
        query = query.filter(EmployeeProfile.department == dept_filter)
    if role_name_filter:
        query = query.join(Role, Employee.role_id == Role.id).filter(Role.name == role_name_filter)
    return query.order_by(EmployeeProfile.id).all()


def get_employee_by_id(db: Session, employee_profile_id: int) -> EmployeeProfile | None:
    """Gets employee profile by the profile ID."""
    return db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()


def get_employee_by_user_id(db: Session, user_id: int) -> EmployeeProfile | None:
    """Gets employee profile by the credentials/Employee ID."""
    return db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == user_id).first()


def create_employee(db: Session, user_id: int, department: str, joined_at: date) -> EmployeeProfile:
    employee = EmployeeProfile(
        employee_id=user_id,
        department=department,
        joined_at=joined_at,
        manager_id=None
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee_fields(db: Session, employee_profile_id: int, fields: dict) -> EmployeeProfile | None:
    db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).update(fields)
    db.commit()
    return get_employee_by_id(db, employee_profile_id)


def set_employee_active(db: Session, employee_profile_id: int, is_active: bool) -> None:
    profile = get_employee_by_id(db, employee_profile_id)
    if profile:
        db.query(Employee).filter(Employee.id == profile.employee_id).update({"is_active": is_active})
        db.commit()


def assign_manager(db: Session, employee_user_id: int, manager_user_id: int | None) -> None:
    """Assigns manager profile to employee profile based on their credentials IDs."""
    emp_profile = db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == employee_user_id).first()
    if not emp_profile:
        return
    
    if manager_user_id:
        mgr_profile = db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == manager_user_id).first()
        if mgr_profile:
            emp_profile.manager_id = mgr_profile.id
    else:
        emp_profile.manager_id = None
        
    db.commit()


def get_employees_by_manager(db: Session, manager_user_id: int) -> list[EmployeeProfile]:
    """Returns all active employee profiles reporting to the manager identified by manager_user_id."""
    mgr_profile = db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == manager_user_id).first()
    if not mgr_profile:
        return []
    return (
        db.query(EmployeeProfile)
        .join(Employee)
        .filter(EmployeeProfile.manager_id == mgr_profile.id, Employee.is_active == True)
        .all()
    )
