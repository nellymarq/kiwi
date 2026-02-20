"""
Hydration and electrolyte management for Kiwi.

Evidence-based hydration science:
- Sweat rate calculation from pre/post-exercise body weight
- Sport-specific sweat loss normative ranges
- Electrolyte loss estimation (sodium, potassium, chloride, magnesium)
- Rehydration protocol design (1.5× rule, ORS composition)
- Urine color hydration status classification
- Heat acclimatization adjustments
- Hyponatremia risk assessment

References:
- Sawka et al. (2007) Med Sci Sports Exerc — ACSM Position Stand: Exercise and Fluid Replacement
- Baker et al. (2016) Sports Med — Sweat electrolyte variability
- Shirreffs & Sawka (2011) JSAMS — Fluid and electrolyte needs
- Maughan & Shirreffs (2010) Scand J Med Sci Sports — Dehydration and performance
- Casa et al. (2015) J Athl Training — Heat illness prevention
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# ── Sweat Loss Estimation ──────────────────────────────────────────────────────

# Sport-specific mean sweat rates (L/h) at moderate intensity in temperate conditions
# Source: Baker & Jeukendrup 2014, Sawka et al. 2007
SPORT_SWEAT_RATES: dict[str, dict] = {
    "running": {
        "min_L_hr": 0.5, "typical_L_hr": 1.2, "max_L_hr": 2.5,
        "notes": "Increases significantly with pace and heat; ~0.8L/h per 10°C ambient temperature rise",
    },
    "cycling": {
        "min_L_hr": 0.4, "typical_L_hr": 1.0, "max_L_hr": 2.0,
        "notes": "Lower than running due to wind cooling; stationary cycling 30–50% higher",
    },
    "swimming": {
        "min_L_hr": 0.2, "typical_L_hr": 0.5, "max_L_hr": 1.0,
        "notes": "Water cooling and suppressed thirst; often underestimated by athletes",
    },
    "basketball": {
        "min_L_hr": 0.8, "typical_L_hr": 1.4, "max_L_hr": 2.5,
        "notes": "High-intensity interval nature; significant game-to-game variability",
    },
    "football_soccer": {
        "min_L_hr": 0.8, "typical_L_hr": 1.5, "max_L_hr": 3.0,
        "notes": "Elite players can lose 2–3L per 45-min half in hot conditions",
    },
    "strength_training": {
        "min_L_hr": 0.2, "typical_L_hr": 0.7, "max_L_hr": 1.5,
        "notes": "High variability by exercise selection; compound movements produce more sweat",
    },
    "tennis": {
        "min_L_hr": 0.5, "typical_L_hr": 1.2, "max_L_hr": 2.5,
        "notes": "Extended match duration amplifies total losses; humidity key factor",
    },
    "rowing": {
        "min_L_hr": 1.0, "typical_L_hr": 1.5, "max_L_hr": 2.5,
        "notes": "Full-body aerobic; indoor erg produces higher rates than on-water",
    },
    "combat_sports": {
        "min_L_hr": 0.8, "typical_L_hr": 1.5, "max_L_hr": 3.0,
        "notes": "Sauna/cutting practices outside normal physiological sweat; risky",
    },
    "general": {
        "min_L_hr": 0.3, "typical_L_hr": 1.0, "max_L_hr": 2.5,
        "notes": "Use for cross-training or when sport not listed",
    },
}

# Electrolyte concentration in sweat (mmol/L)
# Source: Baker et al. 2016 Sports Med systematic review
SWEAT_ELECTROLYTE_CONCENTRATION: dict[str, dict] = {
    "sodium": {
        "mean_mmol_L": 50, "range_mmol_L": (10, 90), "unit": "mmol/L",
        "molecular_weight": 23.0,  # g/mol
        "mg_per_mmol": 23.0,
    },
    "potassium": {
        "mean_mmol_L": 5, "range_mmol_L": (3, 8), "unit": "mmol/L",
        "molecular_weight": 39.1,
        "mg_per_mmol": 39.1,
    },
    "chloride": {
        "mean_mmol_L": 45, "range_mmol_L": (5, 80), "unit": "mmol/L",
        "molecular_weight": 35.5,
        "mg_per_mmol": 35.5,
    },
    "magnesium": {
        "mean_mmol_L": 0.3, "range_mmol_L": (0.1, 0.5), "unit": "mmol/L",
        "molecular_weight": 24.3,
        "mg_per_mmol": 24.3,
    },
}


@dataclass
class SweatLoss:
    liters: float
    duration_hours: float
    sweat_rate_L_hr: float
    sodium_mg: float
    potassium_mg: float
    chloride_mg: float
    magnesium_mg: float
    sport: str = "general"
    heat_adjusted: bool = False

    def summary(self) -> str:
        return (
            f"Total Sweat Loss: {self.liters:.2f} L over {self.duration_hours:.1f}h "
            f"({self.sweat_rate_L_hr:.2f} L/h)\n"
            f"  Sodium:    {self.sodium_mg:.0f} mg ({self.sodium_mg/23:.0f} mmol)\n"
            f"  Potassium: {self.potassium_mg:.0f} mg ({self.potassium_mg/39.1:.0f} mmol)\n"
            f"  Chloride:  {self.chloride_mg:.0f} mg\n"
            f"  Magnesium: {self.magnesium_mg:.0f} mg"
        )


def calculate_sweat_loss(
    pre_weight_kg: float,
    post_weight_kg: float,
    fluid_consumed_L: float = 0.0,
    duration_hours: float = 1.0,
    sport: str = "general",
    ambient_temp_c: float = 20.0,
    acclimatized: bool = False,
) -> SweatLoss:
    """
    Calculate sweat loss and electrolyte losses from pre/post-exercise body weight.

    Sweat Volume = (pre_weight - post_weight) + fluid_consumed
    (Urine losses assumed negligible during exercise; correction ±0.1 kg for clothing/food)

    Args:
        pre_weight_kg: Body weight before exercise (kg).
        post_weight_kg: Body weight after exercise (kg).
        fluid_consumed_L: Volume of fluids consumed during exercise (L).
        duration_hours: Session duration (hours).
        sport: Key from SPORT_SWEAT_RATES.
        ambient_temp_c: Environmental temperature (°C). Default 20°C.
        acclimatized: Heat-acclimatized athletes have higher sweat rate but lower [Na+].

    Returns:
        SweatLoss with volume, rate, and electrolyte breakdown.
    """
    weight_loss_kg = pre_weight_kg - post_weight_kg
    sweat_liters = max(0.0, weight_loss_kg + fluid_consumed_L)

    # Heat adjustment: ~10% more sweating per 5°C above 20°C
    heat_factor = 1.0
    heat_adjusted = False
    if ambient_temp_c > 20:
        heat_factor = 1.0 + ((ambient_temp_c - 20) / 5) * 0.10
        heat_factor = min(heat_factor, 1.5)  # cap at 50% increase
        heat_adjusted = True

    # Acclimatization: higher sweat rate, lower sodium concentration
    na_concentration = SWEAT_ELECTROLYTE_CONCENTRATION["sodium"]["mean_mmol_L"]
    if acclimatized:
        # Acclimatized athletes sweat more but conserve sodium (lower [Na+])
        na_concentration = max(25, na_concentration - 15)
        heat_factor *= 1.10

    sweat_liters_corrected = sweat_liters * heat_factor
    sweat_rate = sweat_liters_corrected / max(duration_hours, 0.1)

    # Electrolyte losses
    sodium_mmol = sweat_liters_corrected * na_concentration
    potassium_mmol = sweat_liters_corrected * SWEAT_ELECTROLYTE_CONCENTRATION["potassium"]["mean_mmol_L"]
    chloride_mmol = sweat_liters_corrected * SWEAT_ELECTROLYTE_CONCENTRATION["chloride"]["mean_mmol_L"]
    magnesium_mmol = sweat_liters_corrected * SWEAT_ELECTROLYTE_CONCENTRATION["magnesium"]["mean_mmol_L"]

    return SweatLoss(
        liters=round(sweat_liters_corrected, 2),
        duration_hours=round(duration_hours, 2),
        sweat_rate_L_hr=round(sweat_rate, 2),
        sodium_mg=round(sodium_mmol * 23.0, 0),
        potassium_mg=round(potassium_mmol * 39.1, 0),
        chloride_mg=round(chloride_mmol * 35.5, 0),
        magnesium_mg=round(magnesium_mmol * 24.3, 1),
        sport=sport,
        heat_adjusted=heat_adjusted,
    )


def estimate_sweat_loss_by_sport(
    sport: str,
    duration_hours: float,
    body_weight_kg: float = 75.0,
    intensity: str = "moderate",
    ambient_temp_c: float = 20.0,
) -> SweatLoss:
    """
    Estimate sweat loss by sport when pre/post weights are unavailable.

    Args:
        sport: Key from SPORT_SWEAT_RATES.
        duration_hours: Session duration.
        body_weight_kg: Body weight for scaling (L/h doesn't scale with weight directly,
                        but larger athletes sweat ~10–15% more per kg LBM increase).
        intensity: 'easy' / 'moderate' / 'hard'.
        ambient_temp_c: Environmental temperature.

    Returns:
        SweatLoss estimate.
    """
    sport_data = SPORT_SWEAT_RATES.get(sport.lower().replace(" ", "_"), SPORT_SWEAT_RATES["general"])

    # Intensity scaling
    intensity_factor = {"easy": 0.7, "moderate": 1.0, "hard": 1.3}.get(intensity.lower(), 1.0)
    base_rate = sport_data["typical_L_hr"] * intensity_factor

    # Body weight scaling (reference person ~75kg; ±5% per 10kg difference)
    weight_factor = 1.0 + ((body_weight_kg - 75) / 75) * 0.10
    weight_factor = max(0.7, min(1.3, weight_factor))

    # Heat adjustment
    heat_factor = 1.0
    heat_adjusted = False
    if ambient_temp_c > 20:
        heat_factor = 1.0 + ((ambient_temp_c - 20) / 5) * 0.10
        heat_factor = min(heat_factor, 1.5)
        heat_adjusted = True

    sweat_rate = base_rate * weight_factor * heat_factor
    sweat_liters = sweat_rate * duration_hours

    na = SWEAT_ELECTROLYTE_CONCENTRATION["sodium"]["mean_mmol_L"]
    k  = SWEAT_ELECTROLYTE_CONCENTRATION["potassium"]["mean_mmol_L"]
    cl = SWEAT_ELECTROLYTE_CONCENTRATION["chloride"]["mean_mmol_L"]
    mg = SWEAT_ELECTROLYTE_CONCENTRATION["magnesium"]["mean_mmol_L"]

    return SweatLoss(
        liters=round(sweat_liters, 2),
        duration_hours=duration_hours,
        sweat_rate_L_hr=round(sweat_rate, 2),
        sodium_mg=round(sweat_liters * na * 23.0, 0),
        potassium_mg=round(sweat_liters * k * 39.1, 0),
        chloride_mg=round(sweat_liters * cl * 35.5, 0),
        magnesium_mg=round(sweat_liters * mg * 24.3, 1),
        sport=sport,
        heat_adjusted=heat_adjusted,
    )


# ── Rehydration Protocol ───────────────────────────────────────────────────────

@dataclass
class RehydrationProtocol:
    total_fluid_target_L: float      # 1.25–1.5× sweat loss
    first_hour_target_L: float       # aggressive first-hour target
    sodium_target_mg: float          # replace ~80% of losses
    potassium_target_mg: float
    ors_concentration_mg_per_L: dict  # ORS recipe
    timing_hours: float              # recommended completion window
    urgency: str                     # immediate / moderate / gradual
    warnings: list[str]
    evidence: str = "🟢 Strong"


def design_rehydration_protocol(
    sweat_loss: SweatLoss,
    time_to_next_activity_hours: float = 24.0,
    weight_deficit_pct: Optional[float] = None,
) -> RehydrationProtocol:
    """
    Design an evidence-based rehydration protocol.

    Target fluid intake: 1.25–1.5× sweat loss to account for urine output.
    Sodium is essential to stimulate thirst and retain ingested fluid.
    Complete rehydration within 4–6h if next performance within 24h.

    Args:
        sweat_loss: SweatLoss from calculate_sweat_loss().
        time_to_next_activity_hours: Hours until next training or competition.
        weight_deficit_pct: Optional body weight deficit %. If None, derived from sweat loss.

    Returns:
        RehydrationProtocol with targets, ORS recipe, and timing.
    """
    # Fluid target: 1.5× for general, 1.25× if more than 24h until next activity
    if time_to_next_activity_hours > 24:
        rehydration_factor = 1.25
    else:
        rehydration_factor = 1.5

    total_fluid_L = sweat_loss.liters * rehydration_factor
    first_hour_L = min(total_fluid_L * 0.4, 0.8)  # 40% in first hour, cap at 800ml (GI tolerance)

    # Sodium replacement: replace 80% of losses
    na_target_mg = sweat_loss.sodium_mg * 0.80
    k_target_mg = sweat_loss.potassium_mg * 0.80

    # ORS concentration (mg/L of rehydration fluid)
    na_concentration_mg_L = na_target_mg / total_fluid_L if total_fluid_L > 0 else 500

    ors = {
        "sodium_mg_per_L": round(max(300, min(1500, na_concentration_mg_L)), 0),
        "potassium_mg_per_L": round(k_target_mg / total_fluid_L if total_fluid_L > 0 else 100, 0),
        "carbohydrate_g_per_L": 20,  # ~4-8% CHO aids absorption
        "notes": "Sports drink or electrolyte mix; ORS solution, or sodium-rich food + water",
    }

    # Urgency based on timing and loss magnitude
    if time_to_next_activity_hours <= 4:
        urgency = "immediate"
        timing_hours = min(3.0, time_to_next_activity_hours * 0.8)
    elif time_to_next_activity_hours <= 12:
        urgency = "moderate"
        timing_hours = 4.0
    else:
        urgency = "gradual"
        timing_hours = 6.0

    # Warnings
    warnings: list[str] = []
    sweat_pct_body_weight = (sweat_loss.liters / 75) * 100  # crude proxy
    if weight_deficit_pct is not None and weight_deficit_pct > 2:
        warnings.append(
            f"Body weight deficit {weight_deficit_pct:.1f}% — dehydration is impairing performance "
            f"(>2% threshold). Rehydrate before next session."
        )
    if sweat_loss.sodium_mg > 3000:
        warnings.append(
            f"High sodium loss ({sweat_loss.sodium_mg:.0f}mg) — salty sweat phenotype likely. "
            "Use high-sodium electrolyte products or add salt to meals."
        )
    if na_concentration_mg_L < 300:
        warnings.append(
            "Low sodium in rehydration fluid risks dilutional hyponatremia — "
            "especially with large fluid volumes. Add electrolytes."
        )
    if total_fluid_L > 3.0:
        warnings.append(
            f"Large fluid deficit ({total_fluid_L:.1f}L target) — spread rehydration over "
            f"multiple hours. Excess rapid intake risks hyponatremia."
        )

    return RehydrationProtocol(
        total_fluid_target_L=round(total_fluid_L, 2),
        first_hour_target_L=round(first_hour_L, 2),
        sodium_target_mg=round(na_target_mg, 0),
        potassium_target_mg=round(k_target_mg, 0),
        ors_concentration_mg_per_L=ors,
        timing_hours=timing_hours,
        urgency=urgency,
        warnings=warnings,
    )


def format_rehydration_report(protocol: RehydrationProtocol, sweat_loss: SweatLoss) -> str:
    """Human-readable rehydration protocol report."""
    lines = [
        "═══════════════════════════════════════════════════",
        "            REHYDRATION PROTOCOL                  ",
        "═══════════════════════════════════════════════════",
        "",
        sweat_loss.summary(),
        "",
        f"Urgency : {protocol.urgency.upper()}",
        f"Target  : {protocol.total_fluid_target_L:.2f} L total over {protocol.timing_hours:.0f}h",
        f"Hour 1  : {protocol.first_hour_target_L:.2f} L (aggressive early rehydration)",
        "",
        "Electrolyte Targets:",
        f"  Sodium    : {protocol.sodium_target_mg:.0f} mg",
        f"  Potassium : {protocol.potassium_target_mg:.0f} mg",
        "",
        "ORS Concentration (per L of fluid):",
        f"  Sodium    : {protocol.ors_concentration_mg_per_L['sodium_mg_per_L']:.0f} mg",
        f"  Potassium : {protocol.ors_concentration_mg_per_L['potassium_mg_per_L']:.0f} mg",
        f"  CHO       : {protocol.ors_concentration_mg_per_L['carbohydrate_g_per_L']}g",
        f"  Note      : {protocol.ors_concentration_mg_per_L['notes']}",
        "",
        f"Evidence: {protocol.evidence}",
    ]

    if protocol.warnings:
        lines.append("\n⚠️  Warnings:")
        for w in protocol.warnings:
            lines.append(f"  • {w}")

    return "\n".join(lines)


# ── Urine Color / Hydration Status ────────────────────────────────────────────

# Based on Armstrong et al. 1994 IJSNEM — urine color chart
URINE_COLOR_CHART: list[tuple[int, str, str, str]] = [
    # (color_number, color_name, status, action)
    (1, "very pale yellow / near clear", "Well hydrated",              "No action needed — maintain intake."),
    (2, "pale yellow",                   "Well hydrated",              "Continue current fluid intake."),
    (3, "light yellow",                  "Adequately hydrated",        "Continue current intake."),
    (4, "yellow",                        "Adequately hydrated",        "Increase fluid intake slightly."),
    (5, "dark yellow",                   "Mildly dehydrated (~1–2%)",  "Drink 400–600ml now."),
    (6, "amber / honey",                 "Dehydrated (~2–3%)",         "Drink 600–900ml with electrolytes immediately."),
    (7, "burnt orange",                  "Significantly dehydrated",   "Urgent rehydration needed — add electrolytes."),
    (8, "brown / dark tea",              "Severely dehydrated / possible rhabdomyolysis risk",
        "Seek medical attention if with muscle pain/weakness; urgent rehydration."),
]


def urine_color_status(color_number: int) -> dict:
    """
    Return hydration status from urine color number (1–8).

    Args:
        color_number: 1 (very pale) to 8 (brown). Match against Armstrong chart.

    Returns:
        Dict with status, action, and dehydration estimate.
    """
    color_number = max(1, min(8, color_number))
    num, color_name, status, action = URINE_COLOR_CHART[color_number - 1]
    return {
        "color_number": num,
        "color_name": color_name,
        "status": status,
        "action": action,
        "dehydrated": color_number >= 5,
        "urgent": color_number >= 7,
        "evidence": "🟢 Strong — Armstrong et al. 1994 IJSNEM; validated USG proxy",
    }


# ── Hyponatremia Risk Assessment ───────────────────────────────────────────────

def hyponatremia_risk(
    event_duration_hours: float,
    fluid_intake_L_hr: float,
    event_type: str = "endurance",
    body_weight_kg: float = 70.0,
) -> dict:
    """
    Assess exercise-associated hyponatremia (EAH) risk.

    Risk factors (Hew-Butler et al. 2015 Clin J Sport Med):
    - Overconsumption of hypotonic fluid (primary driver)
    - Long event duration (>4h)
    - Slow pace (more time to drink relative to sweat rate)
    - Female sex, low body weight

    Args:
        event_duration_hours: Total event/race duration.
        fluid_intake_L_hr: Planned fluid intake rate.
        event_type: 'endurance' / 'ultra' / 'team_sport'.
        body_weight_kg: Athlete body weight.

    Returns:
        Risk level, primary drivers, and prevention strategies.
    """
    risk_score = 0
    drivers = []

    # Intake vs expected sweat rate
    expected_sweat_L_hr = SPORT_SWEAT_RATES.get(event_type, SPORT_SWEAT_RATES["general"])["typical_L_hr"]
    if fluid_intake_L_hr > expected_sweat_L_hr:
        overconsumption_pct = ((fluid_intake_L_hr - expected_sweat_L_hr) / expected_sweat_L_hr) * 100
        risk_score += 2
        drivers.append(
            f"Planned intake ({fluid_intake_L_hr:.1f} L/h) exceeds expected sweat rate "
            f"({expected_sweat_L_hr:.1f} L/h) by {overconsumption_pct:.0f}%."
        )
    elif fluid_intake_L_hr > expected_sweat_L_hr * 0.8:
        risk_score += 1
        drivers.append(f"Intake near sweat rate threshold — monitor closely.")

    if event_duration_hours >= 6:
        risk_score += 2
        drivers.append(f"Long event duration ({event_duration_hours:.0f}h) — cumulative overdrinking risk.")
    elif event_duration_hours >= 4:
        risk_score += 1
        drivers.append(f"Event duration {event_duration_hours:.0f}h — moderate EAH risk.")

    if body_weight_kg < 60:
        risk_score += 1
        drivers.append(f"Low body weight ({body_weight_kg:.0f}kg) — lower dilution threshold.")

    # Risk categorization
    if risk_score >= 4:
        risk_level = "HIGH"
        recommendation = (
            "Do NOT drink to a schedule. Drink to thirst only. "
            "Use sodium-containing sports drinks (≥500mg Na/L). "
            "Target no more than 0.5–0.6 L/h if thirst is low."
        )
    elif risk_score >= 2:
        risk_level = "MODERATE"
        recommendation = (
            "Drink to thirst. Include sodium-containing drinks. "
            "Avoid plain water as sole hydration source for events >3h."
        )
    else:
        risk_level = "LOW"
        recommendation = (
            "Standard hydration strategy: drink to thirst with electrolytes. "
            "Monitor urine color target (3–4 on Armstrong scale)."
        )

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "drivers": drivers,
        "recommendation": recommendation,
        "key_warning": (
            "EAH is caused by drinking too much fluid, not too little. "
            "Symptoms: nausea, headache, swelling, confusion. "
            "Severe EAH can be fatal. Do not treat with more fluid — seek medical attention."
        ),
        "evidence": "🟢 Strong — Hew-Butler et al. 2015 Clin J Sport Med consensus statement",
    }


# ── Pre-Exercise Hydration Protocol ───────────────────────────────────────────

def pre_exercise_hydration_plan(
    body_weight_kg: float,
    event_duration_hours: float,
    ambient_temp_c: float = 20.0,
    sport: str = "general",
    start_hours_from_now: float = 3.0,
) -> dict:
    """
    Generate a pre-exercise hydration plan.

    ACSM/GSSI guidelines (Sawka et al. 2007):
    - Start exercise euhydrated (urine color 1–3)
    - Drink 5–10 mL/kg in the 2–4h before exercise
    - Include sodium-rich foods/beverages to aid fluid retention

    Args:
        body_weight_kg: Body weight in kg.
        event_duration_hours: Planned duration.
        ambient_temp_c: Expected environmental temperature.
        sport: From SPORT_SWEAT_RATES.
        start_hours_from_now: Hours until exercise begins.

    Returns:
        Pre-exercise hydration schedule and fluid targets.
    """
    # ACSM target: 5–10 mL/kg over 2–4h pre-exercise
    pre_hydration_low_mL = body_weight_kg * 5
    pre_hydration_high_mL = body_weight_kg * 10

    sport_data = SPORT_SWEAT_RATES.get(sport.lower().replace(" ", "_"), SPORT_SWEAT_RATES["general"])
    expected_sweat_L_hr = sport_data["typical_L_hr"]

    # Heat adjustment
    if ambient_temp_c > 25:
        expected_sweat_L_hr *= 1.0 + ((ambient_temp_c - 25) / 5) * 0.10

    total_expected_sweat_L = expected_sweat_L_hr * event_duration_hours

    # Intra-exercise target (drink to thirst, loose range)
    intra_low_L_hr = max(0.4, expected_sweat_L_hr * 0.5)
    intra_high_L_hr = min(expected_sweat_L_hr, 1.0)  # cap at 1L/h for most sports

    schedule = []
    if start_hours_from_now >= 4:
        schedule.append(f"T-4h: Drink {pre_hydration_high_mL:.0f}mL of water or low-sugar sports drink.")
        schedule.append(f"T-2h: Drink 300–500mL with a sodium-containing snack.")
        schedule.append("T-1h: No large fluid bolus — sip 150–250mL if thirsty.")
        schedule.append("T-15min: 150–250mL water or dilute sports drink.")
    elif start_hours_from_now >= 2:
        schedule.append(f"T-2h: Drink {pre_hydration_high_mL:.0f}mL water or sports drink.")
        schedule.append(f"T-1h: 300–500mL with sodium-containing snack.")
        schedule.append("T-15min: 150–250mL if tolerated.")
    else:
        schedule.append(f"T-{int(start_hours_from_now*60)}min: Drink {pre_hydration_low_mL:.0f}–{pre_hydration_high_mL:.0f}mL now.")
        schedule.append("Avoid large fluid boluses close to exercise start (GI distress risk).")

    return {
        "pre_exercise_target_mL": f"{pre_hydration_low_mL:.0f}–{pre_hydration_high_mL:.0f}",
        "intra_exercise_L_hr": f"{intra_low_L_hr:.1f}–{intra_high_L_hr:.1f}",
        "total_expected_sweat_L": round(total_expected_sweat_L, 1),
        "schedule": schedule,
        "sodium_recommendation": (
            "Include 500–700mg sodium/L in fluid or via sodium-rich foods during pre-hydration "
            "to stimulate thirst and improve fluid retention."
        ),
        "urine_target": "Urine color 1–3 (pale to light yellow) at exercise start.",
        "evidence": "🟢 Strong — Sawka et al. 2007 MSSE ACSM Position Stand",
    }
