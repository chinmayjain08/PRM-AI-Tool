from client.api_client.http_client import HttpClient


def login(username: str, password: str) -> dict:
    return HttpClient.post("/auth/login", {"username": username, "password": password})


def change_password(new_password: str, confirm_password: str) -> dict:
    return HttpClient.post("/auth/change-password", {
        "new_password":     new_password,
        "confirm_password": confirm_password,
    })
