from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, confirm_action


def show_deactivate_user() -> None:
    while True:
        draw_box("DEACTIVATE USER ACCOUNT")
        u_id = prompt_integer("Enter Target User ID (or 0 to cancel)", 0, 99999)
        if u_id == 0:
            return

        if confirm_action(f"Deactivate user account (ID: {u_id})?"):
            try:
                res = admin_api.deactivate_user(u_id)
                print_success(res.get("message", "User account deactivated successfully."))
                return
            except ServerError as error:
                print_error(str(error))
