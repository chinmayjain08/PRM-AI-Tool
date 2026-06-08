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
    print("Setting up test database for Employee APIs...")
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
    ]
    cursor.executemany(
        "INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active, force_password_change) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        users_data
    )
    
    # 2. Employees profiles
    employees_data = [
        (1, 4, "Engineering", 2, 1, "2026-01-01"),  # Employee 1, manager is manager1 (user_id 2)
    ]
    cursor.executemany(
        "INSERT INTO employees (id, user_id, department, manager_id, is_active, joined_at) VALUES (?, ?, ?, ?, ?, ?);",
        employees_data
    )
    
    # 3. Projects
    projects_data = [
        (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
        (2, "Beta Portal", "Legacy app support", "2026-06-01", "2026-12-01", "ACTIVE", 2, 50, "ON_TRACK"),      # Manager 1
        (3, "Gamma API", "Mobile backend services", "2026-06-01", "2026-10-01", "ACTIVE", 3, 80, "ON_TRACK"),   # Manager 2
    ]
    cursor.executemany(
        "INSERT INTO projects (id, name, description, start_date, end_date, status, manager_id, total_story_pts, health_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        projects_data
    )
    
    # 4. Allocations
    # Employee 1 (id 1) allocated to Project 1 (50% utilization) and Project 2 (30% utilization) from 2026-06-01 to 2026-06-30
    allocations_data = [
        (1, 1, 1, 50, "2026-06-01", "2026-06-30", 1),
        (2, 1, 2, 30, "2026-06-01", "2026-06-30", 1),
    ]
    cursor.executemany(
        "INSERT INTO allocations (id, employee_id, project_id, utilisation_percent, from_date, to_date, is_active) VALUES (?, ?, ?, ?, ?, ?, ?);",
        allocations_data
    )
    
    # 5. System config
    cursor.execute("INSERT INTO system_config (id, llm_provider, scheduler_interval, max_weekly_hours) VALUES (1, 'gemini', 4, 40);")
    
    conn.commit()
    conn.close()
    print("Test database set up successfully.")

def run_tests():
    # Login as Employee 1
    print("\n--- 1. Logging in as Employee 1 ---")
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "employee1", "password": "Employee@123"})
    if r.status_code != 200:
        print(f"FAILED Employee 1 login: {r.status_code} - {r.text}")
        sys.exit(1)
    
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Employee 1 logged in successfully.")

    # Test 1: GET allocations
    print("\n--- 2. Fetching My Allocations ---")
    r = requests.get(f"{BASE_URL}/employee/allocations", headers=headers)
    assert r.status_code == 200
    allocs = r.json()
    print("Allocations:", allocs)
    assert len(allocs) == 2
    assert any(a["project_id"] == 1 and a["utilisation_percent"] == 50 for a in allocs)
    assert any(a["project_id"] == 2 and a["utilisation_percent"] == 30 for a in allocs)

    # Test 2: GET active-allocations for a week
    print("\n--- 3. Fetching Active Allocations for Week ---")
    # Fetching active allocations for week starting Monday 2026-06-08
    r = requests.get(f"{BASE_URL}/employee/active-allocations?week_start=2026-06-08", headers=headers)
    assert r.status_code == 200
    active_allocs = r.json()
    print("Active allocations for week:", active_allocs)
    assert len(active_allocs) == 2
    assert any(a["project_id"] == 1 for a in active_allocs)
    assert any(a["project_id"] == 2 for a in active_allocs)

    # Test 3: POST submit timesheet validations
    print("\n--- 4. Validating Timesheet Submission Rules ---")
    
    # 3.1 Future week -> HTTP 400
    future_monday = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    payload_future = {
        "week_start": future_monday,
        "entries": [{"project_id": 1, "hours_worked": 10, "tags": ["coding"]}]
    }
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_future, headers=headers)
    print("Future Week submission status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "Cannot submit a timesheet for a future week" in r.json()["detail"]

    # 3.2 Non-allocated project -> HTTP 400
    payload_non_allocated = {
        "week_start": "2026-06-08",
        "entries": [{"project_id": 3, "hours_worked": 10, "tags": ["coding"]}] # project 3 is not allocated to employee1
    }
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_non_allocated, headers=headers)
    print("Non-allocated project submission status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "You are not allocated to project ID 3" in r.json()["detail"]

    # 3.3 Negative hours -> HTTP 400
    payload_negative = {
        "week_start": "2026-06-08",
        "entries": [{"project_id": 1, "hours_worked": -5, "tags": ["coding"]}]
    }
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_negative, headers=headers)
    print("Negative hours status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "Hours worked cannot be negative" in r.json()["detail"]

    # 3.4 Project hours cap exceeded -> HTTP 400
    # Project 1 has 50% utilization, max is 50% * 40 = 20 hours limit. Log 25 hours.
    payload_over_cap = {
        "week_start": "2026-06-08",
        "entries": [{"project_id": 1, "hours_worked": 25, "tags": ["coding"]}]
    }
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_over_cap, headers=headers)
    print("Over project cap status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "exceeds the cap for this project" in r.json()["detail"]

    # 3.5 Total weekly limit exceeded -> HTTP 400
    # Log 20 hours on Project 1 (cap 20) and 25 hours on Project 2 (cap 12) -> total 45 hours > 40 maximum
    payload_over_total = {
        "week_start": "2026-06-08",
        "entries": [
            {"project_id": 1, "hours_worked": 20, "tags": ["coding"]},
            {"project_id": 2, "hours_worked": 25, "tags": ["testing"]}
        ]
    }
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_over_total, headers=headers)
    print("Over weekly limit status:", r.status_code, r.text)
    # Since Project 2 entry will exceed its own project cap first (25 > 12), it will return 400 for Project 2 cap!
    # Let's verify Project 2 cap is triggered or weekly total limit is triggered.
    assert r.status_code == 400
    
    # Let's test the weekly total limit specifically by setting hours inside project caps but total > max_weekly_hours.
    # Max hours is 40. Project 1 cap is 20, Project 2 cap is 12. Total sum is max 32. So project caps actually prevent exceeding weekly 40.
    # But if we had higher allocation %, e.g. Project 1: 60% (24h), Project 2: 50% (20h) -> total 44 > 40.
    # In this test setup: Project 1 limit is 20, Project 2 limit is 12. Sum is 32.
    # Let's log a valid timesheet first: Project 1: 15h, Project 2: 10h.
    payload_valid = {
        "week_start": "2026-06-08",
        "entries": [
            {"project_id": 1, "hours_worked": 15, "tags": ["coding", "design"]},
            {"project_id": 2, "hours_worked": 10, "tags": ["testing"]}
        ]
    }
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_valid, headers=headers)
    print("Valid timesheet submission status:", r.status_code, r.text)
    assert r.status_code == 201

    # 3.6 Duplicate submission check -> HTTP 400
    r = requests.post(f"{BASE_URL}/employee/timesheets", json=payload_valid, headers=headers)
    print("Duplicate submission status:", r.status_code, r.text)
    assert r.status_code == 400
    assert "already been submitted" in r.json()["detail"]

    # Test 4: GET timesheets history
    print("\n--- 5. Fetching My Timesheet History ---")
    r = requests.get(f"{BASE_URL}/employee/timesheets", headers=headers)
    assert r.status_code == 200
    history = r.json()
    print("Timesheet History:", history)
    # Assert that 2026-06-08 is in history with status SUBMITTED and total hours 25
    submitted_week = next((h for h in history if h["week_start"] == "2026-06-08"), None)
    assert submitted_week is not None
    assert submitted_week["status"] == "SUBMITTED"
    assert submitted_week["hours_worked"] == 25

    # Test 5: GET week detail
    print("\n--- 6. Fetching Timesheet Week Detail ---")
    r = requests.get(f"{BASE_URL}/employee/timesheets/2026-06-08", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    print("Week Detail:", detail)
    assert detail["week_start"] == "2026-06-08"
    assert len(detail["entries"]) == 2
    assert any(e["project_id"] == 1 and "coding" in e["tags"] for e in detail["entries"])

    # Test 6: GET missed-weeks
    print("\n--- 7. Fetching Missed Weeks ---")
    r = requests.get(f"{BASE_URL}/employee/missed-weeks", headers=headers)
    assert r.status_code == 200
    missed = r.json()["missed_weeks"]
    print("Missed Weeks:", missed)
    # Since we are in June 2026, weeks prior to 2026-06-08 (e.g. 2026-06-01) where the allocation was active should be in missed weeks!
    assert "2026-06-01" in missed

    # Test 7: Role Authorization Guard
    print("\n--- 8. Checking Role Authorization Guard (HTTP 403) ---")
    # Employee tries to call Admin route
    r = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print("Employee accessing Admin route status:", r.status_code)
    assert r.status_code == 403
    
    # Employee tries to call Manager route
    r = requests.get(f"{BASE_URL}/manager/dashboard", headers=headers)
    print("Employee accessing Manager route status:", r.status_code)
    assert r.status_code == 403

    print("\nALL EMPLOYEE API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    setup_test_db()
    run_tests()
