"""
Application entry point.
Handles login, routes to the correct role menu.
"""

import sys

from client.api_client.http_client import HttpClient
from client.screens.login_screen import show_login_screen
from client.screens.admin.admin_menu import show_admin_menu
from client.screens.manager.manager_menu import show_manager_menu
from client.screens.employee.employee_menu import show_employee_menu


# Dictionary dispatch — adding a new role = adding one key here.
# Open/Closed Principle: existing code is not modified.
ROLE_TO_MENU = {
    "ADMIN":    show_admin_menu,
    "MANAGER":  show_manager_menu,
    "EMPLOYEE": show_employee_menu,
}


def main() -> None:
    try:
        token, role, full_name = show_login_screen()
        HttpClient.set_token(token)
        _launch_menu_for_role(role)
    except KeyboardInterrupt:
        print("\n\nGoodbye.")
        sys.exit(0)


def _launch_menu_for_role(role: str) -> None:
    """Routes the logged-in user to their role-specific menu."""
    menu_function = ROLE_TO_MENU.get(role)
    if menu_function is None:
        raise ValueError(f"Unknown role received from server: '{role}'")
    menu_function()


if __name__ == "__main__":
    main()
