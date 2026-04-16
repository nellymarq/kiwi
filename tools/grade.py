"""
GRADE Evidence Grading — Structured confidence assessment for research claims.

GRADE (Grading of Recommendations Assessment, Development, and Evaluation) is
the gold standard methodology for rating certainty of evidence. Adapted for
sports nutrition and performance research.

Reference: GRADE Handbook https://gdt.gradepro.org/app/handbook/handbook.html
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Starting levels by study design
DESIGN_STARTING_LEVEL: dict[str, int] = {
    "systematic_review": 4,          # HIGH
    "meta_analysis": 4,
    "rct": 4,
    "cohort": 2,                     # LOW
    "case_control": 2,
    "cross_sectional": 1,            # VERY LOW
    "case_series": 1,
    "expert_opinion": 1,
    "mechanistic": 1,
    "animal_study": 1,
}

CERTAINTY_LABELS = {
    4: "HIGH",
    3: "MODERATE",
    2: "LOW",
    1: "VERY LOW",
}

CERTAINTY_EMOJI = {
    "HIGH": "🟢",
    "MODERATE": "🟡",
    "LOW": "🟠",
    "VERY LOW": "🔵",
}


@dataclass
class GradeInputs:
    """Inputs for GRADE evidence assessment."""
    study_design: str                        # From DESIGN_STARTING_LEVEL keys

    # DOWNGRADE factors (each can subtract 1-2 levels)
    risk_of_bias: Literal["none", "serious", "very_serious"] = "none"
    inconsistency: Literal["none", "serious", "very_serious"] = "none"
    indirectness: Literal["none", "serious", "very_serious"] = "none"
    imprecision: Literal["none", "serious", "very_serious"] = "none"
    publication_bias: Literal["none", "suspected", "strongly_suspected"] = "none"

    # UPGRADE factors (observational evidence only)
    large_effect: bool = False               # RR > 2 or < 0.5
    dose_response: bool = False              # Clear dose-response gradient
    confounders_against: bool = False        # Plausible confounders would reduce effect


@dataclass
class GradeAssessment:
    """Output of GRADE evidence assessment."""
    certainty_level: int                     # 1-4
    certainty_label: str                     # VERY LOW / LOW / MODERATE / HIGH
    emoji: str
    starting_level: int
    downgrades: list[tuple[str, int]] = field(default_factory=list)
    upgrades: list[tuple[str, int]] = field(default_factory=list)
    rationale: str = ""

    def display(self) -> str:
        lines = [
            f"{self.emoji} Certainty of Evidence: {self.certainty_label}",
            f"   Starting level: {CERTAINTY_LABELS[self.starting_level]} (based on study design)",
        ]
        if self.downgrades:
            lines.append("   Downgrades:")
            for reason, pts in self.downgrades:
                lines.append(f"     -{pts}: {reason}")
        if self.upgrades:
            lines.append("   Upgrades:")
            for reason, pts in self.upgrades:
                lines.append(f"     +{pts}: {reason}")
        if self.rationale:
            lines.append(f"   Rationale: {self.rationale}")
        return "\n".join(lines)


def _downgrade_points(severity: str) -> int:
    return {"none": 0, "serious": 1, "very_serious": 2, "suspected": 1, "strongly_suspected": 2}.get(severity, 0)


def assess(inputs: GradeInputs) -> GradeAssessment:
    """Apply GRADE methodology to produce a certainty assessment."""
    design_key = inputs.study_design.lower().replace(" ", "_").replace("-", "_")
    starting = DESIGN_STARTING_LEVEL.get(design_key, 2)
    level = starting

    downgrades: list[tuple[str, int]] = []
    upgrades: list[tuple[str, int]] = []

    # Apply downgrades
    for name, value in (
        ("Risk of bias", inputs.risk_of_bias),
        ("Inconsistency", inputs.inconsistency),
        ("Indirectness", inputs.indirectness),
        ("Imprecision", inputs.imprecision),
        ("Publication bias", inputs.publication_bias),
    ):
        pts = _downgrade_points(value)
        if pts > 0:
            level -= pts
            downgrades.append((f"{name} ({value})", pts))

    # Apply upgrades (only for observational evidence that started at LOW)
    if starting <= 2:
        if inputs.large_effect:
            level += 1
            upgrades.append(("Large effect size", 1))
        if inputs.dose_response:
            level += 1
            upgrades.append(("Dose-response gradient", 1))
        if inputs.confounders_against:
            level += 1
            upgrades.append(("Plausible confounders would reduce effect", 1))

    level = max(1, min(4, level))
    label = CERTAINTY_LABELS[level]

    rationale = (
        f"{design_key.replace('_', ' ').title()} starting at {CERTAINTY_LABELS[starting]}. "
        + (f"Downgraded {starting - level} level(s) for {len(downgrades)} factor(s). "
           if level < starting else "")
        + (f"Upgraded {level - starting} level(s). " if level > starting else "")
    )

    return GradeAssessment(
        certainty_level=level,
        certainty_label=label,
        emoji=CERTAINTY_EMOJI[label],
        starting_level=starting,
        downgrades=downgrades,
        upgrades=upgrades,
        rationale=rationale.strip(),
    )


def assess_from_evidence_tier(tier_emoji: str, study_design: str = "rct") -> GradeAssessment:
    """Convert Kiwi's existing emoji tier system to GRADE for continuity."""
    tier_to_level = {"🟢": 4, "🟡": 3, "🟠": 2, "🔵": 1}
    level = tier_to_level.get(tier_emoji, 2)
    label = CERTAINTY_LABELS[level]
    return GradeAssessment(
        certainty_level=level,
        certainty_label=label,
        emoji=CERTAINTY_EMOJI[label],
        starting_level=DESIGN_STARTING_LEVEL.get(study_design.lower(), 4),
        rationale=f"Legacy tier mapping: {tier_emoji} → {label}",
    )
