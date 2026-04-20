"""Progress and team command handlers (Tier 53).

Sync-only.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from memory.progress import KNOWN_METRICS
from tools.proactive import check_biomarker, format_proactive_actions
from tools.team_analytics import format_team_summary

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_track(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /track — record a metric value with optional note + proactive biomarker check."""
    parts = query[7:].strip().split(maxsplit=2)
    if len(parts) >= 2:
        metric = parts[0].lower().replace(" ", "_")
        try:
            value = float(parts[1])
            note = parts[2] if len(parts) > 2 else ""
            kiwi.progress.record(metric, value, note=note)
            unit = KNOWN_METRICS.get(metric, "")
            kiwi.console.print(f"[dim]  Tracked: {metric} = {value} {unit}"
                          + (f" ({note})" if note else "") + "[/dim]")
            sex = kiwi.profile.get("sex") or "male"
            current_supps = kiwi.profile.get("current_supplements") or []
            actions = check_biomarker(metric, value, sex=sex, current_supplements=current_supps)
            if actions:
                kiwi.console.print()
                kiwi.console.print(format_proactive_actions(actions))
        except ValueError:
            kiwi.console.print(f"[dim red]  Value must be numeric: /track {metric} <number>[/dim red]")
    else:
        metrics_list = ", ".join(sorted(KNOWN_METRICS.keys())[:15]) + "..."
        kiwi.console.print("[dim]  Usage: /track <metric> <value> [note][/dim]")
        kiwi.console.print(f"[dim]  Known metrics: {metrics_list}[/dim]")


def handle_trends_with_metric(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /trends <metric> — time-series for one metric."""
    metric = query[8:].strip().lower().replace(" ", "_")
    if metric:
        output = kiwi.progress.format_trend(metric)
        kiwi.console.print(Panel(output, title=f"[cyan]Trend: {metric}[/cyan]", border_style="cyan", box=box.SIMPLE))
    else:
        kiwi.console.print("[dim]  Usage: /trends <metric>[/dim]")


def handle_dashboard(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /trends (no args) or /dashboard — latest-value dashboard across all metrics."""
    output = kiwi.progress.format_dashboard()
    kiwi.console.print(Panel(output, title="[cyan]Progress Dashboard[/cyan]", border_style="cyan", box=box.SIMPLE))


def handle_team(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /team — cross-client analytics summary."""
    summary = format_team_summary()
    kiwi.console.print(Panel(
        summary,
        title="[cyan]Team Analytics[/cyan]",
        border_style="cyan", box=box.SIMPLE,
    ))
