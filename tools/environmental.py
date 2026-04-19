"""
Environmental performance factors for Kiwi.

Evidence-based tools for environmental training adaptation:
- Altitude training optimizer (hypoxic dose, acclimatization timelines)
- Heat acclimatization (WBGT, core temp thresholds)
- Air quality adjustment (AQI-based training modifications)
- Cold exposure protocols
- Jet lag / travel fatigue management

References:
- Chapman RF et al. (2014) J Appl Physiol — Altitude training consensus
- Racinais S et al. (2015) Br J Sports Med — Heat and exercise consensus
- Carlisle AJ & Sharp NCC (2001) Sports Med — Exercise and outdoor air pollution
- Halson SL (2014) J Sports Sci — Sleep in elite athletes
- Waterhouse J et al. (2007) Br J Sports Med — Jet lag and travel fatigue
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class AltitudeProtocol:
    target_altitude_m: int
    current_altitude_m: int
    acclimatization_days: int
    training_modifications: list[str]
    nutrition_adjustments: list[str]
    risks: list[str]
    optimal_living_altitude_m: int
    optimal_training_altitude_m: int
    expected_hb_increase_pct: float
    evidence: str
    key_references: list[str]


@dataclass
class HeatAcclimatization:
    wbgt: float
    risk_category: str
    acclimatization_status: str
    training_modifications: list[str]
    hydration_protocol: list[str]
    cooling_strategies: list[str]
    warning_signs: list[str]
    evidence: str


@dataclass
class AirQualityAdjustment:
    aqi: int
    category: str
    training_recommendation: str
    modifications: list[str]
    health_notes: list[str]
    evidence: str


@dataclass
class ColdExposureProtocol:
    temperature_c: float
    wind_chill_c: float | None
    risk_level: str
    clothing_layers: list[str]
    training_modifications: list[str]
    nutrition_adjustments: list[str]
    warning_signs: list[str]
    evidence: str


@dataclass
class JetLagProtocol:
    time_zones_crossed: int
    direction: str  # "east" or "west"
    adjustment_days: int
    pre_travel: list[str]
    during_travel: list[str]
    post_arrival: list[str]
    light_exposure: str
    melatonin_protocol: str
    training_modifications: list[str]
    evidence: str


# ── WBGT Risk Categories ────────────────────────────────────────────────────

WBGT_CATEGORIES = {
    "low": {"range": (0, 18), "flag": "Green", "description": "Normal activity"},
    "moderate": {"range": (18, 23), "flag": "Yellow", "description": "Increased monitoring"},
    "high": {"range": (23, 28), "flag": "Orange", "description": "Reduce intensity/duration"},
    "very_high": {"range": (28, 32), "flag": "Red", "description": "Limit intense exercise"},
    "extreme": {"range": (32, 50), "flag": "Black", "description": "Cancel or postpone outdoor exercise"},
}

# ── AQI Categories ──────────────────────────────────────────────────────────

AQI_CATEGORIES = {
    "good": {"range": (0, 50), "color": "Green"},
    "moderate": {"range": (51, 100), "color": "Yellow"},
    "unhealthy_sensitive": {"range": (101, 150), "color": "Orange"},
    "unhealthy": {"range": (151, 200), "color": "Red"},
    "very_unhealthy": {"range": (201, 300), "color": "Purple"},
    "hazardous": {"range": (301, 500), "color": "Maroon"},
}


# ── Core Functions ───────────────────────────────────────────────────────────

def altitude_training_protocol(
    target_altitude_m: int,
    current_altitude_m: int = 0,
    duration_weeks: int = 3,
    sport: str = "endurance",
) -> AltitudeProtocol:
    """
    Generate altitude training protocol based on Live High–Train Low model.

    Optimal parameters (Chapman et al. 2014):
    - Living altitude: 2000–2500m
    - Training altitude: <1500m (or supplement with low-altitude sessions)
    - Duration: minimum 3–4 weeks for hematological adaptation
    - Hypoxic dose: ≥12h/day at altitude for erythropoietic response
    """
    # Acclimatization time (rough: 1 day per 300m above 2500m)
    if target_altitude_m <= 2000:
        acclim_days = 3
    elif target_altitude_m <= 2500:
        acclim_days = 5
    elif target_altitude_m <= 3500:
        acclim_days = 7 + (target_altitude_m - 2500) // 300
    else:
        acclim_days = 14 + (target_altitude_m - 3500) // 300

    # Training modifications
    modifications = []
    if target_altitude_m > 1500:
        modifications.append(f"Reduce training intensity by {min(30, (target_altitude_m - 1500) // 50)}% for first 5 days")
        modifications.append("Reduce interval pace by 5-10 sec/km for first week")
    if target_altitude_m > 2500:
        modifications.append("Limit sessions to 60-75% of sea-level volume initially")
        modifications.append("No high-intensity sessions for first 3-5 days")
    modifications.append("Monitor SpO2 — concern if <90% at rest, <80% during exercise")
    modifications.append("Increase recovery time between hard sessions by 25-50%")

    # Nutrition adjustments
    nutrition = [
        "Increase iron intake: 100mg elemental iron/day (altitude increases erythropoiesis)",
        "Increase carbohydrate intake by 15-20% (higher carb reliance at altitude)",
        "Increase fluid intake by 500-1000mL/day (increased respiratory and urinary water loss)",
        "Ensure adequate protein (1.6-2.0g/kg) for altitude-induced muscle protein breakdown",
    ]
    if target_altitude_m > 3000:
        nutrition.append("Consider acetazolamide prophylaxis (125-250mg BID, discuss with physician)")

    # Risks
    risks = ["Acute Mountain Sickness (headache, nausea, fatigue)"]
    if target_altitude_m > 2500:
        risks.append("High-Altitude Pulmonary Edema (HAPE) — rare below 3000m")
        risks.append("High-Altitude Cerebral Edema (HACE) — very rare below 4000m")
    if target_altitude_m > 3500:
        risks.append("Severe AMS requiring descent")
    risks.append("Sleep disruption (periodic breathing at altitude)")
    risks.append("Overtraining risk due to compounded stress")

    # Optimal altitudes (LHTL model)
    optimal_live = min(max(target_altitude_m, 2000), 2500)
    optimal_train = min(target_altitude_m, 1500)

    # Expected hemoglobin increase (~1% per week at 2000-2500m for 3-4 weeks)
    weeks_at_altitude = max(duration_weeks - 1, 1)  # subtract acclimatization
    hb_increase = min(weeks_at_altitude * 1.0, 4.0) if target_altitude_m >= 1800 else 0.0

    return AltitudeProtocol(
        target_altitude_m=target_altitude_m,
        current_altitude_m=current_altitude_m,
        acclimatization_days=acclim_days,
        training_modifications=modifications,
        nutrition_adjustments=nutrition,
        risks=risks,
        optimal_living_altitude_m=optimal_live,
        optimal_training_altitude_m=optimal_train,
        expected_hb_increase_pct=round(hb_increase, 1),
        evidence="🟢 Strong — Chapman RF et al. (2014) J Appl Physiol; Millet GP et al. (2010) Sports Med",
        key_references=[
            "Chapman RF et al. (2014) J Appl Physiol — Altitude training for sea-level competition",
            "Millet GP et al. (2010) Sports Med — Altitude training and team sports",
            "Saunders PU et al. (2009) Sports Med — Endurance training and altitude",
        ],
    )


def heat_acclimatization_protocol(
    wbgt: float,
    acclimatized: bool = False,
    sport: str = "general",
) -> HeatAcclimatization:
    """
    Generate heat acclimatization and safety protocol based on WBGT.

    WBGT (Wet Bulb Globe Temperature) thresholds:
    - <18°C: Green flag — normal activity
    - 18-23°C: Yellow — increased monitoring
    - 23-28°C: Orange — reduce intensity/duration
    - 28-32°C: Red — limit intense exercise
    - >32°C: Black — cancel/postpone outdoor exercise
    """
    # Determine risk category
    if wbgt < 18:
        category = "low"
    elif wbgt < 23:
        category = "moderate"
    elif wbgt < 28:
        category = "high"
    elif wbgt < 32:
        category = "very_high"
    else:
        category = "extreme"

    status = "acclimatized" if acclimatized else "not_acclimatized"

    # Training modifications
    modifications = []
    if category == "low":
        modifications = ["Normal training — standard hydration protocols"]
    elif category == "moderate":
        modifications = [
            "Monitor athletes for early heat illness signs",
            "Ensure adequate hydration breaks every 15-20 min",
            "Reduce protective equipment if possible",
        ]
    elif category == "high":
        modifications = [
            "Reduce exercise intensity by 15-25%",
            "Shorten session duration or add rest breaks",
            "Move training to cooler time of day",
            "Mandatory hydration breaks every 15 min",
        ]
        if not acclimatized:
            modifications.append("Reduce intensity by additional 10% for non-acclimatized athletes")
    elif category == "very_high":
        modifications = [
            "Limit intense exercise to 30-45 min",
            "Mandatory rest-to-work ratio of 1:1",
            "Ice towels and cold water immersion available",
            "Move to indoor facility if possible",
        ]
        if not acclimatized:
            modifications.append("STRONGLY consider cancelling for non-acclimatized athletes")
    else:
        modifications = [
            "CANCEL or POSTPONE outdoor exercise",
            "Indoor training only with air conditioning",
            "If outdoor event mandatory: reduce to minimal duration",
        ]

    # Hydration protocol
    hydration = [
        "Pre-exercise: 5-7 mL/kg body weight 2-4h before",
        "During: 150-250 mL every 15-20 min",
    ]
    if category in ("high", "very_high", "extreme"):
        hydration.append("Sodium: 0.5-0.7g/L in fluid (higher in heavy sweaters)")
        hydration.append("Post-exercise: 1.25-1.5 L per kg body weight lost")
        hydration.append("Monitor urine color (target: pale yellow)")

    # Cooling strategies
    cooling = []
    if category in ("moderate", "high"):
        cooling = ["Cold water (10-15°C) during breaks", "Ice towels on neck/wrists", "Shade during rest periods"]
    elif category in ("very_high", "extreme"):
        cooling = [
            "Cold water immersion (10-15°C) pre-cooling",
            "Ice vests and ice towels",
            "Menthol mouth rinse (perceptual cooling)",
            "Cold water dousing between bouts",
            "Rectal temperature monitoring for high-risk activities",
        ]

    warnings = [
        "Headache, dizziness, or confusion → STOP immediately, cool and hydrate",
        "Nausea or vomiting → STOP, seek medical attention",
        "Core temperature >40°C → medical emergency (exertional heat stroke)",
        "Cessation of sweating despite exertion → EMERGENCY",
    ]

    return HeatAcclimatization(
        wbgt=wbgt,
        risk_category=category,
        acclimatization_status=status,
        training_modifications=modifications,
        hydration_protocol=hydration,
        cooling_strategies=cooling,
        warning_signs=warnings,
        evidence="🟢 Strong — Racinais S et al. (2015) Br J Sports Med; Casa DJ et al. (2015) J Athl Train",
    )


def air_quality_adjustment(aqi: int) -> AirQualityAdjustment:
    """
    Training modifications based on Air Quality Index (AQI).

    EPA AQI categories:
    - 0-50: Good
    - 51-100: Moderate
    - 101-150: Unhealthy for sensitive groups
    - 151-200: Unhealthy
    - 201-300: Very unhealthy
    - 301-500: Hazardous
    """
    if aqi <= 50:
        return AirQualityAdjustment(
            aqi=aqi,
            category="good",
            training_recommendation="Normal training — no restrictions",
            modifications=[],
            health_notes=["Air quality is satisfactory"],
            evidence="🟢 Strong — EPA AQI guidelines; Carlisle & Sharp (2001) Sports Med",
        )
    elif aqi <= 100:
        return AirQualityAdjustment(
            aqi=aqi,
            category="moderate",
            training_recommendation="Normal training — sensitive individuals should monitor symptoms",
            modifications=[
                "Athletes with asthma: use pre-exercise bronchodilator",
                "Consider indoor training for unusually sensitive individuals",
            ],
            health_notes=[
                "Acceptable for most athletes",
                "Sensitive groups (asthma, respiratory conditions) may experience symptoms",
            ],
            evidence="🟢 Strong — EPA AQI guidelines",
        )
    elif aqi <= 150:
        return AirQualityAdjustment(
            aqi=aqi,
            category="unhealthy_sensitive",
            training_recommendation="Reduce prolonged outdoor exertion for sensitive groups",
            modifications=[
                "Reduce outdoor training duration to <60 min",
                "Move high-intensity sessions indoors",
                "Avoid training near major roads",
                "Reduce intensity for outdoor sessions",
            ],
            health_notes=[
                "General public may not be affected",
                "Athletes with respiratory conditions should avoid outdoor exertion",
                "Increased ventilation during exercise amplifies pollutant exposure 10-20x",
            ],
            evidence="🟡 Moderate — EPA AQI guidelines; Giles LV & Koehle MS (2014) Br J Sports Med",
        )
    elif aqi <= 200:
        return AirQualityAdjustment(
            aqi=aqi,
            category="unhealthy",
            training_recommendation="Move all training indoors or reduce significantly",
            modifications=[
                "All high-intensity training moved indoors",
                "Outdoor activity limited to light walking/warm-up only",
                "If outdoor training unavoidable: reduce duration to <30 min",
                "N95 mask for outdoor travel",
            ],
            health_notes=[
                "Everyone may begin to experience health effects",
                "Athletes at higher risk due to increased ventilation rates",
                "Particulate matter impairs lung function and exercise capacity",
            ],
            evidence="🟡 Moderate — EPA AQI guidelines",
        )
    elif aqi <= 300:
        return AirQualityAdjustment(
            aqi=aqi,
            category="very_unhealthy",
            training_recommendation="Avoid all outdoor exercise — indoor only",
            modifications=[
                "ALL training moved indoors with air filtration",
                "If no indoor facility: rest day recommended",
                "Reduce training volume by 30-50% even indoors",
            ],
            health_notes=[
                "Health alert: everyone at risk",
                "Significant reduction in VO2max expected",
                "Airway inflammation persists for 24-48h after exposure",
            ],
            evidence="🟡 Moderate — EPA AQI guidelines",
        )
    else:
        return AirQualityAdjustment(
            aqi=aqi,
            category="hazardous",
            training_recommendation="CANCEL all exercise — health emergency",
            modifications=[
                "No exercise of any kind recommended",
                "Remain indoors with air purification",
                "If must travel: N95/P100 mask required",
            ],
            health_notes=[
                "HEALTH EMERGENCY — serious health effects for everyone",
                "Exercise in these conditions dangerous even for healthy athletes",
                "Seek medical attention if experiencing respiratory symptoms",
            ],
            evidence="🟢 Strong — EPA AQI guidelines",
        )


def cold_exposure_protocol(
    temperature_c: float,
    wind_speed_kmh: float = 0,
    precipitation: bool = False,
) -> ColdExposureProtocol:
    """
    Generate cold weather training protocol.

    Wind chill calculated using Environment Canada formula.
    """
    # Wind chill calculation (Environment Canada formula)
    if wind_speed_kmh > 5 and temperature_c < 10:
        wind_chill = (
            13.12 + 0.6215 * temperature_c
            - 11.37 * (wind_speed_kmh ** 0.16)
            + 0.3965 * temperature_c * (wind_speed_kmh ** 0.16)
        )
        wind_chill = round(wind_chill, 1)
    else:
        wind_chill = None

    effective_temp = wind_chill if wind_chill is not None else temperature_c

    # Risk level
    if effective_temp > 5:
        risk_level = "low"
    elif effective_temp > -5:
        risk_level = "moderate"
    elif effective_temp > -15:
        risk_level = "high"
    elif effective_temp > -25:
        risk_level = "very_high"
    else:
        risk_level = "extreme"

    # Clothing layers
    layers = []
    if effective_temp > 5:
        layers = ["Moisture-wicking base layer", "Light outer layer"]
    elif effective_temp > -5:
        layers = [
            "Moisture-wicking base layer (merino wool or synthetic)",
            "Insulating mid-layer (fleece)",
            "Wind-resistant outer shell",
            "Gloves and ear protection",
        ]
    elif effective_temp > -15:
        layers = [
            "Thermal base layer (merino wool)",
            "Insulating mid-layer (heavy fleece or down)",
            "Windproof/waterproof outer shell",
            "Insulated gloves, balaclava, thermal hat",
            "Insulated footwear with moisture barriers",
        ]
    else:
        layers = [
            "Heavy thermal base layer",
            "Double insulating layers",
            "Heavy windproof/waterproof shell",
            "Expedition-grade gloves, balaclava, goggles",
            "Vapor barrier socks + insulated boots",
        ]

    if precipitation:
        layers.append("Waterproof outer layer ESSENTIAL — wet cold dramatically increases heat loss")

    # Training modifications
    modifications = []
    if risk_level == "low":
        modifications = ["Normal training — warm up thoroughly", "Adjust clothing for comfort"]
    elif risk_level == "moderate":
        modifications = [
            "Extended warm-up (15-20 min indoors before outdoor session)",
            "Shorten outdoor exposure to <90 min",
            "Warm fluids during breaks",
            "Cover extremities (fingers, ears, nose most vulnerable)",
        ]
    elif risk_level == "high":
        modifications = [
            "Limit outdoor sessions to 45-60 min",
            "Indoor warm-up mandatory (20+ min)",
            "Reduce intensity by 10-15% (cold + exercise = bronchospasm risk)",
            "Buddy system — monitor each other for frostbite signs",
            "Scarf/mask over mouth to warm inspired air",
        ]
    elif risk_level == "very_high":
        modifications = [
            "Move training indoors if possible",
            "Outdoor exposure <30 min only if necessary",
            "Reduce intensity significantly",
            "Frostbite risk within 10-30 min on exposed skin",
        ]
    else:
        modifications = [
            "CANCEL outdoor training — extreme hypothermia/frostbite risk",
            "Indoor training only",
            "Frostbite risk within minutes on exposed skin",
        ]

    # Nutrition adjustments
    nutrition = [
        "Increase caloric intake by 10-25% (shivering thermogenesis)",
        "Warm carbohydrate-rich fluids during training",
    ]
    if effective_temp < -5:
        nutrition.append("Hot meals pre-exercise (internal warming)")
        nutrition.append("Extra carbohydrates: glycogen depletion faster in cold")
    if effective_temp < -15:
        nutrition.append("High-calorie snacks every 30 min for extended exposure")

    warnings = [
        "Numbness in extremities → rewarm immediately",
        "White/gray waxy skin → frostbite — seek medical attention",
        "Uncontrollable shivering → hypothermia onset — rewarm and seek shelter",
        "Confusion or slurred speech → moderate hypothermia — EMERGENCY",
    ]

    return ColdExposureProtocol(
        temperature_c=temperature_c,
        wind_chill_c=wind_chill,
        risk_level=risk_level,
        clothing_layers=layers,
        training_modifications=modifications,
        nutrition_adjustments=nutrition,
        warning_signs=warnings,
        evidence="🟡 Moderate — Castellani JW & Young AJ (2016) Compr Physiol; Nimmo M (2004) Sports Med",
    )


def jet_lag_protocol(
    time_zones_crossed: int,
    direction: str = "east",
) -> JetLagProtocol:
    """
    Generate jet lag management protocol.

    General rule: ~1 day per time zone to fully adjust.
    Eastward travel harder than westward (phase advance vs delay).
    """
    if time_zones_crossed < 0:
        time_zones_crossed = abs(time_zones_crossed)

    direction = direction.lower()

    # Adjustment days (eastward harder)
    if direction == "east":
        adjustment_days = int(time_zones_crossed * 1.2)
    else:
        adjustment_days = int(time_zones_crossed * 0.8)
    adjustment_days = max(1, adjustment_days)

    # Pre-travel strategies
    pre_travel = []
    if time_zones_crossed >= 3:
        if direction == "east":
            pre_travel = [
                f"Shift sleep schedule 30 min earlier per day for {min(time_zones_crossed, 3)} days before departure",
                "Morning bright light exposure (advance circadian clock)",
                "Avoid evening blue light exposure",
            ]
        else:
            pre_travel = [
                f"Shift sleep schedule 30 min later per day for {min(time_zones_crossed, 3)} days before departure",
                "Evening bright light exposure (delay circadian clock)",
                "Avoid morning bright light",
            ]
    else:
        pre_travel = ["Minimal pre-travel adjustment needed for <3 time zones"]

    pre_travel.append("Sleep well the nights before travel — sleep banking helps")
    pre_travel.append("Avoid alcohol and heavy meals before travel")

    # During travel
    during_travel = [
        "Set watch to destination time zone immediately",
        "Stay hydrated: 250mL per hour of flight",
        "Avoid excessive caffeine (stop 8h before intended sleep at destination)",
        "Move around the cabin every 1-2 hours",
        "Compression socks for flights >4 hours",
    ]
    if time_zones_crossed >= 5:
        during_travel.append("Short naps OK (20-30 min) but avoid long sleep on plane")

    # Post-arrival
    post_arrival = []
    if direction == "east":
        post_arrival = [
            "Seek morning bright light at destination (outdoor walk 7-9am local)",
            "Avoid bright light in late afternoon/evening for first 2-3 days",
            "Anchor meals to local schedule immediately",
            "Light exercise in morning (helps advance circadian clock)",
            "Avoid naps >30 min — push through to local bedtime",
        ]
    else:
        post_arrival = [
            "Seek afternoon/evening bright light at destination",
            "Avoid morning bright light for first 2-3 days",
            "Anchor meals to local schedule immediately",
            "Exercise in afternoon/evening (helps delay circadian clock)",
            "Short naps OK (<30 min) if extremely fatigued",
        ]

    post_arrival.append("No critical competition decisions for 24-48h after arrival")
    post_arrival.append(f"Allow {adjustment_days} days before major competition")

    # Light exposure protocol
    if direction == "east":
        light = ("Morning light exposure (7-10am local time) — advance circadian phase. "
                "Avoid evening light. Blue-light blocking glasses after 6pm local time.")
    else:
        light = ("Evening light exposure (4-8pm local time) — delay circadian phase. "
                "Avoid early morning bright light for first 2-3 days.")

    # Melatonin protocol
    if time_zones_crossed >= 3:
        if direction == "east":
            melatonin = (f"0.5-3mg melatonin at local bedtime (destination) starting first evening. "
                        f"Continue for {min(time_zones_crossed, 5)} days. Take 30-60 min before desired sleep.")
        else:
            melatonin = (f"0.5-3mg melatonin at local bedtime if difficulty sleeping. "
                        f"May not be needed for westward travel. Use for {min(time_zones_crossed, 4)} days max.")
    else:
        melatonin = "Not typically needed for <3 time zones. Good sleep hygiene sufficient."

    # Training modifications
    training = [
        "Day 1-2: Light activity only (walk, easy jog, mobility)",
        f"Day 3-{min(adjustment_days, 5)}: Moderate intensity (60-70% max HR)",
    ]
    if time_zones_crossed >= 5:
        training.append("No high-intensity training for first 3-4 days")
        training.append("RPE-based training preferred over pace/power targets")
    training.append(f"Full training: day {adjustment_days}+")
    training.append("Monitor HRV — expect elevated resting HR for 2-3 days")

    return JetLagProtocol(
        time_zones_crossed=time_zones_crossed,
        direction=direction,
        adjustment_days=adjustment_days,
        pre_travel=pre_travel,
        during_travel=during_travel,
        post_arrival=post_arrival,
        light_exposure=light,
        melatonin_protocol=melatonin,
        training_modifications=training,
        evidence="🟢 Strong — Waterhouse J et al. (2007) Br J Sports Med; Halson SL (2014) J Sports Sci",
    )


# ── Formatting Functions ─────────────────────────────────────────────────────

def format_altitude_protocol(proto: AltitudeProtocol) -> str:
    """Human-readable altitude protocol."""
    lines = [
        "═══ Altitude Training Protocol ═══",
        f"  Target:      {proto.target_altitude_m}m (from {proto.current_altitude_m}m)",
        f"  Acclimatize: {proto.acclimatization_days} days",
        f"  Live High:   {proto.optimal_living_altitude_m}m",
        f"  Train Low:   {proto.optimal_training_altitude_m}m",
        f"  Expected Hb: +{proto.expected_hb_increase_pct}%",
        "",
        "── Training Modifications ──",
    ]
    for m in proto.training_modifications:
        lines.append(f"  • {m}")
    lines += ["", "── Nutrition ──"]
    for n in proto.nutrition_adjustments:
        lines.append(f"  • {n}")
    lines += ["", "── Risks ──"]
    for r in proto.risks:
        lines.append(f"  ⚠ {r}")
    lines += ["", "── Evidence ──", f"  {proto.evidence}"]
    return "\n".join(lines)


def format_heat_protocol(proto: HeatAcclimatization) -> str:
    """Human-readable heat protocol."""
    lines = [
        "═══ Heat Safety Protocol ═══",
        f"  WBGT:        {proto.wbgt}°C",
        f"  Risk:        {proto.risk_category.upper()}",
        f"  Status:      {proto.acclimatization_status}",
        "",
        "── Training ──",
    ]
    for m in proto.training_modifications:
        lines.append(f"  • {m}")
    lines += ["", "── Hydration ──"]
    for h in proto.hydration_protocol:
        lines.append(f"  • {h}")
    if proto.cooling_strategies:
        lines += ["", "── Cooling ──"]
        for c in proto.cooling_strategies:
            lines.append(f"  • {c}")
    lines += ["", "── Evidence ──", f"  {proto.evidence}"]
    return "\n".join(lines)


def format_cold_protocol(proto: ColdExposureProtocol) -> str:
    """Human-readable cold exposure protocol."""
    wc = f"{proto.wind_chill_c}°C" if proto.wind_chill_c is not None else "n/a"
    lines = [
        "═══ Cold Exposure Protocol ═══",
        f"  Temperature: {proto.temperature_c}°C",
        f"  Wind Chill:  {wc}",
        f"  Risk Level:  {proto.risk_level.upper()}",
        "",
        "── Clothing Layers ──",
    ]
    for layer in proto.clothing_layers:
        lines.append(f"  • {layer}")
    lines += ["", "── Training Modifications ──"]
    for m in proto.training_modifications:
        lines.append(f"  • {m}")
    lines += ["", "── Nutrition ──"]
    for n in proto.nutrition_adjustments:
        lines.append(f"  • {n}")
    lines += ["", "── Warning Signs ──"]
    for w in proto.warning_signs:
        lines.append(f"  ⚠ {w}")
    lines += ["", "── Evidence ──", f"  {proto.evidence}"]
    return "\n".join(lines)


def format_air_quality(aq: AirQualityAdjustment) -> str:
    """Human-readable AQI report."""
    lines = [
        "═══ Air Quality Assessment ═══",
        f"  AQI:         {aq.aqi}",
        f"  Category:    {aq.category.replace('_', ' ').title()}",
        f"  Recommendation: {aq.training_recommendation}",
    ]
    if aq.modifications:
        lines += ["", "── Modifications ──"]
        for m in aq.modifications:
            lines.append(f"  • {m}")
    lines += ["", "── Evidence ──", f"  {aq.evidence}"]
    return "\n".join(lines)


def format_jet_lag(proto: JetLagProtocol) -> str:
    """Human-readable jet lag protocol."""
    lines = [
        "═══ Jet Lag Management Protocol ═══",
        f"  Zones Crossed: {proto.time_zones_crossed} ({proto.direction})",
        f"  Est. Adjustment: {proto.adjustment_days} days",
        "",
        "── Pre-Travel ──",
    ]
    for p in proto.pre_travel:
        lines.append(f"  • {p}")
    lines += ["", "── During Travel ──"]
    for d in proto.during_travel:
        lines.append(f"  • {d}")
    lines += ["", "── Post-Arrival ──"]
    for a in proto.post_arrival:
        lines.append(f"  • {a}")
    lines += [
        "", "── Light Exposure ──", f"  {proto.light_exposure}",
        "", "── Melatonin ──", f"  {proto.melatonin_protocol}",
        "", "── Evidence ──", f"  {proto.evidence}",
    ]
    return "\n".join(lines)
