from datetime import datetime
from client.utils.display import draw_box
from client.utils.input_helpers import prompt_choice


def show_manager_menu(full_name: str) -> None:
    while True:
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M")
        draw_box("MANAGER DASHBOARD", f"Welcome, {full_name} | {current_time}")
        
        options = [
            "Resource Dashboard",
            "Allocate Resource",
            "My Projects",
            "View Team Timesheets",
            "AI Assistant",
            "Log Out"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.manager.resource_dashboard import show_resource_dashboard
            show_resource_dashboard()
        elif choice == 2:
            from client.screens.manager.allocate_resource import show_allocate_resource
            show_allocate_resource()
        elif choice == 3:
            from client.screens.manager.my_projects import show_my_projects
            show_my_projects()
        elif choice == 4:
            from client.screens.manager.timesheets_view import show_timesheets_view
            show_timesheets_view()
        elif choice == 5:
            from client.screens.manager.ai_assistant import show_ai_assistant
            show_ai_assistant()
        elif choice == 6:
            print("\nLogging out...\n")
            break
