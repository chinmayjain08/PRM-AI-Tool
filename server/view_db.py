import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set cwd and pythonpath
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.core.config import settings
from app.models.user import User
from app.models.employee import Employee
from app.models.project import Project, Milestone
from app.models.allocation import Allocation
from app.models.timesheet import Timesheet
from app.models.skill import Skill

# Establish DB Session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def draw_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

try:
    draw_header("USERS")
    users = db.query(User).all()
    print(f"{'ID':<5} | {'Username':<15} | {'Email':<25} | {'Role':<10} | {'Active':<8}")
    print("-" * 72)
    for u in users:
        print(f"{u.id:<5} | {u.username:<15} | {u.email:<25} | {u.role:<10} | {str(u.is_active):<8}")

    draw_header("EMPLOYEES")
    employees = db.query(Employee).all()
    print(f"{'ID':<5} | {'User ID':<8} | {'Department':<15} | {'Manager ID':<10} | {'Joined Date':<12}")
    print("-" * 58)
    for emp in employees:
        manager_id = emp.manager_id if emp.manager_id is not None else "None"
        print(f"{emp.id:<5} | {emp.user_id:<8} | {emp.department:<15} | {str(manager_id):<10} | {str(emp.joined_date):<12}")

    draw_header("PROJECTS")
    projects = db.query(Project).all()
    print(f"{'ID':<5} | {'Name':<20} | {'Status':<10} | {'Health':<10} | {'Manager ID':<10}")
    print("-" * 63)
    for p in projects:
        print(f"{p.id:<5} | {p.name:<20} | {p.status:<10} | {p.health_status:<10} | {p.manager_id:<10}")

    draw_header("ALLOCATIONS")
    allocations = db.query(Allocation).all()
    print(f"{'ID':<5} | {'Employee ID':<12} | {'Project ID':<10} | {'Utilization %':<15} | {'Active':<8}")
    print("-" * 56)
    for a in allocations:
        print(f"{a.id:<5} | {a.employee_id:<12} | {a.project_id:<10} | {a.utilisation_percent:<15} | {str(a.is_active):<8}")

    draw_header("TIMESHEETS")
    timesheets = db.query(Timesheet).all()
    print(f"{'ID':<5} | {'Employee ID':<12} | {'Project ID':<10} | {'Hours':<8} | {'Status':<10}")
    print("-" * 51)
    for t in timesheets:
        print(f"{t.id:<5} | {t.employee_id:<12} | {t.project_id:<10} | {t.hours_worked:<8} | {t.status:<10}")

except Exception as e:
    print(f"Error querying database: {e}")
finally:
    db.close()
