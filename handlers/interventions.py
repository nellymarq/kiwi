"""Intervention tracking command handler (Tier 54).

Single-entry handler with 4 subcommands: start, stop, check, list.
Sync-only.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_intervention(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /intervention start|stop|check|list — track supplement/protocol interventions with outcomes."""
    parts = query[14:].strip().split(maxsplit=3)
    if not parts:
        kiwi.console.print("[dim]  Usage: /intervention start|stop|check|list <name> [dose] [target_metric][/dim]")
    elif parts[0] == "start" and len(parts) >= 2:
        name = parts[1]
        dose = parts[2] if len(parts) > 2 else ""
        target = parts[3] if len(parts) > 3 else ""
        kiwi.interventions.start(name, dose, target)
        kiwi.console.print(f"[dim]  Started intervention: [cyan]{name}[/cyan]"
                      + (f" ({dose})" if dose else "")
                      + (f" → tracking {target}" if target else "")
                      + "[/dim]")
    elif parts[0] == "stop" and len(parts) >= 2:
        reason = parts[2] if len(parts) > 2 else ""
        if kiwi.interventions.stop(parts[1], reason):
            kiwi.console.print(f"[dim]  Stopped intervention: {parts[1]}[/dim]")
        else:
            kiwi.console.print(f"[dim red]  No active intervention '{parts[1]}' found[/dim red]")
    elif parts[0] == "check" and len(parts) >= 2:
        result = kiwi.interventions.check_outcome(parts[1])
        kiwi.console.print(Panel(
            kiwi.interventions.format_outcome(result),
            title="[cyan]Intervention Outcome[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))
    elif parts[0] == "list":
        kiwi.console.print(Panel(
            kiwi.interventions.format_active(),
            title="[cyan]Active Interventions[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))
    else:
        kiwi.console.print("[dim]  /intervention start <name> [dose] [target_metric][/dim]")
        kiwi.console.print("[dim]  /intervention stop <name> [reason][/dim]")
        kiwi.console.print("[dim]  /intervention check <name>[/dim]")
        kiwi.console.print("[dim]  /intervention list[/dim]")
