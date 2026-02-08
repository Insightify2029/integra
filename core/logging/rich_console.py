# core/logging/rich_console.py
"""
INTEGRA - Rich Console Output
==============================
Enhanced console output with rich formatting, colors, tables, and progress bars.

Uses the `rich` library for professional console display.

Usage:
    from core.logging.rich_console import console, print_table, print_panel

    # Print styled text
    console.print("[bold green]Success![/bold green] Data saved.")

    # Display a table
    print_table(
        title="Employee Stats",
        columns=["Department", "Count", "Avg Salary"],
        rows=[
            ["IT", "25", "8,500"],
            ["HR", "12", "7,200"],
        ]
    )

    # Display a panel
    print_panel("System started successfully", title="INTEGRA", style="green")

    # Progress bar
    with rich_progress("Processing employees...") as progress:
        task = progress.add_task("Loading", total=100)
        for i in range(100):
            progress.update(task, advance=1)

    # Startup banner
    print_startup_banner()
"""

from typing import List, Optional, Sequence

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
    from rich.text import Text
    from rich.theme import Theme
    from rich import box

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ─── Theme ─────────────────────────────────────────────────

_INTEGRA_THEME = None
if HAS_RICH:
    _INTEGRA_THEME = Theme({
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "critical": "bold white on red",
        "header": "bold blue",
        "muted": "dim",
        "accent": "bold #2563eb",
    })


# ─── Console Instance ──────────────────────────────────────

if HAS_RICH:
    console = Console(theme=_INTEGRA_THEME)
else:
    # Fallback: plain print wrapper
    class _FallbackConsole:
        """Minimal fallback when rich is not installed."""

        @staticmethod
        def print(*args, **kwargs):
            # Strip style/markup kwargs
            kwargs.pop("style", None)
            kwargs.pop("highlight", None)
            kwargs.pop("markup", None)
            print(*args, **kwargs)

        @staticmethod
        def rule(title: str = "", **kwargs):
            line = f"{'─' * 20} {title} {'─' * 20}" if title else "─" * 60
            print(line)

        @staticmethod
        def log(*args, **kwargs):
            kwargs.pop("style", None)
            print(*args)

    console = _FallbackConsole()


# ─── Table Helper ──────────────────────────────────────────

def print_table(
    title: str,
    columns: List[str],
    rows: Sequence[Sequence[str]],
    show_lines: bool = False,
    title_style: str = "accent",
) -> None:
    """
    Print a formatted table to the console.

    Args:
        title: Table title.
        columns: Column header names.
        rows: List of row data (each row is a sequence of strings).
        show_lines: Show row separator lines.
        title_style: Rich style for the title.
    """
    if not HAS_RICH:
        # Fallback: simple text table
        print(f"\n  {title}")
        print("  " + " | ".join(columns))
        print("  " + "-" * (sum(len(c) + 3 for c in columns)))
        for row in rows:
            print("  " + " | ".join(str(c) for c in row))
        print()
        return

    table = Table(
        title=title,
        title_style=title_style,
        box=box.ROUNDED,
        show_lines=show_lines,
        padding=(0, 1),
    )

    # Column styles based on position
    _col_styles = ["cyan", "green", "yellow", "magenta", "blue", "red"]
    for i, col_name in enumerate(columns):
        style = _col_styles[i % len(_col_styles)]
        table.add_column(col_name, style=style, no_wrap=True)

    for row in rows:
        table.add_row(*(str(cell) for cell in row))

    console.print()
    console.print(table)
    console.print()


# ─── Panel Helper ──────────────────────────────────────────

def print_panel(
    message: str,
    title: str = "INTEGRA",
    style: str = "blue",
    subtitle: Optional[str] = None,
) -> None:
    """
    Print a bordered panel with a message.

    Args:
        message: The main text.
        title: Panel title.
        style: Border color/style.
        subtitle: Optional subtitle at the bottom.
    """
    if not HAS_RICH:
        border = "═" * 50
        print(f"\n  {border}")
        print(f"  ║ {title}: {message}")
        if subtitle:
            print(f"  ║ {subtitle}")
        print(f"  {border}\n")
        return

    panel = Panel(
        message,
        title=title,
        subtitle=subtitle,
        style=style,
        padding=(1, 2),
    )
    console.print(panel)


# ─── Progress Helper ──────────────────────────────────────

def rich_progress(description: str = "Processing...") -> "Progress":
    """
    Create a rich progress bar context manager.

    Usage:
        with rich_progress("Loading data") as progress:
            task = progress.add_task("Reading", total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    if not HAS_RICH:
        # Return a minimal no-op context manager
        class _NoOpProgress:
            def __enter__(self):
                print(f"  {description}")
                return self

            def __exit__(self, *args):
                print("  Done.")

            @staticmethod
            def add_task(name: str, total: int = 100):
                return 0

            @staticmethod
            def update(task_id, advance: int = 1):
                pass

        return _NoOpProgress()

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )


# ─── Status Messages ──────────────────────────────────────

def print_success(message: str) -> None:
    """Print a success message."""
    if HAS_RICH:
        console.print(f"  [success]✓[/success] {message}")
    else:
        print(f"  [OK] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    if HAS_RICH:
        console.print(f"  [error]✗[/error] {message}")
    else:
        print(f"  [ERROR] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    if HAS_RICH:
        console.print(f"  [warning]⚠[/warning] {message}")
    else:
        print(f"  [WARN] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    if HAS_RICH:
        console.print(f"  [info]ℹ[/info] {message}")
    else:
        print(f"  [INFO] {message}")


# ─── Startup Banner ───────────────────────────────────────

def print_startup_banner(version: str = "2.1.0", debug_mode: bool = False) -> None:
    """
    Print the INTEGRA startup banner.

    Args:
        version: Application version.
        debug_mode: Whether debug mode is active.
    """
    if not HAS_RICH:
        print("═" * 50)
        print(f"  INTEGRA v{version}")
        print(f"  Integrated Management System")
        mode = "Development" if debug_mode else "Production"
        print(f"  Mode: {mode}")
        print("═" * 50)
        return

    mode_text = "[warning]Development[/warning]" if debug_mode else "[success]Production[/success]"

    banner_text = (
        f"[bold accent]INTEGRA[/bold accent] v{version}\n"
        f"[muted]Integrated Management System[/muted]\n\n"
        f"Mode: {mode_text}"
    )

    panel = Panel(
        banner_text,
        title="[bold]INTEGRA[/bold]",
        subtitle="[muted]نظام الإدارة المتكامل[/muted]",
        style="accent",
        padding=(1, 4),
    )
    console.print()
    console.print(panel)
    console.print()


# ─── Stats Table Helper ──────────────────────────────────

def print_stats_table(
    title: str,
    stats: dict,
    style: str = "cyan",
) -> None:
    """
    Print a key-value stats table.

    Args:
        title: Table title.
        stats: Dictionary of {label: value}.
        style: Value column style.
    """
    columns = ["البند", "القيمة"]
    rows = [[str(k), str(v)] for k, v in stats.items()]
    print_table(title=title, columns=columns, rows=rows)


# ─── Traceback Helper ─────────────────────────────────────

def print_exception() -> None:
    """Print the current exception with rich formatting."""
    if HAS_RICH:
        console.print_exception(show_locals=False, max_frames=10)
    else:
        import traceback
        traceback.print_exc()


# ─── Module Exports ───────────────────────────────────────

__all__ = [
    "HAS_RICH",
    "console",
    "print_table",
    "print_panel",
    "rich_progress",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_startup_banner",
    "print_stats_table",
    "print_exception",
]
