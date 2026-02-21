"""
Body composition analysis for Kiwi.

Evidence-based body composition tracking and interpretation:
- Body fat estimation methods (skinfold, BIA, DEXA interpretation)
- Fat-free mass index (FFMI) — natural muscular potential
- Energy Availability (EA) screening for RED-S
- Body composition targets by sport
- Rate of weight change safety limits

References:
- Jackson & Pollock (1978) Br J Nutr — Skinfold body fat equations
- Schutz et al. (2002) Int J Obesity — FFMI normative data
- Mountjoy et al. (2018) Br J Sports Med — IOC RED-S consensus 2018
- Sundgot-Borgen et al. (2013) Br J Sports Med — Body composition in sport
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Literal


# ── Body Fat Estimation ───────────────────────────────────────────────────────

@dataclass
class BodyFatResult:
    method: str
    body_fat_pct: float
    fat_mass_kg: float
    lean_mass_kg: float
    category: str         # essential / athletic / fitness / average / obese
    sport_context: str
    evidence: str


# Category thresholds (ACSM / NSCA guidelines)
BF_CATEGORIES_MALE = [
    (0,   5,  "essential"),     # minimum essential fat
    (5,  13,  "athletic"),
    (13, 18,  "fitness"),
    (18, 25,  "average"),
    (25, 100, "obese"),
]

BF_CATEGORIES_FEMALE = [
    (0,  12, "essential"),
    (12, 20, "athletic"),
    (20, 25, "fitness"),
    (25, 32, "average"),
    (32, 100, "obese"),
]


def classify_body_fat(bf_pct: float, sex: str = "male") -> str:
    """Classify body fat % into ACSM category."""
    table = BF_CATEGORIES_MALE if sex.lower() == "male" else BF_CATEGORIES_FEMALE
    for low, high, cat in table:
        if low <= bf_pct < high:
            return cat
    return "unknown"


# Sport-specific body composition targets
SPORT_BF_TARGETS: dict[str, dict] = {
    "running_distance": {"male": (5, 12), "female": (12, 20), "notes": "Lower BF correlates with VO2max/kg; RED-S risk below ranges"},
    "cycling": {"male": (6, 15), "female": (14, 22), "notes": "Power-to-weight ratio critical for climbing; less so for time trial"},
    "swimming": {"male": (8, 15), "female": (14, 22), "notes": "Some body fat aids buoyancy; very low BF may impair insulation"},
    "powerlifting": {"male": (10, 25), "female": (18, 30), "notes": "BF less critical; weight class management drives composition"},
    "bodybuilding": {"male": (3, 6), "female": (10, 14), "notes": "Competition only — unsustainable below these ranges"},
    "basketball": {"male": (6, 15), "female": (15, 22), "notes": "Position-dependent: guards leaner than centers"},
    "football_soccer": {"male": (6, 14), "female": (14, 22), "notes": "Position-dependent; midfielders typically leanest"},
    "rugby": {"male": (8, 18), "female": (16, 25), "notes": "Backs leaner than forwards; mass beneficial for contact"},
    "combat_sports": {"male": (5, 15), "female": (12, 22), "notes": "Weight class sport; fight weight vs. training weight"},
    "crossfit": {"male": (8, 16), "female": (16, 24), "notes": "Balance of strength and conditioning; no extreme leanness needed"},
    "general_fitness": {"male": (10, 20), "female": (18, 28), "notes": "Health-optimal range for general population"},
}


def estimate_body_fat_jackson_pollock_3(
    sex: str,
    age: int,
    skinfold_chest_mm: float = 0,
    skinfold_abdomen_mm: float = 0,
    skinfold_thigh_mm: float = 0,
    skinfold_tricep_mm: float = 0,
    skinfold_suprailiac_mm: float = 0,
) -> float:
    """
    Estimate body fat % using Jackson-Pollock 3-site skinfold equation.

    Males: chest + abdomen + thigh
    Females: tricep + suprailiac + thigh

    Returns body fat percentage.
    """
    if sex.lower() == "male":
        s = skinfold_chest_mm + skinfold_abdomen_mm + skinfold_thigh_mm
        body_density = (
            1.10938 - 0.0008267 * s + 0.0000016 * s**2 - 0.0002574 * age
        )
    else:
        s = skinfold_tricep_mm + skinfold_suprailiac_mm + skinfold_thigh_mm
        body_density = (
            1.0994921 - 0.0009929 * s + 0.0000023 * s**2 - 0.0001392 * age
        )

    # Siri equation: BF% = (495 / body_density) - 450
    bf_pct = (495.0 / body_density) - 450.0
    return round(max(0.0, bf_pct), 1)


def analyze_body_composition(
    weight_kg: float,
    body_fat_pct: float,
    sex: str = "male",
    height_cm: float = 175.0,
    sport: str = "general_fitness",
    age: int = 25,
) -> BodyFatResult:
    """
    Analyze body composition with sport-specific context.

    Args:
        weight_kg: Total body weight.
        body_fat_pct: Measured or estimated body fat %.
        sex: 'male' or 'female'.
        height_cm: Height in cm (for FFMI calculation).
        sport: Key from SPORT_BF_TARGETS.
        age: Age in years.

    Returns:
        BodyFatResult with categorization and sport context.
    """
    fat_mass = weight_kg * (body_fat_pct / 100)
    lean_mass = weight_kg - fat_mass
    category = classify_body_fat(body_fat_pct, sex)

    sport_data = SPORT_BF_TARGETS.get(sport, SPORT_BF_TARGETS["general_fitness"])
    sex_key = sex.lower()
    target_range = sport_data.get(sex_key, sport_data.get("male", (10, 20)))

    if body_fat_pct < target_range[0]:
        sport_context = (
            f"BELOW sport target range ({target_range[0]}–{target_range[1]}%). "
            f"Risk of RED-S, hormonal disruption, impaired immunity. "
            f"{sport_data.get('notes', '')}"
        )
    elif body_fat_pct > target_range[1]:
        sport_context = (
            f"ABOVE sport target range ({target_range[0]}–{target_range[1]}%). "
            f"May benefit from gradual fat loss (0.5–1% BW/week max). "
            f"{sport_data.get('notes', '')}"
        )
    else:
        sport_context = (
            f"Within sport target range ({target_range[0]}–{target_range[1]}%). "
            f"{sport_data.get('notes', '')}"
        )

    return BodyFatResult(
        method="Analysis",
        body_fat_pct=round(body_fat_pct, 1),
        fat_mass_kg=round(fat_mass, 1),
        lean_mass_kg=round(lean_mass, 1),
        category=category,
        sport_context=sport_context,
        evidence="🟢 Strong — ACSM/NSCA classification; sport targets from Sundgot-Borgen et al. 2013",
    )


# ── FFMI — Fat-Free Mass Index ────────────────────────────────────────────────

@dataclass
class FFMIResult:
    ffmi: float           # kg/m²
    adjusted_ffmi: float  # normalized to 1.80m height
    interpretation: str
    natural_limit_note: str
    evidence: str = "🟡 Moderate — Schutz et al. 2002, Kouri et al. 1995"


def calculate_ffmi(
    weight_kg: float,
    body_fat_pct: float,
    height_cm: float,
) -> FFMIResult:
    """
    Calculate Fat-Free Mass Index (FFMI).

    FFMI = lean_mass_kg / height_m²
    Adjusted FFMI = FFMI + 6.1 × (1.80 - height_m)

    Normative values (Kouri et al. 1995):
    - Average male: 18–20
    - Athletic male: 20–22
    - Highly muscular: 22–25
    - Natural ceiling: ~25 (Schutz et al.)
    - Suspicious of PED use: >25

    Args:
        weight_kg: Total body weight.
        body_fat_pct: Body fat percentage.
        height_cm: Height in cm.

    Returns:
        FFMIResult with raw FFMI, adjusted FFMI, and interpretation.
    """
    height_m = height_cm / 100.0
    lean_mass = weight_kg * (1 - body_fat_pct / 100.0)
    ffmi = lean_mass / (height_m ** 2)
    adjusted_ffmi = ffmi + 6.1 * (1.80 - height_m)

    if adjusted_ffmi < 18:
        interpretation = "Below average muscularity"
    elif adjusted_ffmi < 20:
        interpretation = "Average muscularity"
    elif adjusted_ffmi < 22:
        interpretation = "Above average — athletic"
    elif adjusted_ffmi < 25:
        interpretation = "Highly muscular — near natural ceiling"
    else:
        interpretation = "Exceeds typical natural limit — possible genetic outlier or PED use"

    natural_note = (
        f"Natural ceiling ~25 FFMI (Kouri et al. 1995). "
        f"Your adjusted FFMI: {adjusted_ffmi:.1f}. "
        f"{'Within natural range.' if adjusted_ffmi <= 25 else 'Above typical natural range.'}"
    )

    return FFMIResult(
        ffmi=round(ffmi, 1),
        adjusted_ffmi=round(adjusted_ffmi, 1),
        interpretation=interpretation,
        natural_limit_note=natural_note,
    )


# ── Energy Availability (EA) — RED-S Screening ───────────────────────────────

@dataclass
class EnergyAvailability:
    ea_kcal_per_kg_ffm: float
    status: str          # optimal / reduced / low / clinical
    risk_level: str      # none / moderate / high / critical
    consequences: list[str]
    recommendations: list[str]
    evidence: str = "🟢 Strong — Mountjoy et al. 2018 IOC RED-S consensus"


# EA thresholds (Loucks et al. 2011; Mountjoy et al. 2018)
EA_THRESHOLDS = {
    "optimal":  (45, 999),   # ≥45 kcal/kg FFM/d
    "reduced":  (30, 45),    # 30–45: subclinical effects begin
    "low":      (20, 30),    # <30: clinical threshold — menstrual/hormonal disruption
    "clinical": (0, 20),     # <20: severe — bone loss, immune suppression, cardiovascular risk
}


def calculate_energy_availability(
    energy_intake_kcal: float,
    exercise_energy_expenditure_kcal: float,
    lean_mass_kg: float,
) -> EnergyAvailability:
    """
    Calculate Energy Availability (EA) for RED-S screening.

    EA = (Energy Intake - Exercise Energy Expenditure) / Fat-Free Mass (kg)

    Thresholds (Loucks et al. 2011):
    - ≥45 kcal/kg FFM/d: Optimal
    - 30–45: Reduced (subclinical effects)
    - <30: Low (clinical threshold — menstrual, bone, hormonal disruption)
    - <20: Critical (severe consequences)

    Args:
        energy_intake_kcal: Daily dietary energy intake.
        exercise_energy_expenditure_kcal: Energy cost of exercise only (not NEAT/TEF).
        lean_mass_kg: Fat-free mass.

    Returns:
        EnergyAvailability with status, risk level, and clinical recommendations.
    """
    if lean_mass_kg <= 0:
        lean_mass_kg = 50.0  # safe default

    ea = (energy_intake_kcal - exercise_energy_expenditure_kcal) / lean_mass_kg

    consequences: list[str] = []
    recommendations: list[str] = []

    if ea >= 45:
        status = "optimal"
        risk_level = "none"
        recommendations.append("Energy availability is optimal. Maintain current intake.")
    elif ea >= 30:
        status = "reduced"
        risk_level = "moderate"
        consequences.append("Subclinical hormonal suppression may begin (LH pulsatility reduction)")
        consequences.append("Mild impairment in bone formation markers")
        recommendations.append(f"Increase daily intake by {int((45 - ea) * lean_mass_kg)} kcal to reach optimal EA.")
        recommendations.append("Monitor menstrual function (females) and libido/mood (males).")
    elif ea >= 20:
        status = "low"
        risk_level = "high"
        consequences.append("Clinical RED-S threshold: menstrual disruption (amenorrhea), bone density loss")
        consequences.append("Impaired immunity, increased injury risk, hormonal disruption (↓T, ↓E2, ↑cortisol)")
        consequences.append("Psychological effects: irritability, depression, disordered eating risk")
        recommendations.append(f"Urgently increase intake by {int((30 - ea) * lean_mass_kg)}–{int((45 - ea) * lean_mass_kg)} kcal/d.")
        recommendations.append("Reduce training volume or increase dietary intake — both are valid strategies.")
        recommendations.append("Screen for disordered eating behaviors. Refer to sports medicine physician.")
    else:
        status = "clinical"
        risk_level = "critical"
        consequences.append("Severe RED-S: bone stress fracture risk, cardiovascular dysfunction")
        consequences.append("Complete menstrual suppression, severe hormonal disruption")
        consequences.append("Immune suppression, impaired growth (adolescents), psychological distress")
        recommendations.append("MEDICAL REFERRAL REQUIRED. This EA level is clinically dangerous.")
        recommendations.append("Immediate dietary counseling. Consider training restriction until EA >30.")
        recommendations.append("Bone density scan (DEXA) recommended. Monitor cardiac function.")

    return EnergyAvailability(
        ea_kcal_per_kg_ffm=round(ea, 1),
        status=status,
        risk_level=risk_level,
        consequences=consequences,
        recommendations=recommendations,
    )


# ── Rate of Weight Change ──────────────────────────────────────────────────────

@dataclass
class WeightChangeGuidance:
    direction: str          # loss / gain / maintain
    rate_kg_per_week: float
    rate_pct_bw_per_week: float
    safe: bool
    lean_mass_preservation_notes: list[str]
    evidence: str


def safe_weight_change_rate(
    current_weight_kg: float,
    target_weight_kg: float,
    body_fat_pct: float,
    sex: str = "male",
    goal: str = "fat_loss",
) -> WeightChangeGuidance:
    """
    Calculate safe rate of weight change with lean mass preservation guidance.

    Evidence-based guidelines (Helms et al. 2014; Garthe et al. 2011):
    - Fat loss: 0.5–1.0% BW/week (slower = more lean mass preservation)
    - Muscle gain: 0.25–0.5% BW/week for trained; up to 1% for novices
    - Contest prep: 0.5–0.7% BW/week over 12–20 weeks

    Args:
        current_weight_kg: Current body weight.
        target_weight_kg: Goal weight.
        body_fat_pct: Current body fat %.
        sex: 'male' or 'female'.
        goal: 'fat_loss' / 'muscle_gain' / 'contest_prep'.

    Returns:
        WeightChangeGuidance with rate and lean mass preservation notes.
    """
    delta = target_weight_kg - current_weight_kg
    direction = "loss" if delta < 0 else "gain" if delta > 0 else "maintain"

    notes: list[str] = []

    if goal == "fat_loss" or (direction == "loss" and goal != "contest_prep"):
        # Slower for leaner individuals
        if body_fat_pct < 12 and sex == "male" or body_fat_pct < 20 and sex == "female":
            rate_pct = 0.5  # Already lean — slow rate
            notes.append("Already lean: use slower rate (0.5% BW/week) to minimize lean mass loss.")
        else:
            rate_pct = 0.7  # Moderate rate
            notes.append("Standard fat loss rate: 0.7% BW/week preserves lean mass well.")

        rate_kg = current_weight_kg * (rate_pct / 100)
        notes.append("Maintain protein at 2.0–2.4g/kg during deficit (Helms et al. 2014).")
        notes.append("Resistance train 3–4×/week to preserve lean mass during deficit.")
        evidence = "🟢 Strong — Helms et al. 2014 JISSN; Garthe et al. 2011 IJSNEM"

    elif goal == "muscle_gain" or direction == "gain":
        rate_pct = 0.35
        rate_kg = current_weight_kg * (rate_pct / 100)
        notes.append("Caloric surplus: 350–500 kcal/d above TDEE for lean gain.")
        notes.append("Protein: 1.6–2.2g/kg (sufficient for MPS even in surplus).")
        notes.append("Expect 50–70% of weight gain as lean mass in trained athletes.")
        evidence = "🟡 Moderate — Slater et al. 2019 Sports Med"

    elif goal == "contest_prep":
        rate_pct = 0.6
        rate_kg = current_weight_kg * (rate_pct / 100)
        notes.append("Contest prep: 0.5–0.7% BW/week over 12–20 weeks to single-digit BF%.")
        notes.append("Protein: 2.3–3.1g/kg lean mass during aggressive deficit.")
        notes.append("Refeed days (1–2×/week at maintenance) may improve hormonal status and adherence.")
        notes.append("Monitor mood, libido, sleep quality — indicators of excessive deficit.")
        evidence = "🟡 Moderate — Helms et al. 2014; Roberts et al. 2020 JISSN"
    else:
        rate_pct = 0.0
        rate_kg = 0.0
        notes.append("Maintain current weight. Focus on body recomposition if desired.")
        evidence = "🟢 Strong"

    weeks_needed = abs(delta) / max(rate_kg, 0.1) if rate_kg > 0 else 0

    safe = rate_pct <= 1.0  # >1%/week is aggressive

    if weeks_needed > 0:
        notes.append(f"Estimated timeline: {weeks_needed:.0f} weeks to reach {target_weight_kg:.1f}kg at {rate_kg:.2f}kg/week.")

    return WeightChangeGuidance(
        direction=direction,
        rate_kg_per_week=round(rate_kg, 2),
        rate_pct_bw_per_week=round(rate_pct, 1),
        safe=safe,
        lean_mass_preservation_notes=notes,
        evidence=evidence,
    )


def format_composition_report(
    result: BodyFatResult,
    ffmi: Optional[FFMIResult] = None,
    ea: Optional[EnergyAvailability] = None,
    weight_plan: Optional[WeightChangeGuidance] = None,
) -> str:
    """Comprehensive body composition report."""
    lines = [
        "═══════════════════════════════════════════════",
        "           BODY COMPOSITION REPORT            ",
        "═══════════════════════════════════════════════",
        "",
        f"  Body Fat     : {result.body_fat_pct:.1f}%",
        f"  Fat Mass     : {result.fat_mass_kg:.1f} kg",
        f"  Lean Mass    : {result.lean_mass_kg:.1f} kg",
        f"  Category     : {result.category.upper()}",
        f"  Sport Context: {result.sport_context}",
        f"  Evidence     : {result.evidence}",
    ]

    if ffmi:
        lines += [
            "",
            "── Fat-Free Mass Index ──",
            f"  FFMI           : {ffmi.ffmi:.1f} kg/m²",
            f"  Adjusted FFMI  : {ffmi.adjusted_ffmi:.1f} kg/m² (normalized to 1.80m)",
            f"  Interpretation : {ffmi.interpretation}",
            f"  {ffmi.natural_limit_note}",
            f"  Evidence       : {ffmi.evidence}",
        ]

    if ea:
        risk_color = {"none": "", "moderate": "⚠", "high": "⚠⚠", "critical": "🚨"}
        lines += [
            "",
            "── Energy Availability (RED-S Screening) ──",
            f"  EA          : {ea.ea_kcal_per_kg_ffm:.1f} kcal/kg FFM/day",
            f"  Status      : {ea.status.upper()} {risk_color.get(ea.risk_level, '')}",
            f"  Risk Level  : {ea.risk_level.upper()}",
        ]
        if ea.consequences:
            lines.append("  Consequences:")
            for c in ea.consequences:
                lines.append(f"    • {c}")
        if ea.recommendations:
            lines.append("  Recommendations:")
            for r in ea.recommendations:
                lines.append(f"    • {r}")
        lines.append(f"  Evidence    : {ea.evidence}")

    if weight_plan and weight_plan.direction != "maintain":
        lines += [
            "",
            "── Weight Change Plan ──",
            f"  Direction : {weight_plan.direction.title()}",
            f"  Rate      : {weight_plan.rate_kg_per_week:.2f} kg/week ({weight_plan.rate_pct_bw_per_week}% BW/week)",
            f"  Safe      : {'Yes' if weight_plan.safe else 'AGGRESSIVE — consider slowing rate'}",
        ]
        for note in weight_plan.lean_mass_preservation_notes:
            lines.append(f"    • {note}")
        lines.append(f"  Evidence  : {weight_plan.evidence}")

    return "\n".join(lines)
