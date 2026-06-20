from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error, print_success, print_warning
from client.utils.input_helpers import prompt_integer, prompt_non_empty, prompt_date, confirm_action, prompt_choice


def show_allocate_resource() -> None:
    while True:
        draw_box("ALLOCATE RESOURCES")
        options = [
            "AI-Assisted Allocation (Single)",
            "AI Team Builder Allocation (Multiple)",
            "Direct Allocation",
            "End Allocation",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            _show_ai_allocation_flow()
        elif choice == 2:
            _show_ai_team_builder_flow()
        elif choice == 3:
            _show_direct_allocation_flow()
        elif choice == 4:
            _show_end_allocation_flow()
        elif choice == 5:
            break


def _show_ai_allocation_flow() -> None:
    draw_box("AI-ASSISTED RESOURCE MATCHING")
    project_id = prompt_integer("Enter Project ID", 1, 99999)
    try:
        project_detail = manager_api.fetch_project_detail(project_id)
        print(f"Project '{project_detail.get('name')}' selected.")
    except ServerError as error:
        print_error(f"Invalid Project ID: {str(error)}")
        input("\nPress Enter to return...")
        return

    requirement = prompt_non_empty("Describe your requirement (e.g. Need a Python dev 10 hrs/week)")
    
    print("\nSearching... (AI matching in progress)\n")
    try:
        # Load name to id mapping from dashboard
        dashboard = manager_api.fetch_dashboard()
        name_to_id = {}
        for b in dashboard.get("bench", []):
            name_to_id[b["full_name"]] = b["id"]
        for a in dashboard.get("allocated", []):
            name_to_id[a["full_name"]] = a["id"]

        response = manager_api.ai_skill_match(requirement)
    except ServerError as error:
        print_error(str(error))
        return

    results = response.get("results", [])
    if not results:
        print_warning("No available employees match this requirement.")
        input("\nPress Enter to continue...")
        return

    draw_divider()
    print("AI-MATCHED RESULTS")
    draw_divider()
    for idx, match in enumerate(results, start=1):
        print(f"{idx}.  {match.get('name')}")
        print(f"    Reason: {match.get('reason')}")
        pct = match.get("suggested_allocation_pct")
        if pct:
            print(f"    Suggested allocation: {pct}%")
        print()

    print("Note: Suggestions are AI-generated. Verify before confirming.\n")
    selection = prompt_integer("Select employee (# or 0 to cancel)", 0, len(results))
    if selection == 0:
        return

    selected = results[selection - 1]
    emp_id = name_to_id.get(selected.get("name"))
    if not emp_id:
        print_error(f"Could not map '{selected.get('name')}' to a valid Employee ID.")
        emp_id = prompt_integer("Please enter the Employee ID manually", 1, 99999)

    util_pct = prompt_integer("Utilisation %", 1, 100)
    from_date = prompt_date("From Date")
    to_date = prompt_date("To Date")

    print("\nValidating...")
    if confirm_action(f"Confirm allocation of {selected.get('name')}?"):
        try:
            manager_api.create_allocation({
                "employee_id": emp_id,
                "project_id": project_id,
                "utilisation_percent": util_pct,
                "from_date": from_date,
                "to_date": to_date
            })
            print_success(f"Allocation saved successfully for {selected.get('name')}.")
        except ServerError as error:
            print_error(str(error))


def _show_ai_team_builder_flow() -> None:
    draw_box("AI TEAM BUILDER ALLOCATION")
    project_id = prompt_integer("Enter Project ID", 1, 99999)
    try:
        project_detail = manager_api.fetch_project_detail(project_id)
        print(f"Project '{project_detail.get('name')}' selected.")
    except ServerError as error:
        print_error(f"Invalid Project ID: {str(error)}")
        input("\nPress Enter to return...")
        return

    requirement = prompt_non_empty("Describe your team requirement (e.g. Need Senior Java Dev, DevOps, and QA Tester)")
    
    print("\nSearching... (AI matching in progress)\n")
    try:
        dashboard = manager_api.fetch_dashboard()
        name_to_id = {}
        for b in dashboard.get("bench", []):
            name_to_id[b["full_name"]] = b["id"]
        for a in dashboard.get("allocated", []):
            name_to_id[a["full_name"]] = a["id"]

        response = manager_api.ai_team_build(requirement)
    except ServerError as error:
        print_error(str(error))
        return

    matches = response.get("matches", [])
    gaps = response.get("gaps", [])

    if not matches and not gaps:
        print_warning("No available employees match this requirement.")
        input("\nPress Enter to continue...")
        return

    if matches:
        draw_divider()
        print("AI-MATCHED RESULTS")
        draw_divider()
        for idx, match in enumerate(matches, start=1):
            free_bnd = match.get('free_bandwidth_hrs', 'N/A')
            print(f"{idx}.  Role: {match.get('role')}")
            print(f"    Name: {match.get('name')} (Free: {free_bnd} hrs/wk)")
            print(f"    Reason: {match.get('reason')}")
            pct = match.get("suggested_allocation_pct")
            if pct:
                print(f"    Suggested allocation: {pct}%")
            print()

    if gaps:
        draw_divider()
        print("GAPS IDENTIFIED")
        draw_divider()
        for gap in gaps:
            print(f"- Role: {gap.get('role')}")
            print(f"  Reason: {gap.get('reason')}")
        print()

    if not matches:
        input("\nPress Enter to continue...")
        return

    print("Note: Suggestions are AI-generated. Verify before confirming.\n")
    if confirm_action("Do you want to allocate these matched candidates to the project?"):
        from_date = prompt_date("From Date")
        to_date = prompt_date("To Date")

        print("\nAllocating team...")
        success_count = 0
        for match in matches:
            emp_name = match.get("name")
            emp_id = name_to_id.get(emp_name)
            
            if not emp_id:
                print_error(f"Could not map '{emp_name}' to a valid Employee ID. Skipping.")
                continue

            util_pct = match.get("suggested_allocation_pct", 50)
            
            try:
                manager_api.create_allocation({
                    "employee_id": emp_id,
                    "project_id": project_id,
                    "utilisation_percent": util_pct,
                    "from_date": from_date,
                    "to_date": to_date
                })
                print_success(f"Allocation saved successfully for {emp_name} ({match.get('role')}).")
                success_count += 1
            except ServerError as error:
                print_error(f"Failed to allocate {emp_name}: {str(error)}")
        
        print(f"\n{success_count}/{len(matches)} team members allocated successfully.")
        input("\nPress Enter to continue...")


def _show_direct_allocation_flow() -> None:
    draw_box("DIRECT RESOURCE ALLOCATION")
    emp_id = prompt_integer("Enter Employee ID", 1, 99999)
    project_id = prompt_integer("Enter Project ID", 1, 99999)
    util_pct = prompt_integer("Utilisation %", 1, 100)
    from_date = prompt_date("From Date")
    to_date = prompt_date("To Date")

    if confirm_action(f"Allocate Employee {emp_id} to Project {project_id}?"):
        try:
            manager_api.create_allocation({
                "employee_id": emp_id,
                "project_id": project_id,
                "utilisation_percent": util_pct,
                "from_date": from_date,
                "to_date": to_date
            })
            print_success("Allocation saved successfully.")
        except ServerError as error:
            print_error(str(error))


def _show_end_allocation_flow() -> None:
    draw_box("TERMINATE RESOURCE ALLOCATION")
    project_id = prompt_integer("Enter Project ID (or 0 to cancel)", 0, 99999)
    if project_id == 0:
        return

    try:
        detail = manager_api.fetch_project_detail(project_id)
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")
        return

    allocations = detail.get("allocations", [])
    active_allocs = [a for a in allocations if a.get("is_active")]

    if not active_allocs:
        print_warning("No active allocations found on this project.")
        input("\nPress Enter to continue...")
        return

    print("\nActive Allocations on this project:")
    from client.utils.display import print_table_header, print_table_row
    header = ["#", "Employee", "%", "From", "To"]
    widths = [4, 18, 6, 12, 12]
    print_table_header(header, widths)
    for idx, a in enumerate(active_allocs, start=1):
        print_table_row([
            idx,
            a.get("employee_name"),
            f"{a.get('utilisation_percent')}%",
            a.get("from_date"),
            a.get("to_date")
        ], widths)
    print()

    choice = prompt_integer(f"Select allocation to end (1-{len(active_allocs)} or 0 to cancel)", 0, len(active_allocs))
    if choice == 0:
        return

    selected_alloc = active_allocs[choice - 1]
    emp_name = selected_alloc.get("employee_name")
    alloc_id = selected_alloc.get("id")

    if confirm_action(f"End {emp_name}'s allocation on this project?"):
        try:
            manager_api.end_allocation(alloc_id)
            print_success(f"Allocation ended. {emp_name} freed from project successfully. ✓")
            input("\nPress Enter to continue...")
        except ServerError as error:
            print_error(str(error))
            input("\nPress Enter to continue...")
