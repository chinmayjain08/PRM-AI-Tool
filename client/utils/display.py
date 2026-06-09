"""
All console formatting functions.
Screens import and call these — they never call print() for borders or icons directly.
"""

from client.utils.constants import BOX_WIDTH, DIVIDER


def draw_box(title: str, subtitle: str = "") -> None:
    """Draws the ╔══╗ header seen in all BRD screens."""
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


def print_error(message: str) -> None:
    """Prints: ✗  Error: {message}"""
    print(f"\n✗  Error: {message}\n")


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
