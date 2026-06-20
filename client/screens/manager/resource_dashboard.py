from datetime import datetime
from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error
from client.utils.input_helpers import prompt_integer


def show_resource_dashboard() -> None:
    while True:
        draw_box("RESOURCE DASHBOARD")
        try:
            dashboard = manager_api.fetch_dashboard()
        except ServerError as error:
            print_error(str(error))
            return

        bench = dashboard.get("bench", [])
        allocated = dashboard.get("allocated", [])

        print("--- ON BENCH ---")
        if bench:
            from client.utils.display import print_table_header, print_table_row
            header = ["ID", "Name", "Department", "Skills"]
            widths = [6, 18, 14, 20]
            print_table_header(header, widths)
            for b in bench:
                skills_str = ", ".join(b.get("skills", []))
                print_table_row([
                    b.get("id"),
                    b.get("full_name"),
                    b.get("department") or "",
                    skills_str,
                ], widths)
        else:
            print("  No employees currently on the bench.")
        print()

        print("--- ACTIVE ALLOCATIONS ---")
        if allocated:
            from client.utils.display import print_table_header, print_table_row
            header = ["ID", "Name", "Project", "Utilisation"]
            widths = [6, 18, 18, 12]
            print_table_header(header, widths)
            for a in allocated:
                print_table_row([
                    a.get("id"),
                    a.get("full_name"),
                    a.get("project_name"),
                    f"{a.get('utilisation_percent')}%",
                ], widths)
        else:
            print("  No active allocations.")
        print()

        draw_divider()
        print("  [D] Drill down into Employee details")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()
        
        if choice == "B":
            return
        elif choice == "D":
            _drill_down_flow()
        else:
            print_error("Invalid option.")


def _drill_down_flow() -> None:
    emp_id = prompt_integer("Enter Employee ID to view", 1, 99999)
    try:
        emp = manager_api.fetch_employee_detail(emp_id)
        draw_box("EMPLOYEE PROFILE DETAIL", emp.get("full_name"))
        print(f"  ID          : {emp.get('id')}")
        print(f"  Email       : {emp.get('email')}")
        print(f"  Department  : {emp.get('department') or 'none'}")
        print(f"  Joined At   : {emp.get('joined_at') or 'none'}")
        print(f"  Status      : {'ACTIVE' if emp.get('is_active') else 'INACTIVE'}")
        if emp.get('timesheet_frozen'):
            print("  Timesheets  : [FROZEN] - Requires Manager Override")
        
        print("\nSkills:")
        if emp.get("skills"):
            for s in emp.get("skills"):
                print(f"  - {s.get('skill_name')} ({s.get('category')}): {s.get('proficiency')}")
        else:
            print("  No skills listed.")
            
        print("\nActive Project Allocations:")
        if emp.get("allocations"):
            print(f"  {'Project':<16} {'%':<5} {'From':<12} {'To':<12}")
            print(f"  {'-'*16} {'-'*5} {'-'*12} {'-'*12}")
            for a in emp.get("allocations"):
                from_dt_str = a.get("from_date")
                to_dt_str = a.get("to_date")
                try:
                    from_dt_str = datetime.strptime(from_dt_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                    to_dt_str = datetime.strptime(to_dt_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                except (ValueError, TypeError):
                    pass
                util_str = f"{a.get('utilisation_percent')}%"
                print(f"  {a.get('project_name'):<16} {util_str:<5} {from_dt_str:<12} {to_dt_str:<12}")
        else:
            print("  No active allocations.")
            
        print()
        draw_divider()
        if emp.get('timesheet_frozen'):
            print("  [R] Restore Timesheet Access")
        print("  [B] Back to Dashboard\n")
        
        while True:
            action = input("Action: ").strip().upper()
            if action == "B":
                return
            elif action == "R" and emp.get('timesheet_frozen'):
                try:
                    manager_api.restore_timesheet_access(emp.get("id"))
                    print("\nSuccess: Timesheet access restored!")
                    break
                except ServerError as error:
                    print_error(str(error))
            else:
                print_error("Invalid option.")
                
        input("\nPress Enter to return to dashboard...")
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")
