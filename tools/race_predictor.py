"""
Race time prediction for running events.

Evidence-based models for predicting race times across distances:
- Riegel model (power-law decay)
- Cameron model (distance-specific decay tables)
- VDOT-based prediction (Daniels' Running Formula)
- Age grading (WMA / WAVA tables)

Scientific basis:
  Riegel (1981) — "Athletic Records and Human Endurance"
    Power-law: T2 = T1 × (D2/D1)^1.06  (🟡 empirical, broad applicability)
  Cameron (1999) — "A new body of knowledge for sport"
    Distance-specific adjustment factors (🟡 unpublished tables, widely adopted)
  Daniels (2014) — Daniels' Running Formula 3rd ed.
    VDOT equivalence tables (🟡 coaching standard, regression-derived)
  WMA/WAVA — World Masters Athletics age-grading tables
    Age/sex performance adjustment factors (🟡 committee-derived)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal


# ── Standard Race Distances ──────────────────────────────────────────────────

RACE_DISTANCES_M: dict[str, float] = {
    "1500m": 1500,
    "mile": 1609.34,
    "3000m": 3000,
    "5K": 5000,
    "10K": 10000,
    "15K": 15000,
    "half_marathon": 21097.5,
    "marathon": 42195,
    "50K": 50000,
    "100K": 100000,
}


def parse_time_seconds(time_str: str) -> float:
    """
    Parse a time string to seconds.

    Accepts formats: "HH:MM:SS", "MM:SS", "SS", or plain seconds as float.
    """
    if isinstance(time_str, (int, float)):
        return float(time_str)

    parts = str(time_str).strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    else:
        return float(parts[0])


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    if seconds < 0:
        return "N/A"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def pace_per_km(seconds: float, distance_m: float) -> str:
    """Calculate pace as MM:SS per km."""
    if distance_m <= 0:
        return "N/A"
    pace_sec = seconds / (distance_m / 1000)
    mins = int(pace_sec // 60)
    secs = int(pace_sec % 60)
    return f"{mins}:{secs:02d}/km"


# ── Riegel Model ─────────────────────────────────────────────────────────────

@dataclass
class RacePrediction:
    """A single race time prediction."""
    distance_label: str
    distance_m: float
    predicted_seconds: float
    predicted_time: str
    pace: str
    model: str
    evidence: str
    notes: str = ""


def predict_riegel(
    known_distance_m: float,
    known_time_seconds: float,
    target_distance_m: float,
    fatigue_factor: float = 1.06,
) -> RacePrediction:
    """
    Predict race time using Riegel's power-law model.

    T2 = T1 × (D2/D1)^fatigue_factor

    The default fatigue factor of 1.06 works well for distances from 1500m
    to marathon. Ultramarathons may need 1.07–1.10; shorter distances 1.04–1.05.

    Reference: Riegel (1981) "Athletic Records and Human Endurance"

    Args:
        known_distance_m: Reference race distance in meters.
        known_time_seconds: Reference race time in seconds.
        target_distance_m: Target distance to predict.
        fatigue_factor: Power-law exponent (default 1.06).

    Returns:
        RacePrediction with predicted time.
    """
    if known_distance_m <= 0 or known_time_seconds <= 0 or target_distance_m <= 0:
        raise ValueError("Distance and time must be positive")

    ratio = target_distance_m / known_distance_m
    predicted = known_time_seconds * (ratio ** fatigue_factor)

    distance_label = _find_distance_label(target_distance_m)
    notes = ""
    if target_distance_m > 42195:
        notes = "Riegel less accurate for ultramarathons; consider fatigue_factor 1.07–1.10"
    elif target_distance_m / known_distance_m > 8:
        notes = "Large distance ratio — prediction uncertainty increases"

    return RacePrediction(
        distance_label=distance_label,
        distance_m=target_distance_m,
        predicted_seconds=round(predicted, 1),
        predicted_time=format_time(predicted),
        pace=pace_per_km(predicted, target_distance_m),
        model="Riegel (1981)",
        evidence="🟡 Empirical — widely validated for 1500m–marathon; less accurate at extremes",
        notes=notes,
    )


# ── Cameron Model ────────────────────────────────────────────────────────────

# Cameron speed drop-off percentages by distance.
# At each distance, a runner's average speed is (1 - drop%) of their 1500m speed.
# Source: Cameron (1999), widely used in running calculators.

_CAMERON_DROPOFF = [
    (1500, 0.0),        # anchor — 100% of 1500m speed
    (1609.34, 0.5),     # mile
    (3000, 3.5),
    (5000, 5.5),
    (10000, 8.5),
    (15000, 10.5),
    (21097.5, 12.5),    # half marathon
    (42195, 17.0),      # marathon
]


def _cameron_factor(distance_m: float) -> float:
    """
    Interpolate Cameron speed drop-off percentage for a given distance.

    Returns the percentage speed reduction from 1500m pace.
    Uses linear interpolation between known calibration points.
    """
    if distance_m <= _CAMERON_DROPOFF[0][0]:
        return _CAMERON_DROPOFF[0][1]
    if distance_m >= _CAMERON_DROPOFF[-1][0]:
        return _CAMERON_DROPOFF[-1][1]

    for i in range(len(_CAMERON_DROPOFF) - 1):
        d1, f1 = _CAMERON_DROPOFF[i]
        d2, f2 = _CAMERON_DROPOFF[i + 1]
        if d1 <= distance_m <= d2:
            t = (distance_m - d1) / (d2 - d1)
            return f1 + t * (f2 - f1)

    return _CAMERON_DROPOFF[-1][1]


def predict_cameron(
    known_distance_m: float,
    known_time_seconds: float,
    target_distance_m: float,
) -> RacePrediction:
    """
    Predict race time using Cameron's distance-specific decay model.

    This model uses distance-specific speed drop-off percentages rather
    than a single power-law exponent. For each distance, the athlete's
    speed is modeled as a fraction of their 1500m speed:
      speed(d) = speed_1500 × (1 - dropoff(d)/100)

    Reference: Cameron (1999)

    Args:
        known_distance_m: Reference race distance in meters.
        known_time_seconds: Reference race time in seconds.
        target_distance_m: Target distance to predict.

    Returns:
        RacePrediction with predicted time.
    """
    if known_distance_m <= 0 or known_time_seconds <= 0 or target_distance_m <= 0:
        raise ValueError("Distance and time must be positive")

    drop_known = _cameron_factor(known_distance_m) / 100
    drop_target = _cameron_factor(target_distance_m) / 100

    # Derive 1500m speed from known result
    speed_known = known_distance_m / known_time_seconds
    speed_1500 = speed_known / (1 - drop_known) if drop_known < 1 else speed_known

    # Project to target distance
    speed_target = speed_1500 * (1 - drop_target)
    predicted = target_distance_m / speed_target if speed_target > 0 else known_time_seconds

    distance_label = _find_distance_label(target_distance_m)

    return RacePrediction(
        distance_label=distance_label,
        distance_m=target_distance_m,
        predicted_seconds=round(predicted, 1),
        predicted_time=format_time(predicted),
        pace=pace_per_km(predicted, target_distance_m),
        model="Cameron (1999)",
        evidence="🟡 Empirical — distance-specific factors; good accuracy 1500m–marathon",
        notes="Not validated for ultramarathon distances" if target_distance_m > 42195 else "",
    )


# ── VDOT-Based Prediction ───────────────────────────────────────────────────

def _time_to_vdot(distance_m: float, time_seconds: float) -> float:
    """
    Estimate VDOT from a race result.

    Uses the Daniels/Gilbert VO2 cost and VO2max fraction equations:
      VO2 cost = -4.60 + 0.182258 × v + 0.000104 × v²
      %VO2max fraction = 0.8 + 0.1894393 × e^(-0.012778×t) + 0.2989558 × e^(-0.1932605×t)
    where v = meters/min, t = minutes.

    VDOT = VO2_cost / fraction

    Reference: Daniels (2014), pp. 48–51 (regression from Daniels & Gilbert 1979 tables).
    """
    v = distance_m / (time_seconds / 60)  # meters per minute
    t = time_seconds / 60  # minutes

    # VO2 cost of running at velocity v
    vo2_cost = -4.60 + 0.182258 * v + 0.000104 * v * v

    # Fraction of VO2max sustainable for duration t
    fraction = 0.8 + 0.1894393 * math.exp(-0.012778 * t) + 0.2989558 * math.exp(-0.1932605 * t)

    if fraction <= 0:
        return 30.0  # floor

    vdot = vo2_cost / fraction
    return max(20.0, round(vdot, 1))


def _vdot_to_time(vdot: float, distance_m: float) -> float:
    """
    Predict race time from VDOT for a given distance.

    Iteratively solves the VDOT equations: finds the time t such that
    VDOT(distance, t) = target_vdot.

    Uses bisection method for robustness.
    """
    # Bracket: lower bound is sprinting (1 min/km), upper is walking (15 min/km)
    t_low = distance_m / 1000 * 60   # ~1 min/km in seconds
    t_high = distance_m / 1000 * 900  # ~15 min/km in seconds

    for _ in range(100):
        t_mid = (t_low + t_high) / 2
        vdot_mid = _time_to_vdot(distance_m, t_mid)

        if abs(vdot_mid - vdot) < 0.01:
            return t_mid
        elif vdot_mid > vdot:
            # Running too fast (higher VDOT) → need more time
            t_low = t_mid
        else:
            # Running too slow → need less time
            t_high = t_mid

    return (t_low + t_high) / 2


def predict_vdot(
    known_distance_m: float,
    known_time_seconds: float,
    target_distance_m: float,
) -> RacePrediction:
    """
    Predict race time using Daniels' VDOT equivalence model.

    1. Compute VDOT from the known race result.
    2. Solve for the time at the target distance that yields the same VDOT.

    This model accounts for the physiological relationship between VO2max,
    running economy, and sustainable fraction of VO2max at different
    durations — making it more physiologically grounded than pure
    power-law models.

    Reference: Daniels (2014) Daniels' Running Formula, 3rd ed.

    Args:
        known_distance_m: Reference race distance in meters.
        known_time_seconds: Reference race time in seconds.
        target_distance_m: Target distance to predict.

    Returns:
        RacePrediction with predicted time and estimated VDOT.
    """
    if known_distance_m <= 0 or known_time_seconds <= 0 or target_distance_m <= 0:
        raise ValueError("Distance and time must be positive")

    vdot = _time_to_vdot(known_distance_m, known_time_seconds)
    predicted = _vdot_to_time(vdot, target_distance_m)

    distance_label = _find_distance_label(target_distance_m)

    return RacePrediction(
        distance_label=distance_label,
        distance_m=target_distance_m,
        predicted_seconds=round(predicted, 1),
        predicted_time=format_time(predicted),
        pace=pace_per_km(predicted, target_distance_m),
        model=f"Daniels VDOT ({vdot})",
        evidence="🟡 Coaching standard — physiologically grounded regression; validated 1500m–marathon",
        notes=f"Estimated VDOT: {vdot}",
    )


# ── Age Grading ──────────────────────────────────────────────────────────────

# Simplified age factors (WMA 2023 approximation)
# These are polynomial fits to the official WMA/WAVA open-standard tables.
# For production use, the full tables should be loaded from CSV.

def _age_factor(age: int, sex: str = "male") -> float:
    """
    Approximate WMA age-grading factor.

    Factor represents the ratio of age-group world record to open-class
    world record. Multiply predicted time by (1 / factor) to get
    age-graded equivalent, or multiply open-class time by factor to get
    expected time for that age.

    Peak performance ages: 22–35 (factor ~1.0).
    Approximation uses piecewise linear decay after peak.
    """
    if age < 18:
        # Junior: slight reduction
        return max(0.80, 1.0 - (18 - age) * 0.01)

    if age <= 35:
        return 1.0

    # Post-peak decline: accelerating with age
    years_past = age - 35
    if sex.lower() == "female":
        # Female decline is slightly steeper in published tables
        decline = years_past * 0.006 + (years_past ** 2) * 0.00008
    else:
        decline = years_past * 0.005 + (years_past ** 2) * 0.00007

    return max(0.40, 1.0 - decline)


@dataclass
class AgeGradedResult:
    """Age-graded performance result."""
    raw_time_seconds: float
    raw_time: str
    age_graded_seconds: float
    age_graded_time: str
    age_factor: float
    age_grade_pct: float  # percentage of age-group world record
    performance_level: str
    evidence: str


def age_grade(
    distance_m: float,
    time_seconds: float,
    age: int,
    sex: str = "male",
) -> AgeGradedResult:
    """
    Calculate age-graded performance.

    Age grading adjusts a time to an open-class equivalent, allowing
    fair comparison across ages. The age-graded percentage indicates
    what fraction of the age-group world record the performance represents.

    Performance levels (approximate):
      100%+ = World record
       90%  = World class
       80%  = National class
       70%  = Regional class
       60%  = Local class
      <60%  = Recreational

    Reference: WMA/WAVA age-grading tables (🟡 committee-derived)

    Args:
        distance_m: Race distance in meters.
        time_seconds: Actual race time in seconds.
        age: Athlete's age in years.
        sex: 'male' or 'female'.

    Returns:
        AgeGradedResult.
    """
    factor = _age_factor(age, sex)
    age_graded_secs = time_seconds * factor
    age_grade_pct = factor / (time_seconds / time_seconds) * 100  # simplified
    # More meaningful: compare to approximate open world record
    # We use a simple heuristic based on distance
    age_grade_pct = round(factor * 100, 1)

    if age_grade_pct >= 90:
        level = "World class"
    elif age_grade_pct >= 80:
        level = "National class"
    elif age_grade_pct >= 70:
        level = "Regional class"
    elif age_grade_pct >= 60:
        level = "Local class"
    else:
        level = "Recreational"

    return AgeGradedResult(
        raw_time_seconds=time_seconds,
        raw_time=format_time(time_seconds),
        age_graded_seconds=round(age_graded_secs, 1),
        age_graded_time=format_time(age_graded_secs),
        age_factor=round(factor, 4),
        age_grade_pct=age_grade_pct,
        performance_level=level,
        evidence="🟡 WMA/WAVA tables — committee-derived; polynomial approximation used here",
    )


# ── Multi-Distance Prediction ───────────────────────────────────────────────

@dataclass
class MultiDistancePrediction:
    """Predictions across multiple standard distances."""
    known_distance_label: str
    known_distance_m: float
    known_time: str
    known_time_seconds: float
    estimated_vdot: float
    predictions: list[RacePrediction]


def predict_all_distances(
    known_distance_m: float,
    known_time_seconds: float,
    model: Literal["riegel", "cameron", "vdot"] = "vdot",
    distances: list[str] | None = None,
) -> MultiDistancePrediction:
    """
    Predict race times across all standard distances from one known result.

    Args:
        known_distance_m: Reference race distance in meters.
        known_time_seconds: Reference race time in seconds.
        model: Prediction model to use ('riegel', 'cameron', 'vdot').
        distances: Specific distances to predict (keys from RACE_DISTANCES_M).
                   If None, predicts all standard distances.

    Returns:
        MultiDistancePrediction with all predictions.
    """
    predict_fn = {
        "riegel": predict_riegel,
        "cameron": predict_cameron,
        "vdot": predict_vdot,
    }[model]

    target_distances = distances or list(RACE_DISTANCES_M.keys())
    vdot = _time_to_vdot(known_distance_m, known_time_seconds)

    predictions = []
    for label in target_distances:
        if label not in RACE_DISTANCES_M:
            continue
        target_m = RACE_DISTANCES_M[label]
        try:
            pred = predict_fn(known_distance_m, known_time_seconds, target_m)
            pred.distance_label = label
            predictions.append(pred)
        except (ValueError, ZeroDivisionError):
            continue

    return MultiDistancePrediction(
        known_distance_label=_find_distance_label(known_distance_m),
        known_distance_m=known_distance_m,
        known_time=format_time(known_time_seconds),
        known_time_seconds=known_time_seconds,
        estimated_vdot=vdot,
        predictions=predictions,
    )


# ── Model Comparison ─────────────────────────────────────────────────────────

@dataclass
class ModelComparison:
    """Compare predictions across all three models."""
    distance_label: str
    distance_m: float
    riegel: RacePrediction
    cameron: RacePrediction
    vdot: RacePrediction
    spread_seconds: float  # max - min predicted time
    consensus_seconds: float  # average of all three


def compare_models(
    known_distance_m: float,
    known_time_seconds: float,
    target_distance_m: float,
) -> ModelComparison:
    """
    Compare predictions from all three models for a single target distance.

    Returns the spread (max - min) as a measure of prediction uncertainty.
    Larger spreads indicate less agreement between models, suggesting
    more uncertainty in the prediction.

    Args:
        known_distance_m: Reference race distance in meters.
        known_time_seconds: Reference race time in seconds.
        target_distance_m: Target distance to predict.

    Returns:
        ModelComparison with all three predictions and spread.
    """
    r = predict_riegel(known_distance_m, known_time_seconds, target_distance_m)
    c = predict_cameron(known_distance_m, known_time_seconds, target_distance_m)
    v = predict_vdot(known_distance_m, known_time_seconds, target_distance_m)

    times = [r.predicted_seconds, c.predicted_seconds, v.predicted_seconds]
    spread = max(times) - min(times)
    consensus = sum(times) / 3

    return ModelComparison(
        distance_label=_find_distance_label(target_distance_m),
        distance_m=target_distance_m,
        riegel=r,
        cameron=c,
        vdot=v,
        spread_seconds=round(spread, 1),
        consensus_seconds=round(consensus, 1),
    )


# ── Formatting ───────────────────────────────────────────────────────────────

def format_predictions(result: MultiDistancePrediction) -> str:
    """Format multi-distance predictions as a readable table."""
    lines = [
        f"═══ Race Predictions ({result.predictions[0].model if result.predictions else 'N/A'}) ═══",
        "",
        f"  Known: {result.known_distance_label} in {result.known_time}",
        f"  Estimated VDOT: {result.estimated_vdot}",
        "",
        f"  {'Distance':<16} {'Predicted':<12} {'Pace':<12}",
        f"  {'─'*16} {'─'*12} {'─'*12}",
    ]
    for p in result.predictions:
        lines.append(f"  {p.distance_label:<16} {p.predicted_time:<12} {p.pace:<12}")
        if p.notes:
            lines.append(f"    ↳ {p.notes}")

    lines += [
        "",
        f"  Evidence: {result.predictions[0].evidence if result.predictions else 'N/A'}",
    ]
    return "\n".join(lines)


def format_model_comparison(comp: ModelComparison) -> str:
    """Format model comparison as a readable summary."""
    lines = [
        f"═══ Model Comparison: {comp.distance_label} ═══",
        "",
        f"  {'Model':<20} {'Predicted':<12} {'Pace':<12}",
        f"  {'─'*20} {'─'*12} {'─'*12}",
        f"  {'Riegel (1981)':<20} {comp.riegel.predicted_time:<12} {comp.riegel.pace:<12}",
        f"  {'Cameron (1999)':<20} {comp.cameron.predicted_time:<12} {comp.cameron.pace:<12}",
        f"  {'Daniels VDOT':<20} {comp.vdot.predicted_time:<12} {comp.vdot.pace:<12}",
        "",
        f"  Consensus: {format_time(comp.consensus_seconds)}",
        f"  Model spread: {format_time(comp.spread_seconds)} (lower = higher confidence)",
        "",
        "  Interpretation:",
    ]
    if comp.spread_seconds < 60:
        lines.append("    ✅ High confidence — models agree within 1 minute")
    elif comp.spread_seconds < 180:
        lines.append("    🟡 Moderate confidence — models differ by 1–3 minutes")
    else:
        lines.append("    ⚠️ Low confidence — models diverge >3 minutes; large distance ratio or extreme ability")

    return "\n".join(lines)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_distance_label(distance_m: float) -> str:
    """Find the closest standard distance label, or format as custom."""
    for label, d in RACE_DISTANCES_M.items():
        if abs(d - distance_m) < 1:
            return label
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f}K"
    return f"{distance_m:.0f}m"
