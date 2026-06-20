from datetime import datetime
from client.api_client import employee_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_warning, draw_divider
from client.utils.input_helpers import prompt_choice


def show_employee_menu(full_name: str) -> None:
    while True:
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M")
        draw_box("EMPLOYEE PORTAL", f"Welcome, {full_name} | {current_time}")
        
        # Check for missed timesheets
        try:
            missed_weeks = employee_api.fetch_missed_weeks().get("missed_weeks", [])
            if missed_weeks:
                print_warning("WARNING: You have missed timesheet submissions for the following weeks:")
                for week in missed_weeks:
                    # Convert YYYY-MM-DD from API back to DD-MM-YYYY for user display
                    try:
                        dt = datetime.strptime(week, "%Y-%m-%d")
                        formatted_week = dt.strftime("%d-%m-%Y")
                    except ValueError:
                        formatted_week = week
                    print(f"  - Week starting: {formatted_week}")
                draw_divider()
                print()
        except ServerError:
            pass

        options = [
            "Submit Timesheet",
            "View Timesheet History",
            "View My Allocations",
            "Log Out"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            from client.screens.employee.submit_timesheet import show_submit_timesheet
            show_submit_timesheet()
        elif choice == 2:
            from client.screens.employee.view_my_timesheets import show_view_my_timesheets
            show_view_my_timesheets()
        elif choice == 3:
            from client.screens.employee.view_my_allocations import show_view_my_allocations
            show_view_my_allocations()
        elif choice == 4:
            print("\nLogging out...\n")
            break
