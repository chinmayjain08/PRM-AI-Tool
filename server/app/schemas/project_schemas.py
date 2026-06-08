from datetime import date
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "PLANNED"  # PLANNED | ACTIVE | ON_HOLD | COMPLETED
    manager_id: int
    total_story_pts: int = 0


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    manager_id: int | None = None
    total_story_pts: int | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    status: str
    manager_id: int | None
    total_story_pts: int
    health_status: str
    done_story_pts: int | None = None

    class Config:
        from_attributes = True


class MilestoneCreate(BaseModel):
    title: str
    due_date: date | None = None
    story_points: int = 0


class MilestoneUpdate(BaseModel):
    status: str  # NOT_STARTED | IN_PROGRESS | DONE


class MilestoneResponse(BaseModel):
    id: int
    project_id: int
    title: str
    due_date: date | None
    story_points: int
    status: str

    class Config:
        from_attributes = True


class ProjectDetailResponse(BaseModel):
    project: ProjectResponse
    milestones: list[MilestoneResponse]
    done_story_pts: int
    remaining_pts: int
