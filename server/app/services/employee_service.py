"""
Employee and account management business rules.
Calls repositories for data — does not write SQL directly.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import employee_repository, allocation_repository
from app.models.employee import Employee, EmployeeProfile
from app.models.role import Role


def create_employee(
    db: Session,
    full_name: str,
    email: str,
    username: str,
    temp_password: str,
    role_name: str,
    department: str,
) -> Employee:
    """
    Creates a new Employee credentials account and automatically creates
    the linked EmployeeProfile record.
    """
    from app.services.auth_service import validate_password_strength
    from app.core.security import hash_password

    validate_password_strength(temp_password)
    _assert_username_is_unique(db, username)
    _assert_email_is_unique(db, email)

    target_role = "RESOURCE" if role_name == "EMPLOYEE" else role_name
    role = db.query(Role).filter(Role.name == target_role).first()
    if not role:
        raise ValueError(f"Role '{role_name}' does not exist")

    dept = department.upper()
    if dept not in ["ENGINEERING", "DELIVERY", "HR", "FINANCE", "OPERATIONS"]:
        raise ValueError("Invalid department name")

    emp = Employee(
        full_name             = full_name,
        email                 = email,
        username              = username,
        hashed_password       = hash_password(temp_password),
        role_id               = role.id,
        is_active             = True,
        force_password_change = True,
    )
    saved_emp = employee_repository.save_new_employee(db, emp)

    employee_repository.create_employee(db, saved_emp.id, department=dept, joined_at=date.today())

    return saved_emp


def reset_employee_password(db: Session, employee_id: int, temp_password: str) -> None:
    """Sets a new temporary password and forces change on next login."""
    from app.services.auth_service import validate_password_strength
    from app.core.security import hash_password

    validate_password_strength(temp_password)
    hashed = hash_password(temp_password)
    employee_repository.update_employee_password(db, employee_id, hashed)
    employee_repository.set_employee_force_password_change(db, employee_id, True)


def deactivate_employee_account(db: Session, employee_id: int) -> None:
    """Deactivates login account and ends allocations for associated profile."""
    employee_repository.set_employee_active_status(db, employee_id, False)
    profile = employee_repository.get_employee_by_user_id(db, employee_id)
    if profile:
        allocation_repository.end_all_allocations_for_employee(db, profile.id, date.today())


def reactivate_employee_account(db: Session, employee_id: int) -> None:
    """Re-enables login account."""
    employee_repository.set_employee_active_status(db, employee_id, True)


def get_all_employees(db: Session, filters: dict) -> list:
    """Returns all employee profiles with current utilisation percentage enriched."""
    profiles = employee_repository.get_all_employees(
        db,
        status_filter=filters.get("status"),
        dept_filter=filters.get("department"),
    )
    enriched = [_enrich_with_utilisation(db, prof) for prof in profiles]
    
    status_filter = filters.get("status")
    if status_filter == "BENCH":
        enriched = [e for e in enriched if e["current_utilisation_percent"] == 0]
    elif status_filter == "ALLOCATED":
        enriched = [e for e in enriched if e["current_utilisation_percent"] > 0]
        
    return enriched


def get_employee_detail(db: Session, employee_profile_id: int) -> dict:
    """Returns full employee profile details."""
    profile = employee_repository.get_employee_by_id(db, employee_profile_id)
    if profile is None:
        raise ValueError(f"Employee with profile ID {employee_profile_id} not found")
    return _enrich_with_utilisation(db, profile)


def deactivate_employee(db: Session, employee_profile_id: int) -> None:
    """Deactivates profile and associated login account, ending all allocations today."""
    profile = employee_repository.get_employee_by_id(db, employee_profile_id)
    if profile is None:
        raise ValueError(f"Employee with profile ID {employee_profile_id} not found")

    allocation_repository.end_all_allocations_for_employee(db, employee_profile_id, date.today())
    employee_repository.set_employee_active(db, employee_profile_id, False)
    employee_repository.set_employee_active_status(db, profile.employee_id, False)


def _enrich_with_utilisation(db: Session, profile: EmployeeProfile) -> dict:
    """Converts profile record into a frontend response dict with active utilization."""
    allocations   = allocation_repository.get_active_allocations_for_employee(db, profile.id)
    total_util    = sum(a.utilisation_percent for a in allocations)
    
    emp = profile.employee
    role_name = emp.role.name if emp and emp.role else ""
    if role_name == "RESOURCE":
        role_name = "EMPLOYEE"
        
    user_dict = {
        "id": emp.id if emp else None,
        "username": emp.username if emp else "",
        "email": emp.email if emp else "",
        "full_name": emp.full_name if emp else "",
        "role": role_name,
    }
    
    return {
        "id":                          profile.id,
        "user_id":                     profile.employee_id,
        "department":                  profile.department,
        "manager_id":                  profile.manager_id,
        "joined_at":                   profile.joined_at,
        "is_active":                   emp.is_active if emp else False,
        "current_utilisation_percent": total_util,
        "status":                      "ALLOCATED" if total_util > 0 else "BENCH",
        "full_name":                   emp.full_name if emp else "",
        "email":                       emp.email if emp else "",
        "user":                        user_dict,
    }


def _assert_username_is_unique(db: Session, username: str) -> None:
    if employee_repository.get_employee_by_username(db, username) is not None:
        raise ValueError(f"Username '{username}' is already taken")


def _assert_email_is_unique(db: Session, email: str) -> None:
    if employee_repository.get_employee_by_email(db, email) is not None:
        raise ValueError(f"Email '{email}' is already registered")
