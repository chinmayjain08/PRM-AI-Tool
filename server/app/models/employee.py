from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id                    = Column(Integer, primary_key=True, index=True)
    username              = Column(String(50), unique=True, nullable=False, index=True)
    email                 = Column(String(100), unique=True, nullable=False, index=True)
    full_name             = Column(String(100), nullable=False)
    hashed_password       = Column(String, nullable=False)
    role_id               = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active             = Column(Boolean, default=True)
    force_password_change = Column(Boolean, default=True)
    created_at            = Column(DateTime, server_default=func.now())

    # Relationships
    role                  = relationship("Role")
    profile               = relationship("EmployeeProfile", back_populates="employee", uselist=False, cascade="all, delete-orphan")


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), unique=True, nullable=False)
    department  = Column(String(50), nullable=False)
    manager_id  = Column(Integer, ForeignKey("employee_profiles.id"), nullable=True)
    joined_at        = Column(Date, nullable=False)
    timesheet_frozen = Column(Boolean, default=False)

    # Relationships
    employee    = relationship("Employee", back_populates="profile")
    manager     = relationship("EmployeeProfile", remote_side=[id])
    skills      = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="employee", cascade="all, delete-orphan")
    timesheets  = relationship("Timesheet", back_populates="employee", cascade="all, delete-orphan")
