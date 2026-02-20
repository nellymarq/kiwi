"""
Recovery analytics for Kiwi.

Evidence-based recovery metrics:
- HRV-based readiness scoring (parasympathetic proxy via rMSSD)
- Muscle damage estimation (DOMS severity proxy)
- Supercompensation window timing
- Deload trigger analysis (multi-factor)
- Recovery modality timing and evidence
- Muscle protein synthesis (MPS) optimization windows

References:
- Plews et al. (2013) Int J Sports Physiol Perform — HRV readiness
- Twist & Eston (2005) Sports Med — DOMS prediction model
- Bosquet et al. (2007) Med Sci Sports Exerc — supercompensation
- Meeusen et al. (2013) Med Sci Sports Exerc — overtraining consensus
- Dupuy et al. (2018) Front Physiol — recovery modality meta-analysis
- Trommelen & van Loon (2016) Nutrients — MPS timing
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ── HRV Readiness ─────────────────────────────────────────────────────────────

@dataclass
class HRVReading:
    rmssd: float        # ms — root mean square of successive differences (parasympathetic proxy)
    resting_hr: float   # bpm — morning resting heart rate
    date: date = field(default_factory=date.today)
    sdnn: Optional[float] = None  # ms — optional full HRV measure


@dataclass
class ReadinessScore:
    score: float          # 0–100
    category: str         # excellent / good / moderate / poor / very_poor
    hrv_trend: str        # rising / stable / declining / insufficient_data
    primary_factor: str   # what drove the score
    recommendations: list[str]
    evidence: str = "🟢 Strong"


# Rolling CV threshold for HRV instability (coefficient of variation > 10%)
_HRV_CV_INSTABILITY = 0.10

# Score thresholds
_READINESS_CATEGORIES = [
    (85, "excellent"),
    (70, "good"),
    (50, "moderate"),
    (30, "poor"),
    (0,  "very_poor"),
]


def compute_readiness(
    hrv_readings: list[HRVReading],
    tsb: Optional[float] = None,
    sleep_debt_hours: float = 0.0,
) -> ReadinessScore:
    """
    Compute a 0–100 readiness score from recent HRV readings.

    Algorithm:
    - Base HRV score: z-score of today's rMSSD relative to 7-day baseline
    - Trend adjustment: ±10 pts for rising/declining trend
    - TSB adjustment: -0.5 pts per unit below -20 (fatigue penalty)
    - Sleep debt penalty: -5 pts per hour of debt (up to -20)

    Args:
        hrv_readings: Chronological list (oldest→newest). Minimum 2 readings.
        tsb: Training Stress Balance (CTL - ATL). None = not available.
        sleep_debt_hours: Cumulative sleep debt (hours). Default 0.

    Returns:
        ReadinessScore with score, category, trend, and recommendations.
    """
    if not hrv_readings:
        return ReadinessScore(
            score=50.0,
            category="moderate",
            hrv_trend="insufficient_data",
            primary_factor="No HRV data provided",
            recommendations=["Measure HRV daily upon waking for at least 3 days to establish baseline."],
        )

    rmssd_values = [r.rmssd for r in hrv_readings]
    today_rmssd = rmssd_values[-1]

    # Need at least 3 readings for meaningful baseline
    if len(rmssd_values) < 3:
        baseline_mean = sum(rmssd_values) / len(rmssd_values)
        baseline_sd = 10.0  # conservative fallback SD (ms)
        trend = "insufficient_data"
    else:
        baseline = rmssd_values[:-1]  # all but today
        baseline_mean = sum(baseline) / len(baseline)
        baseline_sd = max(
            math.sqrt(sum((x - baseline_mean) ** 2 for x in baseline) / len(baseline)),
            5.0,  # floor SD at 5ms to avoid division problems
        )
        # Trend: compare last 3 readings
        recent = rmssd_values[-3:]
        if recent[-1] > recent[0] * 1.05:
            trend = "rising"
        elif recent[-1] < recent[0] * 0.95:
            trend = "declining"
        else:
            trend = "stable"

    # z-score normalized to 0–100 range (±3 SD = full range)
    z = (today_rmssd - baseline_mean) / baseline_sd
    base_score = 50.0 + (z * 16.67)  # ±3 SD → ±50 pts
    base_score = max(0.0, min(100.0, base_score))

    # Trend adjustment
    if trend == "rising":
        trend_adj = 10.0
    elif trend == "declining":
        trend_adj = -10.0
    elif trend == "insufficient_data":
        trend_adj = 0.0
    else:
        trend_adj = 0.0

    # TSB adjustment (fatigue penalty below -20)
    tsb_adj = 0.0
    if tsb is not None and tsb < -20:
        tsb_adj = max(-15.0, (tsb + 20) * 0.5)  # -0.5 per unit below -20, cap at -15

    # Sleep debt penalty
    sleep_adj = max(-20.0, -sleep_debt_hours * 5.0)

    score = max(0.0, min(100.0, base_score + trend_adj + tsb_adj + sleep_adj))

    # Determine primary factor
    factors = {
        "HRV deviation": abs(z) * 16.67,
        "Training stress (TSB)": abs(tsb_adj),
        "Sleep debt": abs(sleep_adj),
    }
    primary_factor = max(factors, key=factors.get)

    # Category
    category = "very_poor"
    for threshold, cat in _READINESS_CATEGORIES:
        if score >= threshold:
            category = cat
            break

    # Recommendations
    recs = []
    if score >= 85:
        recs.append("Excellent recovery — optimal day for high-intensity training or competition.")
    elif score >= 70:
        recs.append("Good readiness — proceed with planned session at full intensity.")
    elif score >= 50:
        recs.append("Moderate readiness — consider reducing volume by 10–20% or moving high-intensity work.")
        if tsb is not None and tsb < -20:
            recs.append(f"Training stress accumulation (TSB={tsb:.0f}) is elevated — prioritize recovery.")
    elif score >= 30:
        recs.append("Poor readiness — substitute with low-intensity aerobic work or active recovery.")
        recs.append("Investigate sleep, nutrition, and hydration status.")
    else:
        recs.append("Very poor readiness — consider full rest day or light yoga/mobility only.")
        recs.append("If <30 score persists >3 days, evaluate for overreaching or illness.")

    if sleep_debt_hours >= 2:
        recs.append(f"Sleep debt of {sleep_debt_hours:.1f}h detected — prioritize sleep over extra training volume.")
    if trend == "declining":
        recs.append("HRV trend declining — progressive fatigue accumulation. Plan a deload within 1–2 weeks.")

    return ReadinessScore(
        score=round(score, 1),
        category=category,
        hrv_trend=trend,
        primary_factor=primary_factor,
        recommendations=recs,
    )


def format_readiness_report(r: ReadinessScore) -> str:
    """Human-readable readiness report."""
    bar_filled = int(r.score / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    lines = [
        f"Readiness Score: {r.score:.0f}/100  [{bar}]",
        f"Category: {r.category.upper().replace('_', ' ')}",
        f"HRV Trend: {r.hrv_trend.replace('_', ' ')}",
        f"Primary Factor: {r.primary_factor}",
        "",
        "Recommendations:",
    ]
    for rec in r.recommendations:
        lines.append(f"  • {rec}")
    return "\n".join(lines)


# ── DOMS / Muscle Damage Estimation ───────────────────────────────────────────

# (session_type → eccentric demand coefficient 0–1)
EXERCISE_DAMAGE_COEFFICIENTS: dict[str, float] = {
    "strength_eccentric_heavy":  0.90,  # slow eccentric, high load (e.g., Romanian DL)
    "strength_eccentric_moderate": 0.65,
    "plyometrics":               0.80,  # stretch-shortening cycle
    "downhill_running":          0.75,
    "running_new":               0.60,  # novel stimulus
    "strength_concentric":       0.25,  # sled pushes, concentric-only
    "isometric":                 0.15,
    "cycling":                   0.20,
    "swimming":                  0.10,
    "yoga_mobility":             0.05,
    "aerobic_easy":              0.10,
    "team_sport":                0.50,  # mixed modality
    "strength_moderate":         0.45,
}

TRAINED_STATUS_MODIFIERS = {
    "untrained":    1.4,
    "recreational": 1.1,
    "trained":      0.8,
    "elite":        0.6,
}


@dataclass
class DOMSEstimate:
    severity: str       # none / mild / moderate / severe
    severity_score: float  # 0–10
    peak_hours: int     # hours post-exercise when DOMS peaks
    resolution_hours: int  # hours until expected resolution
    primary_mechanism: str
    notes: list[str]
    evidence: str = "🟡 Moderate"


def estimate_doms(
    session_type: str,
    rpe: float,
    duration_min: int,
    trained_status: str = "trained",
) -> DOMSEstimate:
    """
    Estimate DOMS severity and timing based on session characteristics.

    Based on Twist & Eston (2005) DOMS prediction framework:
    DOMS_score = eccentric_coefficient × RPE_factor × duration_factor × training_status_modifier

    Args:
        session_type: Key from EXERCISE_DAMAGE_COEFFICIENTS.
        rpe: Session RPE (1–10 scale).
        duration_min: Session duration in minutes.
        trained_status: 'untrained' / 'recreational' / 'trained' / 'elite'.

    Returns:
        DOMSEstimate with severity, peak timing, and resolution window.
    """
    ecc_coef = EXERCISE_DAMAGE_COEFFICIENTS.get(session_type.lower().replace(" ", "_"), 0.40)
    rpe_factor = (rpe / 10.0) ** 1.2  # superlinear RPE effect
    duration_factor = min(1.0, duration_min / 60.0)  # normalized to 60-min session
    status_mod = TRAINED_STATUS_MODIFIERS.get(trained_status.lower(), 1.0)

    raw_score = ecc_coef * rpe_factor * duration_factor * status_mod * 10.0
    severity_score = min(10.0, round(raw_score, 1))

    if severity_score < 1.5:
        severity = "none"
        peak_hours = 24
        resolution_hours = 24
        mechanism = "Minimal mechanical disruption"
    elif severity_score < 4.0:
        severity = "mild"
        peak_hours = 24
        resolution_hours = 48
        mechanism = "Minor myofibrillar disruption + local inflammatory response"
    elif severity_score < 7.0:
        severity = "moderate"
        peak_hours = 48
        resolution_hours = 72
        mechanism = "Sarcomeric Z-band disruption, satellite cell activation, IL-6/IL-8 elevation"
    else:
        severity = "severe"
        peak_hours = 48
        resolution_hours = 96
        mechanism = "Significant myofibrillar damage, prolonged inflammatory cascade, CK elevation"

    notes = []
    if severity_score >= 5:
        notes.append(f"Peak soreness expected ~{peak_hours}h post-session.")
        notes.append("Avoid high-load eccentric work for the same muscle groups until resolved.")
    if trained_status in ("untrained", "recreational"):
        notes.append("Repeated bout effect: subsequent sessions will produce ~40% less DOMS.")
    if severity == "severe":
        notes.append("Monitor for rhabdomyolysis signs: dark urine, extreme weakness — seek medical attention.")

    return DOMSEstimate(
        severity=severity,
        severity_score=severity_score,
        peak_hours=peak_hours,
        resolution_hours=resolution_hours,
        primary_mechanism=mechanism,
        notes=notes,
    )


# ── Supercompensation Window ───────────────────────────────────────────────────

SUPERCOMPENSATION_PROFILES: dict[str, dict] = {
    # session_type → timing windows in hours from session end
    "strength": {
        "fatigue_phase":       (0, 24),    # performance below baseline
        "recovery_phase":      (24, 72),   # return to baseline
        "supercomp_phase":     (72, 120),  # performance peak above baseline
        "detraining_phase":    (120, 240), # adaptation fades without new stimulus
        "next_session_window": (72, 96),   # optimal stimulus timing
    },
    "endurance": {
        "fatigue_phase":       (0, 12),
        "recovery_phase":      (12, 36),
        "supercomp_phase":     (36, 72),
        "detraining_phase":    (72, 168),
        "next_session_window": (36, 60),
    },
    "high_intensity_interval": {
        "fatigue_phase":       (0, 24),
        "recovery_phase":      (24, 48),
        "supercomp_phase":     (48, 96),
        "detraining_phase":    (96, 192),
        "next_session_window": (48, 72),
    },
    "team_sport": {
        "fatigue_phase":       (0, 24),
        "recovery_phase":      (24, 60),
        "supercomp_phase":     (60, 96),
        "detraining_phase":    (96, 192),
        "next_session_window": (60, 84),
    },
}


def supercompensation_window(
    session_type: str,
    session_end_datetime_hours_ago: float = 0,
) -> dict:
    """
    Return supercompensation phase timing for a given session type.

    Args:
        session_type: 'strength' / 'endurance' / 'high_intensity_interval' / 'team_sport'.
        session_end_datetime_hours_ago: Hours elapsed since session ended (0 = just finished).

    Returns:
        Dict with all phase windows, current phase, and hours until supercompensation peak.
    """
    profile = SUPERCOMPENSATION_PROFILES.get(session_type, SUPERCOMPENSATION_PROFILES["strength"])
    elapsed = session_end_datetime_hours_ago

    # Determine current phase
    current_phase = "detraining_phase"
    for phase_name, (start, end) in profile.items():
        if phase_name == "next_session_window":
            continue
        if start <= elapsed < end:
            current_phase = phase_name
            break

    sc_start, sc_end = profile["supercomp_phase"]
    if elapsed < sc_start:
        hours_to_peak = sc_start + (sc_end - sc_start) / 2 - elapsed
    elif elapsed < sc_end:
        hours_to_peak = 0  # currently in supercomp window
    else:
        hours_to_peak = None  # window passed

    return {
        "session_type": session_type,
        "phases": profile,
        "current_phase": current_phase,
        "hours_elapsed": elapsed,
        "hours_to_supercomp_peak": hours_to_peak,
        "optimal_next_session_window_hours": profile["next_session_window"],
        "evidence": "🟡 Moderate — Supercompensation timing extrapolated from Bosquet et al. 2007",
    }


# ── Deload Trigger Analysis ────────────────────────────────────────────────────

@dataclass
class DeloadAssessment:
    should_deload: bool
    urgency: str        # immediate / soon / optional / not_needed
    primary_trigger: str
    triggered_by: list[str]
    deload_type: str    # volume / intensity / complete / none
    duration_weeks: int
    deload_guidance: list[str]
    evidence: str = "🟢 Strong"


def assess_deload_need(
    tsb: Optional[float] = None,
    consecutive_hard_days: int = 0,
    weeks_since_deload: int = 0,
    sleep_debt_hours: float = 0.0,
    subjective_fatigue: Optional[int] = None,  # 1–10
    rpe_drift: Optional[float] = None,  # RPE increase for same load (%); positive = harder
    performance_decline_pct: Optional[float] = None,  # % drop from personal best/norm
) -> DeloadAssessment:
    """
    Multi-factor deload trigger analysis.

    Triggers (Meeusen et al. 2013 consensus + practitioner guidelines):
    - TSB ≤ -30: high fatigue accumulation → deload urgency
    - Consecutive hard days ≥ 5: structural stress
    - Weeks without deload ≥ 4: standard periodization marker
    - Sleep debt ≥ 4h: recovery capacity compromised
    - Subjective fatigue ≥ 8: athlete self-report (valid predictor)
    - RPE drift ≥ 15%: same load feels harder → accumulated fatigue
    - Performance decline ≥ 5%: functional overreaching indicator

    Args:
        tsb: Training Stress Balance (CTL - ATL). Negative = fatigued.
        consecutive_hard_days: Days in a row of RPE ≥ 7 training.
        weeks_since_deload: Training blocks since last structured deload.
        sleep_debt_hours: Cumulative sleep debt (hours).
        subjective_fatigue: Athlete fatigue rating 1–10.
        rpe_drift: % RPE increase at same absolute load. Positive = more effortful.
        performance_decline_pct: % drop in performance vs. recent norm.

    Returns:
        DeloadAssessment with urgency level, type recommendation, and guidance.
    """
    triggers: list[tuple[str, int]] = []  # (description, severity 1-3)

    if tsb is not None:
        if tsb <= -40:
            triggers.append(("TSB ≤ -40 (severe fatigue accumulation)", 3))
        elif tsb <= -30:
            triggers.append(("TSB ≤ -30 (high fatigue accumulation)", 2))
        elif tsb <= -20:
            triggers.append(("TSB -20 to -30 (moderate fatigue)", 1))

    if consecutive_hard_days >= 7:
        triggers.append((f"{consecutive_hard_days} consecutive hard training days", 3))
    elif consecutive_hard_days >= 5:
        triggers.append((f"{consecutive_hard_days} consecutive hard training days", 2))
    elif consecutive_hard_days >= 3:
        triggers.append((f"{consecutive_hard_days} consecutive hard training days", 1))

    if weeks_since_deload >= 6:
        triggers.append((f"{weeks_since_deload} weeks without structured deload (overdue)", 2))
    elif weeks_since_deload >= 4:
        triggers.append((f"{weeks_since_deload} weeks without structured deload", 1))

    if sleep_debt_hours >= 6:
        triggers.append((f"{sleep_debt_hours:.1f}h cumulative sleep debt (severe)", 3))
    elif sleep_debt_hours >= 4:
        triggers.append((f"{sleep_debt_hours:.1f}h cumulative sleep debt", 2))
    elif sleep_debt_hours >= 2:
        triggers.append((f"{sleep_debt_hours:.1f}h cumulative sleep debt", 1))

    if subjective_fatigue is not None:
        if subjective_fatigue >= 9:
            triggers.append((f"Subjective fatigue {subjective_fatigue}/10 (severe)", 3))
        elif subjective_fatigue >= 8:
            triggers.append((f"Subjective fatigue {subjective_fatigue}/10 (high)", 2))
        elif subjective_fatigue >= 7:
            triggers.append((f"Subjective fatigue {subjective_fatigue}/10 (moderate)", 1))

    if rpe_drift is not None and rpe_drift >= 15:
        triggers.append((f"RPE drift +{rpe_drift:.0f}% at same load (accumulated fatigue)", 2))
    elif rpe_drift is not None and rpe_drift >= 10:
        triggers.append((f"RPE drift +{rpe_drift:.0f}% at same load", 1))

    if performance_decline_pct is not None and performance_decline_pct >= 10:
        triggers.append((f"Performance decline {performance_decline_pct:.0f}% (functional overreaching)", 3))
    elif performance_decline_pct is not None and performance_decline_pct >= 5:
        triggers.append((f"Performance decline {performance_decline_pct:.0f}%", 2))

    max_severity = max((s for _, s in triggers), default=0)
    trigger_descriptions = [d for d, _ in triggers]

    if max_severity == 0:
        return DeloadAssessment(
            should_deload=False,
            urgency="not_needed",
            primary_trigger="No deload triggers detected",
            triggered_by=[],
            deload_type="none",
            duration_weeks=0,
            deload_guidance=["Continue planned training. Schedule a preventive deload every 4 weeks."],
        )

    if max_severity == 3 or len(triggers) >= 4:
        urgency = "immediate"
        deload_type = "complete" if max_severity == 3 and len(triggers) >= 3 else "volume"
        duration = 1
    elif max_severity == 2 or len(triggers) >= 2:
        urgency = "soon"
        deload_type = "volume"
        duration = 1
    else:
        urgency = "optional"
        deload_type = "intensity"
        duration = 1

    primary = triggers[0][0] if triggers else "multiple factors"

    guidance = []
    if deload_type == "complete":
        guidance.append("Complete deload: reduce volume by 50–60% AND intensity by 20–30%.")
        guidance.append("Focus on movement quality, mobility, and low-intensity aerobics.")
    elif deload_type == "volume":
        guidance.append("Volume deload: reduce total weekly volume by 40–50%, maintain intensity.")
        guidance.append("Keep 1 high-intensity session to maintain neural adaptations.")
    else:
        guidance.append("Intensity deload: reduce RPE targets by 1–2 points, maintain volume.")

    guidance.append("Prioritize sleep (8–9h), protein intake (1.8–2.2g/kg), and hydration.")
    if urgency == "immediate":
        guidance.append("Do not add new training stressors this week. Reassess HRV daily.")

    return DeloadAssessment(
        should_deload=True,
        urgency=urgency,
        primary_trigger=primary,
        triggered_by=trigger_descriptions,
        deload_type=deload_type,
        duration_weeks=duration,
        deload_guidance=guidance,
    )


# ── Recovery Modalities ────────────────────────────────────────────────────────

RECOVERY_MODALITIES: dict[str, dict] = {
    "cold_water_immersion": {
        "also_known_as": "CWI, ice bath",
        "primary_benefit": "Acute soreness reduction, inflammation management",
        "mechanism": "Vasoconstriction reduces edema; hydrostatic pressure reduces swelling",
        "protocol": "11–15°C for 10–15 min within 60 min post-exercise",
        "best_for": ["Acute DOMS relief", "Multi-day competition", "Core temperature reduction"],
        "cautions": ["Blunts hypertrophy adaptations if used after strength training",
                     "Avoid chronic use in strength/power athletes during adaptation phase"],
        "timing": "0–60 min post-exercise",
        "frequency": "As needed; avoid after strength sessions targeting hypertrophy",
        "evidence": "🟢 Strong for pain; 🟡 Moderate for performance; 🟠 Weak for adaptation cost",
    },
    "contrast_water_therapy": {
        "also_known_as": "CWT, contrast therapy",
        "primary_benefit": "Perceived recovery, muscle function restoration",
        "mechanism": "Alternating vasoconstriction/vasodilation creates 'pumping' effect",
        "protocol": "1 min cold (11–15°C) / 2–3 min hot (38–42°C), repeat 3–4×",
        "best_for": ["Multi-day events", "Team sports recovery", "General soreness"],
        "cautions": ["Less evidence than CWI alone for acute outcomes"],
        "timing": "30–120 min post-exercise",
        "frequency": "1–2× per day during high training loads",
        "evidence": "🟡 Moderate",
    },
    "active_recovery": {
        "also_known_as": "Low-intensity aerobic, flush session",
        "primary_benefit": "Lactate clearance, maintained blood flow, psychological recovery",
        "mechanism": "Low-intensity contraction maintains capillary perfusion; lactate oxidation",
        "protocol": "20–30 min at <60% HRmax or RPE ≤3",
        "best_for": ["Between training days", "Post-competition", "Lactate clearance"],
        "cautions": ["Keep intensity genuinely low — 'active recovery' at RPE >4 is just more training"],
        "timing": "0–24h post hard session",
        "frequency": "1–2× per week or on rest days",
        "evidence": "🟢 Strong for lactate clearance; 🟡 Moderate for DOMS",
    },
    "sleep_extension": {
        "also_known_as": "Napping, sleep banking",
        "primary_benefit": "GH release, MPS, cognitive restoration, HRV recovery",
        "mechanism": "SWS: GH pulse, testosterone, cytokine resolution; REM: motor learning consolidation",
        "protocol": "Extend nightly sleep to 9–10h or 20–30 min naps (avoid >45 min pre-event)",
        "best_for": ["Accumulated sleep debt", "Performance optimization", "Post-competition"],
        "cautions": ["Naps >45 min can impair alertness via SWS inertia; avoid within 6h of bedtime"],
        "timing": "Nap before 3 PM to preserve nocturnal sleep",
        "frequency": "Daily napping beneficial during high training loads",
        "evidence": "🟢 Strong",
    },
    "compression_garments": {
        "also_known_as": "Compression tights, sleeves",
        "primary_benefit": "Perceived muscle soreness reduction, edema management",
        "mechanism": "Graduated pressure reduces interstitial fluid accumulation",
        "protocol": "Wear for 12–24h post-exercise; ≥18 mmHg for therapeutic effect",
        "best_for": ["Travel recovery", "Post-competition soreness", "Lower limb swelling"],
        "cautions": ["Small effect sizes in most RCTs; comfort and compliance often the limiting factor"],
        "timing": "Immediately post-exercise through recovery period",
        "frequency": "As needed",
        "evidence": "🟡 Moderate",
    },
    "massage": {
        "also_known_as": "Sports massage, myofascial release",
        "primary_benefit": "DOMS reduction, perceived recovery, parasympathetic activation",
        "mechanism": "Mechanotransduction: reduces inflammatory cytokines (IL-6, TNF-α), increases PGC-1α",
        "protocol": "30–45 min within 2h post-exercise or 24h later",
        "best_for": ["DOMS management", "Pre-event preparation (lighter), psychological relaxation"],
        "cautions": ["Deep tissue massage immediately post-exercise may transiently increase soreness"],
        "timing": "0–2h or 24–48h post-exercise",
        "frequency": "1–2× per week during heavy training",
        "evidence": "🟡 Moderate — Dupuy et al. 2018 meta-analysis",
    },
    "heat_therapy": {
        "also_known_as": "Sauna, hot bath, infrared",
        "primary_benefit": "Parasympathetic recovery, heat shock protein induction, plasma volume expansion",
        "mechanism": "HSP70 upregulation, plasma volume expansion (+10–12%), opioid-mediated relaxation",
        "protocol": "Traditional sauna: 80–100°C for 15–20 min; infrared: 50–60°C for 30 min",
        "best_for": ["Endurance athletes (plasma volume)", "Parasympathetic recovery", "Late-day stress relief"],
        "cautions": ["Do not use within 24h of competition; ensure hydration (500–750ml fluid replacement)",
                     "Avoid if core temperature already elevated post-exercise"],
        "timing": "≥2–3h post hard session; pre-sleep timing supports sleep onset",
        "frequency": "3–4× per week for cardiovascular adaptation; 1–2× for recovery",
        "evidence": "🟡 Moderate for recovery; 🟢 Strong for plasma volume (endurance)",
    },
    "foam_rolling": {
        "also_known_as": "SMR, self-myofascial release",
        "primary_benefit": "Acute flexibility increase, DOMS attenuation, ROM restoration",
        "mechanism": "Golgi tendon organ inhibition, intrafascial smooth muscle relaxation",
        "protocol": "30–90 sec per muscle group; slow controlled pressure; pre- or post-exercise",
        "best_for": ["Pre-exercise warm-up flexibility", "Post-exercise soreness", "Daily maintenance"],
        "cautions": ["Avoid rolling directly over joints or areas of acute injury"],
        "timing": "Pre-exercise: 60–120 sec; post-exercise: 30–60 sec",
        "frequency": "Daily or as needed",
        "evidence": "🟡 Moderate for ROM and acute soreness; 🔵 Emerging for structural adaptation",
    },
}


def recovery_modality_guide(goal: str = "general", post_session_type: str = "strength") -> str:
    """
    Return evidence-ranked recovery modality recommendations for a given goal.

    Args:
        goal: 'soreness' / 'performance' / 'adaptation' / 'general'
        post_session_type: 'strength' / 'endurance' / 'competition' / 'general'

    Returns:
        Formatted string with prioritized modality recommendations.
    """
    # Priority ordering per goal
    goal_priorities: dict[str, list[str]] = {
        "soreness": [
            "sleep_extension", "massage", "cold_water_immersion",
            "compression_garments", "active_recovery", "foam_rolling"
        ],
        "performance": [
            "sleep_extension", "active_recovery", "cold_water_immersion",
            "contrast_water_therapy", "heat_therapy", "compression_garments"
        ],
        "adaptation": [
            "sleep_extension", "active_recovery", "heat_therapy",
            "foam_rolling", "massage"
            # Note: CWI intentionally lower priority — blunts hypertrophy
        ],
        "general": list(RECOVERY_MODALITIES.keys()),
    }

    priority = goal_priorities.get(goal, goal_priorities["general"])

    # Warn if strength adaptation + CWI
    adaptation_warning = ""
    if post_session_type == "strength" and goal in ("adaptation", "general"):
        adaptation_warning = (
            "\n⚠️  Cold water immersion after strength training blunts "
            "hypertrophy adaptations (Roberts et al. 2015 JPhysiol). "
            "Avoid CWI for 24–48h post strength sessions targeting muscle growth.\n"
        )

    lines = [
        f"Recovery Modalities — Goal: {goal.title()} | Post: {post_session_type.replace('_', ' ').title()}",
        adaptation_warning,
        "─" * 60,
    ]

    for i, key in enumerate(priority, 1):
        if key not in RECOVERY_MODALITIES:
            continue
        mod = RECOVERY_MODALITIES[key]
        lines.append(
            f"\n{i}. {key.replace('_', ' ').title()} ({mod['also_known_as']})"
        )
        lines.append(f"   Protocol : {mod['protocol']}")
        lines.append(f"   Timing   : {mod['timing']}")
        lines.append(f"   Evidence : {mod['evidence']}")
        lines.append(f"   Best for : {', '.join(mod['best_for'][:2])}")

    return "\n".join(lines)


# ── MPS Optimization Windows ───────────────────────────────────────────────────

MPS_WINDOWS: dict[str, dict] = {
    "immediate_post_exercise": {
        "window": "0–60 min post-resistance exercise",
        "priority": "HIGH",
        "protein_target_g": "0.4–0.55g/kg body weight (leucine-rich source)",
        "leucine_threshold": "≥2.5–3g leucine to maximally stimulate MPS",
        "optimal_sources": ["Whey protein (fastest leucine delivery)", "Whole eggs", "Milk"],
        "mechanism": "mTORC1 activation amplified by mechanical stress; AMPK-independent window",
        "evidence": "🟢 Strong — Witard et al. 2014 AJCN, Moore et al. 2009 AJCN",
    },
    "pre_sleep": {
        "window": "30–60 min before sleep",
        "priority": "HIGH",
        "protein_target_g": "30–40g slow-digesting protein",
        "leucine_threshold": "≥2g leucine",
        "optimal_sources": ["Casein protein", "Cottage cheese", "Greek yogurt"],
        "mechanism": "Nocturnal MPS supported by sustained aminoacidemia during overnight fast",
        "evidence": "🟢 Strong — Res et al. 2012 Med Sci Sports Exerc, Trommelen & van Loon 2016",
    },
    "between_sessions": {
        "window": "Every 3–5h throughout the day",
        "priority": "MODERATE",
        "protein_target_g": "0.4g/kg per meal (aim for 4 meals)",
        "leucine_threshold": "≥2–2.5g leucine per meal",
        "optimal_sources": ["Any complete protein source", "Varied diet preferred"],
        "mechanism": "Muscle full effect — MPS refractory period of ~90 min; distribution matters",
        "evidence": "🟢 Strong — Areta et al. 2013 J Physiol",
    },
    "pre_exercise_carbohydrate": {
        "window": "1–4h pre-exercise",
        "priority": "MODERATE",
        "carbohydrate_target_g": "1–4g/kg depending on timing and intensity",
        "notes": "Larger dose (4g/kg) with longer timing (4h); smaller (1–2g/kg) with shorter window (1h)",
        "mechanism": "Glycogen loading maintains high-intensity performance; spares endogenous protein",
        "evidence": "🟢 Strong — Burke et al. 2011 J Sports Sci",
    },
    "intra_exercise": {
        "window": "During sessions >60 min",
        "priority": "HIGH for endurance",
        "carbohydrate_target_g": "30–60g/h for <2.5h; up to 90g/h (2:1 glucose:fructose) for >2.5h",
        "protein_target_g": "Consider 20–30g/h for sessions >3h to reduce BCAA oxidation",
        "mechanism": "Maintains blood glucose, spares glycogen, reduces cortisol spike",
        "evidence": "🟢 Strong",
    },
}


def mps_timing_guide(body_weight_kg: float = 75.0) -> str:
    """Return personalized MPS optimization timing guide."""
    lines = [
        f"MPS Optimization Guide (Body Weight: {body_weight_kg:.0f} kg)",
        "=" * 55,
        "",
    ]

    for window_name, w in MPS_WINDOWS.items():
        lines.append(f"▸ {window_name.replace('_', ' ').title()}")
        lines.append(f"  Window  : {w['window']}")
        lines.append(f"  Priority: {w['priority']}")
        if "protein_target_g" in w:
            target = w["protein_target_g"]
            # Personalize g/kg targets
            if "g/kg" in target:
                try:
                    coef = float(target.split("g/kg")[0].strip().split()[-1])
                    grams = coef * body_weight_kg
                    target = f"{grams:.0f}g ({target})"
                except (ValueError, IndexError):
                    pass
            lines.append(f"  Protein : {target}")
        if "carbohydrate_target_g" in w:
            lines.append(f"  Carbs   : {w['carbohydrate_target_g']}")
        if "optimal_sources" in w:
            lines.append(f"  Sources : {', '.join(w['optimal_sources'][:2])}")
        lines.append(f"  Evidence: {w['evidence']}")
        lines.append("")

    return "\n".join(lines)
