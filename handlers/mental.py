"""Mental performance command handlers (Tier 42).

Sync-only. All return None implicitly. Same pattern as handlers/injury.py
(Tier 41 pilot).

Extracted from kiwi._dispatch_command via mechanical substitution:
self → kiwi, console → kiwi.console.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from kiwi_core.tools.mental_performance import (
    assess_burnout,
    assess_competition_anxiety,
    format_anxiety_report,
    format_burnout_report,
    format_visualization,
    get_visualization_protocol,
    list_visualization_protocols,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_anxiety(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /anxiety — CSAI-2R-style competition anxiety profile."""
    parts = query[8:].strip().split()
    if len(parts) >= 3:
        try:
            cog = float(parts[0])
            som = float(parts[1])
            conf = float(parts[2])
            result = assess_competition_anxiety(cog, som, conf)
            output = format_anxiety_report(result)
            kiwi.console.print(Panel(output, title="[cyan]Competition Anxiety[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /anxiety <cognitive_1_4> <somatic_1_4> <confidence_1_4>[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /anxiety <cognitive_1_4> <somatic_1_4> <confidence_1_4>[/dim]")


def handle_burnout(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /burnout — REST-Q-style stress/recovery balance."""
    arg = query[8:].strip()
    if not arg or " recovery " not in f" {arg} ":
        kiwi.console.print("[dim]  Usage: /burnout stress k1=v1 k2=v2 ... recovery k3=v3 k4=v4 ...[/dim]")
        kiwi.console.print("[dim]  Stress keys: general_stress, emotional_stress, social_stress, training_stress, injury_concern (0-6)[/dim]")
        kiwi.console.print("[dim]  Recovery keys: sleep_quality, social_recovery, physical_recovery, general_wellbeing, self_efficacy (0-6)[/dim]")
    else:
        try:
            stress_part, recovery_part = arg.split(" recovery ", 1)
            stress_part = stress_part.replace("stress", "", 1).strip()
            stress_scores: dict = {}
            recovery_scores: dict = {}
            for token in stress_part.split():
                if "=" in token:
                    k, v = token.split("=", 1)
                    stress_scores[k] = float(v)
            for token in recovery_part.split():
                if "=" in token:
                    k, v = token.split("=", 1)
                    recovery_scores[k] = float(v)
            result = assess_burnout(stress_scores, recovery_scores)
            output = format_burnout_report(result)
            kiwi.console.print(Panel(output, title="[cyan]Burnout Risk[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /burnout stress k1=v1 ... recovery k2=v2 ...[/dim]")


def handle_visualize(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /visualize — list protocols OR lookup by type."""
    arg = query[10:].strip()
    if not arg:
        output = list_visualization_protocols()
        kiwi.console.print(Panel(output, title="[cyan]Visualization Protocols[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        proto = get_visualization_protocol(arg)
        if proto:
            output = format_visualization(proto)
            kiwi.console.print(Panel(output, title=f"[cyan]{proto.name}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        else:
            kiwi.console.print(f"[yellow]  No visualization for '{arg}'. Try /visualize with no args to list available.[/yellow]")
