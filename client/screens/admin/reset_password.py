from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, prompt_non_empty, confirm_action


def show_reset_password() -> None:
    while True:
        draw_box("RESET USER PASSWORD")
        u_id = prompt_integer("Enter Target User ID (or 0 to cancel)", 0, 99999)
        if u_id == 0:
            return

        temp_pw = prompt_non_empty("Enter New Temporary Password")

        if confirm_action(f"Reset password for User (ID: {u_id})?"):
            try:
                res = admin_api.reset_user_password(u_id, temp_pw)
                print_success(res.get("message", "Password reset successfully."))
                return
            except ServerError as error:
                print_error(str(error))
