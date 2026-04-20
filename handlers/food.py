"""Food / nutrition lookup command handlers (Tier 51).

Sync-only. All return None implicitly. /food preserves the Tier 30
early-exit pattern (bare `return` on invalid input).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_food(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /food and /food+ — USDA FoodData Central lookup."""
    include_aminos = q_lower.startswith("/food+ ")
    prefix_len = 7 if include_aminos else 6
    args = query[prefix_len:].strip().split()
    food_name = " ".join(args[:-1]) if args and args[-1].lstrip("-").replace(".", "", 1).isdigit() else " ".join(args)
    grams = float(args[-1]) if args and args[-1].lstrip("-").replace(".", "", 1).isdigit() else 100.0
    if grams <= 0:
        kiwi.console.print("[dim red]  Serving size must be positive.[/dim red]")
        return

    if food_name:
        with kiwi.console.status(
            f"[dim cyan]  Looking up '{food_name}' in USDA FoodData Central...[/dim cyan]",
            spinner="earth",
        ):
            food = kiwi.fdc.search_and_get(
                food_name, serving_g=grams, include_aminos=include_aminos
            )
        if food:
            kiwi.console.print(Panel(
                food.full_report(include_aminos=include_aminos),
                title=f"[cyan]USDA FoodData Central[/cyan]  [dim]FDC#{food.fdc_id}[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        else:
            kiwi.console.print(f"[dim]  No results for '{food_name}'. Try a different name.[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /food chicken breast [150][/dim]")


def handle_compare(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /compare — side-by-side food comparison."""
    raw = query[9:].strip()
    if raw:
        foods = [f.strip() for f in raw.split(",") if f.strip()]
        if len(foods) >= 2:
            with kiwi.console.status(
                f"[dim cyan]  Comparing {len(foods)} foods...[/dim cyan]",
                spinner="earth",
            ):
                table_str = kiwi.fdc.compare_foods(foods)
            kiwi.console.print(Panel(
                table_str,
                title="[cyan]Food Comparison[/cyan]  [dim]USDA FoodData Central[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 1),
            ))
        else:
            kiwi.console.print("[dim]  Usage: /compare chicken breast, salmon, tofu[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /compare chicken breast, salmon, tofu[/dim]")
