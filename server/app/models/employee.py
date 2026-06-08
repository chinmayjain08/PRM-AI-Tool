from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), unique=True)
    department  = Column(String(50))
    manager_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active   = Column(Boolean, default=True)
    joined_at   = Column(Date)

    # Relationships
    user        = relationship("User", foreign_keys=[user_id])
    skills      = relationship("EmployeeSkill", back_populates="employee")
    allocations = relationship("Allocation", back_populates="employee")
    timesheets  = relationship("Timesheet", back_populates="employee")
