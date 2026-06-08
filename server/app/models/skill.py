from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # Backend|Frontend|DevOps|QA|Other


class EmployeeSkill(Base):
    """Association table: Employee ↔ Skill with proficiency level."""
    __tablename__ = "employee_skills"

    employee_id = Column(Integer, ForeignKey("employees.id"), primary_key=True)
    skill_id    = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    proficiency = Column(String(20))   # Beginner | Intermediate | Advanced

    employee = relationship("Employee", back_populates="skills")
    skill    = relationship("Skill")
