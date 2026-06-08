from datetime import date
from pydantic import BaseModel


class EmployeeUpdate(BaseModel):
    department: str | None = None
    joined_at: date | None = None


class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    department: str | None
    manager_id: int | None
    is_active: bool
    joined_at: date | None
    current_utilisation_percent: int | None = None
    status: str | None = None  # ALLOCATED | BENCH

    class Config:
        from_attributes = True


class AssignManagerRequest(BaseModel):
    employee_user_id: int
    manager_user_id: int


class SkillAddRequest(BaseModel):
    skill_name: str
    category: str
    proficiency: str


class ProficiencyUpdateRequest(BaseModel):
    proficiency: str
