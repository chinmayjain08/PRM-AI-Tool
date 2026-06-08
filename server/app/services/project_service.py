"""
Project and milestone management business rules.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.repositories import project_repository, user_repository


def create_project(db: Session, data: dict) -> object:
    """Validates end_date > start_date and that the assigned manager has MANAGER role."""
    _validate_project_dates(data.get("start_date"), data.get("end_date"))
    _validate_manager_role(db, data.get("manager_id"))
    return project_repository.create_project(db, data)


def update_project(db: Session, project_id: int, updates: dict) -> object:
    _validate_project_dates(updates.get("start_date"), updates.get("end_date"))
    if updates.get("manager_id") is not None:
        _validate_manager_role(db, updates.get("manager_id"))
    return project_repository.update_project_fields(db, project_id, updates)


def get_all_projects(db: Session) -> list:
    """Returns all projects enriched with completed story points."""
    projects = project_repository.get_all_projects(db)
    return [_enrich_with_story_points(db, proj) for proj in projects]


def get_project_milestones(db: Session, project_id: int) -> dict:
    """Returns project info + milestones + summary totals."""
    project    = project_repository.get_project_by_id(db, project_id)
    if project is None:
        raise ValueError(f"Project with ID {project_id} not found")
    milestones = project_repository.get_milestones_for_project(db, project_id)
    done_pts   = sum(m.story_points for m in milestones if m.status == "DONE")
    return {
        "project":         project,
        "milestones":      milestones,
        "done_story_pts":  done_pts,
        "remaining_pts":   (project.total_story_pts or 0) - done_pts,
    }


def _validate_project_dates(start_date: date, end_date: date) -> None:
    if start_date and end_date and end_date <= start_date:
        raise ValueError("End date must be after start date")


def _validate_manager_role(db: Session, manager_id: int) -> None:
    if manager_id is not None:
        user = user_repository.get_user_by_id(db, manager_id)
        if user is None or user.role != "MANAGER":
            raise ValueError(f"User ID {manager_id} is not a Manager")


def _enrich_with_story_points(db: Session, project) -> dict:
    milestones = project_repository.get_milestones_for_project(db, project.id)
    done_pts   = sum(m.story_points for m in milestones if m.status == "DONE")
    proj_dict  = {c.name: getattr(project, c.name) for c in project.__table__.columns}
    proj_dict["done_story_pts"] = done_pts
    return proj_dict
