from datetime import datetime
from client.api_client import employee_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error, print_warning
from client.utils.input_helpers import prompt_non_empty


def show_view_my_timesheets() -> None:
    while True:
        draw_box("TIMESHEET HISTORY")
        try:
            history = employee_api.fetch_timesheet_history()
        except ServerError as error:
            print_error(str(error))
            return

        if history:
            from client.utils.display import print_table_header, print_table_row
            header = ["Week Start", "Project", "Hours", "Status"]
            widths = [12, 16, 6, 12]
            print_table_header(header, widths)
            
            for ts in history:
                # Format date YYYY-MM-DD to DD-MM-YYYY
                week_start_str = ts.get("week_start")
                try:
                    dt = datetime.strptime(week_start_str, "%Y-%m-%d")
                    display_week = dt.strftime("%d-%m-%Y")
                except ValueError:
                    display_week = week_start_str

                status = ts.get("status")
                status_display = f"⚠ {status}" if status == "MISSED" else status
                
                print_table_row([
                    display_week,
                    ts.get("project_name") or "",
                    ts.get("hours_worked"),
                    status_display,
                ], widths)
            print()
        else:
            print("No timesheet submission history found.\n")

        print("  [V] View Week Details")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()
        
        if choice == "B":
            return
        elif choice == "V":
            _view_week_detail_flow()
        else:
            print_error("Invalid option.")


def _view_week_detail_flow() -> None:
    draw_box("VIEW WEEK DETAILS")
    raw_date = prompt_non_empty("Enter Week Start Date (DD-MM-YYYY)")
    try:
        week_start = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        print_error("Invalid date format.")
        input("Press Enter to continue...")
        return

    try:
        entries = employee_api.fetch_week_detail(week_start)
        draw_box(f"TIMESHEET FOR WEEK: {raw_date}")
        if entries:
            from client.utils.display import print_table_header, print_table_row
            header = ["Project", "Hours", "Status", "Activity Tags"]
            widths = [16, 6, 10, 20]
            print_table_header(header, widths)
            
            for e in entries:
                tags_str = ", ".join(e.get("tags", []))
                print_table_row([
                    e.get("project_name") or "",
                    e.get("hours_worked"),
                    e.get("status"),
                    tags_str
                ], widths)
            print()
        else:
            print("No timesheet records found for this week.")
            
        draw_divider()
        input("\nPress Enter to return to history...")
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")
