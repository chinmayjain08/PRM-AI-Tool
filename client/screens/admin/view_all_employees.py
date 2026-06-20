from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error
from client.utils.input_helpers import prompt_optional


def show_view_all_employees() -> None:
    status_filter = None
    dept_filter = None
    
    while True:
        draw_box("ALL EMPLOYEES", f"Filters: Status={status_filter or 'ANY'}, Dept={dept_filter or 'ANY'}")
        try:
            employees = admin_api.fetch_all_employees(status=status_filter, dept=dept_filter)
        except ServerError as error:
            print_error(str(error))
            return

        header = ["ID", "Name", "Department", "Status"]
        widths = [6, 18, 14, 12]
        
        from client.utils.display import print_table_header, print_table_row
        print_table_header(header, widths)
        for emp in employees:
            print_table_row([
                emp.get("id"),
                emp.get("user", {}).get("full_name", ""),
                emp.get("department", "") or "",
                emp.get("status", ""),
            ], widths)

        bench     = sum(1 for e in employees if e.get("status") == "BENCH")
        allocated = sum(1 for e in employees if e.get("status") == "ALLOCATED")
        draw_divider()
        print(f"Total: {len(employees)}   |   Allocated: {allocated}   |   Bench: {bench}\n")

        print("  [F] Apply Filters")
        print("  [C] Clear Filters")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()

        if choice == "B":
            return
        elif choice == "F":
            status_input = prompt_optional("Filter by Status (BENCH / ALLOCATED)").upper()
            if status_input in ("BENCH", "ALLOCATED"):
                status_filter = status_input
            else:
                status_filter = None
            dept_input = prompt_optional("Filter by Department")
            dept_filter = dept_input if dept_input else None
        elif choice == "C":
            status_filter = None
            dept_filter = None
        else:
            print_error("Invalid option.")
