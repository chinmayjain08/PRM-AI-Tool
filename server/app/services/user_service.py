"""
User account management business rules.
"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories import user_repository, employee_repository
from app.services.auth_service import validate_password_strength


def create_user(
    db: Session,
    full_name: str,
    email: str,
    username: str,
    temp_password: str,
    role: str,
) -> User:
    """
    Creates a new user account. Validates password strength and uniqueness.
    If the role is EMPLOYEE, also creates the linked Employee record.
    """
    validate_password_strength(temp_password)
    _assert_username_is_unique(db, username)
    _assert_email_is_unique(db, email)

    user = User(
        full_name             = full_name,
        email                 = email,
        username              = username,
        hashed_password       = hash_password(temp_password),
        role                  = role,
        is_active             = True,
        force_password_change = True,
    )
    saved_user = user_repository.save_new_user(db, user)

    if role == "EMPLOYEE":
        from datetime import date
        employee_repository.create_employee(db, saved_user.id, department="Other", joined_at=date.today())

    return saved_user


def reset_user_password(db: Session, user_id: int, temp_password: str) -> None:
    """Sets a new temporary password and forces change on next login."""
    validate_password_strength(temp_password)
    hashed = hash_password(temp_password)
    user_repository.update_user_password(db, user_id, hashed)
    user_repository.set_force_password_change(db, user_id, True)


def deactivate_user(db: Session, user_id: int) -> None:
    """Blocks login. Data is preserved. Also deactivates employee if user is an employee."""
    user = user_repository.get_user_by_id(db, user_id)
    if user:
        user_repository.set_user_active_status(db, user_id, False)
        emp = employee_repository.get_employee_by_user_id(db, user_id)
        if emp:
            from datetime import date
            from app.repositories import allocation_repository
            allocation_repository.end_all_allocations_for_employee(db, emp.id, date.today())
            employee_repository.set_employee_active(db, emp.id, False)


def reactivate_user(db: Session, user_id: int) -> None:
    """Re-enables login. Previous allocations are NOT restored (BRD rule)."""
    user_repository.set_user_active_status(db, user_id, True)
    user = user_repository.get_user_by_id(db, user_id)
    if user and user.role == "EMPLOYEE":
        emp = employee_repository.get_employee_by_user_id(db, user_id)
        if emp:
            employee_repository.set_employee_active(db, emp.id, True)


def _assert_username_is_unique(db: Session, username: str) -> None:
    if user_repository.get_user_by_username(db, username) is not None:
        raise ValueError(f"Username '{username}' is already taken")


def _assert_email_is_unique(db: Session, email: str) -> None:
    if user_repository.get_user_by_email(db, email) is not None:
        raise ValueError(f"Email '{email}' is already registered")
