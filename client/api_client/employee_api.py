from client.api_client.http_client import HttpClient


def fetch_my_allocations():
    return HttpClient.get("/employee/allocations")


def fetch_active_allocations_for_week(week_start: str):
    params = {}
    if week_start:
        params["week_start"] = week_start
    return HttpClient.get("/employee/active-allocations", params=params)


def fetch_timesheet_history():
    return HttpClient.get("/employee/timesheets")


def fetch_week_detail(week_start: str):
    return HttpClient.get(f"/employee/timesheets/{week_start}")


def submit_timesheet(week_start: str, entries: list):
    return HttpClient.post("/employee/timesheets", {
        "week_start": week_start,
        "entries": entries,
    })


def fetch_missed_weeks():
    return HttpClient.get("/employee/missed-weeks")
