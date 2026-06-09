from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.constants import HEALTH_ICONS
from client.utils.display import draw_box, draw_divider, print_error, print_success, print_warning
from client.utils.input_helpers import prompt_integer


def show_my_projects() -> None:
    while True:
        draw_box("MY MANAGED PROJECTS")
        try:
            projects = manager_api.fetch_my_projects()
        except ServerError as error:
            print_error(str(error))
            return

        if projects:
            from client.utils.display import print_table_header, print_table_row
            header = ["ID", "Project Name", "Status", "Health"]
            widths = [6, 18, 12, 14]
            print_table_header(header, widths)
            for p in projects:
                health = p.get("health_status")
                icon = HEALTH_ICONS.get(health, "⚪")
                print_table_row([
                    p.get("id"),
                    p.get("name"),
                    p.get("status"),
                    f"{icon} {health}",
                ], widths)
            print()
        else:
            print("You do not currently manage any projects.\n")

        print("  [D] Drill down into Project Detail")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()
        
        if choice == "B":
            return
        elif choice == "D":
            _drill_down_flow(projects)
        else:
            print_error("Invalid option.")


def _drill_down_flow(projects: list) -> None:
    p_id = prompt_integer("Enter Project ID to view", 1, 99999)
    existing = next((p for p in projects if p.get("id") == p_id), None)
    if not existing:
        print_error("Project ID not found in your list.")
        input("Press Enter to continue...")
        return

    while True:
        try:
            detail = manager_api.fetch_project_detail(p_id)
        except ServerError as error:
            print_error(str(error))
            input("Press Enter to continue...")
            return

        proj = detail.get("project", {})
        milestones = detail.get("milestones", [])
        allocations = detail.get("allocations", [])
        risk_flags = detail.get("risk_flags", [])

        draw_box(f"PROJECT: {proj.get('name').upper()}", f"Status: {proj.get('status')} | Health: {proj.get('health_status')}")
        print(f"  Description : {proj.get('description') or 'none'}")
        print(f"  Start Date  : {proj.get('start_date')}")
        print(f"  End Date    : {proj.get('end_date')}")
        print(f"  Story Pts   : {proj.get('total_story_pts')}")

        print("\n--- RISK FLAGS ---")
        if risk_flags:
            for flag in risk_flags:
                print_warning(flag)
        else:
            print("  No risk flags detected. Project is healthy.")

        print("\n--- MILESTONES ---")
        if milestones:
            from client.utils.display import print_table_header, print_table_row
            header = ["ID", "Milestone Title", "Due Date", "Story Pts", "Status"]
            widths = [6, 18, 12, 10, 14]
            print_table_header(header, widths)
            for m in milestones:
                print_table_row([
                    m.get("id"),
                    m.get("title"),
                    m.get("due_date"),
                    m.get("story_points"),
                    m.get("status"),
                ], widths)
        else:
            print("  No milestones defined.")

        print("\n--- ACTIVE TEAM ALLOCATIONS ---")
        if allocations:
            from client.utils.display import print_table_header, print_table_row
            header = ["ID", "Employee Name", "Util %", "From Date", "To Date"]
            widths = [6, 18, 8, 12, 12]
            print_table_header(header, widths)
            for a in allocations:
                print_table_row([
                    a.get("id"),
                    a.get("employee_name"),
                    f"{a.get('utilisation_percent')}%",
                    a.get("from_date"),
                    a.get("to_date"),
                ], widths)
        else:
            print("  No active allocations.")

        print("\n  [A] Generate AI Risk Summary")
        print("  [B] Back\n")
        
        sub_choice = input("Choice: ").strip().upper()
        if sub_choice == "B":
            return
        elif sub_choice == "A":
            _ai_risk_summary_flow(p_id)
        else:
            print_error("Invalid option.")


def _ai_risk_summary_flow(project_id: int) -> None:
    draw_box("AI PROJECT RISK PREDICTIVE SUMMARY")
    print("\nGenerating AI Risk Summary... (Connecting to LLM)\n")
    try:
        response = manager_api.ai_risk_summary(project_id)
        summary = response.get("summary")
        draw_divider()
        print(summary)
        draw_divider()
        input("\nPress Enter to return to project details...")
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")
