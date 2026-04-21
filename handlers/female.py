"""Female-athlete command handlers (Tier 44).

Sync-only. All return None implicitly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from kiwi_core.tools.female_athlete import (
    CYCLE_PHASES,
    calculate_iron_needs,
    format_reds_report,
    match_training_to_phase,
    postpartum_return_protocol,
    screen_reds,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_cycle(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /cycle — no args lists phases, with day+sport runs match."""
    parts = query[6:].strip().split()
    if not parts:
        lines = ["═══ Menstrual Cycle Phases ═══", ""]
        for phase in CYCLE_PHASES:
            lines.append(f"  {phase.phase_name}  (days {phase.day_range[0]}-{phase.day_range[1]})")
        output = "\n".join(lines)
        kiwi.console.print(Panel(output, title="[cyan]Cycle Phases[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        try:
            day = int(parts[0])
            sport = parts[1] if len(parts) > 1 else kiwi.profile.data.get("sport", "general")
            match = match_training_to_phase(day, sport)
            phase = match["phase"]
            lines = [
                f"Day {day} — Phase: {phase.phase_name.replace('_', ' ').title()}",
                f"Days range: {phase.day_range[0]}-{phase.day_range[1]}",
                "",
                f"Focus: {match['recommended_focus']}",
                f"Intensity modifier: {match['intensity_modifier']}x",
                "",
                f"Hormonal: {phase.hormonal_profile}",
                "",
                f"Training: {phase.training_recommendations}",
                "",
                f"Nutrition: {phase.nutrition_notes}",
                "",
                f"Key nutrients: {', '.join(match['key_nutrients'])}",
                "",
                f"Injury risk: {match['injury_risk_notes']}",
            ]
            output = "\n".join(lines)
            kiwi.console.print(Panel(output, title=f"[cyan]Cycle Training — Day {day}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /cycle [day_1-28] [sport][/dim]")


def handle_reds(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /reds — RED-S screening via key=value responses."""
    arg = query[5:].strip()
    if not arg:
        kiwi.console.print("[dim]  Usage: /reds key=value [key=value ...][/dim]")
        kiwi.console.print("[dim]  Keys: bmi, menstrual_status, bone_stress_injuries, disordered_eating, weight_loss_pct, mood_disturbance, gi_issues, recurrent_illness, declining_performance, low_energy_availability[/dim]")
    else:
        responses: dict = {}
        for token in arg.split():
            if "=" not in token:
                continue
            k, v = token.split("=", 1)
            vl = v.lower()
            if vl in ("true", "yes", "y", "1"):
                responses[k] = True
            elif vl in ("false", "no", "n", "0"):
                responses[k] = False
            else:
                try:
                    responses[k] = float(v) if "." in v else int(v)
                except ValueError:
                    responses[k] = v
        result = screen_reds(responses)
        output = format_reds_report(result)
        kiwi.console.print(Panel(output, title="[cyan]RED-S Screening[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
        kiwi._state["last_output"] = output


def handle_iron(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /iron — iron needs by menstrual status + training hours + diet."""
    parts = query[5:].strip().split()
    if len(parts) >= 2:
        try:
            menstrual_status = parts[0]
            hours = float(parts[1])
            diet = parts[2] if len(parts) > 2 else "omnivore"
            result = calculate_iron_needs(menstrual_status, hours, diet)
            lines = [
                f"RDA: {result['rda_mg']} mg",
                f"Recommended: {result['recommended_mg']} mg/day",
                "",
                f"Rationale: {result['rationale']}",
                "",
                f"Monitoring: {result['monitoring']}",
            ]
            output = "\n".join(lines)
            kiwi.console.print(Panel(output, title="[cyan]Iron Needs (Female Athlete)[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /iron <menstrual_status> <weekly_hours> [omnivore|vegetarian|vegan][/dim]")
            kiwi.console.print("[dim]  menstrual_status: normal, heavy, amenorrheic[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /iron <menstrual_status> <weekly_hours> [omnivore|vegetarian|vegan][/dim]")


def handle_postpartum(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /postpartum — return-to-sport protocol by weeks + delivery."""
    parts = query[11:].strip().split()
    if len(parts) >= 1:
        try:
            weeks = int(parts[0])
            delivery = parts[1] if len(parts) > 1 else "vaginal"
            complications = parts[2].split(",") if len(parts) > 2 else []
            result = postpartum_return_protocol(weeks, delivery_type=delivery, complications=complications)
            lines = [
                f"Phase: {result.phase}",
                f"Weeks postpartum: {result.weeks_postpartum}",
                "",
                "Exercise Guidelines:",
            ]
            lines += [f"  • {g}" for g in result.exercise_guidelines]
            if result.contraindications:
                lines += ["", "Contraindications:"] + [f"  ⚠ {c}" for c in result.contraindications]
            if result.progression_criteria:
                lines += ["", "Progression Criteria:"] + [f"  • {c}" for c in result.progression_criteria]
            output = "\n".join(lines)
            kiwi.console.print(Panel(output, title="[cyan]Postpartum Return-to-Sport[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /postpartum <weeks> [vaginal|c-section] [comma,sep,complications][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /postpartum <weeks> [vaginal|c-section] [comma,sep,complications][/dim]")
