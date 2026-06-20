from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_non_empty, prompt_choice, confirm_action


def show_create_user() -> None:
    while True:
        draw_box("CREATE USER ACCOUNT")
        full_name = prompt_non_empty("Full Name")
        email = prompt_non_empty("Email Address")
        username = prompt_non_empty("Username")
        temp_pw = prompt_non_empty("Temporary Password")
        
        print("\nSelect User Role:")
        roles = ["ADMIN", "MANAGER", "EMPLOYEE"]
        role_idx = prompt_choice("Role", roles)
        role = roles[role_idx - 1]

        print("\nSelect Department:")
        departments = ["Engineering", "Delivery", "HR", "Finance", "Operations"]
        dept_idx = prompt_choice("Department", departments)
        dept = departments[dept_idx - 1].upper()

        payload = {
            "full_name": full_name,
            "email": email,
            "username": username,
            "temp_password": temp_pw,
            "role": role,
            "department": dept
        }

        if confirm_action("Save new user account?"):
            try:
                user = admin_api.create_user(payload)
                print_success(f"User account created with ID: {user.get('id')}.")
                return
            except ServerError as error:
                print_error(str(error))
