"""
Admin API routes. All protected by require_admin dependency.
Routes are thin — they receive, delegate to a service, and return.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.services import employee_service, user_service, project_service
from app.repositories import allocation_repository, project_repository, skill_repository
from app.schemas.user_schemas import UserCreate, UserResponse, ResetPasswordRequest
from app.schemas.employee_schemas import EmployeeUpdate, EmployeeResponse, AssignManagerRequest, SkillAddRequest, ProficiencyUpdateRequest
from app.schemas.project_schemas import ProjectCreate, ProjectUpdate, ProjectResponse, MilestoneCreate, MilestoneUpdate, MilestoneResponse, ProjectDetailResponse
from app.schemas.allocation_schemas import AllocationResponse


router = APIRouter(dependencies=[Depends(require_admin)])


# ── User Management ───────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    try:
        user = user_service.create_user(
            db,
            full_name=body.full_name,
            email=body.email,
            username=body.username,
            temp_password=body.temp_password,
            role=body.role
        )
        return user
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    from app.repositories import user_repository
    return user_repository.get_all_users(db)


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        user_service.reset_user_password(db, user_id, body.temp_password)
        return {"message": "Password reset. User will be prompted to change it on next login."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user_service.deactivate_user(db, user_id)
    return {"message": "User deactivated"}


@router.post("/users/{user_id}/reactivate")
def reactivate_user(user_id: int, db: Session = Depends(get_db)):
    user_service.reactivate_user(db, user_id)
    return {"message": "User reactivated. Previous allocations are not restored."}


# ── Employee Management ───────────────────────────────────────────────────────

@router.get("/employees", response_model=list[EmployeeResponse])
def get_all_employees(status: str = None, dept: str = None, db: Session = Depends(get_db)):
    return employee_service.get_all_employees(db, {"status": status, "department": dept})


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee_detail(employee_id: int, db: Session = Depends(get_db)):
    try:
        return employee_service.get_employee_detail(db, employee_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, body: EmployeeUpdate, db: Session = Depends(get_db)):
    from app.repositories import employee_repository
    fields = body.model_dump(exclude_unset=True)
    return employee_repository.update_employee_fields(db, employee_id, fields)


@router.post("/employees/{employee_id}/deactivate")
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    try:
        employee_service.deactivate_employee(db, employee_id)
        return {"message": "Employee deactivated. All active allocations ended."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post("/employees/assign-manager")
def assign_manager(body: AssignManagerRequest, db: Session = Depends(get_db)):
    from app.repositories import employee_repository
    employee_repository.assign_manager(db, body.employee_user_id, body.manager_user_id)
    return {"message": "Manager assigned"}


# ── Skill Management ──────────────────────────────────────────────────────────

@router.get("/employees/{employee_id}/skills")
def get_employee_skills(employee_id: int, db: Session = Depends(get_db)):
    skills = skill_repository.get_skills_for_employee(db, employee_id)
    return [
        {
            "skill_id": s.skill_id,
            "skill_name": s.skill.name,
            "category": s.skill.category,
            "proficiency": s.proficiency
        }
        for s in skills
    ]


@router.post("/employees/{employee_id}/skills", status_code=status.HTTP_201_CREATED)
def add_skill(employee_id: int, body: SkillAddRequest, db: Session = Depends(get_db)):
    res = skill_repository.add_skill_to_employee(
        db,
        employee_id=employee_id,
        skill_name=body.skill_name,
        category=body.category,
        proficiency=body.proficiency
    )
    return {
        "skill_id": res.skill_id,
        "skill_name": res.skill.name,
        "category": res.skill.category,
        "proficiency": res.proficiency
    }


@router.put("/employees/{employee_id}/skills/{skill_id}")
def update_skill_proficiency(employee_id: int, skill_id: int, body: ProficiencyUpdateRequest, db: Session = Depends(get_db)):
    skill_repository.update_skill_proficiency(db, employee_id, skill_id, body.proficiency)
    return {"message": "Proficiency updated"}


@router.delete("/employees/{employee_id}/skills/{skill_id}")
def remove_skill(employee_id: int, skill_id: int, db: Session = Depends(get_db)):
    skill_repository.remove_skill_from_employee(db, employee_id, skill_id)
    return {"message": "Skill removed"}


# ── Project Management ────────────────────────────────────────────────────────

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    try:
        project = project_service.create_project(db, body.model_dump())
        return project
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/projects", response_model=list[ProjectResponse])
def get_all_projects(db: Session = Depends(get_db)):
    return project_service.get_all_projects(db)


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.get_project_milestones(db, project_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, body: ProjectUpdate, db: Session = Depends(get_db)):
    try:
        fields = body.model_dump(exclude_unset=True)
        return project_service.update_project(db, project_id, fields)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# ── Milestone Management ──────────────────────────────────────────────────────

@router.get("/projects/{project_id}/milestones", response_model=list[MilestoneResponse])
def get_milestones(project_id: int, db: Session = Depends(get_db)):
    return project_repository.get_milestones_for_project(db, project_id)


@router.post("/projects/{project_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
def add_milestone(project_id: int, body: MilestoneCreate, db: Session = Depends(get_db)):
    return project_repository.add_milestone(
        db,
        project_id=project_id,
        title=body.title,
        due_date=body.due_date,
        story_points=body.story_points
    )


@router.put("/milestones/{milestone_id}")
def update_milestone_status(milestone_id: int, body: MilestoneUpdate, db: Session = Depends(get_db)):
    project_repository.update_milestone_status(db, milestone_id, body.status)
    return {"message": "Milestone updated"}


# ── Allocations (read-only for Admin) ────────────────────────────────────────

@router.get("/allocations", response_model=list[AllocationResponse])
def get_all_allocations(
    employee_id: int = None,
    project_id:  int = None,
    db: Session = Depends(get_db),
):
    return allocation_repository.get_all_allocations(db, employee_id, project_id)


# ── System Configuration ──────────────────────────────────────────────────────

@router.get("/config")
def get_system_config(db: Session = Depends(get_db)):
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if config and config.llm_api_key:
        config.llm_api_key = "****" + config.llm_api_key[-4:]   # mask the key
    return config


@router.put("/config")
def update_system_config(body: dict, db: Session = Depends(get_db)):
    from app.models.system_config import SystemConfig
    db.query(SystemConfig).filter(SystemConfig.id == 1).update(body)
    db.commit()
    return {"message": "Configuration updated"}
