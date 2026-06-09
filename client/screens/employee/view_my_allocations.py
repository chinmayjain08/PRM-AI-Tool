from client.api_client import employee_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error


def show_view_my_allocations() -> None:
    while True:
        draw_box("MY PROJECT ALLOCATIONS")
        try:
            allocations = employee_api.fetch_my_allocations()
        except ServerError as error:
            print_error(str(error))
            return

        if allocations:
            from client.utils.display import print_table_header, print_table_row
            header = ["Project Name", "Util %", "From Date", "To Date", "Active"]
            widths = [18, 8, 12, 12, 8]
            print_table_header(header, widths)
            
            for a in allocations:
                print_table_row([
                    a.get("project_name") or "",
                    f"{a.get('utilisation_percent')}%",
                    a.get("from_date"),
                    a.get("to_date"),
                    "YES" if a.get("is_active") else "NO",
                ], widths)
            print()
        else:
            print("You currently have no project allocations.\n")

        draw_divider()
        input("\nPress Enter to return to menu...")
        return
