import requests
import sys

BASE_URL = "http://localhost:8000"

def run_tests():
    print("1. Logging in as Admin...")
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Chinmay@08"})
    if r.status_code != 200:
        print(f"FAILED Admin login: {r.status_code} - {r.text}")
        sys.exit(1)
    
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in successfully.")

    print("\n2. Creating a Manager user...")
    manager_data = {
        "full_name": "Delivery Manager",
        "email": "manager@prmtool.com",
        "username": "manager1",
        "temp_password": "Manager@123",
        "role": "MANAGER",
        "department": "DELIVERY"
    }
    r = requests.post(f"{BASE_URL}/admin/users", json=manager_data, headers=headers)
    if r.status_code != 201:
        print(f"FAILED Create Manager: {r.status_code} - {r.text}")
        sys.exit(1)
    manager_id = r.json()["id"]
    print(f"Manager created with ID: {manager_id}")

    print("\n3. Creating an Employee user...")
    employee_data = {
        "full_name": "Developer Employee",
        "email": "employee@prmtool.com",
        "username": "employee1",
        "temp_password": "Employee@123",
        "role": "EMPLOYEE",
        "department": "ENGINEERING"
    }
    r = requests.post(f"{BASE_URL}/admin/users", json=employee_data, headers=headers)
    if r.status_code != 201:
        print(f"FAILED Create Employee: {r.status_code} - {r.text}")
        sys.exit(1)
    employee_user_id = r.json()["id"]
    print(f"Employee User created with ID: {employee_user_id}")

    print("\n4. Verifying all users list...")
    r = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    users = r.json()
    print(f"Total Users in DB: {len(users)}")
    assert any(u["username"] == "manager1" for u in users)
    assert any(u["username"] == "employee1" for u in users)

    print("\n5. Verifying employees list...")
    r = requests.get(f"{BASE_URL}/admin/employees", headers=headers)
    employees = r.json()
    print(f"Total Employees in DB: {len(employees)}")
    employee = next((e for e in employees if e["user_id"] == employee_user_id), None)
    assert employee is not None
    employee_id = employee["id"]
    print(f"Employee Profile ID: {employee_id}")

    print("\n6. Creating a Project...")
    project_data = {
        "name": "Alpha Portal",
        "description": "Customer web portal",
        "start_date": "2026-06-01",
        "end_date": "2026-09-01",
        "status": "ACTIVE",
        "manager_id": manager_id,
        "total_story_pts": 100
    }
    r = requests.post(f"{BASE_URL}/admin/projects", json=project_data, headers=headers)
    if r.status_code != 201:
        print(f"FAILED Create Project: {r.status_code} - {r.text}")
        sys.exit(1)
    project_id = r.json()["id"]
    print(f"Project created with ID: {project_id}")

    print("\n7. Adding a Milestone to Project...")
    milestone_data = {
        "title": "Design Complete",
        "due_date": "2026-07-01",
        "story_points": 30
    }
    r = requests.post(f"{BASE_URL}/admin/projects/{project_id}/milestones", json=milestone_data, headers=headers)
    if r.status_code != 201:
        print(f"FAILED Create Milestone: {r.status_code} - {r.text}")
        sys.exit(1)
    milestone_id = r.json()["id"]
    print(f"Milestone created with ID: {milestone_id}")

    print("\n8. Adding a Skill to Employee...")
    skill_data = {
        "skill_name": "Python",
        "category": "Backend",
        "proficiency": "Advanced"
    }
    r = requests.post(f"{BASE_URL}/admin/employees/{employee_id}/skills", json=skill_data, headers=headers)
    if r.status_code != 201:
        print(f"FAILED Add Skill: {r.status_code} - {r.text}")
        sys.exit(1)
    skill_id = r.json()["skill_id"]
    print(f"Skill added: {r.json()}")

    print("\n9. Updating Skill Proficiency...")
    r = requests.put(f"{BASE_URL}/admin/employees/{employee_id}/skills/{skill_id}", json={"proficiency": "Intermediate"}, headers=headers)
    print(f"Proficiency update status: {r.status_code} - {r.json()}")
    assert r.status_code == 200

    print("\n10. Fetching Employee Skills...")
    r = requests.get(f"{BASE_URL}/admin/employees/{employee_id}/skills", headers=headers)
    skills = r.json()
    print(f"Employee skills: {skills}")
    assert any(s["skill_name"] == "Python" and s["proficiency"] == "Intermediate" for s in skills)

    print("\n11. Fetching System Config...")
    r = requests.get(f"{BASE_URL}/admin/config", headers=headers)
    config = r.json()
    print(f"System Config: {config}")

    print("\n12. Updating System Config...")
    r = requests.put(f"{BASE_URL}/admin/config", json={"llm_provider": "ollama", "max_weekly_hours": 40}, headers=headers)
    print(f"Config update status: {r.status_code} - {r.json()}")
    assert r.status_code == 200

    print("\nALL ADMIN API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
