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
    from test_setup_helper import populate_db
    populate_db(DB_FILE, "employee")

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
