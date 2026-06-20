from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.constants import MILESTONE_STATUSES
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, prompt_choice, prompt_non_empty, prompt_date


def show_manage_milestones() -> None:
    while True:
        draw_box("PROJECT MILESTONES")
        project_id = prompt_integer("Enter Project ID (or 0 to cancel)", 0, 99999)
        if project_id == 0:
            return

        try:
            # Verify project exists
            admin_api.fetch_project(project_id)
        except ServerError as error:
            print_error(str(error))
            continue

        _milestones_submenu(project_id)


def _milestones_submenu(project_id: int) -> None:
    while True:
        draw_box("MILESTONES LIST", f"Project ID: {project_id}")
        try:
            milestones = admin_api.fetch_milestones(project_id)
        except ServerError as error:
            print_error(str(error))
            return

        if milestones:
            from client.utils.display import print_table_header, print_table_row
            header = ["#", "Title", "Due Date", "Story Pts", "Status"]
            widths = [4, 18, 12, 10, 14]
            print_table_header(header, widths)
            for idx, m in enumerate(milestones, start=1):
                print_table_row([
                    idx,
                    m.get("title"),
                    m.get("due_date"),
                    m.get("story_points"),
                    m.get("status"),
                ], widths)
            print()
        else:
            print("No milestones exist for this project.\n")

        options = [
            "Add Milestone to Project",
            "Update Milestone Status",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            _add_milestone_flow(project_id)
        elif choice == 2:
            _update_milestone_flow(project_id, milestones)
        elif choice == 3:
            break


def _add_milestone_flow(project_id: int) -> None:
    draw_box("ADD MILESTONE")
    title = prompt_non_empty("Milestone Title")
    due_date = prompt_date("Due Date")
    story_points = prompt_integer("Story Points", 0, 1000)

    try:
        admin_api.add_milestone(project_id, {
            "title": title,
            "due_date": due_date,
            "story_points": story_points
        })
        print_success("Milestone added successfully.")
    except ServerError as error:
        print_error(str(error))


def _update_milestone_flow(project_id: int, milestones: list) -> None:
    if not milestones:
        print_error("No milestones available to update.")
        input("Press Enter to continue...")
        return

    draw_box("UPDATE MILESTONE STATUS")
    choice = prompt_integer(f"Enter Milestone # to update (1-{len(milestones)} or 0 to cancel)", 0, len(milestones))
    if choice == 0:
        return

    existing = milestones[choice - 1]
    m_id = existing.get("id")

    print("\nSelect New Milestone Status:")
    status_idx = prompt_choice("Status", MILESTONE_STATUSES)
    status = MILESTONE_STATUSES[status_idx - 1]
    
    if confirm_action(f"Update milestone '{existing.get('title')}' status to {status}?"):
        try:
            admin_api.update_milestone_status(m_id, status)
            print_success("Milestone status updated successfully. ✓")
            input("\nPress Enter to continue...")
        except ServerError as error:
            print_error(str(error))
            input("\nPress Enter to continue...")
