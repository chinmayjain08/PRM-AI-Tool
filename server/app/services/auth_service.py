"""
Authentication business rules.
No SQL here — calls user_repository for data.
No HTTP here — raises ValueError; the route layer converts to HTTP responses.
"""

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories import user_repository


def login(db, username: str, password: str) -> dict:
    """
    Validates credentials and returns login data.
    Raises ValueError on any failure (wrong password, inactive user, not found).
    """
    user = user_repository.get_user_by_username(db, username)

    if user is None or not user.is_active:
        raise ValueError("Invalid username or password")

    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid username or password")

    token = create_access_token({"sub": user.username, "role": user.role})

    return {
        "access_token":         token,
        "role":                 user.role,
        "full_name":            user.full_name,
        "force_password_change": user.force_password_change,
    }


def change_password(db, user_id: int, new_password: str) -> None:
    """
    Validates strength, hashes the new password, and clears the
    force_password_change flag.
    """
    validate_password_strength(new_password)
    hashed = hash_password(new_password)
    user_repository.update_user_password(db, user_id, hashed)
    user_repository.set_force_password_change(db, user_id, False)


def validate_password_strength(password: str) -> None:
    """
    Raises ValueError with a clear message if the password does not meet rules.
    Rules come from named constants — not hardcoded numbers.
    """
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long")

    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number")
