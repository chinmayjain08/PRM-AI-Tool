from client.utils.display import draw_box
from client.utils.input_helpers import prompt_choice


def show_manage_employees_menu() -> None:
    while True:
        draw_box("MANAGE EMPLOYEES & ACCOUNTS")
        options = [
            "Create New Employee",
            "View All Employees (Profiles)",
            "View All User Accounts",
            "Update Employee Profile",
            "Manage Employee Skills",
            "Assign Manager to Employee",
            "Reset Employee Password",
            "Deactivate Employee/User",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.admin.create_user import show_create_user
            show_create_user()
        elif choice == 2:
            from client.screens.admin.view_all_employees import show_view_all_employees
            show_view_all_employees()
        elif choice == 3:
            from client.screens.admin.view_all_users import show_view_all_users
            show_view_all_users()
        elif choice == 4:
            from client.screens.admin.update_employee import show_update_employee
            show_update_employee()
        elif choice == 5:
            from client.screens.admin.manage_skills import show_manage_skills
            show_manage_skills()
        elif choice == 6:
            from client.screens.admin.assign_manager import show_assign_manager
            show_assign_manager()
        elif choice == 7:
            from client.screens.admin.reset_password import show_reset_password
            show_reset_password()
        elif choice == 8:
            from client.screens.admin.deactivate_employee import show_deactivate_employee
            show_deactivate_employee()
        elif choice == 9:
            break
