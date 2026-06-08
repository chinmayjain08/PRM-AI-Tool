import os
import sqlite3
import sys
import requests
from datetime import date, timedelta

sys.stdout.reconfigure(encoding='utf-8')


# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.security import hash_password

BASE_URL = "http://localhost:8000"
DB_FILE = "test.db"

def setup_test_db():
    print("Setting up test database for Manager APIs...")
    if not os.path.exists(DB_FILE):
        print("Error: test.db does not exist. Please run alembic migrations first.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_FILE)
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
    
    # 1. Users
    users_data = [
        (1, "admin", "admin@prmtool.com", "System Admin", admin_pw, "ADMIN", 1, 0),
        (2, "manager1", "manager1@prmtool.com", "Project Manager One", mgr_pw, "MANAGER", 1, 0),
        (3, "manager2", "manager2@prmtool.com", "Project Manager Two", mgr_pw, "MANAGER", 1, 0),
        (4, "employee1", "employee1@prmtool.com", "Developer Employee One", emp_pw, "EMPLOYEE", 1, 0),
        (5, "employee2", "employee2@prmtool.com", "QA Employee Two", emp_pw, "EMPLOYEE", 1, 0),
    ]
    cursor.executemany(
        "INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active, force_password_change) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        users_data
    )
    
    # 2. Employees profiles
    employees_data = [
        (1, 4, "Engineering", 2, 1, "2026-01-01"),  # Employee 1, manager is manager1 (user_id 2)
        (2, 5, "QA", 3, 1, "2026-01-15"),           # Employee 2, manager is manager2 (user_id 3)
    ]
    cursor.executemany(
        "INSERT INTO employees (id, user_id, department, manager_id, is_active, joined_at) VALUES (?, ?, ?, ?, ?, ?);",
        employees_data
    )
    
    # 3. Projects
    projects_data = [
        (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
        (2, "Beta Legacy", "Legacy app support", "2025-01-01", "2026-01-01", "COMPLETED", 2, 50, "ON_TRACK"),    # Manager 1
        (3, "Gamma API", "Mobile backend services", "2026-06-01", "2026-10-01", "ACTIVE", 3, 80, "ON_TRACK"),   # Manager 2
    ]
    cursor.executemany(
        "INSERT INTO projects (id, name, description, start_date, end_date, status, manager_id, total_story_pts, health_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        projects_data
    )
    
    # 4. System config
    cursor.execute("INSERT INTO system_config (id, llm_provider, scheduler_interval, max_weekly_hours) VALUES (1, 'gemini', 4, 40);")
    
    conn.commit()
    conn.close()
    print("Test database set up successfully.")

def run_tests():
    # Login as Manager 1
    print("\n--- 1. Logging in as Manager 1 ---")
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "manager1", "password": "Manager@123"})
    if r.status_code != 200:
        print(f"FAILED Manager 1 login: {r.status_code} - {r.text}")
        sys.exit(1)
    
    token_m1 = r.json()["access_token"]
    headers_m1 = {"Authorization": f"Bearer {token_m1}"}
    print("Manager 1 logged in successfully.")

    # Login as Manager 2
    print("\n--- Logging in as Manager 2 ---")
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "manager2", "password": "Manager@123"})
    if r.status_code != 200:
        print(f"FAILED Manager 2 login: {r.status_code} - {r.text}")
        sys.exit(1)
    
    token_m2 = r.json()["access_token"]
    headers_m2 = {"Authorization": f"Bearer {token_m2}"}
    print("Manager 2 logged in successfully.")

    # Test 1: Dashboard list (Manager 1)
    print("\n--- 2. Fetching Manager 1 Dashboard ---")
    r = requests.get(f"{BASE_URL}/manager/dashboard", headers=headers_m1)
    assert r.status_code == 200
    dashboard = r.json()
    print("Dashboard:", dashboard)
    # Check that employee1 is on bench (since they have no allocations) and employee2 is not returned (different team)
    bench_ids = [e["id"] for e in dashboard["bench"]]
    assert 1 in bench_ids
    assert 2 not in bench_ids
    assert len(dashboard["allocated"]) == 0
    print("Dashboard verification passed.")

    # Test 2: Employee Detail Scope
    print("\n--- 3. Fetching Employee Details (Team vs External) ---")
    # Employee 1 (id 1) belongs to Manager 1 team -> HTTP 200
    r = requests.get(f"{BASE_URL}/manager/employees/1", headers=headers_m1)
    print("Employee 1 profile:", r.json())
    assert r.status_code == 200
    assert r.json()["full_name"] == "Developer Employee One"
    
    # Employee 2 (id 2) belongs to Manager 2 team -> HTTP 403 for Manager 1
    r = requests.get(f"{BASE_URL}/manager/employees/2", headers=headers_m1)
    print("Accessing Employee 2 response status:", r.status_code)
    assert r.status_code == 403

    # Test 3: Create Allocation
    print("\n--- 4. Creating and Validating Allocations ---")
    # 3.1 Allocation with from_date >= to_date -> HTTP 400
    alloc_invalid_date = {
        "employee_id": 1,
        "project_id": 1,
        "utilisation_percent": 50,
        "from_date": "2026-06-20",
        "to_date": "2026-06-10"
    }
    r = requests.post(f"{BASE_URL}/manager/allocations", json=alloc_invalid_date, headers=headers_m1)
    print("Invalid Date Allocation status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "From date must be before to date" in r.json()["detail"]

    # 3.2 Allocation on COMPLETED project -> HTTP 400
    alloc_completed = {
        "employee_id": 1,
        "project_id": 2, # Project 2 is COMPLETED
        "utilisation_percent": 50,
        "from_date": "2026-06-10",
        "to_date": "2026-06-20"
    }
    r = requests.post(f"{BASE_URL}/manager/allocations", json=alloc_completed, headers=headers_m1)
    print("Completed Project Allocation status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "Only ACTIVE or PLANNED projects" in r.json()["detail"]

    # 3.3 Allocation to another manager's project -> HTTP 400
    alloc_other_mgr = {
        "employee_id": 1,
        "project_id": 3, # Project 3 belongs to Manager 2
        "utilisation_percent": 50,
        "from_date": "2026-06-10",
        "to_date": "2026-06-20"
    }
    r = requests.post(f"{BASE_URL}/manager/allocations", json=alloc_other_mgr, headers=headers_m1)
    print("Another Manager's Project Allocation status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "You can only allocate to your own projects" in r.json()["detail"]

    # 3.4 Valid Allocation -> HTTP 201
    alloc_valid = {
        "employee_id": 1,
        "project_id": 1,
        "utilisation_percent": 60,
        "from_date": "2026-06-10",
        "to_date": "2026-06-20"
    }
    r = requests.post(f"{BASE_URL}/manager/allocations", json=alloc_valid, headers=headers_m1)
    print("Valid Allocation status:", r.status_code, r.text)
    assert r.status_code == 201
    allocation_id = r.json()["id"]

    # Verify dashboard shows employee1 as allocated
    r = requests.get(f"{BASE_URL}/manager/dashboard", headers=headers_m1)
    dashboard = r.json()
    print("Allocated dashboard section:", dashboard["allocated"])
    assert len(dashboard["bench"]) == 0
    assert len(dashboard["allocated"]) == 1
    assert dashboard["allocated"][0]["id"] == 1
    assert dashboard["allocated"][0]["utilisation"] == 60

    # 3.5 Over-utilisation -> HTTP 400
    alloc_overuse = {
        "employee_id": 1,
        "project_id": 1,
        "utilisation_percent": 50, # 60 + 50 = 110%
        "from_date": "2026-06-12",
        "to_date": "2026-06-18"
    }
    r = requests.post(f"{BASE_URL}/manager/allocations", json=alloc_overuse, headers=headers_m1)
    print("Over-utilisation status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "Maximum allowed is 100%" in r.json()["detail"]

    # Test 4: End Allocation
    print("\n--- 5. Ending and Scoping Allocations ---")
    # Try ending the allocation using Manager 2 (not the owner of Project 1) -> HTTP 400
    r = requests.delete(f"{BASE_URL}/manager/allocations/{allocation_id}", headers=headers_m2)
    print("Ending allocation by non-owner status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "You can only end allocations on your own projects" in r.json()["detail"]

    # End the allocation using Manager 1 -> HTTP 200
    r = requests.delete(f"{BASE_URL}/manager/allocations/{allocation_id}", headers=headers_m1)
    print("Ending allocation by owner status:", r.status_code, r.text)
    assert r.status_code == 200

    # Verify employee1 is back on bench
    r = requests.get(f"{BASE_URL}/manager/dashboard", headers=headers_m1)
    assert len(r.json()["bench"]) == 1

    # Test 5: Projects List and Scoping
    print("\n--- 6. Projects List and Scope ---")
    r = requests.get(f"{BASE_URL}/manager/projects", headers=headers_m1)
    projects = r.json()
    print("Manager 1 projects:", projects)
    assert r.status_code == 200
    assert len(projects) == 2
    assert any(p["name"] == "Alpha Portal" and p["health_icon"] == "🟢" for p in projects)
    
    # Fetch project details (scoped)
    r = requests.get(f"{BASE_URL}/manager/projects/1", headers=headers_m1)
    print("Project 1 details:", r.json())
    assert r.status_code == 200
    
    r = requests.get(f"{BASE_URL}/manager/projects/3", headers=headers_m1)
    print("Accessing Project 3 (Manager 2's) status:", r.status_code)
    assert r.status_code == 403

    # Test 6: Project Health calculation
    print("\n--- 7. Verifying Dynamic Project Health & Risk Flags ---")
    # Direct SQLite insert of an overdue milestone for Project 1
    print("Inserting overdue milestone in database...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO milestones (id, project_id, title, due_date, story_points, status) VALUES (1, 1, 'Design Review', '2026-06-01', 20, 'NOT_STARTED');"
    )
    conn.commit()
    conn.close()

    # Re-fetch project details. Due to overdue milestone, status should calculate as AT_RISK.
    r = requests.get(f"{BASE_URL}/manager/projects/1", headers=headers_m1)
    detail = r.json()
    print("Updated Project 1 Details (Health calculated):", detail["project"]["health_status"])
    print("Risk flags:", detail["risk_flags"])
    # Note: computed at query time / in project detail or health updates
    assert detail["project"]["health_status"] == "AT_RISK"
    assert len(detail["risk_flags"]) > 0
    assert "Design Review milestone is" in detail["risk_flags"][0]

    # Test 7: Timesheets
    print("\n--- 8. Fetching Team Timesheets ---")
    r = requests.get(f"{BASE_URL}/manager/timesheets", headers=headers_m1)
    print("Timesheets response:", r.status_code, r.json())
    assert r.status_code == 200

    # Test 8: AI Stubs
    print("\n--- 9. Verifying AI Endpoints Stubs ---")
    r = requests.post(f"{BASE_URL}/manager/ai/skill-match", json={"skills": ["Python"]}, headers=headers_m1)
    assert r.status_code == 200
    assert "AI Skill Match not yet configured" in r.json()["message"]

    r = requests.get(f"{BASE_URL}/manager/ai/risk-summary/1", headers=headers_m1)
    assert r.status_code == 200
    assert "AI Risk Summary not yet configured" in r.json()["message"]

    print("\nALL MANAGER API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    setup_test_db()
    run_tests()
