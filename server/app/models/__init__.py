# Import all models here so Alembic can find them when generating migrations.
from app.models.role import Role
from app.models.permission import Permission, role_permissions
from app.models.employee import Employee, EmployeeProfile
from app.models.skill import Skill, EmployeeSkill
from app.models.project import Project, Milestone
from app.models.allocation import Allocation
from app.models.timesheet import Timesheet, TimesheetTag
from app.models.system_config import SystemConfig
from app.models.enums import TimesheetStatus, ProjectStatus, ProjectHealthStatus, MilestoneStatus, ProficiencyLevel
