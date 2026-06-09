from datetime import datetime
from client.utils.display import draw_box
from client.utils.input_helpers import prompt_choice


def show_admin_menu(full_name: str) -> None:
    while True:
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M")
        draw_box("ADMIN DASHBOARD", f"Welcome, {full_name} | {current_time}")
        
        options = [
            "Manage Employees",
            "Manage Projects",
            "View All Allocations",
            "Manage Users",
            "System Configuration",
            "Log Out"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.admin.manage_employees_menu import show_manage_employees_menu
            show_manage_employees_menu()
        elif choice == 2:
            from client.screens.admin.manage_projects_menu import show_manage_projects_menu
            show_manage_projects_menu()
        elif choice == 3:
            from client.screens.admin.view_all_allocations import show_view_all_allocations
            show_view_all_allocations()
        elif choice == 4:
            from client.screens.admin.manage_users_menu import show_manage_users_menu
            show_manage_users_menu()
        elif choice == 5:
            from client.screens.admin.system_config import show_system_config
            show_system_config()
        elif choice == 6:
            print("\nLogging out...\n")
            break
