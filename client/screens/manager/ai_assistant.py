from client.api_client import manager_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error, print_warning
from client.utils.input_helpers import prompt_integer, prompt_choice, prompt_non_empty


def show_ai_assistant() -> None:
    while True:
        draw_box("AI ASSISTANT HUB")
        options = [
            "AI Skill Matcher (Find Candidates)",
            "AI Project Risk Summary",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            _ai_skill_match_flow()
        elif choice == 2:
            _ai_risk_summary_flow()
        elif choice == 3:
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


def _ai_risk_summary_flow() -> None:
    draw_box("AI PROJECT RISK SUMMARY")
    p_id = prompt_integer("Enter Project ID", 1, 99999)
    print("\nGenerating predictive risk summary... (Connecting to LLM)\n")
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
