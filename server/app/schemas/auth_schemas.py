from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token:          str
    role:                  str
    full_name:             str
    force_password_change: bool


class ChangePasswordRequest(BaseModel):
    new_password:     str
    confirm_password: str


class MessageResponse(BaseModel):
    """Generic response for operations that only return a status message."""
    message: str
