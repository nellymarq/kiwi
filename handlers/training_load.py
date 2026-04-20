"""Training-load command handlers (Tier 52).

Sync-only. Accesses kiwi._pending_sessions and kiwi.load_calc for
ATL/CTL/TSB. /session and /prilepin preserve Tier 30 early-exit
pattern (bare `return` on invalid input).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.periodization import (
    TrainingSession,
    format_block_plan,
    get_block_plan,
    prilepins_recommendation,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_session(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /session — log a training session to the ephemeral pending list."""
    parts = query.split()
    if len(parts) >= 4:
        try:
            day = int(parts[1])
            duration = float(parts[2])
            rpe = float(parts[3])
            if duration <= 0 or not (1 <= rpe <= 10):
                kiwi.console.print("[dim red]  Duration must be positive, RPE must be 1–10.[/dim red]")
                return
            sport = " ".join(parts[4:]) if len(parts) > 4 else ""
            s = TrainingSession(date_offset=day, duration_min=duration, rpe=rpe, sport=sport)
            kiwi._pending_sessions.append(s)
            kiwi.console.print(
                f"[dim]  Session logged: Day {day} | {duration:.0f}min | "
                f"RPE {rpe} | Load {s.session_load:.0f} AU[/dim]\n"
                f"[dim]  Total sessions: {len(kiwi._pending_sessions)}. "
                f"Use /load to compute ATL/CTL/TSB.[/dim]"
            )
        except ValueError:
            kiwi.console.print("[dim]  Usage: /session <day_offset> <minutes> <rpe_1-10> [sport][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /session 0 60 7 cycling[/dim]")


def handle_load(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /load — compute ATL/CTL/TSB from pending sessions."""
    if not kiwi._pending_sessions:
        kiwi.console.print(
            "[dim]  No sessions logged. Use /session <day> <min> <rpe> to add sessions.[/dim]\n"
            "[dim]  Example: /session 0 60 7 running[/dim]"
        )
    else:
        metrics = kiwi.load_calc.compute(kiwi._pending_sessions)
        ramp = kiwi.load_calc.ramp_rate(kiwi._pending_sessions)
        content = metrics.display() + "\n"
        if "ramp_rates" in ramp:
            content += "\n  Ramp Rate Analysis:\n"
            for r in ramp["ramp_rates"]:
                safe_icon = "✅" if r["safe"] else "⚠️"
                content += (
                    f"  Week {r['week']}: {r['load_au']:.0f} AU  "
                    f"({r['ramp_pct']:+.1f}%)  {safe_icon}\n"
                )
        kiwi.console.print(Panel(
            content,
            title=f"[cyan]Training Load Analysis[/cyan]  [dim]({len(kiwi._pending_sessions)} sessions)[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))


def handle_blocks(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /blocks — periodization block plan for a sport."""
    parts = query.split()
    sport = parts[1].lower() if len(parts) > 1 else "strength"
    athlete_name = kiwi.profile.data.get("name", "")
    blocks = get_block_plan(sport)
    report = format_block_plan(blocks, athlete_name=athlete_name)
    kiwi.console.print(Panel(
        report,
        title=f"[cyan]Periodization Plan[/cyan]  [dim]{sport.title()}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def handle_prilepin(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /prilepin — optimal rep range from intensity %."""
    try:
        pct = float(query.split()[1])
        if not (50 <= pct <= 110):
            kiwi.console.print("[dim red]  Intensity must be 50–110% of 1RM.[/dim red]")
            return
        result = prilepins_recommendation(pct)
        kiwi.console.print(Panel(
            result["note"] + "\n\n"
            f"  Optimal total reps: {result.get('optimal_total_reps', 'N/A')}\n"
            f"  Rep range: {result.get('rep_range', 'N/A')}\n"
            f"  Evidence: {result['evidence']}",
            title=f"[cyan]Prilepin's Table[/cyan]  [dim]{pct:.0f}% intensity[/dim]",
            border_style="cyan",
            box=box.SIMPLE,
        ))
    except (ValueError, IndexError):
        kiwi.console.print("[dim]  Usage: /prilepin 80[/dim]")
