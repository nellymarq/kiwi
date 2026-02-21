"""
Training zone calculation for Kiwi.

Evidence-based training intensity zones and distribution:
- Heart rate zones (Karvonen, %HRmax, LTHR-based)
- Power zones (FTP-based — Coggan/Allen model)
- Pace zones for running (Daniels' VDOT)
- VO2max estimation methods (Cooper, Rockport, HR-based)
- Training intensity distribution (polarized vs. pyramidal vs. threshold)

References:
- Seiler (2010) Scand J Med Sci Sports — Polarized training in endurance athletes
- Coggan & Allen (2010) Training and Racing with a Power Meter — Power zone model
- Daniels (2014) Daniels' Running Formula — VDOT tables and pace zones
- Karvonen et al. (1957) Ann Med Exp Biol Fenn — Heart rate reserve formula
- Tanaka et al. (2001) JACC — Age-predicted HRmax formula
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Literal


# ── VO2max Estimation ────────────────────────────────────────────────────────

@dataclass
class VO2maxEstimate:
    vo2max: float           # mL/kg/min
    method: str
    fitness_category: str   # poor / fair / average / good / excellent / superior
    age_sex_percentile: str
    evidence: str


# Normative VO2max categories (ACSM Guidelines, 10th ed.)
VO2MAX_CATEGORIES_MALE = [
    (0,   25,  "very poor"),
    (25,  34,  "poor"),
    (34,  43,  "fair"),
    (43,  53,  "good"),
    (53,  60,  "excellent"),
    (60,  999, "superior"),
]

VO2MAX_CATEGORIES_FEMALE = [
    (0,   24,  "very poor"),
    (24,  31,  "poor"),
    (31,  39,  "fair"),
    (39,  47,  "good"),
    (47,  55,  "excellent"),
    (55,  999, "superior"),
]


def classify_vo2max(vo2max: float, sex: str = "male") -> str:
    """Classify VO2max into ACSM fitness category."""
    table = VO2MAX_CATEGORIES_MALE if sex.lower() == "male" else VO2MAX_CATEGORIES_FEMALE
    for low, high, cat in table:
        if low <= vo2max < high:
            return cat
    return "unknown"


def estimate_vo2max_cooper(distance_m: float) -> VO2maxEstimate:
    """
    Estimate VO2max from 12-minute Cooper test distance.

    Formula: VO2max = (distance_m - 504.9) / 44.73
    Reference: Cooper (1968) JAMA

    Args:
        distance_m: Total distance covered in 12 minutes (meters).

    Returns:
        VO2maxEstimate.
    """
    vo2max = (distance_m - 504.9) / 44.73
    vo2max = max(10.0, round(vo2max, 1))

    return VO2maxEstimate(
        vo2max=vo2max,
        method="Cooper 12-min test",
        fitness_category=classify_vo2max(vo2max),
        age_sex_percentile="Apply ACSM normative tables for age/sex-specific percentile",
        evidence="🟡 Moderate — Cooper (1968); SEE ±3.5 mL/kg/min vs. lab VO2max",
    )


def estimate_vo2max_hr_based(
    hr_rest: int,
    hr_max: int,
    age: int,
    sex: str = "male",
) -> VO2maxEstimate:
    """
    Estimate VO2max from resting + max heart rate.

    Uth et al. (2004) formula: VO2max ≈ 15.3 × (HRmax / HRrest)

    Args:
        hr_rest: Resting heart rate (bpm).
        hr_max: Maximum heart rate (bpm). If unknown, use predict_hr_max().
        age: Age in years.
        sex: 'male' or 'female'.

    Returns:
        VO2maxEstimate.
    """
    if hr_rest <= 0:
        hr_rest = 60
    vo2max = 15.3 * (hr_max / hr_rest)
    vo2max = round(vo2max, 1)

    return VO2maxEstimate(
        vo2max=vo2max,
        method=f"HR ratio (Uth et al. 2004) — HRmax={hr_max}, HRrest={hr_rest}",
        fitness_category=classify_vo2max(vo2max, sex),
        age_sex_percentile="Apply ACSM normative tables for age/sex-specific percentile",
        evidence="🟡 Moderate — Uth et al. (2004); SEE ±5 mL/kg/min; best for young active adults",
    )


def predict_hr_max(age: int, method: str = "tanaka") -> int:
    """
    Predict maximum heart rate.

    Methods:
    - tanaka: 208 - 0.7 × age (Tanaka et al. 2001, most accurate overall)
    - fox: 220 - age (traditional, less accurate)
    - gulati: 206 - 0.88 × age (Gulati et al. 2010, female-specific)

    Args:
        age: Age in years.
        method: Prediction formula to use.

    Returns:
        Predicted HRmax (bpm).
    """
    if method == "fox":
        return 220 - age
    elif method == "gulati":
        return round(206 - 0.88 * age)
    else:  # tanaka (default)
        return round(208 - 0.7 * age)


# ── Heart Rate Zones ─────────────────────────────────────────────────────────

@dataclass
class HRZone:
    zone: int
    name: str
    hr_low: int
    hr_high: int
    purpose: str
    typical_duration: str
    physiological_target: str


def calculate_hr_zones_karvonen(
    hr_rest: int,
    hr_max: int,
) -> list[HRZone]:
    """
    Calculate 5-zone HR model using Karvonen (Heart Rate Reserve) method.

    HRtarget = HRrest + intensity% × (HRmax - HRrest)

    Zone model based on Seiler (2010) 3-zone mapped to common 5-zone:
    - Zone 1: Recovery / Easy (50–60% HRR)
    - Zone 2: Aerobic Base (60–70% HRR)
    - Zone 3: Tempo / Threshold approach (70–80% HRR)
    - Zone 4: Threshold / VO2max (80–90% HRR)
    - Zone 5: Anaerobic / Max effort (90–100% HRR)

    Args:
        hr_rest: Resting heart rate (bpm).
        hr_max: Maximum heart rate (bpm).

    Returns:
        List of 5 HRZone objects.
    """
    hrr = hr_max - hr_rest

    def hr_at(pct: float) -> int:
        return round(hr_rest + pct * hrr)

    return [
        HRZone(
            zone=1, name="Recovery / Easy",
            hr_low=hr_at(0.50), hr_high=hr_at(0.60),
            purpose="Active recovery, warm-up, cool-down",
            typical_duration="30–90 min",
            physiological_target="Fat oxidation, capillary development, aerobic enzyme upregulation",
        ),
        HRZone(
            zone=2, name="Aerobic Base",
            hr_low=hr_at(0.60), hr_high=hr_at(0.70),
            purpose="Endurance foundation, long runs/rides",
            typical_duration="60–180+ min",
            physiological_target="Mitochondrial biogenesis, stroke volume adaptation, lactate clearance",
        ),
        HRZone(
            zone=3, name="Tempo",
            hr_low=hr_at(0.70), hr_high=hr_at(0.80),
            purpose="Sustained effort, marathon pace, sweetspot training",
            typical_duration="20–60 min continuous",
            physiological_target="Lactate threshold approach, carbohydrate metabolism, fatigue resistance",
        ),
        HRZone(
            zone=4, name="Threshold / VO2max",
            hr_low=hr_at(0.80), hr_high=hr_at(0.90),
            purpose="Threshold intervals, 10K-5K race effort",
            typical_duration="3–8 min intervals × 4–6 reps",
            physiological_target="Lactate threshold elevation, VO2max development, cardiac output",
        ),
        HRZone(
            zone=5, name="Anaerobic / Max",
            hr_low=hr_at(0.90), hr_high=hr_max,
            purpose="Short maximal efforts, sprint intervals",
            typical_duration="30s–2 min intervals × 4–8 reps",
            physiological_target="Anaerobic capacity, neuromuscular power, fast-twitch recruitment",
        ),
    ]


# ── Power Zones (Coggan/Allen Model) ────────────────────────────────────────

@dataclass
class PowerZone:
    zone: int
    name: str
    power_low: int     # watts
    power_high: int    # watts (0 = no ceiling)
    pct_ftp_low: float
    pct_ftp_high: float
    purpose: str
    typical_duration: str


def calculate_power_zones(ftp_watts: int) -> list[PowerZone]:
    """
    Calculate 7-zone power model based on Functional Threshold Power (FTP).

    Coggan/Allen model (Training and Racing with a Power Meter):
    - Zone 1: Active Recovery (<55% FTP)
    - Zone 2: Endurance (55–75% FTP)
    - Zone 3: Tempo (76–90% FTP)
    - Zone 4: Lactate Threshold (91–105% FTP)
    - Zone 5: VO2max (106–120% FTP)
    - Zone 6: Anaerobic Capacity (121–150% FTP)
    - Zone 7: Neuromuscular Power (>150% FTP)

    Args:
        ftp_watts: Functional Threshold Power in watts.

    Returns:
        List of 7 PowerZone objects.
    """
    def pwr(pct: float) -> int:
        return round(ftp_watts * pct)

    return [
        PowerZone(
            zone=1, name="Active Recovery",
            power_low=0, power_high=pwr(0.55),
            pct_ftp_low=0, pct_ftp_high=0.55,
            purpose="Recovery rides, warm-up, cool-down",
            typical_duration="30–90 min",
        ),
        PowerZone(
            zone=2, name="Endurance",
            power_low=pwr(0.55), power_high=pwr(0.75),
            pct_ftp_low=0.55, pct_ftp_high=0.75,
            purpose="Base training, long rides, fat oxidation",
            typical_duration="1–5+ hours",
        ),
        PowerZone(
            zone=3, name="Tempo",
            power_low=pwr(0.76), power_high=pwr(0.90),
            pct_ftp_low=0.76, pct_ftp_high=0.90,
            purpose="Sweetspot training, sustained efforts",
            typical_duration="20–60 min continuous",
        ),
        PowerZone(
            zone=4, name="Lactate Threshold",
            power_low=pwr(0.91), power_high=pwr(1.05),
            pct_ftp_low=0.91, pct_ftp_high=1.05,
            purpose="Threshold intervals, 40K TT effort",
            typical_duration="8–30 min intervals",
        ),
        PowerZone(
            zone=5, name="VO2max",
            power_low=pwr(1.06), power_high=pwr(1.20),
            pct_ftp_low=1.06, pct_ftp_high=1.20,
            purpose="VO2max development, 3–8 min power",
            typical_duration="3–8 min intervals × 3–6 reps",
        ),
        PowerZone(
            zone=6, name="Anaerobic Capacity",
            power_low=pwr(1.21), power_high=pwr(1.50),
            pct_ftp_low=1.21, pct_ftp_high=1.50,
            purpose="Anaerobic intervals, short sprints",
            typical_duration="30s–2 min × 4–8 reps",
        ),
        PowerZone(
            zone=7, name="Neuromuscular Power",
            power_low=pwr(1.50), power_high=0,
            pct_ftp_low=1.50, pct_ftp_high=0,
            purpose="Max sprints, jumps, neuromuscular recruitment",
            typical_duration="<30s, full recovery between",
        ),
    ]


# ── Running Pace Zones (Daniels' VDOT-inspired) ────────────────────────────

@dataclass
class PaceZone:
    zone: str
    name: str
    pace_min_per_km: float  # min/km (faster limit)
    pace_max_per_km: float  # min/km (slower limit)
    purpose: str
    typical_session: str


def calculate_pace_zones(vdot: float) -> list[PaceZone]:
    """
    Calculate running pace zones from VDOT score.

    Simplified Daniels model using VDOT-to-pace regression:
    - Easy: VDOT pace × 1.25–1.35
    - Marathon: VDOT pace × 1.10–1.15
    - Threshold: VDOT pace × 1.00–1.05
    - Interval: VDOT pace × 0.92–0.97
    - Repetition: VDOT pace × 0.85–0.90

    Approximate VDOT pace (min/km) = 133.0 / VDOT + 1.32
    (Regression approximation of Daniels' VDOT tables; ±10-15 sec/km at extremes)

    Args:
        vdot: VDOT score (typically 30–85 for recreational to elite).

    Returns:
        List of PaceZone objects.
    """
    # Base pace at threshold ~= reference pace derived from VDOT
    # Regression approximation of Daniels' VDOT tables (formula outputs):
    #   VDOT 30 → ~5:45, VDOT 40 → ~4:39, VDOT 50 → ~3:58,
    #   VDOT 60 → ~3:32, VDOT 70 → ~3:14, VDOT 80 → ~2:59
    # Note: Approximation; accuracy ±10-15 sec/km vs published tables at extremes
    base_pace = 133.0 / max(vdot, 20) + 1.32  # min/km at threshold

    def fmt_pace(p: float) -> float:
        return round(p, 2)

    return [
        PaceZone(
            zone="E", name="Easy",
            pace_min_per_km=fmt_pace(base_pace * 1.25),
            pace_max_per_km=fmt_pace(base_pace * 1.35),
            purpose="Aerobic development, recovery runs",
            typical_session="30–90 min easy running",
        ),
        PaceZone(
            zone="M", name="Marathon",
            pace_min_per_km=fmt_pace(base_pace * 1.10),
            pace_max_per_km=fmt_pace(base_pace * 1.15),
            purpose="Marathon-specific endurance",
            typical_session="10–20 km at marathon pace",
        ),
        PaceZone(
            zone="T", name="Threshold",
            pace_min_per_km=fmt_pace(base_pace * 1.00),
            pace_max_per_km=fmt_pace(base_pace * 1.05),
            purpose="Lactate threshold development, tempo runs",
            typical_session="20–40 min continuous or 5–10 min repeats",
        ),
        PaceZone(
            zone="I", name="Interval",
            pace_min_per_km=fmt_pace(base_pace * 0.92),
            pace_max_per_km=fmt_pace(base_pace * 0.97),
            purpose="VO2max development",
            typical_session="3–5 min repeats × 4–6, equal jog recovery",
        ),
        PaceZone(
            zone="R", name="Repetition",
            pace_min_per_km=fmt_pace(base_pace * 0.85),
            pace_max_per_km=fmt_pace(base_pace * 0.90),
            purpose="Speed, running economy, neuromuscular",
            typical_session="200–400m reps × 8–12, full recovery",
        ),
    ]


# ── Training Intensity Distribution ─────────────────────────────────────────

@dataclass
class IntensityDistribution:
    model: str                    # polarized / pyramidal / threshold
    zone_1_pct: float             # % of total training time in zone 1 (low)
    zone_2_pct: float             # zone 2 (moderate / threshold)
    zone_3_pct: float             # zone 3 (high intensity)
    description: str
    best_for: str
    evidence: str
    weekly_example: dict[str, str]


def recommend_intensity_distribution(
    sport: str = "endurance",
    level: str = "intermediate",
    phase: str = "base",
) -> IntensityDistribution:
    """
    Recommend training intensity distribution model.

    Three evidence-based models (Seiler 2010):

    1. Polarized (80/0/20): Most time easy, remainder hard. Skip the middle.
       Best for: Well-trained endurance athletes, 6+ training hours/week.
       Evidence: 🟢 Strong — Stöggl & Sperlich (2015) meta-analysis

    2. Pyramidal (75/15/10): Most easy, some moderate, less high intensity.
       Best for: Recreational athletes, general fitness, team sports.
       Evidence: 🟡 Moderate — Practical and sustainable

    3. Threshold (50/40/10): High proportion of moderate-intensity work.
       Best for: Time-limited athletes, sweetspot training philosophy.
       Evidence: 🟡 Moderate — Effective short-term; higher fatigue risk

    Args:
        sport: Sport type ('endurance', 'team_sport', 'strength', 'hybrid').
        level: 'beginner', 'intermediate', 'advanced', 'elite'.
        phase: Training phase ('base', 'build', 'peak', 'race', 'transition').

    Returns:
        IntensityDistribution with model recommendation.
    """
    # Default: pyramidal for most athletes
    if sport in ("endurance",) and level in ("advanced", "elite"):
        return IntensityDistribution(
            model="polarized",
            zone_1_pct=80,
            zone_2_pct=0,
            zone_3_pct=20,
            description=(
                "Polarized: ~80% of training at low intensity (Zone 1–2), ~20% at high intensity "
                "(Zone 4–5). Minimize time in 'moderate' Zone 3. This model produces the greatest "
                "improvements in well-trained endurance athletes."
            ),
            best_for="Well-trained endurance athletes training 6+ hours/week",
            evidence="🟢 Strong — Seiler (2010); Stöggl & Sperlich (2015); Muñoz et al. (2014)",
            weekly_example={
                "monday": "Rest or easy cross-training (Z1)",
                "tuesday": "High-intensity intervals: 5 × 4min Z4–5, 3min recovery",
                "wednesday": "Easy run/ride 60–90min (Z1–2)",
                "thursday": "Easy run/ride 45–60min (Z1–2)",
                "friday": "High-intensity intervals: 8 × 3min Z4–5, 3min recovery",
                "saturday": "Long easy run/ride 90–180min (Z1–2)",
                "sunday": "Easy recovery (Z1) or rest",
            },
        )

    elif sport == "strength" or (sport == "hybrid" and level in ("beginner", "intermediate")):
        return IntensityDistribution(
            model="threshold",
            zone_1_pct=50,
            zone_2_pct=40,
            zone_3_pct=10,
            description=(
                "Threshold/sweetspot: ~50% easy, ~40% at moderate intensity (Z3 — tempo/sweetspot), "
                "~10% high intensity. Time-efficient; good for concurrent training."
            ),
            best_for="Strength athletes with conditioning goals; time-limited athletes",
            evidence="🟡 Moderate — Effective for concurrent training; higher chronic fatigue risk",
            weekly_example={
                "monday": "Strength training + 20min Z2 conditioning",
                "tuesday": "30min sweetspot intervals (Z3)",
                "wednesday": "Strength training + easy cardio (Z1)",
                "thursday": "40min tempo (Z3)",
                "friday": "Strength training",
                "saturday": "HIIT session: 6 × 2min Z5 (Z1 recovery)",
                "sunday": "Rest or easy walk (Z1)",
            },
        )

    else:
        # Pyramidal — safe default for most athletes
        if phase in ("build", "peak", "race"):
            z1, z2, z3 = 70, 15, 15
        else:
            z1, z2, z3 = 80, 12, 8

        return IntensityDistribution(
            model="pyramidal",
            zone_1_pct=z1,
            zone_2_pct=z2,
            zone_3_pct=z3,
            description=(
                f"Pyramidal: ~{z1}% easy, ~{z2}% moderate, ~{z3}% high intensity. "
                f"Progressive volume with structured intensity. Sustainable and effective."
            ),
            best_for="Recreational to intermediate athletes; team sports; general fitness",
            evidence="🟡 Moderate — Practical, sustainable; matches most training plan structures",
            weekly_example={
                "monday": "Easy session (Z1–2)",
                "tuesday": "Tempo/threshold work (Z3)",
                "wednesday": "Easy session (Z1–2)",
                "thursday": "Moderate effort (Z2–3)",
                "friday": "Rest or easy (Z1)",
                "saturday": "Interval session: 4 × 5min Z4, 3min recovery",
                "sunday": "Long easy session (Z1–2)",
            },
        )


# ── Formatting ──────────────────────────────────────────────────────────────

def format_hr_zones(zones: list[HRZone]) -> str:
    """Format HR zones into a readable table."""
    lines = [
        "═══ Heart Rate Training Zones (Karvonen HRR) ═══",
        "",
        f"  {'Zone':<6} {'Name':<22} {'HR Range':<14} {'Purpose'}",
        f"  {'─'*6} {'─'*22} {'─'*14} {'─'*40}",
    ]
    for z in zones:
        lines.append(
            f"  Z{z.zone:<5} {z.name:<22} {z.hr_low}–{z.hr_high} bpm   {z.purpose}"
        )

    lines += [
        "",
        "Physiological targets:",
    ]
    for z in zones:
        lines.append(f"  Z{z.zone}: {z.physiological_target}")

    return "\n".join(lines)


def format_power_zones(zones: list[PowerZone]) -> str:
    """Format power zones into a readable table."""
    lines = [
        "═══ Power Training Zones (Coggan/Allen FTP Model) ═══",
        "",
        f"  {'Zone':<6} {'Name':<24} {'Power (W)':<14} {'%FTP':<12} {'Purpose'}",
        f"  {'─'*6} {'─'*24} {'─'*14} {'─'*12} {'─'*35}",
    ]
    for z in zones:
        high_str = f"{z.power_high}" if z.power_high > 0 else "Max"
        pct_high = f"{z.pct_ftp_high:.0%}" if z.pct_ftp_high > 0 else "Max"
        lines.append(
            f"  Z{z.zone:<5} {z.name:<24} {z.power_low}–{high_str:<8} "
            f"{z.pct_ftp_low:.0%}–{pct_high:<6} {z.purpose}"
        )

    return "\n".join(lines)


def format_pace_zones(zones: list[PaceZone]) -> str:
    """Format running pace zones into a readable table."""
    lines = [
        "═══ Running Pace Zones (Daniels' VDOT Model) ═══",
        "",
        f"  {'Zone':<4} {'Name':<14} {'Pace (min/km)':<16} {'Purpose'}",
        f"  {'─'*4} {'─'*14} {'─'*16} {'─'*40}",
    ]
    for z in zones:
        # Convert decimal min to mm:ss
        def to_mmss(m: float) -> str:
            mins = int(m)
            secs = int((m - mins) * 60)
            return f"{mins}:{secs:02d}"
        lines.append(
            f"  {z.zone:<4} {z.name:<14} {to_mmss(z.pace_min_per_km)}–{to_mmss(z.pace_max_per_km):<8} {z.purpose}"
        )

    lines += [
        "",
        "Session guidance:",
    ]
    for z in zones:
        lines.append(f"  {z.zone}: {z.typical_session}")

    return "\n".join(lines)


def format_intensity_distribution(dist: IntensityDistribution) -> str:
    """Format intensity distribution recommendation."""
    lines = [
        f"═══ Training Intensity Distribution: {dist.model.upper()} ═══",
        "",
        f"  Zone 1 (Low)      : {dist.zone_1_pct:.0f}%",
        f"  Zone 2 (Moderate) : {dist.zone_2_pct:.0f}%",
        f"  Zone 3 (High)     : {dist.zone_3_pct:.0f}%",
        "",
        f"  {dist.description}",
        "",
        f"  Best for: {dist.best_for}",
        f"  Evidence: {dist.evidence}",
        "",
        "  Weekly Example:",
    ]
    for day, session in dist.weekly_example.items():
        lines.append(f"    {day.title():<10}: {session}")

    return "\n".join(lines)
