from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error, print_success, print_warning
from client.utils.input_helpers import prompt_integer, prompt_non_empty, prompt_date, confirm_action, prompt_choice


def show_allocate_resource() -> None:
    while True:
        draw_box("ALLOCATE RESOURCES")
        options = [
            "AI-Assisted Allocation",
            "Direct Allocation",
            "End Allocation",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            _show_ai_allocation_flow()
        elif choice == 2:
            _show_direct_allocation_flow()
        elif choice == 3:
            _show_end_allocation_flow()
        elif choice == 4:
            break


def _show_ai_allocation_flow() -> None:
    draw_box("AI-ASSISTED RESOURCE MATCHING")
    project_id = prompt_integer("Enter Project ID", 1, 99999)
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
    alloc_id = prompt_integer("Enter Allocation ID to terminate (or 0 to cancel)", 0, 99999)
    if alloc_id == 0:
        return

    if confirm_action(f"Are you sure you want to end allocation ID: {alloc_id}?"):
        try:
            manager_api.end_allocation(alloc_id)
            print_success("Allocation ended successfully.")
        except ServerError as error:
            print_error(str(error))
