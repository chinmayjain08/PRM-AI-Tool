from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.constants import PROJECT_STATUSES_UPDATE
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, prompt_optional, prompt_date, prompt_choice, confirm_action


def show_update_project() -> None:
    while True:
        draw_box("UPDATE PROJECT PROFILE")
        project_id = prompt_integer("Enter Project ID (or 0 to cancel)", 0, 99999)
        if project_id == 0:
            return

        try:
            detail = admin_api.fetch_project(project_id)
        except ServerError as error:
            print_error(str(error))
            continue

        project = detail.get("project", {})
        print(f"\nCurrent Profile:")
        print(f"  Name            : {project.get('name')}")
        print(f"  Description     : {project.get('description') or 'none'}")
        print(f"  Start Date      : {project.get('start_date')}")
        print(f"  End Date        : {project.get('end_date')}")
        print(f"  Status          : {project.get('status')}")
        print(f"  Manager User ID : {project.get('manager_id')}")
        print(f"  Total Story Pts : {project.get('total_story_pts')}\n")

        new_name = prompt_optional("New Project Name")
        new_desc = prompt_optional("New Description")
        
        print("\nEnter New Date Range (leave blank to keep current):")
        new_start = prompt_optional("New Start Date (DD-MM-YYYY)")
        if new_start:
            # Parse start date using input_helpers style logic
            from datetime import datetime
            try:
                new_start = datetime.strptime(new_start, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                print_error("Invalid date. Skipping start date update.")
                new_start = None

        new_end = prompt_optional("New End Date (DD-MM-YYYY)")
        if new_end:
            from datetime import datetime
            try:
                new_end = datetime.strptime(new_end, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                print_error("Invalid date. Skipping end date update.")
                new_end = None

        print("\nSelect New Project Status (or press Enter to skip):")
        status_choice = prompt_optional("Enter status index (1: PLANNED, 2: ACTIVE, 3: ON_HOLD, 4: COMPLETED)")
        new_status = None
        if status_choice:
            try:
                idx = int(status_choice)
                if 1 <= idx <= len(PROJECT_STATUSES_UPDATE):
                    new_status = PROJECT_STATUSES_UPDATE[idx - 1]
            except ValueError:
                pass

        new_mgr = prompt_optional("New Manager User ID")
        new_pts = prompt_optional("New Total Story Points")

        updates = {}
        if new_name: updates["name"] = new_name
        if new_desc: updates["description"] = new_desc
        if new_start: updates["start_date"] = new_start
        if new_end: updates["end_date"] = new_end
        if new_status: updates["status"] = new_status
        if new_mgr: updates["manager_id"] = int(new_mgr)
        if new_pts: updates["total_story_pts"] = int(new_pts)

        if not updates:
            print_error("No fields updated.")
            continue

        if confirm_action("Save changes?"):
            try:
                admin_api.update_project(project_id, updates)
                print_success("Project updated successfully.")
                return
            except ServerError as error:
                print_error(str(error))
