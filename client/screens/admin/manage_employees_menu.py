from client.utils.display import draw_box
from client.utils.input_helpers import prompt_choice


def show_manage_employees_menu() -> None:
    while True:
        draw_box("MANAGE EMPLOYEES")
        options = [
            "View All Employees",
            "Update Employee Profile",
            "Deactivate Employee",
            "Manage Employee Skills",
            "Assign Manager to Employee",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.admin.view_all_employees import show_view_all_employees
            show_view_all_employees()
        elif choice == 2:
            from client.screens.admin.update_employee import show_update_employee
            show_update_employee()
        elif choice == 3:
            from client.screens.admin.deactivate_employee import show_deactivate_employee
            show_deactivate_employee()
        elif choice == 4:
            from client.screens.admin.manage_skills import show_manage_skills
            show_manage_skills()
        elif choice == 5:
            from client.screens.admin.assign_manager import show_assign_manager
            show_assign_manager()
        elif choice == 6:
            break
