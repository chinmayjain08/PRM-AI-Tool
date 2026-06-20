from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.constants import PROJECT_STATUSES_CREATE
from client.utils.display import draw_box, print_error, print_success
from client.utils.input_helpers import prompt_non_empty, prompt_optional, prompt_date, prompt_choice, prompt_integer, confirm_action


def show_create_project() -> None:
    while True:
        draw_box("CREATE PROJECT")
        name = prompt_non_empty("Project Name")
        desc = prompt_optional("Description")
        
        print("\nEnter Date Range:")
        start_date = prompt_date("Start Date")
        end_date = prompt_date("End Date")
        
        print("\nSelect Project Status:")
        status_idx = prompt_choice("Status", PROJECT_STATUSES_CREATE)
        status = PROJECT_STATUSES_CREATE[status_idx - 1]

        manager_id = prompt_integer("Manager's User ID", 1, 99999)
        story_pts = prompt_integer("Total Story Points", 0, 10000)

        payload = {
            "name": name,
            "description": desc,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "manager_id": manager_id,
            "total_story_pts": story_pts
        }

        if confirm_action("Save new project?"):
            try:
                project = admin_api.create_project(payload)
                print_success(f"Project '{project.get('name')}' created successfully with ID: {project.get('id')}.")
                return
            except ServerError as error:
                print_error(str(error))
