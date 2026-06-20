import sqlite3
import os
from datetime import date, timedelta
from app.core.security import hash_password

def populate_db(db_file: str, mode: str):
    print(f"Setting up test database for {mode} APIs...")
    if not os.path.exists(db_file):
        print(f"Error: {db_file} does not exist. Please run alembic migrations first.")
        import sys
        sys.exit(1)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Enable foreign keys and clear tables
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if row[0] not in ('sqlite_sequence', 'alembic_version')]
    for table in tables:
        cursor.execute(f"DELETE FROM {table};")
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Hash passwords
    admin_pw = hash_password("NewAdmin@123")
    mgr_pw = hash_password("Manager@123")
    emp_pw = hash_password("Employee@123")
    
    # 1. Populate roles and permissions
    cursor.executemany("INSERT INTO roles (id, name) VALUES (?, ?);", [
        (1, "ADMIN"),
        (2, "MANAGER"),
        (3, "RESOURCE")
    ])
    
    cursor.executemany("INSERT INTO permissions (id, name, description) VALUES (?, ?, ?);", [
        (1, "MANAGE_EMPLOYEES", ""),
        (2, "MANAGE_SKILLS", ""),
        (3, "MANAGE_SYSTEM_CONFIG", ""),
        (4, "VIEW_REPORTS", ""),
        (5, "MANAGE_PROJECTS", ""),
        (6, "MANAGE_ALLOCATIONS", ""),
        (7, "APPROVE_TIMESHEETS", ""),
        (8, "VIEW_TEAM", ""),
        (9, "SUBMIT_OWN_TIMESHEET", ""),
        (10, "VIEW_OWN_ALLOCATIONS", ""),
        (11, "VIEW_OWN_PROFILE", ""),
        (12, "UPDATE_OWN_SKILLS", "")
    ])
    
    role_perms = [
        (1, 1), (1, 2), (1, 3), (1, 4),
        (2, 5), (2, 6), (2, 7), (2, 8),
        (3, 9), (3, 10), (3, 11), (3, 12)
    ]
    cursor.executemany("INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?);", role_perms)

    # 2. Employees (id, username, email, full_name, hashed_password, role_id, is_active, force_password_change)
    employees_data = [
        (1, "admin", "admin@prmtool.com", "System Admin", admin_pw, 1, 1, 0),
        (2, "manager1", "manager1@prmtool.com", "Project Manager One", mgr_pw, 2, 1, 0),
        (3, "manager2", "manager2@prmtool.com", "Project Manager Two", mgr_pw, 2, 1, 0),
        (4, "employee1", "employee1@prmtool.com", "Developer Employee One", emp_pw, 3, 1, 0),
        (5, "employee2", "employee2@prmtool.com", "Developer Employee Two", emp_pw, 3, 1, 0),
    ]
    cursor.executemany(
        "INSERT INTO employees (id, username, email, full_name, hashed_password, role_id, is_active, force_password_change) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        employees_data
    )
    
    # 3. Employee Profiles (id, employee_id, department, manager_id, joined_at)
    if mode in ('real_gemini', 'scheduler_ai'):
        profiles_data = [
            (1, 4, "Engineering", 2, "2026-01-01"),  # employee1 (profile 1) reports to mgr 2
            (2, 2, "Management", None, "2026-01-01"),  # manager1 (profile 2) links to user 2
            (3, 3, "Management", None, "2026-01-01"),  # manager2 (profile 3) links to user 3
            (4, 5, "Engineering", 2, "2026-01-01"),  # employee2 (profile 4) reports to mgr 2
        ]
    elif mode == 'manager':
        profiles_data = [
            (1, 4, "Engineering", 2, "2026-01-01"),  # employee1 (profile 1) reports to mgr 2
            (2, 2, "Management", None, "2026-01-01"),  # manager1 (profile 2) links to user 2
            (3, 3, "Management", None, "2026-01-01"),  # manager2 (profile 3) links to user 3
            (4, 5, "QA", 3, "2026-01-15"),           # employee2 (profile 4) reports to mgr 3
        ]
    else:  # employee
        profiles_data = [
            (1, 4, "Engineering", 2, "2026-01-01"),  # employee1 (profile 1) links to user 4, reports to mgr 2
            (2, 2, "Management", None, "2026-01-01"),  # manager1 (profile 2) links to user 2
        ]
        
    cursor.executemany(
        "INSERT INTO employee_profiles (id, employee_id, department, manager_id, joined_at) VALUES (?, ?, ?, ?, ?);",
        profiles_data
    )
    
    # 4. Employee skills
    if mode == 'real_gemini':
        cursor.execute("INSERT INTO skills (id, name, category) VALUES (1, 'Python', 'Backend');")
        cursor.execute("INSERT INTO employee_skills (employee_id, skill_id, proficiency) VALUES (1, 1, 'Advanced');")
        
    # 5. Projects
    if mode == 'manager':
        projects_data = [
            (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
            (2, "Beta Legacy", "Legacy app support", "2025-01-01", "2026-01-01", "COMPLETED", 2, 50, "ON_TRACK"),    # Manager 1
            (3, "Gamma API", "Mobile backend services", "2026-06-01", "2026-10-01", "ACTIVE", 3, 80, "ON_TRACK"),   # Manager 2
        ]
    elif mode == 'employee':
        projects_data = [
            (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
            (2, "Beta Portal", "Legacy app support", "2026-06-01", "2026-12-01", "ACTIVE", 2, 50, "ON_TRACK"),      # Manager 1
            (3, "Gamma API", "Mobile backend services", "2026-06-01", "2026-10-01", "ACTIVE", 3, 80, "ON_TRACK"),   # Manager 2
        ]
    else:  # real_gemini, scheduler_ai
        projects_data = [
            (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
        ]
    cursor.executemany(
        "INSERT INTO projects (id, name, description, start_date, end_date, status, manager_id, total_story_pts, health_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        projects_data
    )
    
    # 6. Milestones
    if mode in ('real_gemini', 'scheduler_ai'):
        overdue_date = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO milestones (id, project_id, title, due_date, story_points, status) VALUES (1, 1, 'Design Review', ?, 20, 'NOT_STARTED');",
            (overdue_date,)
        )
    
    # 7. Allocations
    if mode == 'employee':
        allocations_data = [
            (1, 1, 1, 50, "2026-06-01", "2026-06-30", 1),
            (2, 1, 2, 30, "2026-06-01", "2026-06-30", 1),
        ]
    elif mode in ('real_gemini', 'scheduler_ai'):
        allocations_data = [
            (1, 1, 1, 60, "2026-06-01", "2026-12-31", 1),
            (2, 4, 1, 100, "2026-06-01", "2026-12-31", 1),
        ]
    else: # manager
        allocations_data = []
        
    if allocations_data:
        cursor.executemany(
            "INSERT INTO allocations (id, employee_id, project_id, utilisation_percent, from_date, to_date, is_active) VALUES (?, ?, ?, ?, ?, ?, ?);",
            allocations_data
        )
        
    # 8. System config
    if mode == 'real_gemini':
        cursor.execute("INSERT INTO system_config (id, llm_provider, llm_api_key, scheduler_interval, max_weekly_hours) VALUES (1, 'gemini', '', 4, 40);")
    else:
        cursor.execute("INSERT INTO system_config (id, llm_provider, llm_api_key, scheduler_interval, max_weekly_hours) VALUES (1, 'ollama', 'mock-key', 4, 40);")
        
    conn.commit()
    conn.close()
    print("Test database set up successfully.")
