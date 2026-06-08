from datetime import date, datetime
from pydantic import BaseModel


class TimesheetTagResponse(BaseModel):
    id: int
    timesheet_id: int
    tag: str

    class Config:
        from_attributes = True


class TimesheetResponse(BaseModel):
    id: int
    employee_id: int
    project_id: int
    week_start: date
    hours_worked: int
    status: str
    submitted_at: datetime
    tags: list[TimesheetTagResponse] = []

    class Config:
        from_attributes = True


class TimesheetEntryCreate(BaseModel):
    project_id: int
    hours_worked: int
    tags: list[str] = []


class TimesheetSubmission(BaseModel):
    week_start: date
    entries: list[TimesheetEntryCreate]

