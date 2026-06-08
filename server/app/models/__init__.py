# Import all models here so Alembic can find them when generating migrations.
from app.models.user import User
from app.models.employee import Employee
from app.models.skill import Skill, EmployeeSkill
from app.models.project import Project, Milestone
from app.models.allocation import Allocation
from app.models.timesheet import Timesheet, TimesheetTag
from app.models.system_config import SystemConfig
