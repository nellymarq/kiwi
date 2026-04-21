"""
Proactive Recommendations — Auto-link biomarker findings to actionable next steps.

When a biomarker is recorded or interpreted, this module checks if it triggers
any evidence-based intervention from the supplement DB, interaction safety, or
monitoring protocol. Returns structured suggestions without requiring manual
tool chaining.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kiwi_core.tools.biomarkers import BIOMARKER_DB, BiomarkerInterpreter
from kiwi_core.tools.supplements import SUPPLEMENT_DB, DosingProtocol
from kiwi_core.tools.interactions import lookup_interactions


# Mapping: biomarker status → relevant supplement keywords
BIOMARKER_SUPPLEMENT_MAP: dict[str, list[str]] = {
    "ferritin": ["iron", "vitamin_c"],
    "hemoglobin": ["iron", "vitamin_c", "vitamin_b12", "folate"],
    "vitamin_d": ["vitamin_d", "magnesium"],
    "testosterone_male": ["zinc", "vitamin_d", "ashwagandha", "tongkat_ali"],
    "testosterone_female": ["zinc", "vitamin_d"],
    "cortisol_morning": ["ashwagandha", "rhodiola", "phosphatidylserine"],
    "magnesium": ["magnesium"],
    "crp": ["omega_3", "curcumin"],
    "homocysteine": ["folate", "vitamin_b12"],
    "fasting_insulin": ["berberine", "magnesium"],
    "tsh": ["selenium"],
    "free_t3": ["selenium"],
    "tpo_antibodies": ["selenium"],
    "dhea_s": ["rhodiola", "ashwagandha"],
    "mma": ["vitamin_b12"],
    "serum_selenium": ["selenium"],
    "serum_copper": ["zinc"],
}


@dataclass
class ProactiveAction:
    trigger: str
    severity: str  # "info", "warning", "action"
    message: str
    supplements: list[str] = field(default_factory=list)
    interactions_to_check: list[str] = field(default_factory=list)
    suggested_command: str = ""


def check_biomarker(
    marker_key: str,
    value: float,
    sex: str = "male",
    current_supplements: list[str] | None = None,
) -> list[ProactiveAction]:
    """
    Check a biomarker value and return proactive action suggestions.
    Returns empty list if value is normal and no action needed.
    """
    interpreter = BiomarkerInterpreter()
    result = interpreter.interpret(marker_key, value, sex=sex)
    if not result:
        return []

    actions: list[ProactiveAction] = []
    status = result.status

    if status in ("NORMAL", "ATHLETIC_NORM"):
        return []

    # Build action based on status
    relevant_supps = BIOMARKER_SUPPLEMENT_MAP.get(marker_key, [])

    if status in ("LOW", "ATHLETIC_LOW", "CRITICAL_LOW"):
        available_supps = [s for s in relevant_supps if s in SUPPLEMENT_DB]
        if available_supps:
            supp_names = [SUPPLEMENT_DB[s].name for s in available_supps]
            supp_doses = [f"{SUPPLEMENT_DB[s].name}: {SUPPLEMENT_DB[s].maintenance_dose}" for s in available_supps]

            # Check interactions with current stack
            interaction_warnings = []
            if current_supplements:
                all_compounds = list(current_supplements) + [SUPPLEMENT_DB[s].name for s in available_supps]
                interactions = lookup_interactions(all_compounds, min_severity="monitor")
                for ix in interactions:
                    interaction_warnings.append(
                        f"{ix.compound_a} + {ix.compound_b}: {ix.severity} — {ix.recommendation[:100]}"
                    )

            actions.append(ProactiveAction(
                trigger=f"{result.name} = {value} {result.unit} ({status})",
                severity="action",
                message=f"{result.name} is below optimal. Consider: {', '.join(supp_names)}.",
                supplements=available_supps,
                interactions_to_check=interaction_warnings,
                suggested_command=f"/optimize_stack" if len(available_supps) > 1 else f"/supp {available_supps[0]}",
            ))

        if result.ref.action_if_low:
            actions.append(ProactiveAction(
                trigger=f"{result.name} ({status})",
                severity="warning",
                message=result.ref.action_if_low,
            ))

    elif status in ("HIGH", "CRITICAL_HIGH"):
        if result.ref.action_if_high:
            actions.append(ProactiveAction(
                trigger=f"{result.name} = {value} {result.unit} ({status})",
                severity="warning",
                message=result.ref.action_if_high,
            ))

    return actions


def format_proactive_actions(actions: list[ProactiveAction]) -> str:
    """Format proactive actions for display."""
    if not actions:
        return ""

    lines = []
    for a in actions:
        icon = {"info": "💡", "warning": "⚠️", "action": "🎯"}.get(a.severity, "•")
        lines.append(f"{icon} {a.trigger}")
        lines.append(f"   {a.message}")
        if a.supplements:
            lines.append(f"   Supplements: {', '.join(a.supplements)}")
        if a.interactions_to_check:
            lines.append("   Interaction flags:")
            for w in a.interactions_to_check[:3]:
                lines.append(f"     {w}")
        if a.suggested_command:
            lines.append(f"   Try: {a.suggested_command}")
        lines.append("")

    return "\n".join(lines)
