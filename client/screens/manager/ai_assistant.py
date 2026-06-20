from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error, print_warning
from client.utils.input_helpers import prompt_integer, prompt_choice, prompt_non_empty


def show_ai_assistant() -> None:
    while True:
        draw_box("AI ASSISTANT HUB")
        options = [
            "AI Skill Matcher (Find Candidates)",
            "AI Team Builder",
            "AI Project Risk Summary",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            _ai_skill_match_flow()
        elif choice == 2:
            _ai_team_build_flow()
        elif choice == 3:
            _ai_risk_summary_flow()
        elif choice == 4:
            break


def _ai_skill_match_flow() -> None:
    draw_box("AI SKILL MATCHING")
    requirement = prompt_non_empty("Describe your requirement (e.g. Python backend dev 10 hrs/week)")
    print("\nProcessing requirement query with AI model...\n")
    try:
        response = manager_api.ai_skill_match(requirement)
        results = response.get("results", [])
        if not results:
            print_warning("No available employees match this requirement capacity/skills.")
            input("\nPress Enter to continue...")
            return

        draw_divider()
        print("AI MATCHED CANDIDATES")
        draw_divider()
        for idx, match in enumerate(results, start=1):
            print(f"{idx}. Name: {match.get('name')}")
            print(f"   Reason: {match.get('reason')}")
            pct = match.get("suggested_allocation_pct")
            if pct:
                print(f"   Suggested Allocation: {pct}%")
            print()
        draw_divider()
        input("\nPress Enter to continue...")
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")


def _ai_team_build_flow() -> None:
    draw_box("AI TEAM BUILDER")
    requirement = prompt_non_empty("Describe your team requirement (e.g. Need Senior Java Dev, DevOps, and QA Tester)")
    print("\nProcessing team requirement with AI model...\n")
    try:
        response = manager_api.ai_team_build(requirement)
        matches = response.get("matches", [])
        gaps = response.get("gaps", [])

        if not matches and not gaps:
            print_warning("No output from AI Team Builder.")
            input("\nPress Enter to continue...")
            return

        if matches:
            draw_divider()
            print("AI MATCHED CANDIDATES")
            draw_divider()
            for idx, match in enumerate(matches, start=1):
                free_bnd = match.get('free_bandwidth_hrs', 'N/A')
                print(f"{idx}. Role: {match.get('role')}")
                print(f"   Name: {match.get('name')} (Free: {free_bnd} hrs/wk)")
                print(f"   Reason: {match.get('reason')}")
                pct = match.get("suggested_allocation_pct")
                if pct:
                    print(f"   Suggested Allocation: {pct}%")
                print()

        if gaps:
            draw_divider()
            print("GAPS IDENTIFIED")
            draw_divider()
            for gap in gaps:
                print(f"- Role: {gap.get('role')}")
                print(f"  Reason: {gap.get('reason')}")
            print()

        draw_divider()
        input("\nPress Enter to continue...")
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")


def _ai_risk_summary_flow() -> None:
    draw_box("AI PROJECT RISK SUMMARY")
    try:
        projects = manager_api.fetch_my_projects()
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")
        return

    if not projects:
        print_warning("You do not currently manage any projects.")
        input("\nPress Enter to continue...")
        return

    print("Select project:")
    from client.utils.constants import HEALTH_ICONS
    for idx, p in enumerate(projects, start=1):
        health = p.get("health_status")
        icon = HEALTH_ICONS.get(health, "⚪")
        print(f"  {idx}.  {p.get('name'):<20} {icon} {health}")
    print()

    choice = prompt_integer(f"Enter project number (1-{len(projects)} or 0 to cancel)", 0, len(projects))
    if choice == 0:
        return

    selected = projects[choice - 1]
    p_id = selected.get("id")
    p_name = selected.get("name")

    print(f"\nGenerating predictive risk summary for {p_name}... (Connecting to LLM)\n")
    try:
        response = manager_api.ai_risk_summary(p_id)
        summary = response.get("summary")
        draw_divider()
        print(summary)
        draw_divider()
        input("\nPress Enter to continue...")
    except ServerError as error:
        print_error(str(error))
        input("\nPress Enter to continue...")
