from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import ProficiencyLevel


class Skill(Base):
    __tablename__ = "skills"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # Backend|Frontend|DevOps|QA|Other


class EmployeeSkill(Base):
    """Association table: EmployeeProfile ↔ Skill with proficiency level."""
    __tablename__ = "employee_skills"

    employee_id = Column(Integer, ForeignKey("employee_profiles.id"), primary_key=True)
    skill_id    = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    proficiency = Column(Enum("Beginner", "Intermediate", "Advanced", name="proficiency_level", native_enum=True))

    employee = relationship("EmployeeProfile", back_populates="skills")
    skill    = relationship("Skill")

