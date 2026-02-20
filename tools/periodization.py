"""
Periodization & Training Load Calculator.

Evidence-based training load management for sport performance.

Covers:
- Acute Training Load (ATL) — rolling 7-day exponential moving average
- Chronic Training Load (CTL) — rolling 42-day exponential moving average
- Training Stress Balance (TSB) = CTL - ATL (form / freshness)
- RPE-based session load (sRPE = RPE × duration)
- Ramp rate calculation and RED-S / overtraining risk flags
- Periodization block planner (Base → Build → Peak → Taper)
- Prilepin's Table (classical powerlifting volume targets)

Scientific basis:
  Banister et al. 1975 — Fitness-Fatigue model
  Foster et al. 2001 — Session RPE (sRPE) method (🟢 RCT validated)
  Mujika & Padilla 2003 — Taper models
  Halson 2014 — Monitoring athlete load (🟢 Review)
  Impellizzeri et al. 2019 — Internal vs external load
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal


# ── Types ──────────────────────────────────────────────────────────────────────

Mesocycle = Literal["base", "build", "peak", "taper", "competition"]
RPEScale = Literal["borg10", "borg20", "rpe"]   # Borg CR10, Borg 20-pt, RPE


# ── Session RPE (sRPE) Conversion ─────────────────────────────────────────────

RPE_TO_BORG_CR10 = {
    1: 0.5, 2: 1.0, 3: 2.0, 4: 3.0, 5: 4.0,
    6: 5.0, 7: 6.0, 8: 7.0, 9: 8.0, 10: 10.0,
}

# Prilepin's Table — optimal volume per intensity zone (classical powerlifting)
# Format: (intensity_min_pct, intensity_max_pct, optimal_reps, rep_range)
PRILEPINS_TABLE = [
    (55, 65, 24, (18, 30)),
    (65, 70, 18, (12, 24)),
    (70, 80, 15, (12, 20)),
    (80, 90, 10, (7, 12)),
    (90, 100, 4,  (1, 4)),
]


@dataclass
class TrainingSession:
    """A single training session with load data."""
    date_offset: int   # Days from start (0-indexed)
    duration_min: float
    rpe: float         # CR10 scale (1–10)
    sport: str = ""
    notes: str = ""

    @property
    def session_load(self) -> float:
        """sRPE load = RPE × duration (arbitrary units, AU)."""
        return round(self.rpe * self.duration_min, 1)

    def display(self) -> str:
        return (
            f"Day {self.date_offset:3d} | {self.sport or 'Training':12s} | "
            f"{self.duration_min:4.0f}min | RPE {self.rpe:4.1f} | "
            f"Load {self.session_load:6.0f} AU"
            + (f"  — {self.notes}" if self.notes else "")
        )


@dataclass
class LoadMetrics:
    """
    ATL / CTL / TSB calculation output using exponential moving averages.

    ATL (Acute Training Load)    — τ = 7 days  (fatigue)
    CTL (Chronic Training Load)  — τ = 42 days (fitness)
    TSB (Training Stress Balance) = CTL - ATL  (form / freshness)
    """
    atl: float      # Acute Training Load (7-day EMA)
    ctl: float      # Chronic Training Load (42-day EMA)
    tsb: float      # Training Stress Balance
    monotony: float # Daily load mean / SD — monotony index
    strain: float   # Weekly load × monotony

    @property
    def form_status(self) -> str:
        """Interpret TSB as athlete form/freshness."""
        if self.tsb > 25:
            return "Detraining risk (too fresh / underloaded)"
        if self.tsb > 5:
            return "Optimal race readiness (fresh)"
        if self.tsb >= -10:
            return "Building (productive zone)"
        if self.tsb >= -30:
            return "Accumulation (high training stress)"
        return "Overreaching risk (dangerously fatigued)"

    @property
    def overreaching_risk(self) -> bool:
        return self.tsb <= -30

    def display(self) -> str:
        lines = [
            f"  ATL  (Fatigue):  {self.atl:6.1f} AU   [7-day EMA]",
            f"  CTL  (Fitness):  {self.ctl:6.1f} AU   [42-day EMA]",
            f"  TSB  (Form):     {self.tsb:+6.1f} AU   {self.form_status}",
            "",
            f"  Monotony Index:  {self.monotony:.2f}   {'⚠️ High monotony (>2)' if self.monotony > 2 else '✅ Acceptable'}",
            f"  Weekly Strain:   {self.strain:.0f} AU",
        ]
        if self.overreaching_risk:
            lines.append("  🚨 OVERREACHING RISK: TSB < -30. Reduce load immediately.")
        return "\n".join(lines)


@dataclass
class PeriodizationBlock:
    """A single mesocycle block."""
    name: Mesocycle
    weeks: int
    intensity_pct: float    # % of 1RM / max HR / FTP
    volume_pct: float       # % of peak volume
    goal: str
    key_sessions: list[str] = field(default_factory=list)

    def display(self) -> str:
        bar_intensity = "█" * int(self.intensity_pct / 10) + "░" * (10 - int(self.intensity_pct / 10))
        bar_volume = "█" * int(self.volume_pct / 10) + "░" * (10 - int(self.volume_pct / 10))
        lines = [
            f"  {self.name.upper():12s} ({self.weeks} weeks)",
            f"    Intensity: [{bar_intensity}] {self.intensity_pct:.0f}%",
            f"    Volume:    [{bar_volume}] {self.volume_pct:.0f}%",
            f"    Goal: {self.goal}",
        ]
        if self.key_sessions:
            lines.append("    Key sessions:")
            for s in self.key_sessions:
                lines.append(f"      • {s}")
        return "\n".join(lines)


# ── Load Calculator ────────────────────────────────────────────────────────────

class TrainingLoadCalculator:
    """
    Computes ATL/CTL/TSB from a series of training sessions using
    exponential moving averages (EMA) — the Banister Fitness-Fatigue model.
    """

    ATL_TAU = 7.0   # Time constant for fatigue (days)
    CTL_TAU = 42.0  # Time constant for fitness (days)

    def __init__(self):
        self.atl_k = math.exp(-1 / self.ATL_TAU)
        self.ctl_k = math.exp(-1 / self.CTL_TAU)

    def compute(self, sessions: list[TrainingSession]) -> LoadMetrics:
        """
        Compute ATL/CTL/TSB from session list.
        Sessions need not be on consecutive days; gaps are handled by
        applying zero-load days between sessions.
        """
        if not sessions:
            return LoadMetrics(atl=0.0, ctl=0.0, tsb=0.0, monotony=0.0, strain=0.0)

        # Sort by date and build daily load array
        sessions_sorted = sorted(sessions, key=lambda s: s.date_offset)
        max_day = sessions_sorted[-1].date_offset
        daily_load = [0.0] * (max_day + 1)
        for s in sessions_sorted:
            daily_load[s.date_offset] += s.session_load

        # EMA forward pass
        atl = 0.0
        ctl = 0.0
        for load in daily_load:
            atl = load * (1 - self.atl_k) + atl * self.atl_k
            ctl = load * (1 - self.ctl_k) + ctl * self.ctl_k

        tsb = ctl - atl

        # Monotony and strain (last 7 days)
        recent = daily_load[-7:] if len(daily_load) >= 7 else daily_load
        mean_load = sum(recent) / len(recent) if recent else 0
        sd = math.sqrt(sum((x - mean_load) ** 2 for x in recent) / len(recent)) if recent else 0
        monotony = mean_load / sd if sd > 0 else 0
        strain = sum(recent) * monotony

        return LoadMetrics(
            atl=round(atl, 1),
            ctl=round(ctl, 1),
            tsb=round(tsb, 1),
            monotony=round(monotony, 2),
            strain=round(strain, 1),
        )

    def ramp_rate(self, sessions: list[TrainingSession]) -> dict:
        """
        Compute weekly load ramp rate.
        Guideline: <10% week-over-week increase to reduce injury risk.
        Reference: Gabbett 2016 — ACWR and injury risk (🟡 cohort).
        """
        if len(sessions) < 2:
            return {"error": "Need at least 2 weeks of data"}

        sessions_sorted = sorted(sessions, key=lambda s: s.date_offset)
        total_days = sessions_sorted[-1].date_offset - sessions_sorted[0].date_offset

        if total_days < 13:
            return {"error": "Need at least 14 days of data for ramp rate"}

        # Split into weekly buckets
        weeks: dict[int, float] = {}
        for s in sessions_sorted:
            week = s.date_offset // 7
            weeks[week] = weeks.get(week, 0) + s.session_load

        week_list = [(w, v) for w, v in sorted(weeks.items())]
        ramp_rates = []
        for i in range(1, len(week_list)):
            prev_load = week_list[i - 1][1]
            curr_load = week_list[i][1]
            if prev_load > 0:
                rate = (curr_load - prev_load) / prev_load * 100
                ramp_rates.append({
                    "week": week_list[i][0] + 1,
                    "load_au": curr_load,
                    "ramp_pct": round(rate, 1),
                    "safe": abs(rate) <= 10,
                })

        return {
            "weekly_loads": [{"week": w + 1, "load_au": v} for w, v in week_list],
            "ramp_rates": ramp_rates,
            "max_ramp": max((abs(r["ramp_pct"]) for r in ramp_rates), default=0),
            "guideline": "< 10% weekly increase recommended (Gabbett 2016 🟡)",
        }


# ── Prilepin's Table ───────────────────────────────────────────────────────────

def prilepins_recommendation(intensity_pct: float) -> dict:
    """
    Return Prilepin's volume recommendations for a given intensity.
    Classic powerlifting guideline for optimal volume within intensity zones.
    Uses half-open intervals [lo, hi) so zone boundaries (e.g. 70%) resolve
    to the upper zone (70–80% → 15 reps), matching the original table intent.
    The last zone (90–100%) is fully closed [90, 100].
    """
    for i, (lo, hi, optimal, (rep_min, rep_max)) in enumerate(PRILEPINS_TABLE):
        is_last = i == len(PRILEPINS_TABLE) - 1
        in_range = (lo <= intensity_pct <= hi) if is_last else (lo <= intensity_pct < hi)
        if in_range:
            return {
                "intensity_pct": intensity_pct,
                "optimal_total_reps": optimal,
                "rep_range": f"{rep_min}–{rep_max}",
                "note": f"At {intensity_pct:.0f}%: aim for {optimal} total reps ({rep_min}–{rep_max} range)",
                "evidence": "Prilepin's Table 1974 (🟡 empirical)",
            }
    return {
        "intensity_pct": intensity_pct,
        "optimal_total_reps": None,
        "note": f"Intensity {intensity_pct:.0f}% outside Prilepin's documented range (55–100%)",
        "evidence": "N/A",
    }


# ── Block Periodization Planner ───────────────────────────────────────────────

BLOCK_TEMPLATES: dict[str, list[PeriodizationBlock]] = {
    "strength": [
        PeriodizationBlock(
            name="base", weeks=4, intensity_pct=65, volume_pct=70,
            goal="GPP — build work capacity and movement quality",
            key_sessions=["4×8 @65%", "Tempo work", "Aerobic base 2–3×/week"],
        ),
        PeriodizationBlock(
            name="build", weeks=4, intensity_pct=80, volume_pct=100,
            goal="Hypertrophy / strength accumulation",
            key_sessions=["5×5 @80%", "Accessory volume", "Weekly AMRAP sets"],
        ),
        PeriodizationBlock(
            name="peak", weeks=3, intensity_pct=92, volume_pct=55,
            goal="Peaking — CNS adaptation, peak strength expression",
            key_sessions=["2–3 heavy singles", "5×2–3 @90%+", "Minimal accessories"],
        ),
        PeriodizationBlock(
            name="taper", weeks=1, intensity_pct=80, volume_pct=30,
            goal="Reduce fatigue, maintain neural drive",
            key_sessions=["1–2 heavy singles @85–90%", "Low volume, full recovery"],
        ),
    ],
    "endurance": [
        PeriodizationBlock(
            name="base", weeks=8, intensity_pct=65, volume_pct=60,
            goal="Aerobic base — Zone 2 / MAF development",
            key_sessions=["Long slow distance (LSD)", "2× tempo", "Daily easy running"],
        ),
        PeriodizationBlock(
            name="build", weeks=6, intensity_pct=75, volume_pct=100,
            goal="Lactate threshold + VO2max intervals",
            key_sessions=["Weekly threshold run (20–40min @LT)", "VO2max intervals 5×5min", "Mid-long run"],
        ),
        PeriodizationBlock(
            name="peak", weeks=3, intensity_pct=85, volume_pct=70,
            goal="Race-specific pace + sharpening",
            key_sessions=["Race pace intervals", "Tune-up race", "Lactate test"],
        ),
        PeriodizationBlock(
            name="taper", weeks=2, intensity_pct=80, volume_pct=35,
            goal="ATL drop, CTL maintenance — peak freshness",
            key_sessions=["Short race-pace strides", "Easy 20–30min daily"],
        ),
    ],
    "hypertrophy": [
        PeriodizationBlock(
            name="base", weeks=3, intensity_pct=60, volume_pct=60,
            goal="Anatomical adaptation — joint prep, movement skill",
            key_sessions=["3×15–20 @60%", "Unilateral balance work", "Light conditioning"],
        ),
        PeriodizationBlock(
            name="build", weeks=6, intensity_pct=75, volume_pct=100,
            goal="Hypertrophy accumulation — high volume, moderate intensity",
            key_sessions=["4×8–12 @75%", "Supersets / drop sets", "RPE 8 working sets"],
        ),
        PeriodizationBlock(
            name="peak", weeks=2, intensity_pct=85, volume_pct=55,
            goal="Intensity peak + muscle fiber recruitment",
            key_sessions=["3×5 @85%", "Reduce frequency, increase load"],
        ),
        PeriodizationBlock(
            name="taper", weeks=1, intensity_pct=70, volume_pct=40,
            goal="Deload — tissue repair, supercompensation",
            key_sessions=["Light 3×12", "No failure sets", "Active recovery"],
        ),
    ],
}


def get_block_plan(sport_type: str = "strength") -> list[PeriodizationBlock]:
    """Return a periodization block plan for the given sport type."""
    return BLOCK_TEMPLATES.get(sport_type, BLOCK_TEMPLATES["strength"])


def format_block_plan(blocks: list[PeriodizationBlock], athlete_name: str = "") -> str:
    """Format a complete periodization plan as a readable string."""
    total_weeks = sum(b.weeks for b in blocks)
    header = f"Periodization Plan{f' — {athlete_name}' if athlete_name else ''}"
    lines = [
        header,
        f"Total duration: {total_weeks} weeks",
        "=" * 60,
    ]
    week = 1
    for b in blocks:
        lines.append(f"\nWeeks {week}–{week + b.weeks - 1}:")
        lines.append(b.display())
        week += b.weeks
    lines.append(f"\n{'=' * 60}")
    lines.append("Reference: Bompa & Buzzichelli, Periodization 5th ed. (🟡)")
    return "\n".join(lines)
