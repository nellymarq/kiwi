"""
Nutrient Gap Analyzer — Identify micronutrient gaps based on profile and stack.

Given athlete demographics, training status, and current supplement stack,
identifies likely micronutrient gaps using sport-adjusted RDA/AI values.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NutrientNeed:
    nutrient: str
    rda_ai: float        # Standard RDA or AI
    athlete_target: float # Sport-adjusted target
    unit: str
    current_source: str   # "diet", "supplement", "both", "none"
    gap_severity: str     # "covered", "likely_gap", "high_risk"
    note: str


# Athlete-adjusted micronutrient targets (per day)
# Based on ISSN, IOC, ACSM position stands
ATHLETE_TARGETS: dict[str, dict] = {
    "iron": {
        "rda_male": 8, "rda_female": 18, "athlete_adj_male": 12, "athlete_adj_female": 25,
        "unit": "mg", "high_risk": ["female", "endurance", "vegetarian", "vegan"],
    },
    "calcium": {
        "rda": 1000, "athlete_adj": 1500, "unit": "mg",
        "high_risk": ["female", "amenorrhea", "low_energy"],
    },
    "vitamin_d": {
        "rda": 600, "athlete_adj": 2000, "unit": "IU",
        "high_risk": ["indoor_sport", "northern_latitude", "dark_skin"],
    },
    "magnesium": {
        "rda_male": 420, "rda_female": 320, "athlete_adj_male": 500, "athlete_adj_female": 400,
        "unit": "mg", "high_risk": ["high_sweat", "endurance", "combat_sports"],
    },
    "zinc": {
        "rda_male": 11, "rda_female": 8, "athlete_adj_male": 15, "athlete_adj_female": 12,
        "unit": "mg", "high_risk": ["vegetarian", "vegan", "high_sweat"],
    },
    "omega_3": {
        "rda": 250, "athlete_adj": 2000, "unit": "mg EPA+DHA",
        "high_risk": ["low_fish_intake", "inflammatory_conditions"],
    },
    "vitamin_b12": {
        "rda": 2.4, "athlete_adj": 100, "unit": "mcg",
        "high_risk": ["vegetarian", "vegan", "metformin", "ppi"],
    },
    "folate": {
        "rda": 400, "athlete_adj": 800, "unit": "mcg DFE",
        "high_risk": ["female_childbearing", "mthfr", "alcohol"],
    },
    "vitamin_c": {
        "rda": 90, "athlete_adj": 200, "unit": "mg",
        "high_risk": ["smoker", "high_training_volume"],
    },
    "selenium": {
        "rda": 55, "athlete_adj": 100, "unit": "mcg",
        "high_risk": ["thyroid_issues", "low_soil_selenium"],
    },
    "potassium": {
        "rda": 2600, "athlete_adj": 4700, "unit": "mg",
        "high_risk": ["high_sweat", "endurance", "combat_sports"],
    },
    "sodium": {
        "rda": 500, "athlete_adj": 2000, "unit": "mg (during exercise)",
        "high_risk": ["high_sweat", "endurance", "hot_climate"],
    },
    "choline": {
        "rda_male": 550, "rda_female": 425, "athlete_adj": 550, "unit": "mg",
        "high_risk": ["endurance", "low_egg_intake"],
    },
}

SUPPLEMENT_NUTRIENT_MAP: dict[str, list[str]] = {
    "iron": ["iron"],
    "vitamin_d": ["vitamin_d"],
    "magnesium": ["magnesium"],
    "zinc": ["zinc"],
    "omega_3": ["omega_3"],
    "vitamin_b12": ["vitamin_b12"],
    "folate": ["folate"],
    "vitamin_c": ["vitamin_c"],
    "selenium": ["selenium"],
    "potassium": ["potassium"],
    "choline": ["choline"],
    "calcium": ["calcium"],
    "multivitamin": ["iron", "vitamin_d", "magnesium", "zinc", "vitamin_b12",
                      "folate", "vitamin_c", "selenium"],
}


def analyze_gaps(
    sex: str = "male",
    sport: str = "",
    dietary_restrictions: list[str] | None = None,
    current_supplements: list[str] | None = None,
    health_conditions: list[str] | None = None,
) -> list[NutrientNeed]:
    """Analyze nutrient gaps based on profile and current stack."""
    restrictions = [r.lower() for r in (dietary_restrictions or [])]
    supplements = [s.lower().replace("-", "_").replace(" ", "_") for s in (current_supplements or [])]
    conditions = [c.lower() for c in (health_conditions or [])]
    sport_lower = sport.lower()

    # Determine which nutrients are covered by supplements
    covered_nutrients: set[str] = set()
    for supp in supplements:
        for key, nutrients in SUPPLEMENT_NUTRIENT_MAP.items():
            if key in supp or supp in key:
                covered_nutrients.update(nutrients)

    results: list[NutrientNeed] = []

    for nutrient, data in ATHLETE_TARGETS.items():
        # Determine RDA and athlete target by sex
        if sex.lower() in ("female", "f"):
            rda = data.get("rda_female", data.get("rda", 0))
            target = data.get("athlete_adj_female", data.get("athlete_adj", rda))
        else:
            rda = data.get("rda_male", data.get("rda", 0))
            target = data.get("athlete_adj_male", data.get("athlete_adj", rda))

        unit = data.get("unit", "")
        high_risk_factors = data.get("high_risk", [])

        # Determine coverage
        is_supplemented = nutrient in covered_nutrients
        current_source = "supplement" if is_supplemented else "diet"

        # Assess risk
        risk_hits = []
        for factor in high_risk_factors:
            if factor in sex.lower():
                risk_hits.append(factor)
            if factor in sport_lower:
                risk_hits.append(factor)
            if factor in " ".join(restrictions):
                risk_hits.append(factor)
            if factor in " ".join(conditions):
                risk_hits.append(factor)

        if is_supplemented:
            severity = "covered"
        elif risk_hits:
            severity = "high_risk"
        else:
            severity = "likely_gap"

        note = ""
        if risk_hits:
            note = f"Risk factors: {', '.join(risk_hits)}"
        if not is_supplemented and severity != "covered":
            note += f" — not currently supplemented"

        results.append(NutrientNeed(
            nutrient=nutrient,
            rda_ai=rda,
            athlete_target=target,
            unit=unit,
            current_source=current_source,
            gap_severity=severity,
            note=note.strip(" —"),
        ))

    # Sort: high_risk first, then likely_gap, then covered
    severity_order = {"high_risk": 0, "likely_gap": 1, "covered": 2}
    results.sort(key=lambda x: severity_order.get(x.gap_severity, 1))

    return results


def format_gap_analysis(gaps: list[NutrientNeed]) -> str:
    """Format nutrient gap analysis for display."""
    if not gaps:
        return "No gap analysis data."

    icons = {"high_risk": "🔴", "likely_gap": "🟡", "covered": "✅"}
    lines = ["Nutrient Gap Analysis", "=" * 40, ""]

    for g in gaps:
        icon = icons.get(g.gap_severity, "•")
        lines.append(
            f"{icon} {g.nutrient:<15} "
            f"Target: {g.athlete_target:.0f} {g.unit:<10} "
            f"({g.current_source})"
        )
        if g.note:
            lines.append(f"   {g.note}")

    high_risk = [g for g in gaps if g.gap_severity == "high_risk"]
    likely = [g for g in gaps if g.gap_severity == "likely_gap"]
    covered = [g for g in gaps if g.gap_severity == "covered"]

    lines.append("")
    lines.append(f"Summary: {len(high_risk)} high-risk · {len(likely)} likely gaps · {len(covered)} covered")

    if high_risk:
        lines.append("")
        lines.append("Priority supplements to consider:")
        for g in high_risk:
            lines.append(f"  → /supp {g.nutrient}")

    return "\n".join(lines)
