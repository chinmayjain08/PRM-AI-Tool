from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id                  = Column(Integer, primary_key=True, index=True)
    employee_id         = Column(Integer, ForeignKey("employees.id"))
    project_id          = Column(Integer, ForeignKey("projects.id"))
    utilisation_percent = Column(Integer, nullable=False)    # 0 to 100
    from_date           = Column(Date, nullable=False)
    to_date             = Column(Date, nullable=False)
    is_active           = Column(Boolean, default=True)

    employee = relationship("Employee", back_populates="allocations")
    project  = relationship("Project")
