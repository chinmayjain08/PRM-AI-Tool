from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.constants import HEALTH_ICONS
from client.utils.display import draw_box, draw_divider, print_error


def show_view_all_projects() -> None:
    while True:
        draw_box("ALL PROJECTS")
        try:
            projects = admin_api.fetch_all_projects()
        except ServerError as error:
            print_error(str(error))
            return

        header = ["ID", "Name", "Status", "Story Pts (Done/Total)", "Health"]
        widths = [6, 14, 10, 24, 14]
        
        from client.utils.display import print_table_header, print_table_row
        print_table_header(header, widths)
        for p in projects:
            sp_col = f"{p.get('done_story_pts')}/{p.get('total_story_pts')}"
            health = p.get("health_status")
            health_icon = HEALTH_ICONS.get(health, "⚪")
            print_table_row([
                p.get("id"),
                p.get("name"),
                p.get("status"),
                sp_col,
                f"{health_icon} {health}",
            ], widths)

        draw_divider()
        input("\nPress Enter to return to menu...")
        return
