"""Body composition command handlers (Tier 46).

Sync-only. All return None implicitly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.body_composition import (
    analyze_body_composition,
    calculate_energy_availability,
    calculate_ffmi,
    estimate_body_fat_jackson_pollock_3,
    format_composition_report,
    safe_weight_change_rate,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_skinfold(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /skinfold — Jackson-Pollock 3-site body fat estimation."""
    parts = query[10:].strip().split()
    if len(parts) >= 5:
        sex, age_s = parts[0], parts[1]
        s1, s2, s3 = float(parts[2]), float(parts[3]), float(parts[4])
        age = int(age_s)
        if sex.lower() == "male":
            bf = estimate_body_fat_jackson_pollock_3(sex, age, skinfold_chest_mm=s1, skinfold_abdomen_mm=s2, skinfold_thigh_mm=s3)
        else:
            bf = estimate_body_fat_jackson_pollock_3(sex, age, skinfold_tricep_mm=s1, skinfold_suprailiac_mm=s2, skinfold_thigh_mm=s3)
        kiwi.console.print(Panel(f"Estimated Body Fat: {bf:.1f}% (Jackson-Pollock 3-site)", title="[cyan]Skinfold Estimation[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /skinfold <sex> <age> <site1_mm> <site2_mm> <site3_mm>[/dim]")
        kiwi.console.print("[dim]  Males: chest, abdomen, thigh | Females: tricep, suprailiac, thigh[/dim]")


def handle_bodyfat(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /bodyfat — body composition analysis + FFMI."""
    parts = query[9:].strip().split()
    if len(parts) >= 2:
        wt, bf_pct = float(parts[0]), float(parts[1])
        sport = parts[2] if len(parts) > 2 else kiwi.profile.data.get("sport", "general_fitness")
        sex = kiwi.profile.data.get("sex", "male")
        ht = kiwi.profile.data.get("height_cm", 175)
        result = analyze_body_composition(wt, bf_pct, sex, ht, sport)
        ffmi = calculate_ffmi(wt, bf_pct, ht)
        report = format_composition_report(result, ffmi=ffmi)
        kiwi.console.print(Panel(report, title="[cyan]Body Composition Analysis[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /bodyfat <weight_kg> <body_fat_%> [sport][/dim]")


def handle_ffmi(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /ffmi — Fat-Free Mass Index calculation."""
    parts = query[5:].strip().split()
    if len(parts) >= 3:
        wt, bf_pct, ht = float(parts[0]), float(parts[1]), float(parts[2])
        result = calculate_ffmi(wt, bf_pct, ht)
        lines = [
            f"FFMI: {result.ffmi:.1f} kg/m²",
            f"Adjusted FFMI: {result.adjusted_ffmi:.1f} kg/m² (normalized to 1.80m)",
            f"Interpretation: {result.interpretation}",
            f"{result.natural_limit_note}",
            f"Evidence: {result.evidence}",
        ]
        kiwi.console.print(Panel("\n".join(lines), title="[cyan]Fat-Free Mass Index[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /ffmi <weight_kg> <body_fat_%> <height_cm>[/dim]")


def handle_ea(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /ea — Energy Availability (Loucks thresholds, RED-S screening)."""
    parts = query[4:].strip().split()
    if len(parts) >= 3:
        intake, exercise, lm = float(parts[0]), float(parts[1]), float(parts[2])
        ea = calculate_energy_availability(intake, exercise, lm)
        lines = [
            f"Energy Availability: {ea.ea_kcal_per_kg_ffm:.1f} kcal/kg FFM/day",
            f"Status: {ea.status.upper()}",
            f"Risk Level: {ea.risk_level.upper()}",
        ]
        if ea.consequences:
            lines.append("\nConsequences:")
            for c in ea.consequences:
                lines.append(f"  • {c}")
        if ea.recommendations:
            lines.append("\nRecommendations:")
            for r in ea.recommendations:
                lines.append(f"  • {r}")
        kiwi.console.print(Panel("\n".join(lines), title="[cyan]Energy Availability (RED-S Screening)[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /ea <energy_intake_kcal> <exercise_expenditure_kcal> <lean_mass_kg>[/dim]")


def handle_weightplan(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /weightplan — safe weight change rate by goal type."""
    parts = query[12:].strip().split()
    if len(parts) >= 3:
        now_kg, goal_kg, bf = float(parts[0]), float(parts[1]), float(parts[2])
        goal = parts[3] if len(parts) > 3 else "fat_loss"
        sex = kiwi.profile.data.get("sex", "male")
        wc = safe_weight_change_rate(now_kg, goal_kg, bf, sex, goal)
        lines = [
            f"Direction: {wc.direction.title()}",
            f"Rate: {wc.rate_kg_per_week:.2f} kg/week ({wc.rate_pct_bw_per_week}% BW/week)",
            f"Safe: {'Yes' if wc.safe else 'AGGRESSIVE — consider slowing'}",
            "",
        ]
        for note in wc.lean_mass_preservation_notes:
            lines.append(f"  • {note}")
        lines.append(f"\nEvidence: {wc.evidence}")
        kiwi.console.print(Panel("\n".join(lines), title="[cyan]Weight Change Plan[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print("[dim]  Usage: /weightplan <current_kg> <target_kg> <body_fat_%> [goal: fat_loss/muscle_gain/contest_prep][/dim]")
