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
    print("Setting up test database for Scheduler & AI APIs...")
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
        (4, "employee1", "employee1@prmtool.com", "Developer Employee One", emp_pw, "EMPLOYEE", 1, 0),
        (5, "employee2", "employee2@prmtool.com", "Developer Employee Two", emp_pw, "EMPLOYEE", 1, 0),
    ]
    cursor.executemany(
        "INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active, force_password_change) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        users_data
    )
    
    # 2. Employees profiles
    employees_data = [
        (1, 4, "Engineering", 2, 1, "2026-01-01"),  # Employee 1, manager is manager1 (user_id 2)
        (2, 5, "Engineering", 2, 1, "2026-01-01"),  # Employee 2, manager is manager1 (user_id 2)
    ]
    cursor.executemany(
        "INSERT INTO employees (id, user_id, department, manager_id, is_active, joined_at) VALUES (?, ?, ?, ?, ?, ?);",
        employees_data
    )
    
    # 3. Projects
    # We set health_status to ON_TRACK initially; the scheduler will update it to AT_RISK because of the overdue milestone.
    projects_data = [
        (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
    ]
    cursor.executemany(
        "INSERT INTO projects (id, name, description, start_date, end_date, status, manager_id, total_story_pts, health_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        projects_data
    )
    
    # 4. Milestones
    # Overdue milestone: due 7 days ago
    overdue_date = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO milestones (id, project_id, title, due_date, story_points, status) VALUES (1, 1, 'Design Review', ?, 20, 'NOT_STARTED');",
        (overdue_date,)
    )
    
    # 5. Allocations
    # Employee 1 (id 1) allocated 60% (16 hours free), Employee 2 (id 2) allocated 100% (0 hours free)
    allocations_data = [
        (1, 1, 1, 60, "2026-06-01", "2026-12-31", 1),
        (2, 2, 1, 100, "2026-06-01", "2026-12-31", 1),
    ]
    cursor.executemany(
        "INSERT INTO allocations (id, employee_id, project_id, utilisation_percent, from_date, to_date, is_active) VALUES (?, ?, ?, ?, ?, ?, ?);",
        allocations_data
    )
    
    # 6. System config (LLM API Key starts as NULL/None to verify 503)
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

    # Login as Admin
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "NewAdmin@123"})
    token_admin = r.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # Test 1: LLM Key not configured -> HTTP 503
    print("\n--- 2. Checking AI Call fails when Key is missing ---")
    r = requests.post(
        f"{BASE_URL}/manager/ai/skill-match",
        json={"requirement": "I need a Python developer 10 hrs/week"},
        headers=headers_m1
    )
    print("AI Call response status:", r.status_code, r.text)
    assert r.status_code == 503
    assert "LLM API key is not set or is empty" in r.json()["detail"]

    # Test 2: Configuring LLM details
    print("\n--- 3. Configuring LLM Provider and API key ---")
    r = requests.put(
        f"{BASE_URL}/admin/config",
        json={"llm_provider": "gemini", "llm_api_key": "mock-key", "max_weekly_hours": 40},
        headers=headers_admin
    )
    assert r.status_code == 200
    print("API Key configured successfully.")

    # Test 3: AI Skill Match capacity check
    print("\n--- 4. Running AI Skill Match (Capacity filtering) ---")
    # 4.1 Match for "10 hrs/week" -> employee1 has 16 free hours, employee2 has 0. Only employee1 is qualified.
    r = requests.post(
        f"{BASE_URL}/manager/ai/skill-match",
        json={"requirement": "I need a Python developer 10 hrs/week"},
        headers=headers_m1
    )
    print("Skill Match 10 hrs/week status:", r.status_code, r.json())
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 1
    assert results[0]["name"] == "Developer Employee One"

    # 4.2 Match for "20 hrs/week" -> nobody has 20 free capacity -> returns empty results with a message
    r = requests.post(
        f"{BASE_URL}/manager/ai/skill-match",
        json={"requirement": "I need a Python developer 20 hrs/week"},
        headers=headers_m1
    )
    print("Skill Match 20 hrs/week status:", r.status_code, r.json())
    assert r.status_code == 200
    assert len(r.json()["results"]) == 0
    assert "No available employees match" in r.json()["message"]

    # Test 4: AI Risk Summary
    print("\n--- 5. Generating AI Risk Summary ---")
    r = requests.get(f"{BASE_URL}/manager/ai/risk-summary/1", headers=headers_m1)
    print("Risk Summary response status:", r.status_code, r.json())
    assert r.status_code == 200
    assert "summary" in r.json()
    assert len(r.json()["summary"]) > 50

    # Test 5: Running Background Scheduler tasks
    print("\n--- 6. Verifying Background Scheduler Tasks ---")
    
    # Import and run scheduler tasks directly in python process
    print("Triggering run_all_scheduled_tasks() directly...")
    from app.core.scheduler import run_all_scheduled_tasks
    run_all_scheduled_tasks()

    # Verify database update outcomes:
    # 5.1 Project health updated to AT_RISK because of the overdue milestone.
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT health_status FROM projects WHERE id = 1;")
    health = cursor.fetchone()[0]
    print("Scheduler-updated Project 1 Health:", health)
    assert health == "AT_RISK"

    # 5.2 Missed timesheets created for the past completed week for employee1 & employee2
    last_monday = (date.today() - timedelta(days=date.today().weekday() + 7)).strftime("%Y-%m-%d")
    cursor.execute("SELECT employee_id, status FROM timesheets WHERE week_start = ?;", (last_monday,))
    timesheets = cursor.fetchall()
    print("Generated missed timesheets:", timesheets)
    # Check that two missed rows were created (employee_id 1 and 2)
    assert len(timesheets) == 2
    assert all(t[1] == "MISSED" for t in timesheets)
    
    conn.close()
    print("\nALL SCHEDULER & AI API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    setup_test_db()
    run_tests()
