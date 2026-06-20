from datetime import datetime
from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error
from client.utils.input_helpers import prompt_optional


def show_view_all_allocations() -> None:
    emp_id_filter = None
    proj_id_filter = None
    
    while True:
        draw_box("ALL PROJECT ALLOCATIONS", f"Filters: Employee={emp_id_filter or 'ANY'}, Project={proj_id_filter or 'ANY'}")
        try:
            allocs = admin_api.fetch_all_allocations(emp_id=emp_id_filter, proj_id=proj_id_filter)
        except ServerError as error:
            print_error(str(error))
            return

        header = ["Employee", "Project", "%", "From", "To"]
        widths = [18, 18, 6, 12, 12]
        
        from client.utils.display import print_table_header, print_table_row
        print_table_header(header, widths)
        for a in allocs:
            from_dt_str = a.get("from_date")
            to_dt_str = a.get("to_date")
            try:
                from_dt_str = datetime.strptime(from_dt_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                to_dt_str = datetime.strptime(to_dt_str, "%Y-%m-%d").strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                pass
            print_table_row([
                a.get("employee_name") or f"ID {a.get('employee_id')}",
                a.get("project_name") or f"ID {a.get('project_id')}",
                f"{a.get('utilisation_percent')}%",
                from_dt_str,
                to_dt_str,
            ], widths)

        draw_divider()
        print(f"Total Allocations Found: {len(allocs)}\n")

        print("  [F] Apply Filters")
        print("  [C] Clear Filters")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()

        if choice == "B":
            return
        elif choice == "F":
            emp_input = prompt_optional("Filter by Employee ID")
            emp_id_filter = int(emp_input) if emp_input else None
            
            proj_input = prompt_optional("Filter by Project ID")
            proj_id_filter = int(proj_input) if proj_input else None
        elif choice == "C":
            emp_id_filter = None
            proj_id_filter = None
        else:
            print_error("Invalid option.")
