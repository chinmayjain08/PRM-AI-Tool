from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error
from client.utils.input_helpers import prompt_optional


def show_timesheets_view() -> None:
    week_filter = None
    
    while True:
        draw_box("TEAM TIMESHEETS LOGS", f"Week Start: {week_filter or 'Last Monday'}")
        try:
            timesheets = manager_api.fetch_team_timesheets(week_start=week_filter)
        except ServerError as error:
            print_error(str(error))
            return

        header = ["ID", "Employee Name", "Project Name", "Hours", "Status", "Tags"]
        widths = [6, 16, 16, 6, 12, 18]
        
        from client.utils.display import print_table_header, print_table_row
        print_table_header(header, widths)
        for ts in timesheets:
            status = ts.get("status")
            status_display = f"⚠ {status}" if status == "MISSED" else status
            tags_str = ", ".join(ts.get("tags", []))
            
            print_table_row([
                ts.get("id") or "",
                ts.get("employee_name"),
                ts.get("project_name"),
                ts.get("hours_worked"),
                status_display,
                tags_str,
            ], widths)

        draw_divider()
        print(f"Total entries: {len(timesheets)}\n")

        print("  [F] Filter by Another Week")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()

        if choice == "B":
            return
        elif choice == "F":
            week_input = prompt_optional("Enter Week Start Date (DD-MM-YYYY)")
            if week_input:
                from datetime import datetime
                try:
                    week_filter = datetime.strptime(week_input, "%d-%m-%Y").strftime("%Y-%m-%d")
                except ValueError:
                    print_error("Invalid date. Keeping current filter.")
            else:
                week_filter = None
        else:
            print_error("Invalid option.")
