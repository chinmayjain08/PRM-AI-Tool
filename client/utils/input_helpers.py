"""
All user input collection and validation.
Every screen uses these functions — never raw input() or getpass() inline.

DRY Principle: one set of validators for the entire client application.
"""

import getpass
from datetime import datetime

from client.utils.display import print_error


def prompt_non_empty(label: str) -> str:
    """Asks for input. Re-prompts until a non-empty string is entered."""
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print_error("This field cannot be empty.")


def prompt_password(label: str) -> str:
    """Uses getpass so the password is not echoed on screen."""
    while True:
        value = getpass.getpass(f"{label}: ").strip()
        if value:
            return value
        print_error("Password cannot be empty.")


def prompt_choice(label: str, options: list[str]) -> int:
    """
    Displays a numbered list of options.
    Returns the 1-based index of the user's choice.
    Re-prompts on invalid input.
    """
    for index, option in enumerate(options, start=1):
        print(f"  {index}. {option}")
    while True:
        try:
            choice = input(f"\n{label}: ").strip()
            # Allow case insensitive selection if needed, but here we require numeric choice.
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num
            print_error(f"Enter a number between 1 and {len(options)}.")
        except ValueError:
            print_error("Please enter a valid number.")


def prompt_integer(label: str, min_val: int = 0, max_val: int = 100) -> int:
    """Prompts for an integer in [min_val, max_val]. Re-prompts if out of range."""
    while True:
        try:
            value = int(input(f"{label}: ").strip())
            if min_val <= value <= max_val:
                return value
            print_error(f"Enter a number between {min_val} and {max_val}.")
        except ValueError:
            print_error("Please enter a valid whole number.")


def prompt_date(label: str) -> str:
    """
    Prompts for a date in DD-MM-YYYY format.
    Re-prompts if the format is invalid.
    Returns the date as a YYYY-MM-DD string (ISO format for the API).
    """
    while True:
        raw = input(f"{label} (DD-MM-YYYY): ").strip()
        try:
            parsed = datetime.strptime(raw, "%d-%m-%Y")
            return parsed.strftime("%Y-%m-%d")   # convert to ISO for API
        except ValueError:
            print_error("Invalid date. Use DD-MM-YYYY format (e.g. 01-06-2026).")


def prompt_optional(label: str) -> str:
    """Returns the input string or empty string if the user presses Enter."""
    return input(f"{label} (optional, press Enter to skip): ").strip()


def confirm_action(message: str) -> bool:
    """
    Prints [Y] Yes   [B] Back and waits for input.
    Returns True for Y/y, False for B/b. Re-prompts otherwise.
    """
    while True:
        choice = input(f"\n{message}\n[Y] Yes     [B] Back\n\nChoice: ").strip().upper()
        if choice == "Y":
            return True
        if choice == "B":
            return False
        print_error("Enter Y or B.")


def prompt_multi_select(label: str, options: list[str]) -> list[str]:
    """
    Displays a numbered list and prompts for comma-separated choices.
    Returns the selected option strings (not indices).
    Handles 'Other' as a free-text option.
    """
    for index, option in enumerate(options, start=1):
        print(f"  {index:2}. {option}")

    while True:
        raw = input(f"\n{label} (comma-separated, e.g. 1, 3): ").strip()
        try:
            indices   = [int(x.strip()) for x in raw.split(",") if x.strip()]
            selected  = []
            for idx in indices:
                if not (1 <= idx <= len(options)):
                    raise ValueError
                if options[idx - 1] == "Other":
                    custom = prompt_non_empty("Enter custom tag")
                    selected.append(custom)
                else:
                    selected.append(options[idx - 1])
            if selected:
                return selected
            print_error("Select at least one option.")
        except ValueError:
            print_error(f"Enter numbers between 1 and {len(options)}, separated by commas.")
