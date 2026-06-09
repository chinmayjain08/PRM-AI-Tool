from client.api_client.http_client import HttpClient


def fetch_dashboard():
    return HttpClient.get("/manager/dashboard")


def fetch_employee_detail(employee_id: int):
    return HttpClient.get(f"/manager/employees/{employee_id}")


def fetch_my_projects():
    return HttpClient.get("/manager/projects")


def fetch_project_detail(project_id: int):
    return HttpClient.get(f"/manager/projects/{project_id}")


def create_allocation(data: dict):
    return HttpClient.post("/manager/allocations", data)


def end_allocation(allocation_id: int):
    return HttpClient.delete(f"/manager/allocations/{allocation_id}")


def fetch_team_timesheets(week_start: str = None):
    params = {}
    if week_start:
        params["week_start"] = week_start
    return HttpClient.get("/manager/timesheets", params=params)


def ai_skill_match(requirement: str):
    return HttpClient.post("/manager/ai/skill-match", {"requirement": requirement})


def ai_risk_summary(project_id: int):
    return HttpClient.get(f"/manager/ai/risk-summary/{project_id}")
