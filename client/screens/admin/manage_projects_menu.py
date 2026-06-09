from client.utils.display import draw_box
from client.utils.input_helpers import prompt_choice


def show_manage_projects_menu() -> None:
    while True:
        draw_box("MANAGE PROJECTS")
        options = [
            "Create Project",
            "View All Projects",
            "Update Project Profile",
            "Manage Milestones",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.admin.create_project import show_create_project
            show_create_project()
        elif choice == 2:
            from client.screens.admin.view_all_projects import show_view_all_projects
            show_view_all_projects()
        elif choice == 3:
            from client.screens.admin.update_project import show_update_project
            show_update_project()
        elif choice == 4:
            from client.screens.admin.manage_milestones import show_manage_milestones
            show_manage_milestones()
        elif choice == 5:
            break
