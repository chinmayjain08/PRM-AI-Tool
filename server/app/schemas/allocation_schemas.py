from datetime import date
from pydantic import BaseModel


class AllocationResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    project_id: int
    project_name: str
    max_hours: int
    utilisation_percent: int
    from_date: date
    to_date: date
    is_active: bool

    class Config:
        from_attributes = True


class AllocationCreate(BaseModel):
    employee_id: int
    project_id: int
    utilisation_percent: int
    from_date: date
    to_date: date

