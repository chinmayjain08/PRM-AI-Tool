from datetime import date, timedelta, datetime
from client.api_client import employee_api
from client.api_client.http_client import ServerError
from client.utils.constants import ACTIVITY_TAGS
from client.utils.display import draw_box, draw_divider, print_error, print_success, print_warning
from client.utils.input_helpers import prompt_optional, prompt_integer, prompt_multi_select, confirm_action


def show_submit_timesheet() -> None:
    draw_box("SUBMIT TIMESHEET")
    raw_date = prompt_optional("Enter Week Start Date (DD-MM-YYYY)")
    
    if raw_date:
        try:
            week_start = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print_error("Invalid date format. Returning to menu.")
            input("Press Enter to continue...")
            return
    else:
        # Default to current week's Monday
        today = date.today()
        last_monday = today - timedelta(days=today.weekday())
        week_start = last_monday.strftime("%Y-%m-%d")

    # Format user-friendly date for display
    try:
        dt = datetime.strptime(week_start, "%Y-%m-%d")
        display_week = dt.strftime("%d-%m-%Y")
    except ValueError:
        display_week = week_start

    print(f"\nFetching active projects for week starting: {display_week}...")
    try:
        allocations = employee_api.fetch_active_allocations_for_week(week_start)
    except ServerError as error:
        print_error(str(error))
        input("Press Enter to continue...")
        return

    if not allocations:
        print_warning("No active projects for this week.")
        input("\nPress Enter to continue...")
        return

    entries = []
    for index, allocation in enumerate(allocations, start=1):
        draw_divider()
        print(f"PROJECT {index} OF {len(allocations)} — {allocation.get('project_name')}")
        print(f"  Allocation: {allocation.get('utilisation_percent')}%   "
              f"|   Expected Cap: {allocation.get('max_hours')} hrs max")
        draw_divider()

        hours = prompt_integer("Hours worked this week", 0, allocation.get("max_hours"))
        print("\nWhat did you work on? Select activity tags:\n")
        tags = prompt_multi_select("Select tags", ACTIVITY_TAGS)

        entries.append({
            "project_id":   allocation.get("project_id"),
            "project_name": allocation.get("project_name"),
            "hours_worked": hours,
            "tags":         tags,
        })

    _show_timesheet_summary(entries)
    if confirm_action("Submit Timesheet?"):
        # Strip project_name key before sending to api (the schema only expects project_id, hours_worked, tags)
        api_entries = []
        for entry in entries:
            api_entries.append({
                "project_id": entry["project_id"],
                "hours_worked": entry["hours_worked"],
                "tags": entry["tags"]
            })
            
        try:
            employee_api.submit_timesheet(week_start, api_entries)
            print_success("Timesheet submitted successfully. Status: SUBMITTED ✓")
            input("Press Enter to continue...")
        except ServerError as error:
            print_error(str(error))
            input("Press Enter to continue...")


def _show_timesheet_summary(entries: list) -> None:
    draw_divider()
    print("SUBMISSION SUMMARY")
    draw_divider()
    total = 0
    for entry in entries:
        tags_str = ", ".join(entry["tags"])
        print(f"  {entry['project_name']:<20} {entry['hours_worked']} hrs   [{tags_str}]")
        total += entry["hours_worked"]
    draw_divider()
    print(f"  Total  {total} hrs")
    draw_divider()
