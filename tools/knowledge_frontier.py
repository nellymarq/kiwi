"""
Knowledge Frontier — Identify research gaps for a specific athlete.

Given profile, biomarkers, sport, and research history, identifies topics
that SHOULD have been researched but haven't been. Bridges the gap between
"I have data" and "I know what I'm missing."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FrontierGap:
    topic: str
    priority: str  # "critical", "high", "medium"
    reason: str
    suggested_command: str


# Topic rules: (condition_fn, topic, priority, reason, command)
# condition_fn receives (profile, metrics, research_topics) and returns True if gap exists
FRONTIER_RULES: list[tuple] = []


def _rule(fn, topic, priority, reason, command):
    FRONTIER_RULES.append((fn, topic, priority, reason, command))


# ── Critical gaps (safety-related) ──────────────────────────────────────────

_rule(
    lambda p, m, r: p.get("sex") == "female" and "red-s" not in r and "reds" not in r and "energy availability" not in r,
    "RED-S / energy availability assessment",
    "critical",
    "Female athlete without RED-S screening research",
    "/reds or /risk_screen",
)

_rule(
    lambda p, m, r: "ferritin" in m and any(v < 30 for v in m.get("ferritin", [])) and "iron" not in r,
    "Iron supplementation protocols",
    "critical",
    "Low ferritin tracked but iron supplementation not researched",
    "/synthesize iron supplementation athletes",
)

_rule(
    lambda p, m, r: p.get("sport", "").lower() in ("mma", "boxing", "wrestling", "judo", "combat") and "weight cut" not in r and "weight management" not in r,
    "Weight cut safety and protocols",
    "critical",
    "Combat sport athlete without weight management research",
    "/template weight_cut or /fight_prep",
)

# ── High priority gaps ─────────────────────────────────────────────────────

_rule(
    lambda p, m, r: p.get("training_status") in ("advanced", "elite") and "overtraining" not in r and "recovery" not in r,
    "Overtraining prevention and monitoring",
    "high",
    "Advanced/elite athlete without recovery/overtraining research",
    "/risk_screen or /synthesize overtraining markers",
)

_rule(
    lambda p, m, r: "creatine" in (p.get("current_supplements") or []) and "creatine" not in r,
    "Creatine optimization for your sport",
    "high",
    "Taking creatine but no sport-specific creatine research conducted",
    "/synthesize creatine for your sport",
)

_rule(
    lambda p, m, r: p.get("age") and p.get("age") > 35 and "aging" not in r and "masters" not in r and "longevity" not in r,
    "Masters athlete considerations",
    "high",
    "Athlete over 35 without age-specific training/nutrition research",
    "/synthesize nutrition masters athletes",
)

_rule(
    lambda p, m, r: "sleep" not in r and "circadian" not in r,
    "Sleep optimization for recovery",
    "high",
    "No sleep/recovery research conducted for this athlete",
    "/template sleep_optimization",
)

_rule(
    lambda p, m, r: len(p.get("current_supplements", []) or []) >= 4 and "interaction" not in r and "stack" not in r,
    "Supplement stack interaction check",
    "high",
    "Taking 4+ supplements without documented interaction review",
    "/optimize_stack",
)

# ── Medium priority gaps ────────────────────────────────────────────────────

_rule(
    lambda p, m, r: p.get("sport") and "periodization" not in r and "training plan" not in r,
    "Sport-specific periodization",
    "medium",
    "No training periodization research for this sport",
    "/training_plan",
)

_rule(
    lambda p, m, r: "gut" not in r and "gi" not in r and "digestive" not in r,
    "GI health and gut function",
    "medium",
    "Gut health not investigated — common issue in athletes",
    "/template gut_health",
)

_rule(
    lambda p, m, r: "hydration" not in r and "sweat" not in r,
    "Hydration strategy",
    "medium",
    "No hydration research documented",
    "/sweat or /rehydrate",
)

_rule(
    lambda p, m, r: p.get("sex") == "female" and "menstrual" not in r and "cycle" not in r and "phase" not in r,
    "Menstrual cycle training matching",
    "medium",
    "Female athlete without cycle-phase training research",
    "/cycle or /template female_athlete_health",
)

_rule(
    lambda p, m, r: "mental" not in r and "anxiety" not in r and "visualization" not in r,
    "Mental performance and competition psychology",
    "medium",
    "No mental performance research documented",
    "/anxiety or /visualize",
)


def analyze_frontiers(
    profile: dict[str, Any],
    tracked_metrics: dict[str, list[float]],
    research_history: list[str],
) -> list[FrontierGap]:
    """
    Identify knowledge gaps based on profile, tracked data, and research history.

    Args:
        profile: athlete profile dict
        tracked_metrics: {metric_name: [values]} from progress tracker
        research_history: list of past query strings (lowercased)
    """
    research_lower = " ".join(research_history).lower()
    gaps = []

    for fn, topic, priority, reason, command in FRONTIER_RULES:
        try:
            # Fix lambda closure issue — pass profile explicitly
            if fn(profile, tracked_metrics, research_lower):
                gaps.append(FrontierGap(
                    topic=topic, priority=priority,
                    reason=reason,
                    suggested_command=command,
                ))
        except Exception:
            continue

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2}
    gaps.sort(key=lambda g: priority_order.get(g.priority, 2))

    return gaps


def format_frontiers(gaps: list[FrontierGap]) -> str:
    """Format frontier gaps for display."""
    if not gaps:
        return "No research gaps identified — comprehensive coverage for this athlete."

    icons = {"critical": "🔴", "high": "🟠", "medium": "🟡"}
    lines = ["Research Frontier — Topics Not Yet Investigated", "=" * 50, ""]

    for g in gaps:
        icon = icons.get(g.priority, "•")
        lines.append(f"{icon} [{g.priority.upper()}] {g.topic}")
        lines.append(f"   Why: {g.reason}")
        lines.append(f"   Try: {g.suggested_command}")
        lines.append("")

    critical = sum(1 for g in gaps if g.priority == "critical")
    high = sum(1 for g in gaps if g.priority == "high")
    lines.append(f"Total: {len(gaps)} gaps ({critical} critical, {high} high priority)")

    return "\n".join(lines)
