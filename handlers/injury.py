"""Injury-prevention command handlers (Tier 41 pilot).

Sync-only. All return None implicitly. Architecture: functions taking
kiwi arg (string forward-ref to avoid circular import with kiwi.py).

Extracted from kiwi._dispatch_command lines 3350-3511 via mechanical
substitution: self → kiwi, console → kiwi.console. No refactoring.
"""
from __future__ import annotations

from datetime import datetime as _dt, timedelta as _td, timezone as _tz
from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

if TYPE_CHECKING:
    from kiwi import Kiwi

from tools.injury_prevention import (
    PROTOCOL_DB,
    calculate_acwr,
    calculate_fms_composite,
    format_acwr_report,
    format_prevention_protocol,
    get_prevention_protocol,
    list_prevention_protocols,
    return_to_sport_decision,
    score_fms_movement,
    screen_overuse_risk,
)


def handle_acwr(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /acwr — manual args OR history fallback (Tier 39)."""
    parts = query[5:].strip().split()
    if len(parts) >= 2:
        # Manual-args mode (Tier 30 original behavior)
        try:
            loads = [float(p) for p in parts]
            result = calculate_acwr(loads)
            output = format_acwr_report(result)
            kiwi.console.print(Panel(output, title="[cyan]Acute:Chronic Workload Ratio[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /acwr <load1> <load2> ... OR /acwr alone (reads tracked history)[/dim]")
    else:
        # No-args mode (Tier 39): read from progress history
        raw_loads = kiwi.progress.get_history("training_load", limit=200)
        if raw_loads:
            raw_loads.sort(key=lambda e: e.get("ts", ""))
            by_day: dict = {}
            for e in raw_loads:
                day = str(e.get("ts", ""))[:10]
                if day:
                    by_day[day] = by_day.get(day, 0.0) + float(e.get("value", 0.0))
            today = _dt.now(_tz.utc).date()
            recent_window_days = {
                (today - _td(days=i)).isoformat() for i in range(14)
            }
            recent_days_with_load = [d for d in by_day if d in recent_window_days]
            if len(recent_days_with_load) >= 7:
                sorted_days = sorted(by_day.keys())
                last_28 = sorted_days[-28:]
                daily_loads = [by_day[d] for d in last_28]
                result = calculate_acwr(
                    daily_loads, acute_window=7, chronic_window=28,
                )
                output = format_acwr_report(result)
                kiwi.console.print(Panel(
                    output,
                    title=f"[cyan]Acute:Chronic Workload Ratio[/cyan]  [dim](from {len(recent_days_with_load)} tracked days)[/dim]",
                    border_style="cyan",
                    box=box.ROUNDED,
                    padding=(0, 2),
                ))
                kiwi._state["last_output"] = output
            else:
                kiwi.console.print(
                    f"[dim]  Only {len(recent_days_with_load)} distinct day(s) of training_load in last 14 (need ≥7).[/dim]\n"
                    "[dim]  Usage: /acwr <load1> <load2> ... OR /track training_load <value> to build history.[/dim]"
                )
        else:
            kiwi.console.print(
                "[dim]  No training_load history tracked.[/dim]\n"
                "[dim]  Usage: /acwr <load1> <load2> ... OR /track training_load <value> to build history.[/dim]"
            )


def handle_fms(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /fms — single movement score OR multi-movement composite."""
    parts = query[4:].strip().split()
    if len(parts) >= 2 and len(parts) % 2 == 0:
        try:
            scores = {parts[i]: int(parts[i + 1]) for i in range(0, len(parts), 2)}
            if len(scores) == 1:
                movement, score = next(iter(scores.items()))
                fms = score_fms_movement(movement, score)
                lines = [
                    f"Movement: {fms.movement}",
                    f"Score: {fms.score}/3",
                ]
                if fms.compensations:
                    lines += ["", "Compensations:"] + [f"  • {c}" for c in fms.compensations]
                if fms.corrective_exercises:
                    lines += ["", "Correctives:"] + [f"  • {c}" for c in fms.corrective_exercises]
                output = "\n".join(lines)
                kiwi.console.print(Panel(output, title=f"[cyan]FMS — {movement}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                composite = calculate_fms_composite(scores)
                lines = [
                    f"Composite Score: {composite['composite_score']}/21",
                    f"Risk Level: {composite['risk_level'].upper()}",
                ]
                if composite["priority_movements"]:
                    lines.append(f"Priority: {', '.join(composite['priority_movements'])}")
                if composite["asymmetries"]:
                    lines.append(f"Asymmetries: {', '.join(composite['asymmetries'])}")
                output = "\n".join(lines)
                kiwi.console.print(Panel(output, title="[cyan]FMS Composite[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except (ValueError, KeyError):
            kiwi.console.print("[dim]  Usage: /fms <movement> <score> [<movement> <score> ...]  (scores 0-3)[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /fms <movement> <score> [<movement> <score> ...]  (scores 0-3)[/dim]")
        kiwi.console.print(f"[dim]  Movements: {', '.join(sorted(PROTOCOL_DB.keys())[:3])}..., etc. (see /prevent)[/dim]")


def handle_overuse(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /overuse — screen overuse injury risk by sport + age + hours."""
    parts = query[8:].strip().split()
    if len(parts) >= 3:
        try:
            sport = parts[0]
            age = int(parts[1])
            hours = float(parts[2])
            spec_age = int(parts[3]) if len(parts) > 3 else None
            result = screen_overuse_risk(sport, age, hours, specialization_age=spec_age)
            lines = [
                f"Sport: {result.sport}  Age: {result.age}",
                f"Training: {result.training_history}",
                f"Risk Level: {result.risk_level.upper()}",
            ]
            if result.risk_factors:
                lines += ["", "Risk Factors:"] + [f"  ⚠ {f}" for f in result.risk_factors]
            if result.recommendations:
                lines += ["", "Recommendations:"] + [f"  • {r}" for r in result.recommendations]
            lines += ["", f"Evidence: {result.evidence}"]
            output = "\n".join(lines)
            kiwi.console.print(Panel(output, title="[cyan]Overuse Risk Screening[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /overuse <sport> <age> <weekly_hours> [specialization_age][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /overuse <sport> <age> <weekly_hours> [specialization_age][/dim]")


def handle_return_to_sport(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /return — return-to-sport decision framework."""
    parts = query[7:].strip().split()
    if len(parts) >= 4:
        try:
            injury = parts[0]
            weeks = int(parts[1])
            pain = int(parts[2])
            deficit = float(parts[3])
            result = return_to_sport_decision(injury, weeks, pain, deficit)
            lines = [
                f"Injury: {injury}  Weeks since: {weeks}",
                f"Phase: {result['phase']}",
                f"Cleared: {'YES' if result['cleared'] else 'NO'}",
                f"Timeline: {result['timeline_estimate']}",
            ]
            if result["criteria_met"]:
                lines += ["", "Criteria Met:"] + [f"  ✓ {c}" for c in result["criteria_met"]]
            if result["criteria_remaining"]:
                lines += ["", "Remaining:"] + [f"  • {c}" for c in result["criteria_remaining"]]
            output = "\n".join(lines)
            kiwi.console.print(Panel(output, title="[cyan]Return-to-Sport Decision[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /return <injury> <weeks_since> <pain_0_10> <strength_deficit_%>[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /return <injury> <weeks_since> <pain_0_10> <strength_deficit_%>[/dim]")


def handle_prevent(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /prevent — prevention protocol lookup by injury type."""
    arg = query[8:].strip()
    if not arg:
        output = list_prevention_protocols()
        kiwi.console.print(Panel(output, title="[cyan]Prevention Protocols[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        proto = get_prevention_protocol(arg)
        if proto:
            sport = kiwi.profile.data.get("sport", "general")
            output = format_prevention_protocol(proto, sport)
            kiwi.console.print(Panel(output, title=f"[cyan]{proto.name}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        else:
            kiwi.console.print(f"[yellow]  No protocol for '{arg}'. Try /prevent with no args to list available.[/yellow]")
