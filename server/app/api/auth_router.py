"""
Auth routes — thin HTTP layer only.
All business logic is in auth_service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.employee import Employee
from app.schemas.auth_schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Validates credentials and returns a JWT token."""
    try:
        return auth_service.login(db, body.username, body.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    body:         ChangePasswordRequest,
    db:           Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Changes password for the currently logged-in user."""
    if body.new_password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match",
        )
    try:
        auth_service.change_password(db, current_user.id, body.new_password)
        return {"message": "Password changed successfully"}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
