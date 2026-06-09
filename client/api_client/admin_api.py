from client.api_client.http_client import HttpClient

# ── Users ──────────────────────────────────────────────────────────────────────
def fetch_all_users():
    return HttpClient.get("/admin/users")

def create_user(data: dict):
    return HttpClient.post("/admin/users", data)

def reset_user_password(user_id: int, temp_password: str):
    return HttpClient.post(f"/admin/users/{user_id}/reset-password", {"temp_password": temp_password})

def deactivate_user(user_id: int):
    return HttpClient.post(f"/admin/users/{user_id}/deactivate")

def reactivate_user(user_id: int):
    return HttpClient.post(f"/admin/users/{user_id}/reactivate")

# ── Employees ──────────────────────────────────────────────────────────────────
def fetch_all_employees(status: str = None, dept: str = None):
    params = {}
    if status:
        params["status"] = status
    if dept:
        params["dept"] = dept
    return HttpClient.get("/admin/employees", params=params)

def fetch_employee(employee_id: int):
    return HttpClient.get(f"/admin/employees/{employee_id}")

def update_employee(employee_id: int, data: dict):
    return HttpClient.put(f"/admin/employees/{employee_id}", data)

def deactivate_employee(employee_id: int):
    return HttpClient.post(f"/admin/employees/{employee_id}/deactivate")

def assign_manager(emp_user_id: int, mgr_user_id: int):
    return HttpClient.post("/admin/employees/assign-manager", {"employee_user_id": emp_user_id, "manager_user_id": mgr_user_id})

# ── Skills ─────────────────────────────────────────────────────────────────────
def fetch_employee_skills(employee_id: int):
    return HttpClient.get(f"/admin/employees/{employee_id}/skills")

def add_skill(employee_id: int, data: dict):
    return HttpClient.post(f"/admin/employees/{employee_id}/skills", data)

def update_skill(employee_id: int, skill_id: int, prof: str):
    return HttpClient.put(f"/admin/employees/{employee_id}/skills/{skill_id}", {"proficiency": prof})

def remove_skill(employee_id: int, skill_id: int):
    return HttpClient.delete(f"/admin/employees/{employee_id}/skills/{skill_id}")

# ── Projects ───────────────────────────────────────────────────────────────────
def fetch_all_projects():
    return HttpClient.get("/admin/projects")

def fetch_project(project_id: int):
    return HttpClient.get(f"/admin/projects/{project_id}")

def create_project(data: dict):
    return HttpClient.post("/admin/projects", data)

def update_project(project_id: int, data: dict):
    return HttpClient.put(f"/admin/projects/{project_id}", data)

# ── Milestones ─────────────────────────────────────────────────────────────────
def fetch_milestones(project_id: int):
    return HttpClient.get(f"/admin/projects/{project_id}/milestones")

def add_milestone(project_id: int, data: dict):
    return HttpClient.post(f"/admin/projects/{project_id}/milestones", data)

def update_milestone_status(milestone_id: int, status: str):
    return HttpClient.put(f"/admin/milestones/{milestone_id}", {"status": status})

# ── Allocations & Config ───────────────────────────────────────────────────────
def fetch_all_allocations(emp_id: int = None, proj_id: int = None):
    params = {}
    if emp_id is not None:
        params["employee_id"] = emp_id
    if proj_id is not None:
        params["project_id"] = proj_id
    return HttpClient.get("/admin/allocations", params=params)

def fetch_system_config():
    return HttpClient.get("/admin/config")

def update_system_config(data: dict):
    return HttpClient.put("/admin/config", data)
