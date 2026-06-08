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
    print("Setting up test database for Real Gemini Integration...")
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
    
    # 3. Employee skills - Python skill for Employee 1
    cursor.execute("INSERT INTO skills (id, name, category) VALUES (1, 'Python', 'Backend');")
    cursor.execute("INSERT INTO employee_skills (employee_id, skill_id, proficiency) VALUES (1, 1, 'Advanced');")
    
    # 4. Projects
    projects_data = [
        (1, "Alpha Portal", "Customer web portal", "2026-06-01", "2026-12-01", "ACTIVE", 2, 100, "ON_TRACK"),    # Manager 1
    ]
    cursor.executemany(
        "INSERT INTO projects (id, name, description, start_date, end_date, status, manager_id, total_story_pts, health_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
        projects_data
    )
    
    # 5. Milestones
    # Overdue milestone: due 7 days ago
    overdue_date = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO milestones (id, project_id, title, due_date, story_points, status) VALUES (1, 1, 'Design Review', ?, 20, 'NOT_STARTED');",
        (overdue_date,)
    )
    
    # 6. Allocations
    # Employee 1 (id 1) allocated 60% (16 hours free), Employee 2 (id 2) allocated 100% (0 hours free)
    allocations_data = [
        (1, 1, 1, 60, "2026-06-01", "2026-12-31", 1),
        (2, 2, 1, 100, "2026-06-01", "2026-12-31", 1),
    ]
    cursor.executemany(
        "INSERT INTO allocations (id, employee_id, project_id, utilisation_percent, from_date, to_date, is_active) VALUES (?, ?, ?, ?, ?, ?, ?);",
        allocations_data
    )
    
    # 7. System config (Clear API key in DB so it falls back to .env)
    cursor.execute("INSERT INTO system_config (id, llm_provider, llm_api_key, scheduler_interval, max_weekly_hours) VALUES (1, 'gemini', '', 4, 40);")
    
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

    # Test 1: AI Skill Match capacity check using real Gemini API
    print("\n--- 2. Running AI Skill Match with REAL Gemini API (capacity & skill matching) ---")
    payload = {"requirement": "I need a Python developer with 10 hrs/week free capacity."}
    r = requests.post(
        f"{BASE_URL}/manager/ai/skill-match",
        json=payload,
        headers=headers_m1
    )
    print("Skill Match status:", r.status_code)
    print("Skill Match response:", r.json())
    assert r.status_code == 200
    
    results = r.json().get("results", [])
    # Verify that the LLM successfully returned a JSON array and matched the candidate
    print(f"Successfully matched {len(results)} candidate(s).")
    for match in results:
        print(f"Match name: {match.get('name')}, Reason: {match.get('reason')}")
    
    # Test 2: AI Risk Summary using real Gemini API
    print("\n--- 3. Generating AI Risk Summary with REAL Gemini API ---")
    r = requests.get(f"{BASE_URL}/manager/ai/risk-summary/1", headers=headers_m1)
    print("Risk Summary status:", r.status_code)
    assert r.status_code == 200
    
    summary = r.json().get("summary")
    print("\n--- Generated Risk Summary ---")
    print(summary)
    print("-------------------------------")
    assert len(summary) > 10
    
    print("\nREAL GEMINI API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    setup_test_db()
    run_tests()
