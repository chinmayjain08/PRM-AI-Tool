from client.api_client import admin_api
from client.api_client.http_client import ServerError
from client.utils.constants import SKILL_CATEGORIES, PROFICIENCY_LEVELS
from client.utils.display import draw_box, print_error, print_success, draw_divider
from client.utils.input_helpers import prompt_integer, prompt_choice, prompt_non_empty


def show_manage_skills() -> None:
    while True:
        draw_box("EMPLOYEE SKILLS MATRIX")
        emp_id = prompt_integer("Enter Employee Profile ID (or 0 to cancel)", 0, 99999)
        if emp_id == 0:
            return

        try:
            emp = admin_api.fetch_employee(emp_id)
        except ServerError as error:
            print_error(str(error))
            continue

        _skills_submenu(emp_id, emp.get("full_name"))


def _skills_submenu(emp_id: int, full_name: str) -> None:
    while True:
        draw_box(f"SKILLS FOR {full_name.upper()}", f"Employee Profile ID: {emp_id}")
        try:
            skills = admin_api.fetch_employee_skills(emp_id)
        except ServerError as error:
            print_error(str(error))
            return

        if skills:
            from client.utils.display import print_table_header, print_table_row
            header = ["#", "Skill Name", "Category", "Proficiency"]
            widths = [4, 18, 12, 14]
            print_table_header(header, widths)
            for idx, s in enumerate(skills, start=1):
                print_table_row([
                    idx,
                    s.get("skill_name"),
                    s.get("category"),
                    s.get("proficiency"),
                ], widths)
            print()
        else:
            print("No skills associated with this employee profile.\n")

        options = [
            "Add Skill to Employee",
            "Update Skill Proficiency",
            "Remove Skill from Employee",
            "Back"
        ]
        
        choice = prompt_choice("Select option", options)
        
        if choice == 1:
            _add_skill_flow(emp_id)
        elif choice == 2:
            _update_proficiency_flow(emp_id, skills)
        elif choice == 3:
            _remove_skill_flow(emp_id, skills)
        elif choice == 4:
            break


def _add_skill_flow(emp_id: int) -> None:
    draw_box("ADD SKILL TO EMPLOYEE")
    skill_name = prompt_non_empty("Skill Name (e.g. Python, AWS)")
    
    print("\nSelect Skill Category:")
    cat_idx = prompt_choice("Category", SKILL_CATEGORIES)
    category = SKILL_CATEGORIES[cat_idx - 1]

    print("\nSelect Proficiency Level:")
    prof_idx = prompt_choice("Proficiency", PROFICIENCY_LEVELS)
    proficiency = PROFICIENCY_LEVELS[prof_idx - 1]

    try:
        admin_api.add_skill(emp_id, {
            "skill_name": skill_name,
            "category": category,
            "proficiency": proficiency
        })
        print_success(f"Skill '{skill_name}' successfully added to employee profile.")
    except ServerError as error:
        print_error(str(error))


def _update_proficiency_flow(emp_id: int, skills: list) -> None:
    if not skills:
        print_error("No skills available to update.")
        input("Press Enter to continue...")
        return
        
    draw_box("UPDATE SKILL PROFICIENCY")
    choice = prompt_integer(f"Enter Skill # to update (1-{len(skills)} or 0 to cancel)", 0, len(skills))
    if choice == 0:
        return
        
    existing = skills[choice - 1]
    skill_id = existing.get("skill_id")

    print(f"\nCurrent proficiency for {existing.get('skill_name')}: {existing.get('proficiency')}")
    print("\nSelect New Proficiency Level:")
    prof_idx = prompt_choice("Proficiency", PROFICIENCY_LEVELS)
    proficiency = PROFICIENCY_LEVELS[prof_idx - 1]

    try:
        admin_api.update_skill(emp_id, skill_id, proficiency)
        print_success("Skill proficiency updated successfully.")
    except ServerError as error:
        print_error(str(error))


def _remove_skill_flow(emp_id: int, skills: list) -> None:
    if not skills:
        print_error("No skills available to remove.")
        input("Press Enter to continue...")
        return
        
    draw_box("REMOVE SKILL FROM EMPLOYEE")
    choice = prompt_integer(f"Enter Skill # to remove (1-{len(skills)} or 0 to cancel)", 0, len(skills))
    if choice == 0:
        return
        
    existing = skills[choice - 1]
    skill_id = existing.get("skill_id")

    from client.utils.input_helpers import confirm_action
    if confirm_action(f"Remove skill '{existing.get('skill_name')}' from employee?"):
        try:
            admin_api.remove_skill(emp_id, skill_id)
            print_success("Skill removed successfully.")
        except ServerError as error:
            print_error(str(error))
