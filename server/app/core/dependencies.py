"""
FastAPI dependency functions.
These are injected into route handlers — never called directly.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.repositories import user_repository


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
) -> User:
    """Decodes the JWT and returns the matching User from the database."""
    try:
        payload  = decode_token(token)
        username = payload.get("sub")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = user_repository.get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raises HTTP 403 if the logged-in user is not an ADMIN."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """Raises HTTP 403 if the logged-in user is not a MANAGER."""
    if current_user.role != "MANAGER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")
    return current_user


def require_employee(current_user: User = Depends(get_current_user)) -> User:
    """Raises HTTP 403 if the logged-in user is not an EMPLOYEE."""
    if current_user.role != "EMPLOYEE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee access required")
    return current_user
