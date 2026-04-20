"""Hydration command handlers (Tier 49).

Sync-only. All return None implicitly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.hydration import (
    SPORT_SWEAT_RATES,
    calculate_sweat_loss,
    design_rehydration_protocol,
    estimate_sweat_loss_by_sport,
    format_rehydration_report,
    hyponatremia_risk,
    pre_exercise_hydration_plan,
    urine_color_status,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_sweat(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /sweat — sweat-loss analysis from pre/post weights."""
    parts = query.split()
    if len(parts) >= 3:
        try:
            pre = float(parts[1])
            post = float(parts[2])
            fluid = float(parts[3]) if len(parts) > 3 else 0.0
            hrs = float(parts[4]) if len(parts) > 4 else 1.0
            sport = kiwi.profile.data.get("sport", "general")
            sl = calculate_sweat_loss(pre, post, fluid, hrs, sport=sport)
            kiwi.console.print(Panel(
                sl.summary(),
                title=f"[cyan]Sweat Loss Analysis[/cyan]  [dim]{sport}[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /sweat <pre_kg> <post_kg> [fluid_L] [duration_hrs][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /sweat <pre_kg> <post_kg> [fluid_L] [duration_hrs][/dim]")


def handle_sweatest(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /sweatest — sport-specific sweat-rate estimation."""
    parts = query.split()
    if len(parts) >= 3:
        try:
            sport = parts[1]
            hrs = float(parts[2])
            weight = kiwi.profile.data.get("weight_kg", 75.0)
            intensity = parts[3] if len(parts) > 3 else "moderate"
            sl = estimate_sweat_loss_by_sport(sport, hrs, body_weight_kg=float(weight), intensity=intensity)
            kiwi.console.print(Panel(
                sl.summary(),
                title=f"[cyan]Sweat Estimate[/cyan]  [dim]{sport} · {hrs:.1f}h · {intensity}[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /sweatest running 1.5 [easy|moderate|hard][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /sweatest <sport> <hours> [intensity]  "
                      "Sports: " + ", ".join(list(SPORT_SWEAT_RATES.keys())[:4]) + "...[/dim]")


def handle_rehydrate(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /rehydrate — post-session rehydration protocol."""
    parts = query.split()
    if len(parts) >= 3:
        try:
            pre = float(parts[1])
            post = float(parts[2])
            fluid = float(parts[3]) if len(parts) > 3 else 0.0
            hrs = float(parts[4]) if len(parts) > 4 else 1.0
            time_next = float(parts[5]) if len(parts) > 5 else 24.0
            sport = kiwi.profile.data.get("sport", "general")
            sl = calculate_sweat_loss(pre, post, fluid, hrs, sport=sport)
            protocol = design_rehydration_protocol(sl, time_next)
            kiwi.console.print(Panel(
                format_rehydration_report(protocol, sl),
                title="[cyan]Rehydration Protocol[/cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /rehydrate <pre_kg> <post_kg> [fluid_L] [duration_h] [hours_to_next_session][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /rehydrate <pre_kg> <post_kg>[/dim]")


def handle_urine(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /urine — Armstrong urine-color hydration status."""
    parts = query.split()
    if len(parts) >= 2:
        try:
            color_num = int(parts[1])
            result = urine_color_status(color_num)
            urgent_flag = " ⚠" if result["urgent"] else ""
            lines = [
                f"Color #{result['color_number']}: {result['color_name']}",
                f"Status: {result['status']}{urgent_flag}",
                f"Action: {result['action']}",
                f"Evidence: {result['evidence']}",
            ]
            kiwi.console.print(Panel(
                "\n".join(lines),
                title="[cyan]Urine Color / Hydration Status[/cyan]",
                border_style="red" if result["urgent"] else "cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /urine <1-8>  (1=pale, 8=dark brown)[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /urine <1-8>  (Armstrong urine color scale)[/dim]")


def handle_hyponatremia(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /hyponatremia — EAH risk from event duration + fluid intake."""
    parts = query.split()
    if len(parts) >= 3:
        try:
            event_hrs = float(parts[1])
            intake_L_hr = float(parts[2])
            sport = parts[3] if len(parts) > 3 else kiwi.profile.data.get("sport", "endurance")
            weight = kiwi.profile.data.get("weight_kg", 70.0)
            result = hyponatremia_risk(event_hrs, intake_L_hr, sport, float(weight))
            risk_color = {"HIGH": "red", "MODERATE": "yellow", "LOW": "green"}.get(result["risk_level"], "cyan")
            lines = [
                f"[{risk_color}]Risk Level: {result['risk_level']}[/{risk_color}]",
                "",
                "Risk Factors:",
            ]
            for d in result["drivers"]:
                lines.append(f"  • {d}")
            lines.append(f"\nRecommendation: {result['recommendation']}")
            lines.append(f"\n⚠ {result['key_warning']}")
            lines.append(f"\nEvidence: {result['evidence']}")
            kiwi.console.print(Panel(
                "\n".join(lines),
                title="[cyan]Hyponatremia (EAH) Risk Assessment[/cyan]",
                border_style=risk_color,
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /hyponatremia <event_hours> <fluid_L_per_hr> [sport][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /hyponatremia <event_hours> <L/hr intake>[/dim]")


def handle_prehydrate(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /prehydrate — pre-exercise hydration schedule."""
    parts = query.split()
    sport = parts[1] if len(parts) > 1 else kiwi.profile.data.get("sport", "general")
    hours_to_start = float(parts[2]) if len(parts) > 2 else 3.0
    weight = kiwi.profile.data.get("weight_kg", 75.0)
    plan = pre_exercise_hydration_plan(
        float(weight), event_duration_hours=1.5, sport=sport,
        start_hours_from_now=hours_to_start,
    )
    lines = [
        f"Pre-exercise fluid target: {plan['pre_exercise_target_mL']}mL",
        f"Intra-exercise target: {plan['intra_exercise_L_hr']} L/h",
        f"Expected sweat loss: ~{plan['total_expected_sweat_L']}L",
        f"Urine target: {plan['urine_target']}",
        "",
        "Schedule:",
    ]
    for step in plan["schedule"]:
        lines.append(f"  • {step}")
    lines.append(f"\nSodium: {plan['sodium_recommendation']}")
    lines.append(f"Evidence: {plan['evidence']}")
    kiwi.console.print(Panel(
        "\n".join(lines),
        title=f"[cyan]Pre-Exercise Hydration Plan[/cyan]  [dim]{sport} · T-{hours_to_start:.0f}h[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
