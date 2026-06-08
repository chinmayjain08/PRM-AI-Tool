from datetime import date
from sqlalchemy.orm import Session
from app.models.project import Project, Milestone


def create_project(db: Session, data: dict) -> Project:
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_all_projects(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.id).all()


def get_project_by_id(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()


def update_project_fields(db: Session, project_id: int, fields: dict) -> Project:
    db.query(Project).filter(Project.id == project_id).update(fields)
    db.commit()
    return get_project_by_id(db, project_id)


def get_milestones_for_project(db: Session, project_id: int) -> list[Milestone]:
    return db.query(Milestone).filter(Milestone.project_id == project_id).all()


def add_milestone(
    db: Session,
    project_id: int,
    title: str,
    due_date: date,
    story_points: int,
) -> Milestone:
    milestone = Milestone(
        project_id=project_id,
        title=title,
        due_date=due_date,
        story_points=story_points,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


def update_milestone_status(db: Session, milestone_id: int, status: str) -> None:
    db.query(Milestone).filter(Milestone.id == milestone_id).update({"status": status})
    db.commit()


def get_projects_by_manager(db: Session, manager_user_id: int) -> list[Project]:
    return db.query(Project).filter(Project.manager_id == manager_user_id).all()

