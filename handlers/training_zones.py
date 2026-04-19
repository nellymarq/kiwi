"""Training zones command handlers (Tier 45).

Sync-only. All return None implicitly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.training_zones import (
    calculate_hr_zones_karvonen,
    calculate_pace_zones,
    calculate_power_zones,
    estimate_vo2max_cooper,
    format_hr_zones,
    format_intensity_distribution,
    format_pace_zones,
    format_power_zones,
    predict_hr_max,
    recommend_intensity_distribution,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_hrzones(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /hrzones — Karvonen HR zones from HRrest + HRmax."""
    parts = query[9:].strip().split()
    if len(parts) >= 2:
        hr_rest, hr_max = int(parts[0]), int(parts[1])
        zones = calculate_hr_zones_karvonen(hr_rest, hr_max)
        output = format_hr_zones(zones)
        kiwi.console.print(Panel(output, title=f"[cyan]HR Zones[/cyan]  [dim]HRrest={hr_rest} HRmax={hr_max}[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /hrzones <resting_hr> <max_hr>[/dim]")


def handle_powerzones(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /powerzones — cycling power zones from FTP."""
    parts = query[12:].strip().split()
    if len(parts) >= 1:
        ftp = int(parts[0])
        zones = calculate_power_zones(ftp)
        output = format_power_zones(zones)
        kiwi.console.print(Panel(output, title=f"[cyan]Power Zones[/cyan]  [dim]FTP={ftp}W[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /powerzones <ftp_watts>[/dim]")


def handle_pacezones(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /pacezones — running pace zones from VDOT."""
    parts = query[11:].strip().split()
    if len(parts) >= 1:
        vdot = float(parts[0])
        zones = calculate_pace_zones(vdot)
        output = format_pace_zones(zones)
        kiwi.console.print(Panel(output, title=f"[cyan]Pace Zones[/cyan]  [dim]VDOT={vdot}[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /pacezones <vdot>[/dim]")


def handle_vo2max(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /vo2max — Cooper 12-min test estimation."""
    parts = query[8:].strip().split()
    if len(parts) >= 1:
        dist = float(parts[0])
        result = estimate_vo2max_cooper(dist)
        lines = [
            f"VO2max: {result.vo2max:.1f} mL/kg/min",
            f"Category: {result.fitness_category.title()}",
            f"Method: {result.method}",
            f"Evidence: {result.evidence}",
        ]
        kiwi.console.print(Panel("\n".join(lines), title=f"[cyan]VO2max Estimate[/cyan]  [dim]{dist:.0f}m in 12 min[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /vo2max <distance_meters_in_12min>[/dim]")


def handle_hrmax(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /hrmax — age-predicted HRmax (tanaka/fox/gulati)."""
    parts = query[7:].strip().split()
    if len(parts) >= 1:
        age = int(parts[0])
        method = parts[1] if len(parts) > 1 else "tanaka"
        hr = predict_hr_max(age, method)
        kiwi.console.print(Panel(f"Predicted HRmax: {hr} bpm  (method: {method}, age: {age})", title="[cyan]HRmax Prediction[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /hrmax <age> [method: tanaka/fox/gulati][/dim]")


def handle_distribution(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /distribution — intensity distribution by sport + level + phase."""
    parts = query[13:].strip().split()
    sport = parts[0] if len(parts) > 0 else kiwi.profile.data.get("sport", "endurance")
    level = parts[1] if len(parts) > 1 else "intermediate"
    phase = parts[2] if len(parts) > 2 else "base"
    dist = recommend_intensity_distribution(sport, level, phase)
    output = format_intensity_distribution(dist)
    kiwi.console.print(Panel(output, title=f"[cyan]Intensity Distribution[/cyan]  [dim]{sport}/{level}/{phase}[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
