from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success, print_warning, draw_divider
from client.utils.input_helpers import prompt_integer, confirm_action


def show_deactivate_employee() -> None:
    while True:
        draw_box("DEACTIVATE EMPLOYEE")
        emp_id = prompt_integer("Enter Employee Profile ID (or 0 to cancel)", 0, 99999)
        if emp_id == 0:
            return

        try:
            emp = admin_api.fetch_employee(emp_id)
        except ServerError as error:
            print_error(str(error))
            continue

        print(f"\nTarget Employee: {emp.get('full_name')} (ID: {emp_id})")
        print(f"Department: {emp.get('department') or 'none'}")
        
        if not emp.get("is_active"):
            print_warning("This employee profile is already INACTIVE.")
            input("\nPress Enter to continue...")
            return

        try:
            allocations = admin_api.fetch_all_allocations(emp_id=emp_id)
        except ServerError as error:
            print_error(str(error))
            continue

        active_allocs = [a for a in allocations if a.get("is_active")]

        if active_allocs:
            draw_divider()
            print_warning("WARNING: The following active allocations will be terminated:")
            for alloc in active_allocs:
                print(f"  - Project: {alloc.get('project_name')} | Utilisation: {alloc.get('utilisation_percent')}% | Date Range: {alloc.get('from_date')} to {alloc.get('to_date')}")
            draw_divider()
        else:
            print("\nThis employee has no active project allocations.")

        if confirm_action(f"Deactivate {emp.get('full_name')}?"):
            try:
                res = admin_api.deactivate_employee(emp_id)
                print_success(res.get("message", "Employee profile successfully deactivated."))
                return
            except ServerError as error:
                print_error(str(error))
