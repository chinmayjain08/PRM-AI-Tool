from client.utils.display import draw_box
from client.utils.input_helpers import prompt_choice


def show_manage_users_menu() -> None:
    while True:
        draw_box("MANAGE USERS")
        options = [
            "Create User",
            "View All Users",
            "Reset User Password",
            "Deactivate User",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.admin.create_user import show_create_user
            show_create_user()
        elif choice == 2:
            from client.screens.admin.view_all_users import show_view_all_users
            show_view_all_users()
        elif choice == 3:
            from client.screens.admin.reset_password import show_reset_password
            show_reset_password()
        elif choice == 4:
            from client.screens.admin.deactivate_user import show_deactivate_user
            show_deactivate_user()
        elif choice == 5:
            break
