"""
FastAPI dependency functions.
These are injected into route handlers — never called directly.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.employee import Employee
from app.repositories import employee_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    """Yields a database session. Closes it after the request completes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Employee:
    """Decodes the JWT and returns the matching Employee credentials from the database."""
    try:
        payload  = decode_token(token)
        username = payload.get("sub")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = employee_repository.get_employee_by_username(db, username)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_permission(permission_name: str):
    """Factory dependency to enforce dynamic, permission-based access control."""
    def dependency(current_user: Employee = Depends(get_current_user)) -> Employee:
        if not current_user.role or not any(p.name == permission_name for p in current_user.role.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required"
            )
        return current_user
    return dependency


def require_admin(current_user: Employee = Depends(get_current_user)) -> Employee:
    """Raises HTTP 403 if the logged-in user is not an ADMIN."""
    if not current_user.role or current_user.role.name != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_manager(current_user: Employee = Depends(get_current_user)) -> Employee:
    """Raises HTTP 403 if the logged-in user is not a MANAGER."""
    if not current_user.role or current_user.role.name != "MANAGER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")
    return current_user


def require_employee(current_user: Employee = Depends(get_current_user)) -> Employee:
    """Raises HTTP 403 if the logged-in user is not a RESOURCE."""
    if not current_user.role or current_user.role.name != "RESOURCE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee/Resource access required")
    return current_user
