"""
Comprehensive Dummy Data Seed Script.
Run this script to populate a rich set of dummy data to test all PRM features:
- Scheduler (Timesheet freezing, Project At-Risk)
- AI Risk Summarizer
- AI Skill Matcher / Team Builder
- Email Service
"""

import sys
import os
from datetime import date, timedelta
import random

# Add current folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.employee import Employee, EmployeeProfile
from app.models.skill import Skill, EmployeeSkill
from app.models.project import Project, Milestone
from app.models.allocation import Allocation
from app.models.timesheet import Timesheet, TimesheetTag
from app.models.enums import ProjectStatus, ProjectHealthStatus, MilestoneStatus, TimesheetStatus

def create_user(db, username, email, full_name, role_name, dept, manager_id=None):
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise Exception(f"Role {role_name} not found! Run seed.py first.")
        
    emp = db.query(Employee).filter(Employee.username == username).first()
    if not emp:
        emp = Employee(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hash_password("Password@123"),
            role_id=role.id,
            is_active=True,
            force_password_change=False
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        
        prof = EmployeeProfile(
            employee_id=emp.id,
            department=dept,
            manager_id=manager_id,
            joined_at=date.today() - timedelta(days=random.randint(100, 1000)),
            timesheet_frozen=False
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)
    return emp.profile

def seed_skills(db):
    skill_names = [
        ("Python", "Backend"), ("Java", "Backend"), ("React", "Frontend"),
        ("Docker", "DevOps"), ("Kubernetes", "DevOps"), ("AWS", "DevOps"),
        ("Selenium", "Testing"), ("Jest", "Testing"), ("AI Integration", "Backend")
    ]
    skills = {}
    for name, cat in skill_names:
        s = db.query(Skill).filter(Skill.name == name).first()
        if not s:
            s = Skill(name=name, category=cat)
            db.add(s)
            db.commit()
            db.refresh(s)
        skills[name] = s
    return skills

def assign_skill(db, profile, skill, prof_level):
    existing = db.query(EmployeeSkill).filter_by(employee_id=profile.id, skill_id=skill.id).first()
    if not existing:
        es = EmployeeSkill(employee_id=profile.id, skill_id=skill.id, proficiency=prof_level)
        db.add(es)
        db.commit()

def main():
    db = SessionLocal()
    try:
        print("Seeding skills...")
        skills = seed_skills(db)
        
        print("Seeding managers...")
        mgr1 = create_user(db, "pm_alice", "alice@prmtool.com", "Alice Manager", "MANAGER", "ENGINEERING")
        mgr2 = create_user(db, "pm_bob", "bob@prmtool.com", "Bob Director", "MANAGER", "ENGINEERING")
        
        print("Seeding resources...")
        # Team Alice
        dev1 = create_user(db, "dev_charlie", "charlie@prmtool.com", "Charlie Python Developer", "RESOURCE", "ENGINEERING", mgr1.id)
        dev2 = create_user(db, "dev_diana", "diana@prmtool.com", "Diana Java Developer", "RESOURCE", "ENGINEERING", mgr1.id)
        qa1 = create_user(db, "qa_eve", "eve@prmtool.com", "Eve QA Engineer", "RESOURCE", "TESTING", mgr1.id)
        qa2 = create_user(db, "qa_frank", "frank@prmtool.com", "Frank QA Tester", "RESOURCE", "TESTING", mgr1.id)
        ops1 = create_user(db, "ops_grace", "grace@prmtool.com", "Grace DevOps", "RESOURCE", "OPS", mgr1.id)
        
        # Team Bob
        dev3 = create_user(db, "dev_hank", "hank@prmtool.com", "Hank React Developer", "RESOURCE", "ENGINEERING", mgr2.id)
        ai_dev = create_user(db, "dev_ivy", "ivy@prmtool.com", "Ivy AI Integration Developer", "RESOURCE", "ENGINEERING", mgr2.id)
        ops2 = create_user(db, "ops_jack", "jack@prmtool.com", "Jack DevOps Engineer", "RESOURCE", "OPS", mgr2.id)
        
        print("Assigning skills...")
        assign_skill(db, dev1, skills["Python"], "Intermediate")
        assign_skill(db, dev2, skills["Java"], "Advanced")
        assign_skill(db, qa1, skills["Selenium"], "Intermediate")
        assign_skill(db, qa2, skills["Jest"], "Intermediate")
        assign_skill(db, ops1, skills["Docker"], "Advanced")
        assign_skill(db, dev3, skills["React"], "Advanced")
        assign_skill(db, ai_dev, skills["Python"], "Advanced")
        assign_skill(db, ai_dev, skills["AI Integration"], "Intermediate")
        assign_skill(db, ops2, skills["Kubernetes"], "Intermediate")
        assign_skill(db, ops2, skills["AWS"], "Intermediate")
        
        print("Creating Projects and Milestones...")
        today = date.today()
        
        # Project 1: On Track
        p1 = Project(name="Phoenix API Reboot", description="Modernizing core API", start_date=today - timedelta(days=30), end_date=today + timedelta(days=60), status=ProjectStatus.ACTIVE, manager_id=mgr1.employee_id, total_story_pts=100)
        db.add(p1)
        db.commit()
        db.refresh(p1)
        
        m1 = Milestone(project_id=p1.id, title="Phase 1 Design", due_date=today - timedelta(days=10), story_points=20, status=MilestoneStatus.DONE)
        m2 = Milestone(project_id=p1.id, title="Phase 2 Impl", due_date=today + timedelta(days=20), story_points=80, status=MilestoneStatus.IN_PROGRESS)
        db.add_all([m1, m2])
        db.commit()
        
        # Project 2: AT_RISK (overdue milestone)
        p2 = Project(name="AI Analytics Dashboard", description="Machine learning dashboard", start_date=today - timedelta(days=60), end_date=today + timedelta(days=10), status=ProjectStatus.ACTIVE, manager_id=mgr2.employee_id, total_story_pts=200)
        db.add(p2)
        db.commit()
        db.refresh(p2)
        
        m3 = Milestone(project_id=p2.id, title="Data Pipeline", due_date=today - timedelta(days=15), story_points=50, status=MilestoneStatus.IN_PROGRESS) # Overdue!
        m4 = Milestone(project_id=p2.id, title="Frontend UI", due_date=today + timedelta(days=5), story_points=150, status=MilestoneStatus.NOT_STARTED)
        db.add_all([m3, m4])
        db.commit()
        
        print("Allocating Resources...")
        # Allocate Charlie to P1 (100%)
        a1 = Allocation(employee_id=dev1.id, project_id=p1.id, from_date=p1.start_date, to_date=p1.end_date, utilisation_percent=100, is_active=True)
        # Allocate Hank to P2 (50%)
        a2 = Allocation(employee_id=dev3.id, project_id=p2.id, from_date=p2.start_date, to_date=p2.end_date, utilisation_percent=50, is_active=True)
        db.add_all([a1, a2])
        db.commit()
        
        print("Seeding Timesheets (Missing timesheet scenario)...")
        # Let's say Charlie submitted his timesheet for last week
        last_monday = today - timedelta(days=today.weekday() + 7)
        ts1 = Timesheet(employee_id=dev1.id, project_id=p1.id, week_start=last_monday, hours_worked=40, status=TimesheetStatus.SUBMITTED)
        db.add(ts1)
        db.commit()
        
        # Hank missed his timesheet for last week (Scheduler will catch this)
        # We won't insert one for Hank so that when you run scheduler, it creates a MISSED row.
        
        print("\nDummy data successfully injected!")
        print("You can test:")
        print("1. Team Builder: Try searching for 'QA Engineer', 'DevOps', and 'AI Integration Developer' to see the global matching.")
        print("2. Scheduler: Run 'from app.core.scheduler import run_all_scheduled_tasks; run_all_scheduled_tasks()' in python terminal to trigger the At-Risk email for Project 2 and the Timesheet Reminder for Hank.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
