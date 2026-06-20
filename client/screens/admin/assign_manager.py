from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, confirm_action


def show_assign_manager() -> None:
    while True:
        draw_box("ASSIGN MANAGER TO EMPLOYEE")
        emp_user_id = prompt_integer("Enter Employee User ID (or 0 to cancel)", 0, 99999)
        if emp_user_id == 0:
            return

        mgr_user_id = prompt_integer("Enter Manager User ID (or 0 to cancel)", 0, 99999)
        if mgr_user_id == 0:
            return

        if confirm_action(f"Assign Manager (ID: {mgr_user_id}) to Employee (ID: {emp_user_id})?"):
            try:
                res = admin_api.assign_manager(emp_user_id, mgr_user_id)
                print_success(res.get("message", "Manager assigned successfully."))
                return
            except ServerError as error:
                print_error(str(error))
