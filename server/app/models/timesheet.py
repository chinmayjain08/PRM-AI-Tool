from sqlalchemy import Column, Integer, Date, String, DateTime, ForeignKey, UniqueConstraint, func, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import TimesheetStatus


class Timesheet(Base):
    __tablename__ = "timesheets"
    __table_args__ = (
        UniqueConstraint("employee_id", "project_id", "week_start", name="uq_timesheet_per_week"),
    )

    id           = Column(Integer, primary_key=True, index=True)
    employee_id  = Column(Integer, ForeignKey("employee_profiles.id"))
    project_id   = Column(Integer, ForeignKey("projects.id"))
    week_start   = Column(Date, nullable=False)             # Always a Monday
    hours_worked = Column(Integer, nullable=False)
    status         = Column(Enum(TimesheetStatus, name="timesheet_status", native_enum=True), default=TimesheetStatus.SUBMITTED)
    reminder_count = Column(Integer, default=0)

    submitted_at = Column(DateTime, server_default=func.now())

    employee = relationship("EmployeeProfile", back_populates="timesheets")
    project  = relationship("Project")
    tags     = relationship("TimesheetTag", back_populates="timesheet")


class TimesheetTag(Base):
    __tablename__ = "timesheet_tags"

    id           = Column(Integer, primary_key=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id"))
    tag          = Column(String(100), nullable=False)

    timesheet = relationship("Timesheet", back_populates="tags")
