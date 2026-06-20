"""
All console formatting functions.
Screens import and call these — they never call print() for borders or icons directly.
"""

import os
from client.utils.constants import BOX_WIDTH, DIVIDER


def draw_box(title: str, subtitle: str = "") -> None:
    """Draws the ╔══╗ header seen in all BRD screens."""
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "╔" + "═" * (BOX_WIDTH - 2) + "╗")
    print(f"║  {title:<{BOX_WIDTH - 4}}║")
    if subtitle:
        print(f"║  {subtitle:<{BOX_WIDTH - 4}}║")
    print("╚" + "═" * (BOX_WIDTH - 2) + "╝\n")


def draw_divider() -> None:
    """Prints ──────────────────────────────────────────"""
    print(DIVIDER)


def print_success(message: str) -> None:
    """Prints: ✓  {message}"""
    print(f"\n✓  {message}\n")
    _maybe_pause()


def print_error(message: str) -> None:
    """Prints: ✗  Error: {message}"""
    print(f"\n✗  Error: {message}\n")
    _maybe_pause()


def _maybe_pause() -> None:
    try:
        import inspect
        import os
        stack = inspect.stack()
        # stack[0] is _maybe_pause, stack[1] is print_error/print_success, stack[2] is the caller
        if len(stack) > 2:
            caller_frame = stack[2]
            caller_filename = caller_frame.filename
            if "input_helpers" not in caller_filename:
                has_manual_pause = False
                if os.path.exists(caller_filename):
                    with open(caller_filename, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    line_idx = caller_frame.lineno
                    # Check next 5 lines for manual input or prompts
                    for i in range(line_idx, min(line_idx + 5, len(lines))):
                        line_content = lines[i].strip()
                        if not line_content:
                            continue
                        if "input(" in line_content or "prompt_" in line_content:
                            has_manual_pause = True
                            break
                if not has_manual_pause:
                    input("Press Enter to continue...")
    except Exception:
        pass


def print_warning(message: str) -> None:
    """Prints: ⚠  {message}"""
    print(f"⚠  {message}")


def print_table_row(columns: list, widths: list) -> None:
    """Prints one formatted table row. Columns and widths must have the same length."""
    row = "  ".join(str(col).ljust(width)[:width] for col, width in zip(columns, widths))
    print(row)


def print_table_header(columns: list, widths: list) -> None:
    """Prints the header row then a divider line."""
    print_table_row(columns, widths)
    draw_divider()
