from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, prompt_optional, confirm_action


def show_update_employee() -> None:
    while True:
        draw_box("UPDATE EMPLOYEE PROFILE")
        emp_id = prompt_integer("Enter Employee Profile ID (or 0 to cancel)", 0, 99999)
        if emp_id == 0:
            return

        try:
            emp = admin_api.fetch_employee(emp_id)
        except ServerError as error:
            print_error(str(error))
            continue

        print(f"\nCurrent Profile:")
        print(f"  Name       : {emp.get('full_name')}")
        print(f"  Department : {emp.get('department') or 'none'}")
        print(f"  Status     : {'ACTIVE' if emp.get('is_active') else 'INACTIVE'}\n")

        new_dept = prompt_optional("New Department")
        active_str = prompt_optional("Is Active? (Y/N)").strip().upper()
        
        is_active = None
        if active_str == "Y":
            is_active = True
        elif active_str == "N":
            is_active = False

        data = {}
        if new_dept:
            data["department"] = new_dept
        if is_active is not None:
            data["is_active"] = is_active

        if not data:
            print_error("No fields entered to update.")
            continue

        if confirm_action("Save changes?"):
            try:
                admin_api.update_employee(emp_id, data)
                print_success("Employee updated successfully.")
                return
            except ServerError as error:
                print_error(str(error))
