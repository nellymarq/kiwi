"""
Supplement Timing Schedule — Generate daily timing protocol from athlete's stack.

Takes current supplement list, looks up DosingProtocol timing data, resolves
interaction-based separations, and produces a time-of-day schedule.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kiwi_core.tools.supplements import SUPPLEMENT_DB, resolve_supplement


@dataclass
class TimingSlot:
    time_of_day: str  # "morning", "pre_workout", "post_workout", "with_dinner", "bedtime"
    supplements: list[tuple[str, str]]  # [(name, dose)]


# Timing classification rules based on DosingProtocol.timing field
TIMING_KEYWORDS: dict[str, list[str]] = {
    "morning": ["morning", "am", "breakfast", "empty stomach", "upon waking"],
    "pre_workout": ["pre-workout", "pre workout", "before exercise", "before training", "30-60 min before", "60 min before", "pre-exercise"],
    "post_workout": ["post-workout", "post workout", "after exercise", "after training", "post-exercise"],
    "with_dinner": ["with meal", "with food", "with dinner", "evening meal", "with fat"],
    "bedtime": ["bedtime", "before bed", "before sleep", "evening", "night"],
}

SLOT_DISPLAY = {
    "morning": "☀️  Morning (with breakfast)",
    "pre_workout": "💪 Pre-Workout (30-60 min before)",
    "post_workout": "🏋️ Post-Workout (within 60 min)",
    "with_dinner": "🍽️  With Dinner",
    "bedtime": "🌙 Bedtime (30-60 min before sleep)",
}

SLOT_ORDER = ["morning", "pre_workout", "post_workout", "with_dinner", "bedtime"]

# Supplements that need separation (from interaction DB patterns)
SEPARATION_RULES: list[tuple[str, str, str]] = [
    ("iron", "zinc", "Separate by 2+ hours (compete for DMT1 absorption)"),
    ("iron", "calcium", "Separate by 2+ hours (calcium chelates iron)"),
    ("levothyroxine", "iron", "Separate by 4+ hours"),
    ("levothyroxine", "calcium", "Separate by 4+ hours"),
]


def _classify_timing(timing_str: str) -> str:
    """Classify a DosingProtocol.timing string into a time-of-day slot."""
    t = timing_str.lower()
    for slot, keywords in TIMING_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return slot
    if "any time" in t:
        return "morning"
    return "with_dinner"


def generate_timing_schedule(supplement_names: list[str]) -> list[TimingSlot]:
    """Generate a timing schedule from a list of supplement names."""
    slots: dict[str, list[tuple[str, str]]] = {s: [] for s in SLOT_ORDER}

    for name in supplement_names:
        proto = resolve_supplement(name)
        if not proto:
            slots["morning"].append((name, "dose unknown"))
            continue
        slot = _classify_timing(proto.timing)
        slots[slot].append((proto.name, proto.maintenance_dose))

    return [TimingSlot(time_of_day=s, supplements=slots[s]) for s in SLOT_ORDER if slots[s]]


def check_separation_conflicts(supplement_names: list[str]) -> list[str]:
    """Check if any supplements in the stack need time separation."""
    names_lower = {n.lower().replace("-", "_").replace(" ", "_") for n in supplement_names}
    conflicts = []
    for a, b, note in SEPARATION_RULES:
        if a in names_lower and b in names_lower:
            conflicts.append(f"⚠️ {a} + {b}: {note}")
    return conflicts


def format_timing_schedule(schedule: list[TimingSlot], conflicts: list[str] | None = None) -> str:
    """Format the timing schedule for display."""
    if not schedule:
        return "No supplements to schedule. Set your stack with /profile set current_supplements creatine,caffeine,..."

    lines = ["Daily Supplement Timing Schedule", "=" * 40, ""]
    for slot in schedule:
        header = SLOT_DISPLAY.get(slot.time_of_day, slot.time_of_day)
        lines.append(header)
        for name, dose in slot.supplements:
            lines.append(f"  • {name}: {dose}")
        lines.append("")

    if conflicts:
        lines.append("Timing Conflicts:")
        for c in conflicts:
            lines.append(f"  {c}")
        lines.append("")

    return "\n".join(lines)
