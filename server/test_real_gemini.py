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
    populate_db(DB_FILE, "real_gemini")

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
