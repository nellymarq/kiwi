"""Competition-prep command handler (Tier 58).

Async. Consolidates /fight_prep and /race_prep into one handler with
Tier 35 autonomous enrichment (menstrual_context, cycle_phase_context,
injury_prevention_context) + Tier 40 cycle_day profile extrapolation
fallback.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from tools.female_athlete import format_cycle_training, match_training_to_phase
from tools.injury_prevention import (
    format_prevention_protocol,
    get_prevention_protocol,
    match_prevention_protocol,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


async def handle_competition_prep(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /fight_prep and /race_prep — competition-week integrated protocol."""
    notes_raw = ""
    if " " in query:
        notes_raw = query.split(maxsplit=1)[1].strip()

    # Parse cycle_day=N out of notes (first-match-wins, range 1-28)
    cycle_day = None
    notes_tokens: list = []
    for tok in notes_raw.split():
        if cycle_day is None and tok.startswith("cycle_day="):
            try:
                v = int(tok.split("=", 1)[1])
                if 1 <= v <= 28:
                    cycle_day = v
                    continue
            except ValueError:
                pass
        notes_tokens.append(tok)
    notes = " ".join(notes_tokens)

    # Fall back to profile extrapolation when notes didn't specify
    if cycle_day is None:
        cycle_day = kiwi.profile.get_current_cycle_day()

    sport = kiwi.profile.get("sport") or "combat sports"
    current_weight = kiwi.profile.get("weight_kg") or ""
    supplements_list = kiwi.profile.get("current_supplements") or []
    supplements_text = ", ".join(supplements_list) if supplements_list else "none listed"

    # Autonomous enrichment 1: menstrual_status context line
    menstrual_context = ""
    if kiwi.profile.data.get("sex") == "female":
        ms = kiwi.profile.data.get("menstrual_status")
        if ms in {"normal", "irregular", "amenorrheic", "heavy", "postmenopausal"}:
            menstrual_context = (
                f"Athlete menstrual status (from Kiwi profile — treat as context "
                f"for nutrient timing and injury-risk considerations):\n{ms}"
            )

    # Autonomous enrichment 2: cycle-phase analysis (needs cycle_day + sex=female)
    cycle_phase_context = ""
    if cycle_day is not None and kiwi.profile.data.get("sex") == "female":
        try:
            phase_info = match_training_to_phase(cycle_day, sport)
            phase_obj = phase_info["phase"]
            cycle_phase_context = (
                f"Menstrual cycle phase analysis (Kiwi tool, day {cycle_day}):\n"
                f"{format_cycle_training(phase_obj)}"
            )
        except (ValueError, KeyError):
            cycle_phase_context = ""

    # Autonomous enrichment 3: injury-history first-match prevention via shared helper
    injury_prevention_context = ""
    injury_history = kiwi.profile.data.get("injury_history") or []
    matched_key = match_prevention_protocol(injury_history)
    if matched_key:
        proto = get_prevention_protocol(matched_key)
        if proto:
            proto_text = format_prevention_protocol(proto, sport)
            injury_prevention_context = (
                f"Prior injury context from profile (consider emphasizing "
                f"relevant prevention patterns during taper/peak-week — this "
                f"is supplementary, not a primary rehab directive):\n{proto_text}"
            )

    kiwi.console.print(f"[dim]  Generating competition preparation protocol for {sport}...[/dim]\n")
    result = await kiwi.competition_prep_agent.run({
        "profile_summary": kiwi.profile.to_summary(),
        "sport": sport,
        "event": "competition" if "fight" in q_lower else "race",
        "current_weight": str(current_weight) + " kg" if current_weight else "",
        "target_weight": "",
        "current_supplements": supplements_text,
        "notes": notes,
        "menstrual_context": menstrual_context,
        "cycle_phase_context": cycle_phase_context,
        "injury_prevention_context": injury_prevention_context,
    })
    kiwi._state["last_output"] = result
    kiwi.console.print(result)
