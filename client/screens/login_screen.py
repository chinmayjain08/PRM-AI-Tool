import sys
from client.api_client import auth_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_non_empty, prompt_password


def show_login_screen() -> tuple[str, str, str]:
    """
    Shows the application start screen.
    Returns (access_token, role, full_name) on successful login.
    """
    while True:
        draw_box("PROJECT & RESOURCE MANAGEMENT TOOL", "Learn & Code — Final Project")
        print("  1. Login")
        print("  2. Exit\n")
        choice = input("Enter option: ").strip()

        if choice == "1":
            result = _attempt_login()
            if result:
                return result
        elif choice == "2":
            print("\nGoodbye.")
            sys.exit(0)
        else:
            print_error("Enter 1 or 2.")


def _attempt_login() -> tuple | None:
    """Prompts for credentials and calls the server. Returns None on failure."""
    username = prompt_non_empty("Username")
    password = prompt_password("Password")

    try:
        response = auth_api.login(username, password)
    except ServerError as error:
        print_error(str(error))
        return None

    if response.get("force_password_change"):
        from client.api_client.http_client import HttpClient
        HttpClient.set_token(response["access_token"])
        _show_change_password_screen()

    return response["access_token"], response["role"], response["full_name"]


def _show_change_password_screen() -> None:
    """Forces the user to change their password before accessing any menu."""
    while True:
        draw_box("CHANGE PASSWORD", "You must set a new password to continue.")
        new_pw  = prompt_password("New Password")
        confirm = prompt_password("Confirm Password")

        if new_pw != confirm:
            print_error("Passwords do not match. Try again.")
            continue

        try:
            auth_api.change_password(new_pw, confirm)
            print_success("Password updated. Welcome! ✓")
            return
        except ServerError as error:
            print_error(str(error))
