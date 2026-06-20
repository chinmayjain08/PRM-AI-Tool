from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_integer, prompt_choice, prompt_non_empty, confirm_action


def show_system_config() -> None:
    while True:
        draw_box("SYSTEM CONFIGURATION")
        try:
            config = admin_api.fetch_system_config()
        except ServerError as error:
            print_error(str(error))
            return

        print(f"  LLM Provider       : {config.get('llm_provider')}")
        print(f"  LLM API Key        : {config.get('llm_api_key') or 'not set'}")
        print(f"  Scheduler Interval : {config.get('scheduler_interval')} hours")
        print(f"  Max Weekly Hours   : {config.get('max_weekly_hours')} hours\n")

        options = [
            "Update LLM Provider",
            "Update LLM API Key",
            "Update Scheduler Interval",
            "Update Max Weekly Hours",
            "Back"
        ]
        
        choice = prompt_choice("Select option to modify", options)
        
        if choice == 1:
            _update_provider_flow()
        elif choice == 2:
            _update_key_flow()
        elif choice == 3:
            _update_scheduler_flow()
        elif choice == 4:
            _update_max_hours_flow()
        elif choice == 5:
            break


def _update_provider_flow() -> None:
    draw_box("UPDATE LLM PROVIDER")
    providers = ["gemini", "groq", "ollama"]
    p_idx = prompt_choice("Select Provider", providers)
    provider = providers[p_idx - 1]

    if confirm_action(f"Change LLM Provider to '{provider}'?"):
        try:
            admin_api.update_system_config({"llm_provider": provider})
            print_success("LLM Provider updated successfully.")
        except ServerError as error:
            print_error(str(error))


def _update_key_flow() -> None:
    draw_box("UPDATE LLM API KEY")
    key = prompt_non_empty("Enter New API Key (or type 'mock-key' for testing)")

    if confirm_action("Change LLM API Key?"):
        try:
            admin_api.update_system_config({"llm_api_key": key})
            print_success("LLM API Key updated successfully.")
        except ServerError as error:
            print_error(str(error))


def _update_scheduler_flow() -> None:
    draw_box("UPDATE SCHEDULER INTERVAL")
    interval = prompt_integer("Enter Interval (in hours, between 1 and 168)", 1, 168)

    if confirm_action(f"Change Scheduler Interval to {interval} hour(s)?"):
        try:
            admin_api.update_system_config({"scheduler_interval": interval})
            print_success("Scheduler interval updated successfully.")
        except ServerError as error:
            print_error(str(error))


def _update_max_hours_flow() -> None:
    draw_box("UPDATE MAX WEEKLY HOURS")
    hours = prompt_integer("Enter Max Weekly Hours cap (between 1 and 168)", 1, 168)

    if confirm_action(f"Change Max Weekly Hours cap to {hours} hour(s)?"):
        try:
            admin_api.update_system_config({"max_weekly_hours": hours})
            print_success("Max weekly hours cap updated successfully.")
        except ServerError as error:
            print_error(str(error))
