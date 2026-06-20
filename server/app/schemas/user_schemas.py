from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    username: str
    temp_password: str
    role: str  # ADMIN | MANAGER | EMPLOYEE
    department: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    force_password_change: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    temp_password: str
