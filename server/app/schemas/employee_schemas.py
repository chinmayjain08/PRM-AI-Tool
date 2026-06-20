from datetime import date
from pydantic import BaseModel
from app.models.enums import ProficiencyLevel


class EmployeeUpdate(BaseModel):
    department: str | None = None
    joined_at: date | None = None


class UserNestedResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    department: str | None
    manager_id: int | None
    is_active: bool
    joined_at: date | None
    current_utilisation_percent: int | None = None
    status: str | None = None  # ALLOCATED | BENCH
    full_name: str | None = None
    email: str | None = None
    user: UserNestedResponse | None = None

    class Config:
        from_attributes = True


class AssignManagerRequest(BaseModel):
    employee_user_id: int
    manager_user_id: int


class SkillAddRequest(BaseModel):
    skill_name: str
    category: str
    proficiency: ProficiencyLevel


class ProficiencyUpdateRequest(BaseModel):
    proficiency: ProficiencyLevel

