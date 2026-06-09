from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.display import draw_box, draw_divider, print_error, print_success
from client.utils.input_helpers import prompt_integer, confirm_action


def show_view_all_users() -> None:
    while True:
        draw_box("ALL USER ACCOUNTS")
        try:
            users = admin_api.fetch_all_users()
        except ServerError as error:
            print_error(str(error))
            return

        header = ["ID", "Username", "Email", "Full Name", "Role", "Active"]
        widths = [6, 12, 22, 18, 10, 8]
        
        from client.utils.display import print_table_header, print_table_row
        print_table_header(header, widths)
        for u in users:
            print_table_row([
                u.get("id"),
                u.get("username"),
                u.get("email"),
                u.get("full_name"),
                u.get("role"),
                "YES" if u.get("is_active") else "NO",
            ], widths)

        draw_divider()
        print(f"Total Users: {len(users)}\n")

        print("  [R] Reactivate User")
        print("  [B] Back\n")
        
        choice = input("Choice: ").strip().upper()

        if choice == "B":
            return
        elif choice == "R":
            _reactivate_flow(users)
        else:
            print_error("Invalid option.")


def _reactivate_flow(users: list) -> None:
    draw_box("REACTIVATE USER ACCOUNT")
    u_id = prompt_integer("Enter User ID to reactivate", 1, 99999)
    
    existing = next((u for u in users if u.get("id") == u_id), None)
    if not existing:
        print_error("User ID not found.")
        input("Press Enter to continue...")
        return

    if existing.get("is_active"):
        print_error("This user account is already active.")
        input("Press Enter to continue...")
        return

    if confirm_action(f"Reactivate user '{existing.get('username')}'?"):
        try:
            admin_api.reactivate_user(u_id)
            print_success(f"User account '{existing.get('username')}' successfully reactivated.")
        except ServerError as error:
            print_error(str(error))
