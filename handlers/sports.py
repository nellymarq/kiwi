"""Sports intelligence assessment handler (Tier 55).

Async — invokes run_sports_assessment (which streams via the Anthropic
client). Uses the async pattern established in Tier 51.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from kiwi_core.agents.sports_agent import run_sports_assessment

if TYPE_CHECKING:
    from kiwi import Kiwi


async def handle_assess(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /assess — full Sports Intelligence assessment with streaming output."""
    notes = query[8:].strip() if len(query) > 8 else ""
    kiwi.console.print()
    kiwi.console.print(Panel(
        "[dim]Running Sports Intelligence Assessment...[/dim]",
        title="[bold cyan]Sports Intelligence Agent[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    kiwi.console.print()

    athlete_data = {
        "athlete_name": kiwi.profile.data.get("name", "Athlete"),
        "sport": kiwi.profile.data.get("sport", "General"),
        "training_phase": kiwi.profile.data.get("training_phase", "General Preparation"),
        "hrv_readings": [],
        "tsb": getattr(kiwi, "_last_tsb", None),
        "atl": getattr(kiwi, "_last_atl", None),
        "ctl": getattr(kiwi, "_last_ctl", None),
        "sleep_debt_hours": kiwi.profile.data.get("sleep_debt_hours", 0.0),
        "consecutive_hard_days": kiwi.profile.data.get("consecutive_hard_days", 0),
        "weeks_since_deload": kiwi.profile.data.get("weeks_since_deload", 0),
        "subjective_fatigue": kiwi.profile.data.get("subjective_fatigue"),
        "biomarker_summary": kiwi.profile.data.get("last_biomarker_summary", ""),
        "planned_session": kiwi.profile.data.get("planned_session", ""),
        "notes": notes or kiwi.profile.data.get("athlete_notes", ""),
    }

    def on_assess_text(text: str):
        kiwi.console.print(text, end="", markup=False)

    kiwi.console.print()
    await run_sports_assessment(kiwi.client, athlete_data, on_text=on_assess_text)
    kiwi.console.print()
    kiwi.console.print()
    kiwi.console.rule("[dim]Sports Intelligence Assessment Complete[/dim]")
