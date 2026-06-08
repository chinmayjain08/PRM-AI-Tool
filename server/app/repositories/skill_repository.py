from sqlalchemy.orm import Session
from app.models.skill import Skill, EmployeeSkill


def get_or_create_skill(db: Session, name: str, category: str) -> Skill:
    """Returns existing skill by name, or creates a new one."""
    skill = db.query(Skill).filter(Skill.name == name).first()
    if skill:
        return skill
    skill = Skill(name=name, category=category)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def get_skills_for_employee(db: Session, employee_id: int) -> list[EmployeeSkill]:
    return db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee_id).all()


def add_skill_to_employee(
    db: Session,
    employee_id: int,
    skill_name: str,
    category: str,
    proficiency: str,
) -> EmployeeSkill:
    skill = get_or_create_skill(db, skill_name, category)
    employee_skill = EmployeeSkill(
        employee_id=employee_id,
        skill_id=skill.id,
        proficiency=proficiency,
    )
    db.add(employee_skill)
    db.commit()
    db.refresh(employee_skill)
    return employee_skill


def update_skill_proficiency(db: Session, employee_id: int, skill_id: int, proficiency: str) -> None:
    db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == employee_id,
        EmployeeSkill.skill_id == skill_id,
    ).update({"proficiency": proficiency})
    db.commit()


def remove_skill_from_employee(db: Session, employee_id: int, skill_id: int) -> None:
    db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == employee_id,
        EmployeeSkill.skill_id == skill_id,
    ).delete()
    db.commit()
