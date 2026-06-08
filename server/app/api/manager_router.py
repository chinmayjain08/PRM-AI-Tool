from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_manager
from app.models.user import User
from app.repositories import (
    allocation_repository,
    employee_repository,
    project_repository,
    timesheet_repository,
)
from app.services import allocation_service, project_health_service
from app.schemas.allocation_schemas import AllocationCreate

router = APIRouter(dependencies=[Depends(require_manager)])


# ── Resource Dashboard ────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_resource_dashboard(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_manager),
):
    """
    Returns the manager's team split into bench and allocated groups.
    Scope: employees where manager_id = current_user.id.
    """
    team = employee_repository.get_employees_by_manager(db, current_user.id)
    bench     = []
    allocated = []

    for employee in team:
        active_allocs = allocation_repository.get_active_allocations_for_employee(db, employee.id)
        total_util    = sum(a.utilisation_percent for a in active_allocs)
        if total_util == 0:
            bench.append(_format_bench_employee(employee))
        else:
            allocated.append(_format_allocated_employee(employee, total_util))

    return {"bench": bench, "allocated": allocated}


@router.get("/employees/{employee_id}")
def get_employee_detail(
    employee_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_manager),
):
    """Employee profile + skills + allocations + recent tags. Team-scoped."""
    employee = employee_repository.get_employee_by_id(db, employee_id)
    if employee is None or employee.manager_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your team member")
    
    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "department": employee.department,
        "joined_at": employee.joined_at,
        "is_active": employee.is_active,
        "full_name": employee.user.full_name,
        "email": employee.user.email,
        "skills": [
            {
                "skill_name": es.skill.name,
                "category": es.skill.category,
                "proficiency": es.proficiency
            } for es in employee.skills
        ],
        "allocations": [
            {
                "id": a.id,
                "project_id": a.project_id,
                "project_name": a.project.name,
                "utilisation_percent": a.utilisation_percent,
                "from_date": a.from_date,
                "to_date": a.to_date,
                "is_active": a.is_active
            } for a in allocation_repository.get_active_allocations_for_employee(db, employee.id)
        ]
    }


# ── Allocation ────────────────────────────────────────────────────────────────

@router.post("/allocations", status_code=status.HTTP_201_CREATED)
def create_allocation(
    allocation_data: AllocationCreate,
    db:              Session = Depends(get_db),
    current_user:    User    = Depends(require_manager),
):
    # Assert project belongs to current manager
    project = project_repository.get_project_by_id(db, allocation_data.project_id)
    if not project or project.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only allocate to your own projects"
        )
    
    try:
        allocation = allocation_service.create_allocation(
            db=db,
            employee_id=allocation_data.employee_id,
            project_id=allocation_data.project_id,
            utilisation_percent=allocation_data.utilisation_percent,
            from_date=allocation_data.from_date,
            to_date=allocation_data.to_date
        )
        return {"id": allocation.id, "message": "Allocation saved"}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/allocations/{allocation_id}")
def end_allocation(
    allocation_id: int,
    db:            Session = Depends(get_db),
    current_user:  User    = Depends(require_manager),
):
    try:
        allocation_service.end_allocation(db, allocation_id, current_user.id)
        return {"message": "Allocation ended"}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


# ── Projects ──────────────────────────────────────────────────────────────────

@router.get("/projects")
def get_my_projects(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_manager),
):
    projects = project_repository.get_projects_by_manager(db, current_user.id)
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "status": p.status,
            "manager_id": p.manager_id,
            "total_story_pts": p.total_story_pts,
            "health_status": p.health_status,
            "health_icon": _health_icon(p.health_status)
        }
        for p in projects
    ]


@router.get("/projects/{project_id}")
def get_project_detail(
    project_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_manager),
):
    project = project_repository.get_project_by_id(db, project_id)
    if project is None or project.manager_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your project")

    milestones   = project_repository.get_milestones_for_project(db, project_id)
    allocations  = allocation_repository.get_all_allocations(db, project_id_filter=project_id)
    risk_flags   = project_health_service.collect_risk_flags(db, project_id)

    # Convert project SQLAlchemy model fields to a dict or return clean structure
    # to avoid circular references/Pydantic serialization warnings.
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "status": project.status,
            "manager_id": project.manager_id,
            "total_story_pts": project.total_story_pts,
            "health_status": project.health_status,
            "health_icon": _health_icon(project.health_status)
        },
        "milestones": [
            {
                "id": m.id,
                "project_id": m.project_id,
                "title": m.title,
                "due_date": m.due_date,
                "story_points": m.story_points,
                "status": m.status
            } for m in milestones
        ],
        "allocations": [
            {
                "id": a.id,
                "employee_id": a.employee_id,
                "employee_name": a.employee.user.full_name,
                "utilisation_percent": a.utilisation_percent,
                "from_date": a.from_date,
                "to_date": a.to_date,
                "is_active": a.is_active
            } for a in allocations
        ],
        "risk_flags": risk_flags,
    }


# ── Timesheets (read-only) ────────────────────────────────────────────────────

@router.get("/timesheets")
def get_team_timesheets(
    week_start:   str    = None,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_manager),
):
    """
    Returns team's timesheet entries for the given week.
    Defaults to current week (last Monday) if week_start not provided.
    """
    resolved_week = _resolve_week_start(week_start)
    team = employee_repository.get_employees_by_manager(db, current_user.id)
    timesheets = timesheet_repository.get_team_timesheets_for_week(
        db, [emp.id for emp in team], resolved_week
    )
    return [
        {
            "id": ts.id,
            "employee_id": ts.employee_id,
            "employee_name": ts.employee.user.full_name,
            "project_id": ts.project_id,
            "project_name": ts.project.name,
            "week_start": ts.week_start,
            "hours_worked": ts.hours_worked,
            "status": ts.status,
            "submitted_at": ts.submitted_at,
            "tags": [tag.tag for tag in ts.tags]
        }
        for ts in timesheets
    ]


# ── AI (Stubs — implemented in Phase 7) ──────────────────────────────────────

@router.post("/ai/skill-match")
def ai_skill_match(body: dict, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    """Stub. Implemented in Phase 7."""
    return {"message": "AI Skill Match not yet configured. Implement in Phase 7."}


@router.get("/ai/risk-summary/{project_id}")
def ai_risk_summary(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    """Stub. Implemented in Phase 7."""
    return {"message": "AI Risk Summary not yet configured. Implement in Phase 7."}


# ── Private helpers ───────────────────────────────────────────────────────────

def _format_bench_employee(employee) -> dict:
    return {
        "id":         employee.id,
        "full_name":  employee.user.full_name,
        "department": employee.department,
        "skills":     [es.skill.name for es in employee.skills],
    }


def _format_allocated_employee(employee, total_util: int) -> dict:
    free_percent = 100 - total_util
    return {
        "id":           employee.id,
        "full_name":    employee.user.full_name,
        "utilisation":  total_util,
        "availability": "FULL" if total_util == 100 else f"{free_percent}% free",
    }


def _health_icon(health_status: str) -> str:
    icons = {"ON_TRACK": "🟢", "ATTENTION": "🟡", "AT_RISK": "🔴"}
    return icons.get(health_status, "⚪")


def _resolve_week_start(week_start_str: str | None) -> date:
    if week_start_str:
        return date.fromisoformat(week_start_str)
    today  = date.today()
    return today - timedelta(days=today.weekday())   # last Monday
