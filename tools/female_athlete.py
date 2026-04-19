"""
Female athlete health tools for Kiwi.

Evidence-based tools for female-specific performance and health monitoring:
- Energy availability calculation (Loucks thresholds)
- Menstrual cycle phase–training matching
- RED-S risk screening (IOC consensus, Mountjoy 2018)
- Postpartum return-to-sport protocols
- Iron needs calculation for female athletes

References:
- Loucks AB et al. (2004) J Sports Sci — Energy availability thresholds
- Mountjoy M et al. (2014) Br J Sports Med — IOC consensus on RED-S
- Mountjoy M et al. (2018) Br J Sports Med — RED-S CAT update
- McNulty KL et al. (2020) Sports Med — Menstrual cycle and performance
- Melin AK et al. (2019) Br J Sports Med — Energy availability in athletes
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Thresholds ───────────────────────────────────────────────────────────────

LOUCKS_THRESHOLDS = {
    "optimal": 45.0,       # >45 kcal/kg FFM/day
    "reduced": 30.0,       # 30-45: reduced but functional
    "low": 25.0,           # <30: clinical concern (LEA)
    "severe": 25.0,        # <25: severe clinical concern
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class EnergyAvailability:
    total_energy_intake_kcal: float
    exercise_energy_expenditure_kcal: float
    fat_free_mass_kg: float
    ea_value: float
    classification: str
    risk_level: str
    recommendations: list[str]
    evidence: str


@dataclass
class CyclePhase:
    phase_name: str
    day_range: tuple[int, int]
    hormonal_profile: str
    training_recommendations: str
    nutrition_notes: str
    recovery_notes: str


@dataclass
class REDSScreening:
    risk_score: int
    risk_level: str
    risk_factors: list[str]
    clinical_signs: list[str]
    recommendations: list[str]
    referral_needed: bool
    evidence: str


@dataclass
class PostpartumProtocol:
    phase: str
    weeks_postpartum: int
    exercise_guidelines: list[str]
    contraindications: list[str]
    progression_criteria: list[str]
    key_references: list[str]


# ── Cycle Phase Database ─────────────────────────────────────────────────────

CYCLE_PHASES: list[CyclePhase] = [
    CyclePhase(
        phase_name="early_follicular",
        day_range=(1, 5),
        hormonal_profile="Estrogen and progesterone at nadir. Menstruation occurring.",
        training_recommendations="Lower intensity, focus on technique and skill work. "
            "Strength training effective but may feel harder. Consider reducing volume 10-15%.",
        nutrition_notes="Iron losses via menstruation — ensure adequate iron intake (18-30mg/d). "
            "Anti-inflammatory foods (omega-3, turmeric). Slightly higher calorie needs due to basal metabolic rate.",
        recovery_notes="Prioritize sleep. NSAIDs may be needed for severe cramping but can impair adaptation. "
            "Heat therapy for cramps. Magnesium supplementation may help.",
    ),
    CyclePhase(
        phase_name="late_follicular",
        day_range=(6, 13),
        hormonal_profile="Rising estrogen, low progesterone. FSH stimulating follicle development.",
        training_recommendations="Peak performance window. Rising estrogen supports strength, power, and "
            "endurance. Ideal time for high-intensity work, PRs, and competition. "
            "Estrogen enhances muscle repair and glycogen storage.",
        nutrition_notes="Good carbohydrate utilization — can support higher carb intake. "
            "Protein synthesis may be enhanced. Standard hydration protocols.",
        recovery_notes="Recovery capacity is good. Can tolerate higher training loads. "
            "Estrogen has mild anti-inflammatory effect.",
    ),
    CyclePhase(
        phase_name="ovulation",
        day_range=(14, 14),
        hormonal_profile="Estrogen peak, LH surge triggers ovulation. Brief testosterone rise.",
        training_recommendations="HIGHEST INJURY RISK — estrogen peak increases ACL laxity by 4-8x. "
            "Reduce plyometrics and cutting movements. Neuromuscular control exercises recommended. "
            "Strength may peak due to brief androgen rise.",
        nutrition_notes="Standard nutrition. Some women experience mild bloating or discomfort. "
            "Maintain hydration.",
        recovery_notes="Monitor for joint laxity symptoms. Extra warm-up for lower extremity. "
            "Proprioception and balance work recommended.",
    ),
    CyclePhase(
        phase_name="early_luteal",
        day_range=(15, 21),
        hormonal_profile="Rising progesterone, moderate estrogen. Corpus luteum active.",
        training_recommendations="Good training capacity. Progesterone increases core temperature by 0.3-0.5°C — "
            "adjust cooling strategies for heat training. Endurance capacity maintained. "
            "Steady-state and tempo work effective.",
        nutrition_notes="Progesterone increases fat oxidation — may benefit from slightly higher fat intake. "
            "Basal metabolic rate increases 5-10%. Increased protein catabolism — ensure adequate protein. "
            "Carb needs slightly higher to maintain glycogen.",
        recovery_notes="Core temperature elevation may impair sleep onset. Cool sleeping environment. "
            "Melatonin may be reduced — consider sleep hygiene practices.",
    ),
    CyclePhase(
        phase_name="late_luteal",
        day_range=(22, 28),
        hormonal_profile="Declining estrogen and progesterone. PMS symptoms may appear.",
        training_recommendations="RPE elevated at same intensity. Mood and motivation may decrease. "
            "Reduce high-intensity volume. Focus on technique and moderate steady-state. "
            "Flexibility and mobility work well tolerated.",
        nutrition_notes="Increased cravings (especially carbs and salt) — allow moderate indulgence. "
            "Serotonin may be reduced — tryptophan-rich foods (turkey, milk, nuts). "
            "BMR still elevated 5-10%. Magnesium for cramp prevention.",
        recovery_notes="Sleep quality may deteriorate. Increased fluid retention and bloating. "
            "Self-compassion important — RPE-based training preferred over pace/power targets.",
    ),
]


# ── RED-S Risk Factor Scoring ────────────────────────────────────────────────

REDS_RISK_FACTORS = {
    "low_bmi": {"condition": lambda r: r.get("bmi", 22) < 18.5, "points": 2, "label": "Low BMI (<18.5)"},
    "amenorrhea": {"condition": lambda r: r.get("menstrual_status") == "amenorrheic", "points": 3, "label": "Amenorrhea"},
    "oligomenorrhea": {"condition": lambda r: r.get("menstrual_status") == "irregular", "points": 1, "label": "Oligomenorrhea (irregular cycles)"},
    "bone_stress": {"condition": lambda r: r.get("bone_stress_injuries", 0) >= 1, "points": 2, "label": "Bone stress injury history"},
    "disordered_eating": {"condition": lambda r: r.get("disordered_eating", False), "points": 3, "label": "Disordered eating behaviors"},
    "weight_loss": {"condition": lambda r: r.get("weight_loss_pct", 0) > 5, "points": 2, "label": "Recent weight loss >5%"},
    "mood": {"condition": lambda r: r.get("mood_disturbance", False), "points": 1, "label": "Mood disturbance"},
    "gi_issues": {"condition": lambda r: r.get("gi_issues", False), "points": 1, "label": "GI dysfunction"},
    "illness": {"condition": lambda r: r.get("recurrent_illness", False), "points": 1, "label": "Recurrent illness"},
    "performance": {"condition": lambda r: r.get("declining_performance", False), "points": 1, "label": "Declining performance"},
    "low_ea": {"condition": lambda r: r.get("low_energy_availability", False), "points": 2, "label": "Low energy availability"},
}


# ── Core Functions ───────────────────────────────────────────────────────────

def calculate_energy_availability(
    intake_kcal: float,
    eee_kcal: float,
    ffm_kg: float,
) -> EnergyAvailability:
    """
    Calculate energy availability (EA) using the Loucks framework.

    EA = (Energy Intake - Exercise Energy Expenditure) / Fat-Free Mass

    Thresholds (Loucks et al. 2004):
      >45 kcal/kg FFM/day  — Optimal energy availability
      30–45               — Reduced but functional
      <30                 — Clinical concern (LEA)
      <25                 — Severe concern
    """
    if ffm_kg <= 0:
        raise ValueError("Fat-free mass must be positive")

    ea = (intake_kcal - eee_kcal) / ffm_kg

    if ea >= 45.0:
        classification = "optimal"
        risk_level = "low"
        recommendations = [
            "Energy availability is adequate — maintain current intake",
            "Continue monitoring during intensified training blocks",
        ]
    elif ea >= 30.0:
        classification = "reduced"
        risk_level = "moderate"
        recommendations = [
            "Energy availability is reduced — monitor for symptoms of LEA",
            "Increase energy intake by 300-500 kcal/day or reduce training load",
            "Monitor menstrual regularity, bone health, and mood",
            "Consider consultation with sports dietitian",
        ]
    elif ea >= 25.0:
        classification = "low"
        risk_level = "high"
        recommendations = [
            "LOW ENERGY AVAILABILITY — clinical concern",
            "Increase energy intake immediately by 500-1000 kcal/day",
            "Reduce training volume and intensity",
            "Refer to sports medicine physician and dietitian",
            "Screen for RED-S clinical signs (bone health, menstrual, hormonal)",
            "Monitor weekly: body weight, mood, sleep, menstrual status",
        ]
    else:
        classification = "severe"
        risk_level = "critical"
        recommendations = [
            "SEVERE LOW ENERGY AVAILABILITY — urgent intervention needed",
            "Immediate referral to multidisciplinary team (physician, dietitian, psychologist)",
            "Significant increase in energy intake required",
            "Consider rest from training until EA > 30 kcal/kg FFM/day",
            "Screen for eating disorder pathology",
            "Bone density assessment (DXA) recommended",
        ]

    return EnergyAvailability(
        total_energy_intake_kcal=intake_kcal,
        exercise_energy_expenditure_kcal=eee_kcal,
        fat_free_mass_kg=ffm_kg,
        ea_value=round(ea, 1),
        classification=classification,
        risk_level=risk_level,
        recommendations=recommendations,
        evidence="🟢 Strong — Loucks et al. (2004) J Sports Sci; Mountjoy et al. (2014, 2018) Br J Sports Med",
    )


def get_cycle_phase(day: int) -> CyclePhase:
    """Get the menstrual cycle phase for a given cycle day (1-28)."""
    if day < 1 or day > 28:
        raise ValueError("Cycle day must be between 1 and 28")

    for phase in CYCLE_PHASES:
        if phase.day_range[0] <= day <= phase.day_range[1]:
            return phase

    # Fallback (should not reach here with valid data)
    return CYCLE_PHASES[-1]


def match_training_to_phase(day: int, sport: str = "general") -> dict:
    """Match training recommendations to menstrual cycle phase."""
    phase = get_cycle_phase(day)

    # Intensity modifiers by phase
    modifiers = {
        "early_follicular": 0.85,
        "late_follicular": 1.1,
        "ovulation": 0.95,
        "early_luteal": 1.0,
        "late_luteal": 0.8,
    }

    # Key nutrients by phase
    nutrients = {
        "early_follicular": ["Iron (18-30mg)", "Omega-3 fatty acids", "Vitamin C (iron absorption)", "Magnesium"],
        "late_follicular": ["Carbohydrates (fuel for high-intensity)", "Protein (synthesis window)", "B vitamins"],
        "ovulation": ["Collagen/Vitamin C (connective tissue)", "Calcium", "Standard hydration"],
        "early_luteal": ["Protein (counter catabolism)", "Healthy fats", "Complex carbohydrates", "Sodium"],
        "late_luteal": ["Magnesium (cramp prevention)", "Tryptophan-rich foods", "Complex carbs", "Calcium"],
    }

    # Focus recommendations
    focus = {
        "early_follicular": "Technique, skill work, moderate strength training",
        "late_follicular": "High-intensity training, PRs, competitions, power work",
        "ovulation": "Neuromuscular control, reduce plyometrics/cutting, strength maintenance",
        "early_luteal": "Tempo work, steady-state endurance, moderate-high volume",
        "late_luteal": "Recovery, mobility, technique, RPE-based moderate training",
    }

    # Injury risk notes
    injury_notes = {
        "early_follicular": "Lower injury risk. Joint stability good.",
        "late_follicular": "Low injury risk. Good connective tissue integrity.",
        "ovulation": "HIGHEST ACL INJURY RISK. Estrogen peak → ligament laxity. Extra warm-up, "
                     "avoid aggressive cutting/landing.",
        "early_luteal": "Moderate injury risk. Core temperature elevated — monitor thermoregulation.",
        "late_luteal": "Moderate risk. Coordination may decrease. Fatigue-related injury risk.",
    }

    return {
        "phase": phase,
        "recommended_focus": focus.get(phase.phase_name, "General training"),
        "intensity_modifier": modifiers.get(phase.phase_name, 1.0),
        "key_nutrients": nutrients.get(phase.phase_name, []),
        "injury_risk_notes": injury_notes.get(phase.phase_name, "Standard precautions"),
    }


def screen_reds(responses: dict) -> REDSScreening:
    """
    Screen for Relative Energy Deficiency in Sport (RED-S).

    Based on IOC RED-S Clinical Assessment Tool (Mountjoy et al. 2018).
    """
    score = 0
    factors = []
    clinical_signs = []

    for key, factor in REDS_RISK_FACTORS.items():
        try:
            if factor["condition"](responses):
                score += factor["points"]
                factors.append(factor["label"])
        except (KeyError, TypeError):
            continue

    # Red flags that auto-escalate to high risk
    red_flags = False
    if responses.get("menstrual_status") == "amenorrheic":
        clinical_signs.append("Amenorrhea — functional hypothalamic amenorrhea likely")
        red_flags = True
    if responses.get("bmi", 22) < 17.5:
        clinical_signs.append("BMI < 17.5 — underweight, possible eating disorder")
        red_flags = True
    if responses.get("bone_stress_injuries", 0) >= 2:
        clinical_signs.append("Multiple bone stress injuries — impaired bone health")
        red_flags = True
    if responses.get("disordered_eating", False):
        clinical_signs.append("Disordered eating behaviors identified")

    # Risk level
    if red_flags or score >= 6:
        risk_level = "high"
    elif score >= 3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # Recommendations
    recommendations = []
    if risk_level == "high":
        recommendations = [
            "URGENT: Refer to sports medicine physician",
            "Multidisciplinary team assessment (physician, dietitian, psychologist)",
            "Energy intake assessment and intervention",
            "Bone density screening (DXA) recommended",
            "Menstrual function evaluation (hormone panel)",
            "Consider sport restriction until medical clearance",
        ]
    elif risk_level == "moderate":
        recommendations = [
            "Sports dietitian consultation recommended",
            "Energy availability assessment",
            "Monitor menstrual regularity monthly",
            "Track mood, sleep, and performance trends",
            "Reassess in 4-6 weeks",
        ]
    else:
        recommendations = [
            "Continue current management",
            "Annual screening recommended",
            "Educate on RED-S warning signs",
        ]

    return REDSScreening(
        risk_score=score,
        risk_level=risk_level,
        risk_factors=factors,
        clinical_signs=clinical_signs,
        recommendations=recommendations,
        referral_needed=risk_level == "high",
        evidence="🟢 Strong — Mountjoy et al. (2018) Br J Sports Med — IOC consensus on RED-S",
    )


def postpartum_return_protocol(
    weeks: int,
    delivery_type: str = "vaginal",
    complications: list[str] | None = None,
) -> PostpartumProtocol:
    """
    Generate postpartum return-to-sport protocol based on timeline and delivery type.

    Phases:
      0-2 weeks: Immediate recovery
      2-6 weeks: Early return
      6-12 weeks: Progressive loading
      12-24 weeks: Return to sport
      24+ weeks: Full return
    """
    complications = complications or []
    csection_delay = 2 if delivery_type.lower() in ("c-section", "cesarean", "caesarean") else 0
    effective_weeks = max(0, weeks - csection_delay)

    if effective_weeks < 2:
        phase = "immediate_recovery"
        guidelines = [
            "Walking as tolerated (start with 10-15 min, increase gradually)",
            "Pelvic floor awareness exercises (gentle Kegels if pain-free)",
            "Diaphragmatic breathing exercises",
            "Gentle upper body stretching",
            "NO impact, heavy lifting, or abdominal exercises",
        ]
        contraindications = [
            "Running or impact activities",
            "Heavy resistance training",
            "Abdominal crunches or planks",
            "High-intensity exercise",
        ]
        criteria = [
            "Medical clearance from OB/midwife",
            "Bleeding resolved or minimal",
            "Pain-free walking for 30 minutes",
        ]
    elif effective_weeks < 6:
        phase = "early_return"
        guidelines = [
            "Walking 20-30 min daily",
            "Pelvic floor rehabilitation program",
            "Light resistance training (bodyweight or light weights)",
            "Gentle core activation (modified dead bugs, bird dogs)",
            "Swimming allowed after lochia stops and wounds healed",
        ]
        contraindications = [
            "Running or jumping",
            "Heavy barbell training",
            "Traditional crunches or sit-ups",
            "Breath-holding during exercise (Valsalva)",
        ]
        criteria = [
            "6-week postpartum medical clearance",
            "No pain during daily activities",
            "Good pelvic floor activation (can stop urine stream)",
            "No diastasis recti >2 finger widths",
        ]
    elif effective_weeks < 12:
        phase = "progressive_loading"
        guidelines = [
            "Progressive resistance training (increase loads gradually)",
            "Begin impact testing (single leg hop, double-leg jump)",
            "Return to sport-specific drills at reduced intensity",
            "Core strengthening progression (planks, pallof press)",
            "Cardiovascular conditioning (bike, elliptical, then running)",
        ]
        contraindications = [
            "Heavy maximal lifts until pelvic floor assessed",
            "Competitive sport if any pelvic floor symptoms",
        ]
        criteria = [
            "Pelvic floor physio assessment passed",
            "No leakage during exercise",
            "Return-to-run protocol completed (Goom et al. 2019)",
            "Core strength adequate for sport demands",
        ]
    elif effective_weeks < 24:
        phase = "return_to_sport"
        guidelines = [
            "Gradual return to full training",
            "Sport-specific training at 60-80% intensity, increasing weekly",
            "Full resistance training program",
            "Competition preparation (match fitness)",
            "Monitor recovery — sleep disruption common with infant",
        ]
        contraindications = [
            "Full competition if any pelvic floor symptoms remain",
        ]
        criteria = [
            "Full training load tolerated for 4+ weeks",
            "No pain or pelvic floor symptoms",
            "Sport-specific fitness tests passed",
            "Psychological readiness for competition",
        ]
    else:
        phase = "full_return"
        guidelines = [
            "Full return to competitive sport",
            "Normal training programming",
            "Annual pelvic floor screening recommended",
            "Monitor energy availability (increased needs if breastfeeding: +300-500 kcal/d)",
        ]
        contraindications = []
        criteria = [
            "All sport-specific criteria met",
            "Medical clearance for full competition",
        ]

    # Modification for complications
    if "diastasis_recti" in complications:
        guidelines.insert(0, "DIASTASIS RECTI: Modified core program — avoid traditional crunches, "
                            "focus on transversus abdominis activation. Physio assessment required.")
        contraindications.append("Traditional abdominal exercises until diastasis resolved (<2 finger widths)")

    if "pelvic_floor_dysfunction" in complications:
        guidelines.insert(0, "PELVIC FLOOR DYSFUNCTION: Pelvic floor physiotherapy required before impact/heavy loading.")
        contraindications.append("Impact activities until pelvic floor physio cleared")

    references = [
        "Bø K et al. (2017) Br J Sports Med — Exercise and pregnancy position statement",
        "Goom T et al. (2019) Br J Sports Med — Returning to running postnatal guidelines",
        "Mottola MF et al. (2018) Br J Sports Med — 2019 Canadian guideline for physical activity in pregnancy",
    ]
    if delivery_type.lower() in ("c-section", "cesarean", "caesarean"):
        references.append("Davenport MH et al. (2019) — Exercise after cesarean delivery")

    return PostpartumProtocol(
        phase=phase,
        weeks_postpartum=weeks,
        exercise_guidelines=guidelines,
        contraindications=contraindications,
        progression_criteria=criteria,
        key_references=references,
    )


def calculate_iron_needs(
    menstrual_status: str,
    training_volume_hours: float,
    dietary_pattern: str = "omnivore",
) -> dict:
    """
    Calculate iron needs for female athletes.

    Base RDA: 18mg/day for menstruating females.
    Athletes: 1.3-1.7x multiplier (foot-strike hemolysis, sweat, GI losses).
    Vegetarian/vegan: 1.8x multiplier (lower bioavailability).
    """
    base_rda = 18.0

    # Training volume multiplier
    if training_volume_hours >= 15:
        training_mult = 1.7
    elif training_volume_hours >= 10:
        training_mult = 1.5
    elif training_volume_hours >= 5:
        training_mult = 1.3
    else:
        training_mult = 1.0

    # Dietary pattern multiplier
    diet_mult = 1.8 if dietary_pattern.lower() in ("vegetarian", "vegan", "plant-based") else 1.0

    # Menstrual status adjustment
    menstrual_mult = 1.0
    if menstrual_status == "amenorrheic":
        menstrual_mult = 0.7  # Lower needs without menstruation
        base_rda = 8.0  # Male RDA baseline
    elif menstrual_status == "heavy":
        menstrual_mult = 1.3

    recommended = round(base_rda * training_mult * diet_mult * menstrual_mult, 1)

    rationale_parts = [f"Base RDA: {base_rda}mg"]
    if training_mult > 1.0:
        rationale_parts.append(f"Training volume multiplier: {training_mult}x ({training_volume_hours}h/week)")
    if diet_mult > 1.0:
        rationale_parts.append(f"Plant-based diet multiplier: {diet_mult}x (lower bioavailability)")
    if menstrual_mult != 1.0:
        rationale_parts.append(f"Menstrual adjustment: {menstrual_mult}x ({menstrual_status})")

    monitoring = "Check ferritin every 3-6 months. Target: 30-50 ng/mL for athletes. "
    if recommended > 30:
        monitoring += "HIGH dose recommended — clinical supervision advised. "
    monitoring += "Take with vitamin C, separate from calcium/coffee/tea by 2 hours."

    return {
        "rda_mg": base_rda,
        "recommended_mg": recommended,
        "rationale": ". ".join(rationale_parts),
        "monitoring": monitoring,
    }


# ── Formatting Functions ─────────────────────────────────────────────────────

def format_ea_report(ea: EnergyAvailability) -> str:
    """Human-readable energy availability report."""
    lines = [
        "═══ Energy Availability Assessment ═══",
        "",
        f"  Energy Intake:    {ea.total_energy_intake_kcal:.0f} kcal",
        f"  Exercise Expend:  {ea.exercise_energy_expenditure_kcal:.0f} kcal",
        f"  Fat-Free Mass:    {ea.fat_free_mass_kg:.1f} kg",
        "  ────────────────────────",
        f"  EA Value:         {ea.ea_value:.1f} kcal/kg FFM/day",
        f"  Classification:   {ea.classification.upper()}",
        f"  Risk Level:       {ea.risk_level.upper()}",
        "",
        "── Thresholds ──",
        "  >45 Optimal | 30-45 Reduced | <30 LEA | <25 Severe",
        "",
        "── Recommendations ──",
    ]
    for rec in ea.recommendations:
        lines.append(f"  • {rec}")
    lines += [
        "",
        "── Evidence ──",
        f"  {ea.evidence}",
    ]
    return "\n".join(lines)


def format_reds_report(screening: REDSScreening) -> str:
    """Human-readable RED-S screening report."""
    lines = [
        "═══ RED-S Risk Screening ═══",
        "",
        f"  Risk Score:   {screening.risk_score}",
        f"  Risk Level:   {screening.risk_level.upper()}",
        f"  Referral:     {'YES — URGENT' if screening.referral_needed else 'Not required'}",
    ]

    if screening.risk_factors:
        lines += ["", "── Risk Factors Identified ──"]
        for f in screening.risk_factors:
            lines.append(f"  ⚠ {f}")

    if screening.clinical_signs:
        lines += ["", "── Clinical Signs ──"]
        for s in screening.clinical_signs:
            lines.append(f"  🔴 {s}")

    lines += ["", "── Recommendations ──"]
    for r in screening.recommendations:
        lines.append(f"  • {r}")

    lines += ["", "── Evidence ──", f"  {screening.evidence}"]
    return "\n".join(lines)


def format_cycle_training(phase: CyclePhase) -> str:
    """Human-readable cycle phase training advice."""
    lines = [
        f"═══ Menstrual Cycle Phase: {phase.phase_name.replace('_', ' ').title()} ═══",
        f"  Days: {phase.day_range[0]}–{phase.day_range[1]}",
        "",
        "── Hormonal Profile ──",
        f"  {phase.hormonal_profile}",
        "",
        "── Training ──",
        f"  {phase.training_recommendations}",
        "",
        "── Nutrition ──",
        f"  {phase.nutrition_notes}",
        "",
        "── Recovery ──",
        f"  {phase.recovery_notes}",
    ]
    return "\n".join(lines)
