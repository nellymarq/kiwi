"""
Sleep Optimizer — chronotype analysis, sleep staging, and performance recovery.

Evidence base:
  Walker 2017 — "Why We Sleep" (🟡 popular synthesis, select RCT data)
  Roenneberg et al. 2003 — Munich Chronotype Questionnaire (🟢)
  Buysse et al. 1989 — Pittsburgh Sleep Quality Index (🟢 validated)
  Dement & Kleitman 1957 — REM/NREM cycles (🟢 foundational)
  Fullagar et al. 2015 — Sleep and athlete performance (🟢 review)
  Mah et al. 2011 — Sleep extension in basketball players (🟡 RCT)
  Samuels 2012 — Sleep, recovery, and performance in athletes (🟡)

Covers:
- Chronotype classification (lion/bear/wolf/dolphin + MSFsc)
- Sleep cycle calculator (REM optimization timing)
- Sleep debt tracker
- Athlete sleep recommendations by sport/training phase
- Hormonal sleep window (GH pulse, melatonin, cortisol)
- Caffeine clearance calculator (CYP1A2 aware)
- Pre-sleep protocol generator
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import time, timedelta
from typing import Literal, Optional


# ── Chronotypes ────────────────────────────────────────────────────────────────

Chronotype = Literal["lion", "bear", "wolf", "dolphin"]

CHRONOTYPE_PROFILES = {
    "lion": {
        "label": "Lion (Morning Type)",
        "sleep_window": ("21:30", "05:30"),
        "peak_alertness": ("08:00", "12:00"),
        "peak_physical": ("10:00", "14:00"),
        "description": "Natural early riser. Peak alertness mid-morning. Fades after dinner.",
        "prevalence_pct": 15,
        "morningness_score": "Extreme morning (MEQ > 70)",
        "athlete_notes": "Best suited for morning training. Avoid evening competitions when possible.",
    },
    "bear": {
        "label": "Bear (Intermediate)",
        "sleep_window": ("23:00", "07:00"),
        "peak_alertness": ("10:00", "14:00"),
        "peak_physical": ("14:00", "18:00"),
        "description": "Solar-anchored. Follows the sun. The most common chronotype.",
        "prevalence_pct": 55,
        "morningness_score": "Intermediate (MEQ 42–58)",
        "athlete_notes": "Afternoon training is optimal. Evening events good if well-managed.",
    },
    "wolf": {
        "label": "Wolf (Evening Type)",
        "sleep_window": ("00:30", "08:30"),
        "peak_alertness": ("13:00", "21:00"),
        "peak_physical": ("17:00", "21:00"),
        "description": "Natural night owl. Sluggish mornings. Peaks late afternoon/evening.",
        "prevalence_pct": 15,
        "morningness_score": "Evening type (MEQ < 42)",
        "athlete_notes": "Evening training is ideal. Morning competitions require strategic light exposure.",
    },
    "dolphin": {
        "label": "Dolphin (Light Sleeper)",
        "sleep_window": ("23:30", "06:30"),
        "peak_alertness": ("10:00", "14:00"),
        "peak_physical": ("15:00", "17:00"),
        "description": "Light, restless sleeper. Wakes easily. Often high-functioning anxiety pattern.",
        "prevalence_pct": 10,
        "morningness_score": "Variable (irregular MEQ)",
        "athlete_notes": "Sleep quality more critical than quantity. Strict wind-down routine essential.",
    },
}

# Morningness-Eveningness Questionnaire (MEQ) thresholds
MEQ_THRESHOLDS = [
    (70, 86, "lion"),
    (59, 69, "lion"),    # Moderate morning
    (42, 58, "bear"),    # Intermediate
    (31, 41, "wolf"),    # Moderate evening
    (16, 30, "wolf"),    # Definite evening type
]


# ── Sleep Cycle Science ────────────────────────────────────────────────────────

SLEEP_CYCLE_MINUTES = 90     # One full NREM + REM cycle
SLEEP_ONSET_MINUTES = 15     # Average time to fall asleep
MIN_CYCLES_FOR_RECOVERY = 5  # 5 cycles = 7.5 hours (optimal for most athletes)
MAX_CYCLES_STANDARD = 6      # 6 cycles = 9 hours


@dataclass
class SleepCycleResult:
    """Optimal sleep/wake times based on cycle completion."""
    sleep_time: str          # Bedtime
    wake_times: list[str]    # 4–6 cycle-aligned wake times
    optimal_wake: str        # Best wake time for recovery
    notes: str = ""

    def display(self) -> str:
        lines = [
            f"  Bedtime: {self.sleep_time}  (lights out → fall asleep in ~15min)",
            "",
            "  Wake time options (by complete sleep cycles):",
        ]
        cycle_count = 4
        for t in self.wake_times:
            cycles = cycle_count
            hours = cycles * 90 / 60
            marker = " ← OPTIMAL" if t == self.optimal_wake else ""
            lines.append(f"    {t}  ({cycles} cycles, {hours:.1f}h){marker}")
            cycle_count += 1
        if self.notes:
            lines.append(f"\n  Note: {self.notes}")
        return "\n".join(lines)


# ── Caffeine Clearance ────────────────────────────────────────────────────────

@dataclass
class CaffeineStatus:
    """Caffeine blood level at a given time post-consumption."""
    dose_mg: float
    hours_elapsed: float
    half_life_hours: float
    remaining_mg: float
    pct_remaining: float
    sleep_safe: bool        # < 25mg remaining
    recommendation: str

    def display(self) -> str:
        icon = "✅" if self.sleep_safe else "⚠️"
        return (
            f"  {icon} Dose: {self.dose_mg:.0f}mg caffeine\n"
            f"  Hours elapsed: {self.hours_elapsed:.1f}h\n"
            f"  Half-life used: {self.half_life_hours:.1f}h "
            f"({'fast CYP1A2' if self.half_life_hours <= 4.5 else 'slow CYP1A2'})\n"
            f"  Remaining: {self.remaining_mg:.1f}mg ({self.pct_remaining:.0f}%)\n"
            f"  Sleep safe (< 25mg): {'Yes ✅' if self.sleep_safe else 'No ⚠️'}\n"
            f"  Recommendation: {self.recommendation}"
        )


# ── Hormonal Sleep Windows ─────────────────────────────────────────────────────

HORMONAL_WINDOWS = {
    "melatonin_onset": {
        "window": ("21:00", "22:00"),
        "description": "Melatonin secretion begins ~2h before sleep in darkness.",
        "protocol": "Dim lights, avoid blue light (>480nm), keep room below 68°F (20°C).",
        "evidence": "Cajochen et al. 2011 J Sleep Res 🟢",
    },
    "growth_hormone_pulse": {
        "window": ("23:00", "01:00"),
        "description": "Peak GH pulse occurs during slow-wave sleep (SWS) in first 2 cycles.",
        "protocol": "Avoid carbohydrate/food in 2h before bed (insulin blunts GH). Consider glycine 3g.",
        "evidence": "Van Cauter et al. 2000 Sleep 🟢",
    },
    "cortisol_nadir": {
        "window": ("00:00", "04:00"),
        "description": "Cortisol at lowest. Critical for immune and tissue repair.",
        "protocol": "No light exposure during this window. Blackout curtains essential.",
        "evidence": "Lightman 2008 J Neuroendocrinology 🟢",
    },
    "cortisol_rise": {
        "window": ("05:00", "08:00"),
        "description": "Cortisol awakening response (CAR) prepares the body for the day.",
        "protocol": "Use sunlight/light therapy in first 30min after waking to synchronize CAR.",
        "evidence": "Wust et al. 2000 Psychoneuroendocrinology 🟢",
    },
    "testosterone_peak": {
        "window": ("05:00", "09:00"),
        "description": "Testosterone peaks in morning hours, especially after full-night sleep.",
        "protocol": "Prioritize full sleep duration. Testosterone drops 10–15% after one night of poor sleep.",
        "evidence": "Leproult & Van Cauter 2011 JAMA 🟢",
    },
}


# ── Athlete Sleep Targets ─────────────────────────────────────────────────────

ATHLETE_SLEEP_TARGETS = {
    "endurance": {
        "min_hours": 8.0, "optimal_hours": 9.0,
        "rationale": "High training volume requires extended SWS for muscle glycogen and GH secretion.",
        "evidence": "Mah et al. 2011 Sleep 🟡",
    },
    "strength": {
        "min_hours": 8.0, "optimal_hours": 9.0,
        "rationale": "Testosterone and GH pulsatility during SWS drives hypertrophy and strength gains.",
        "evidence": "Dattilo et al. 2011 Med Hypotheses 🟠",
    },
    "team_sport": {
        "min_hours": 8.0, "optimal_hours": 8.5,
        "rationale": "Cognitive speed, reaction time, and decision-making all improve with sleep extension.",
        "evidence": "Mah et al. 2011 Sleep 🟡",
    },
    "weight_class": {
        "min_hours": 8.5, "optimal_hours": 9.0,
        "rationale": "Sleep restriction raises ghrelin and lowers leptin, impairing appetite control and recovery.",
        "evidence": "Nedeltcheva et al. 2010 Ann Intern Med 🟢",
    },
    "general": {
        "min_hours": 7.5, "optimal_hours": 8.0,
        "rationale": "General health and cognitive performance optimum.",
        "evidence": "Watson et al. 2015 Sleep 🟢",
    },
}


# ── Sleep Debt Tracker ────────────────────────────────────────────────────────

@dataclass
class SleepDebt:
    """Cumulative sleep debt and recovery projection."""
    nightly_actual: list[float]   # Hours of sleep per night (recent)
    target_hours: float

    @property
    def total_debt_hours(self) -> float:
        deficit = sum(max(0, self.target_hours - night) for night in self.nightly_actual)
        return round(deficit, 1)

    @property
    def average_actual(self) -> float:
        return round(sum(self.nightly_actual) / len(self.nightly_actual), 1) if self.nightly_actual else 0

    @property
    def recovery_nights_needed(self) -> int:
        """Nights of extended sleep (target + 1h) needed to clear debt."""
        if self.total_debt_hours <= 0:
            return 0
        return math.ceil(self.total_debt_hours)

    @property
    def performance_impact(self) -> str:
        debt = self.total_debt_hours
        if debt <= 0:
            return "No debt — performance optimal."
        if debt < 2:
            return "Minor debt. Mild cognitive slowing, recovery slightly impaired."
        if debt < 5:
            return "Moderate debt. Reaction time −15%, perceived exertion elevated."
        if debt < 10:
            return "Significant debt. VO2max −3–5%, injury risk elevated."
        return "Severe debt. Major impairment. Mandatory recovery protocol."

    def display(self) -> str:
        nights = len(self.nightly_actual)
        lines = [
            f"  Last {nights} nights: {', '.join(f'{h:.1f}h' for h in self.nightly_actual)}",
            f"  Target per night: {self.target_hours:.1f}h",
            f"  Average actual:   {self.average_actual:.1f}h",
            f"  Total debt:       {self.total_debt_hours:.1f}h",
            f"  Recovery needed:  ~{self.recovery_nights_needed} night(s) of extended sleep",
            "",
            f"  Performance: {self.performance_impact}",
        ]
        return "\n".join(lines)


# ── Public Functions ──────────────────────────────────────────────────────────

def classify_chronotype(meq_score: Optional[int] = None, bedtime_wfree: Optional[str] = None) -> dict:
    """
    Classify chronotype from MEQ score OR free-day bedtime.
    meq_score: 16–86 (Morningness-Eveningness Questionnaire total)
    bedtime_wfree: Typical bedtime on work-free days, e.g. "23:30"
    Returns chronotype profile dict.
    """
    chronotype: Optional[Chronotype] = None

    if meq_score is not None:
        for lo, hi, ct in MEQ_THRESHOLDS:
            if lo <= meq_score <= hi:
                chronotype = ct
                break

    elif bedtime_wfree is not None:
        try:
            h, m = map(int, bedtime_wfree.split(":"))
            # MSFsc proxy: late bedtime (after midnight) → wolf, early → lion
            minutes_past_midnight = h * 60 + m if h < 12 else (h - 24) * 60 + m
            # Free-day midpoint typically bedtime + 4h
            if minutes_past_midnight < -30:       # Before 11:30pm
                chronotype = "lion"
            elif minutes_past_midnight <= 60:     # 11:30pm–1am (inclusive)
                chronotype = "bear"
            elif minutes_past_midnight <= 150:    # 1am–2:30am
                chronotype = "wolf"
            else:
                chronotype = "wolf"
        except Exception:
            chronotype = "bear"

    else:
        return {"error": "Provide meq_score (16-86) or bedtime_wfree ('23:30' format)"}

    if chronotype is None:
        chronotype = "bear"  # Default

    profile = CHRONOTYPE_PROFILES[chronotype]
    return {
        "chronotype": chronotype,
        **profile,
        "training_window": profile["peak_physical"],
        "evidence": "Roenneberg et al. 2003 J Biol Rhythms 🟢",
    }


def optimal_wake_times(bedtime_str: str, num_options: int = 4) -> SleepCycleResult:
    """
    Calculate cycle-aligned wake times for a given bedtime.
    Accounts for ~15 min sleep onset latency.
    Returns options for 4–7 complete sleep cycles.
    """
    h, m = map(int, bedtime_str.split(":"))
    total_onset_minutes = h * 60 + m + SLEEP_ONSET_MINUTES

    wake_options = []
    for cycles in range(4, 4 + num_options):
        total_wake_min = total_onset_minutes + cycles * SLEEP_CYCLE_MINUTES
        wake_h = (total_wake_min // 60) % 24
        wake_m = total_wake_min % 60
        wake_options.append(f"{wake_h:02d}:{wake_m:02d}")

    # Optimal = 5th cycle (7.5h) for most athletes
    optimal_idx = min(1, len(wake_options) - 1)  # Index 1 = 5 cycles (4+1)
    optimal = wake_options[optimal_idx]

    notes = ""
    if h >= 0 and h < 22:
        notes = f"Bedtime {bedtime_str} is earlier than recommended for most adults (target 21:30–23:00)."
    elif h >= 1:
        notes = f"Late bedtime {bedtime_str} will reduce total sleep opportunity. Earlier is better."

    return SleepCycleResult(
        sleep_time=bedtime_str,
        wake_times=wake_options,
        optimal_wake=optimal,
        notes=notes,
    )


def caffeine_clearance(
    dose_mg: float,
    hours_elapsed: float,
    fast_metabolizer: bool = True,
) -> CaffeineStatus:
    """
    Compute remaining caffeine at hours_elapsed post-consumption.
    fast_metabolizer: CYP1A2 *1F/*1F → half-life ~4h
    slow_metabolizer: CYP1A2 *1A → half-life ~7h
    Reference: Sachse et al. 1999 Hepatology (🟡); pharmacogenomics consensus.
    """
    half_life = 4.0 if fast_metabolizer else 7.0
    remaining = dose_mg * (0.5 ** (hours_elapsed / half_life))
    pct_remaining = remaining / dose_mg * 100
    sleep_safe = remaining < 25

    if sleep_safe:
        rec = "Caffeine levels low enough for quality sleep."
    elif remaining < 50:
        rec = f"Wait {half_life:.0f}h more before sleep for best recovery."
    else:
        rec = (
            f"Significant caffeine remaining. Avoid sleep for {math.ceil(hours_elapsed + half_life):.0f}+ hours post-dose. "
            f"Consider melatonin 0.5–1mg for sleep induction, but effectiveness reduced."
        )

    return CaffeineStatus(
        dose_mg=dose_mg,
        hours_elapsed=hours_elapsed,
        half_life_hours=half_life,
        remaining_mg=round(remaining, 1),
        pct_remaining=round(pct_remaining, 1),
        sleep_safe=sleep_safe,
        recommendation=rec,
    )


def sleep_debt_report(nightly_hours: list[float], target_hours: float = 8.0) -> SleepDebt:
    """Create a sleep debt tracker from recent nightly hours."""
    return SleepDebt(nightly_actual=nightly_hours, target_hours=target_hours)


def athlete_sleep_target(sport: str = "general") -> dict:
    """Return evidence-based sleep targets for the given sport type."""
    target = ATHLETE_SLEEP_TARGETS.get(sport.lower(), ATHLETE_SLEEP_TARGETS["general"])
    return {
        "sport": sport,
        **target,
    }


def format_hormonal_windows() -> str:
    """Format the full hormonal sleep window reference table."""
    lines = [
        "Hormonal Sleep Windows — Evidence-Based Reference",
        "=" * 60,
        "",
    ]
    for key, data in HORMONAL_WINDOWS.items():
        lines += [
            f"⏰ {key.replace('_', ' ').title()} ({data['window'][0]}–{data['window'][1]})",
            f"   {data['description']}",
            f"   Protocol: {data['protocol']}",
            f"   {data['evidence']}",
            "",
        ]
    return "\n".join(lines)


def pre_sleep_protocol(
    chronotype: Chronotype = "bear",
    sport: str = "general",
    sleep_time: str = "23:00",
) -> str:
    """
    Generate a personalized pre-sleep protocol based on chronotype and sport.
    """
    target = ATHLETE_SLEEP_TARGETS.get(sport, ATHLETE_SLEEP_TARGETS["general"])
    profile = CHRONOTYPE_PROFILES.get(chronotype, CHRONOTYPE_PROFILES["bear"])

    # Calculate protocol start times
    h, m = map(int, sleep_time.split(":"))
    def subtract_minutes(hours: int, minutes: int, subtract: int) -> str:
        total = hours * 60 + minutes - subtract
        return f"{(total // 60) % 24:02d}:{total % 60:02d}"

    lines = [
        f"Pre-Sleep Protocol — {profile['label']}",
        f"Sport: {sport.title()}  |  Target: {target['optimal_hours']}h/night",
        "=" * 55,
        "",
        f"T-120min ({subtract_minutes(h, m, 120)}):",
        "  • Last meal/protein: 40g casein or mixed protein",
        "  • Begin reducing bright light (use warm 2700K lighting)",
        "  • No high-intensity exercise after this point",
        "",
        f"T-90min ({subtract_minutes(h, m, 90)}):",
        "  • Magnesium glycinate 300–400mg (supports GABA, relaxation)",
        "  • Optional: L-theanine 200mg (non-sedating anxiolytic)",
        "  • Dim all screens or use Night Shift/f.lux at minimum",
        "",
        f"T-60min ({subtract_minutes(h, m, 60)}):",
        "  • Begin winding down — reading, journaling, light stretching",
        "  • Room temperature: 65–68°F (18–20°C)",
        "  • Optional: Glycine 3g (shown to improve SWS quality 🟡)",
        "",
        f"T-30min ({subtract_minutes(h, m, 30)}):",
        "  • Blackout curtains, eye mask if needed",
        "  • No phones/tablets in bedroom",
        "  • Optional: Melatonin 0.5–1mg (low dose preferred) if circadian shift needed",
        "",
        f"Bedtime ({sleep_time}):",
        "  • Sleep onset target: < 20 minutes",
        "  • Keep bedroom dark and quiet (<35 dB, <68°F)",
        "",
        "Morning Protocol:",
        f"  • Target wake: {optimal_wake_times(sleep_time).optimal_wake} ({target['optimal_hours']:.0f}h sleep)",
        "  • Immediate bright light (>10,000 lux) for 10–30min",
        "  • No snoozing — single alarm anchors circadian rhythm",
        "",
        f"Evidence: Fullagar et al. 2015 Sports Med 🟢 | Buysse 1989 🟢",
    ]
    return "\n".join(lines)
