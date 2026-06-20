"""
One-time bootstrap script. Seeds roles, permissions, initial admin, manager, resource accounts,
and default system config. Safe to run multiple times (idempotent).

Usage:
    python seed.py
"""

import sys
import os
from datetime import date

# Add current folder to sys.path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.permission import Permission
from app.models.employee import Employee, EmployeeProfile
from app.models.system_config import SystemConfig

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL    = "admin@prmtool.com"
DEFAULT_ADMIN_PASSWORD = "Admin@1234"

DEFAULT_MANAGER_USERNAME = "manager1"
DEFAULT_MANAGER_EMAIL    = "manager1@prmtool.com"
DEFAULT_MANAGER_PASSWORD = "Manager@1234"

DEFAULT_RESOURCE_USERNAME = "resource1"
DEFAULT_RESOURCE_EMAIL    = "resource1@prmtool.com"
DEFAULT_RESOURCE_PASSWORD = "Resource@1234"


def seed_roles_and_permissions(db) -> dict:
    # 1. Define permissions
    perms_data = {
        # Admin permissions
        "MANAGE_EMPLOYEES": "Create/Update/Deactivate employee accounts and profiles",
        "MANAGE_SKILLS": "Create/Update/Delete skills in lookup table",
        "MANAGE_SYSTEM_CONFIG": "Configure system settings (LLM, max weekly hours, etc.)",
        "VIEW_REPORTS": "View company-wide reports and metrics",
        # Manager permissions
        "MANAGE_PROJECTS": "Create/Update projects and milestones",
        "MANAGE_ALLOCATIONS": "Allocate resources to projects, edit allocations",
        "APPROVE_TIMESHEETS": "Review and approve/reject timesheets for allocated resources",
        "VIEW_TEAM": "View profile and allocations of direct reports",
        # Resource permissions
        "SUBMIT_OWN_TIMESHEET": "Log hours worked on projects where they are allocated",
        "VIEW_OWN_ALLOCATIONS": "View their active and past allocations",
        "VIEW_OWN_PROFILE": "View their own profile/skills details",
        "UPDATE_OWN_SKILLS": "Manage their own skill proficiency levels"
    }

    perms = {}
    for name, desc in perms_data.items():
        perm = db.query(Permission).filter(Permission.name == name).first()
        if not perm:
            perm = Permission(name=name, description=desc)
            db.add(perm)
            db.commit()
            db.refresh(perm)
        perms[name] = perm

    # 2. Define roles and their permission assignments
    roles_data = {
        "ADMIN": ["MANAGE_EMPLOYEES", "MANAGE_SKILLS", "MANAGE_SYSTEM_CONFIG", "VIEW_REPORTS", "MANAGE_PROJECTS"],
        "MANAGER": ["MANAGE_PROJECTS", "MANAGE_ALLOCATIONS", "APPROVE_TIMESHEETS", "VIEW_TEAM"],
        "RESOURCE": ["SUBMIT_OWN_TIMESHEET", "VIEW_OWN_ALLOCATIONS", "VIEW_OWN_PROFILE", "UPDATE_OWN_SKILLS"]
    }

    roles = {}
    for role_name, perm_names in roles_data.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name)
            db.add(role)
            db.commit()
            db.refresh(role)
        
        # Sync permissions
        role.permissions = [perms[pn] for pn in perm_names]
        db.commit()
        roles[role_name] = role

    print("Roles and permissions successfully seeded.")
    return roles


def seed_users_and_profiles(db, roles) -> None:
    # 1. Admin
    admin_emp = db.query(Employee).filter(Employee.username == DEFAULT_ADMIN_USERNAME).first()
    if not admin_emp:
        admin_emp = Employee(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            full_name="System Admin",
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            role_id=roles["ADMIN"].id,
            is_active=True,
            force_password_change=True,
        )
        db.add(admin_emp)
        db.commit()
        db.refresh(admin_emp)
        
        admin_profile = EmployeeProfile(
            employee_id=admin_emp.id,
            department="OPERATIONS",
            manager_id=None,
            joined_at=date.today()
        )
        db.add(admin_profile)
        db.commit()
        print(f"Admin account created: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
    else:
        print("Admin account already exists.")



def create_default_system_config(db) -> None:
    config_exists = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if config_exists:
        print("System config already exists. Skipping.")
        return

    config = SystemConfig(id=1)
    db.add(config)
    db.commit()
    print("Default system config created.")


def main() -> None:
    db = SessionLocal()
    try:
        roles = seed_roles_and_permissions(db)
        seed_users_and_profiles(db, roles)
        create_default_system_config(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
