from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(150), nullable=False)
    description     = Column(Text)
    start_date      = Column(Date)
    end_date        = Column(Date)
    status          = Column(String(20), default="PLANNED")       # PLANNED|ACTIVE|ON_HOLD|COMPLETED
    manager_id      = Column(Integer, ForeignKey("users.id"))
    total_story_pts = Column(Integer, default=0)
    health_status   = Column(String(20), default="ON_TRACK")      # ON_TRACK|ATTENTION|AT_RISK

    manager    = relationship("User")
    milestones = relationship("Milestone", back_populates="project")


class Milestone(Base):
    __tablename__ = "milestones"

    id           = Column(Integer, primary_key=True, index=True)
    project_id   = Column(Integer, ForeignKey("projects.id"))
    title        = Column(String(200), nullable=False)
    due_date     = Column(Date)
    story_points = Column(Integer, default=0)
    status       = Column(String(20), default="NOT_STARTED")      # NOT_STARTED|IN_PROGRESS|DONE

    project = relationship("Project", back_populates="milestones")
