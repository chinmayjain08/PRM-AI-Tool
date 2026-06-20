from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id                  = Column(Integer, primary_key=True, index=True)
    employee_id         = Column(Integer, ForeignKey("employee_profiles.id"))
    project_id          = Column(Integer, ForeignKey("projects.id"))
    utilisation_percent = Column(Integer, nullable=False)    # 0 to 100
    from_date           = Column(Date, nullable=False)
    to_date             = Column(Date, nullable=False)
    is_active           = Column(Boolean, default=True)

    employee = relationship("EmployeeProfile", back_populates="allocations")
    project  = relationship("Project")

    @property
    def project_name(self) -> str:
        return self.project.name if self.project else f"Project {self.project_id}"

    @property
    def employee_name(self) -> str:
        return self.employee.employee.full_name if (self.employee and self.employee.employee) else f"Employee {self.employee_id}"

    @property
    def max_hours(self) -> int:
        from sqlalchemy.orm import object_session
        from app.models.system_config import SystemConfig
        from app.core.config import settings
        
        session = object_session(self)
        max_weekly_hours = settings.DEFAULT_MAX_WEEKLY_HOURS
        if session:
            config = session.query(SystemConfig).filter(SystemConfig.id == 1).first()
            if config:
                max_weekly_hours = config.max_weekly_hours
        
        return int(self.utilisation_percent * max_weekly_hours / 100)
