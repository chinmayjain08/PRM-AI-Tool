from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import ProjectStatus, ProjectHealthStatus, MilestoneStatus


class Project(Base):
    __tablename__ = "projects"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(150), nullable=False)
    description     = Column(Text)
    start_date      = Column(Date)
    end_date        = Column(Date)
    status          = Column(Enum(ProjectStatus, name="project_status", native_enum=True), default=ProjectStatus.PLANNED)
    manager_id      = Column(Integer, ForeignKey("employees.id"))
    total_story_pts = Column(Integer, default=0)
    health_status   = Column(Enum(ProjectHealthStatus, name="project_health_status", native_enum=True), default=ProjectHealthStatus.ON_TRACK)

    manager    = relationship("Employee")
    milestones = relationship("Milestone", back_populates="project")


class Milestone(Base):
    __tablename__ = "milestones"

    id           = Column(Integer, primary_key=True, index=True)
    project_id   = Column(Integer, ForeignKey("projects.id"))
    title        = Column(String(200), nullable=False)
    due_date     = Column(Date)
    story_points = Column(Integer, default=0)
    status       = Column(Enum(MilestoneStatus, name="milestone_status", native_enum=True), default=MilestoneStatus.NOT_STARTED)

    project = relationship("Project", back_populates="milestones")

