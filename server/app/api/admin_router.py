"""
Admin API routes. All protected by fine-grained permission-based dependencies.
Routes are thin — they receive, delegate to a service, and return.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_permission
from app.models.employee import Employee
from app.services import employee_service, project_service
from app.repositories import allocation_repository, project_repository, skill_repository, employee_repository
from app.schemas.user_schemas import UserCreate, UserResponse, ResetPasswordRequest
from app.schemas.employee_schemas import EmployeeUpdate, EmployeeResponse, AssignManagerRequest, SkillAddRequest, ProficiencyUpdateRequest
from app.schemas.project_schemas import ProjectCreate, ProjectUpdate, ProjectResponse, MilestoneCreate, MilestoneUpdate, MilestoneResponse, ProjectDetailResponse
from app.schemas.allocation_schemas import AllocationResponse

router = APIRouter()


# ── User (Employee Account) Management ────────────────────────────────────────

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    try:
        user = employee_service.create_employee(
            db=db,
            full_name=body.full_name,
            email=body.email,
            username=body.username,
            temp_password=body.temp_password,
            role_name=body.role,
            department=body.department
        )
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": "EMPLOYEE" if user.role.name == "RESOURCE" else user.role.name,
            "is_active": user.is_active,
            "force_password_change": user.force_password_change,
            "created_at": user.created_at
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def get_all_users(db: Session = Depends(get_db)):
    users = employee_repository.get_all_employee_accounts(db)
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": "EMPLOYEE" if u.role.name == "RESOURCE" else u.role.name,
            "is_active": u.is_active,
            "force_password_change": u.force_password_change,
            "created_at": u.created_at
        }
        for u in users
    ]


@router.post("/users/{user_id}/reset-password", dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def reset_user_password(user_id: int, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        employee_service.reset_employee_password(db, user_id, body.temp_password)
        return {"message": "Password reset. User will be prompted to change it on next login."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/users/{user_id}/deactivate", dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    employee_service.deactivate_employee_account(db, user_id)
    return {"message": "User deactivated"}


@router.post("/users/{user_id}/reactivate", dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def reactivate_user(user_id: int, db: Session = Depends(get_db)):
    employee_service.reactivate_employee_account(db, user_id)
    return {"message": "User reactivated. Previous allocations are not restored."}


# ── Employee Profile Management ───────────────────────────────────────────────

@router.get("/employees", response_model=list[EmployeeResponse], dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def get_all_employees(status: str = None, dept: str = None, db: Session = Depends(get_db)):
    return employee_service.get_all_employees(db, {"status": status, "department": dept})


@router.get("/employees/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def get_employee_detail(employee_id: int, db: Session = Depends(get_db)):
    try:
        return employee_service.get_employee_detail(db, employee_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.put("/employees/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def update_employee(employee_id: int, body: EmployeeUpdate, db: Session = Depends(get_db)):
    fields = body.model_dump(exclude_unset=True)
    
    # Strictly validate department if updated
    if "department" in fields and fields["department"]:
        dept = fields["department"].upper()
        if dept not in ["ENGINEERING", "DELIVERY", "HR", "FINANCE", "OPERATIONS"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department name")
        fields["department"] = dept
        
    profile = employee_repository.update_employee_fields(db, employee_id, fields)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return employee_service.get_employee_detail(db, employee_id)


@router.post("/employees/{employee_id}/deactivate", dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    try:
        employee_service.deactivate_employee(db, employee_id)
        return {"message": "Employee deactivated. All active allocations ended."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post("/employees/assign-manager", dependencies=[Depends(require_permission("MANAGE_EMPLOYEES"))])
def assign_manager(body: AssignManagerRequest, db: Session = Depends(get_db)):
    # Validate manager constraints
    # manager must have MANAGER role, employee must have RESOURCE role
    emp_profile = employee_repository.get_employee_by_user_id(db, body.employee_user_id)
    mgr_profile = employee_repository.get_employee_by_user_id(db, body.manager_user_id)
    
    if not emp_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not mgr_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")
        
    if emp_profile.employee.role.name != "RESOURCE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only RESOURCE accounts can be assigned a manager")
    if mgr_profile.employee.role.name != "MANAGER":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned manager must have MANAGER role")
        
    employee_repository.assign_manager(db, body.employee_user_id, body.manager_user_id)
    return {"message": "Manager assigned"}


# ── Skill Management ──────────────────────────────────────────────────────────

@router.get("/employees/{employee_id}/skills", dependencies=[Depends(require_permission("MANAGE_SKILLS"))])
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


@router.post("/employees/{employee_id}/skills", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("MANAGE_SKILLS"))])
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


@router.put("/employees/{employee_id}/skills/{skill_id}", dependencies=[Depends(require_permission("MANAGE_SKILLS"))])
def update_skill_proficiency(employee_id: int, skill_id: int, body: ProficiencyUpdateRequest, db: Session = Depends(get_db)):
    skill_repository.update_skill_proficiency(db, employee_id, skill_id, body.proficiency)
    return {"message": "Proficiency updated"}


@router.delete("/employees/{employee_id}/skills/{skill_id}", dependencies=[Depends(require_permission("MANAGE_SKILLS"))])
def remove_skill(employee_id: int, skill_id: int, db: Session = Depends(get_db)):
    skill_repository.remove_skill_from_employee(db, employee_id, skill_id)
    return {"message": "Skill removed"}


# ── Project Management ────────────────────────────────────────────────────────

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    try:
        project = project_service.create_project(db, body.model_dump())
        return project
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/projects", response_model=list[ProjectResponse], dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def get_all_projects(db: Session = Depends(get_db)):
    return project_service.get_all_projects(db)


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse, dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.get_project_milestones(db, project_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.put("/projects/{project_id}", response_model=ProjectResponse, dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def update_project(project_id: int, body: ProjectUpdate, db: Session = Depends(get_db)):
    try:
        fields = body.model_dump(exclude_unset=True)
        return project_service.update_project(db, project_id, fields)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# ── Milestone Management ──────────────────────────────────────────────────────

@router.get("/projects/{project_id}/milestones", response_model=list[MilestoneResponse], dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def get_milestones(project_id: int, db: Session = Depends(get_db)):
    return project_repository.get_milestones_for_project(db, project_id)


@router.post("/projects/{project_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def add_milestone(project_id: int, body: MilestoneCreate, db: Session = Depends(get_db)):
    return project_repository.add_milestone(
        db,
        project_id=project_id,
        title=body.title,
        due_date=body.due_date,
        story_points=body.story_points
    )


@router.put("/milestones/{milestone_id}", dependencies=[Depends(require_permission("MANAGE_PROJECTS"))])
def update_milestone_status(milestone_id: int, body: MilestoneUpdate, db: Session = Depends(get_db)):
    project_repository.update_milestone_status(db, milestone_id, body.status)
    return {"message": "Milestone updated"}


# ── Allocations (read-only for Admin / View Reports) ───────────────────────────

@router.get("/allocations", response_model=list[AllocationResponse], dependencies=[Depends(require_permission("VIEW_REPORTS"))])
def get_all_allocations(
    employee_id: int = None,
    project_id:  int = None,
    db: Session = Depends(get_db),
):
    return allocation_repository.get_all_allocations(db, employee_id, project_id)


# ── System Configuration ──────────────────────────────────────────────────────

@router.get("/config", dependencies=[Depends(require_permission("MANAGE_SYSTEM_CONFIG"))])
def get_system_config(db: Session = Depends(get_db)):
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if config and config.llm_api_key:
        config.llm_api_key = "****" + config.llm_api_key[-4:]   # mask the key
    return config


@router.put("/config", dependencies=[Depends(require_permission("MANAGE_SYSTEM_CONFIG"))])
def update_system_config(body: dict, db: Session = Depends(get_db)):
    from app.models.system_config import SystemConfig
    db.query(SystemConfig).filter(SystemConfig.id == 1).update(body)
    db.commit()
    return {"message": "Configuration updated"}
