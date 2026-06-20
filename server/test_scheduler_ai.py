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
    populate_db(DB_FILE, "scheduler_ai")

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
        json={"llm_provider": "ollama", "llm_api_key": "mock-key", "max_weekly_hours": 40},
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
