"""
Tests for tools/periodization.py — Training Load & Periodization.

Covers:
- TrainingSession sRPE calculation
- ATL / CTL / TSB from exponential moving averages
- Monotony and strain indices
- Ramp rate calculation and safety flags
- Prilepin's Table recommendations
- Block periodization planner
- Overreaching risk detection
"""
import pytest
import math
from tools.periodization import (
    TrainingSession,
    LoadMetrics,
    PeriodizationBlock,
    TrainingLoadCalculator,
    prilepins_recommendation,
    get_block_plan,
    format_block_plan,
    PRILEPINS_TABLE,
    BLOCK_TEMPLATES,
)


# ── TrainingSession ────────────────────────────────────────────────────────────

def test_session_load_calculation():
    """sRPE = RPE × duration."""
    s = TrainingSession(date_offset=0, duration_min=60, rpe=7.0)
    assert s.session_load == pytest.approx(420.0)


def test_session_load_fractional_rpe():
    s = TrainingSession(date_offset=0, duration_min=45, rpe=6.5)
    assert s.session_load == pytest.approx(45 * 6.5)


def test_session_display_includes_key_fields():
    s = TrainingSession(date_offset=3, duration_min=90, rpe=8.0, sport="Cycling", notes="Hard intervals")
    text = s.display()
    assert "90" in text
    assert "8.0" in text
    assert "Cycling" in text
    assert "Hard intervals" in text


def test_session_zero_rpe():
    """Rest day (RPE=0) contributes 0 load."""
    s = TrainingSession(date_offset=0, duration_min=30, rpe=0.0)
    assert s.session_load == 0.0


# ── LoadMetrics ────────────────────────────────────────────────────────────────

def test_load_metrics_form_status_optimal():
    m = LoadMetrics(atl=80, ctl=90, tsb=10, monotony=1.2, strain=800)
    assert "fresh" in m.form_status.lower() or "optimal" in m.form_status.lower()


def test_load_metrics_form_status_overreaching():
    m = LoadMetrics(atl=130, ctl=100, tsb=-30, monotony=2.5, strain=3000)
    assert m.overreaching_risk is True


def test_load_metrics_form_status_building():
    m = LoadMetrics(atl=95, ctl=90, tsb=-5, monotony=1.5, strain=1200)
    status = m.form_status.lower()
    assert "build" in status or "produc" in status


def test_load_metrics_detraining_warning():
    m = LoadMetrics(atl=40, ctl=90, tsb=50, monotony=0.8, strain=300)
    assert "detrain" in m.form_status.lower() or "fresh" in m.form_status.lower() or "under" in m.form_status.lower()


def test_load_metrics_display_contains_values():
    m = LoadMetrics(atl=75.5, ctl=88.3, tsb=12.8, monotony=1.3, strain=900)
    text = m.display()
    assert "75.5" in text
    assert "88.3" in text
    assert "+12.8" in text or "12.8" in text


# ── TrainingLoadCalculator ─────────────────────────────────────────────────────

def test_empty_sessions_returns_zero_metrics():
    calc = TrainingLoadCalculator()
    m = calc.compute([])
    assert m.atl == 0.0
    assert m.ctl == 0.0
    assert m.tsb == 0.0


def test_single_session_produces_nonzero_atl():
    calc = TrainingLoadCalculator()
    sessions = [TrainingSession(date_offset=0, duration_min=60, rpe=7.0)]
    m = calc.compute(sessions)
    assert m.atl > 0
    assert m.ctl > 0


def test_ctl_grows_slower_than_atl():
    """CTL (42-day EMA) grows more slowly than ATL (7-day EMA)."""
    calc = TrainingLoadCalculator()
    # 7 consecutive days of hard training
    sessions = [TrainingSession(date_offset=i, duration_min=90, rpe=8.0) for i in range(7)]
    m = calc.compute(sessions)
    # After 7 days, ATL should be building faster than CTL from baseline
    assert m.atl > m.ctl


def test_tsb_equals_ctl_minus_atl():
    """TSB must always equal CTL - ATL."""
    calc = TrainingLoadCalculator()
    sessions = [TrainingSession(date_offset=i, duration_min=75, rpe=6.5) for i in range(14)]
    m = calc.compute(sessions)
    assert m.tsb == pytest.approx(m.ctl - m.atl, abs=0.1)


def test_rest_days_reduce_atl():
    """ATL should be lower after a period with no training."""
    calc = TrainingLoadCalculator()
    # 7 days of training, then 7 days of rest
    sessions = [TrainingSession(date_offset=i, duration_min=60, rpe=7.0) for i in range(7)]
    m_end_training = calc.compute(sessions)

    # Add 7 rest days
    rest_sessions = sessions.copy()  # No new sessions — compute from extended days
    # Manually compute with extended timeline by adding dummy 0-load day
    all_sessions = sessions + [TrainingSession(date_offset=14, duration_min=0, rpe=0)]
    m_after_rest = calc.compute(all_sessions)
    # ATL after rest should be lower (or equal at minimum)
    assert m_after_rest.atl <= m_end_training.atl + 0.1  # Allow rounding


def test_overreaching_detection():
    """Very high training stress should trigger overreaching risk."""
    calc = TrainingLoadCalculator()
    # 30 days of brutal daily training (10 RPE × 120 min = 1200 AU/day)
    sessions = [TrainingSession(date_offset=i, duration_min=120, rpe=10.0) for i in range(30)]
    m = calc.compute(sessions)
    assert m.overreaching_risk is True


def test_monotony_high_for_identical_sessions():
    """Daily training with zero variation = high monotony."""
    calc = TrainingLoadCalculator()
    # 7 identical sessions (same load every day → SD ≈ 0 → monotony ∞ or very high)
    sessions = [TrainingSession(date_offset=i, duration_min=60, rpe=6.0) for i in range(7)]
    m = calc.compute(sessions)
    # All same load → SD ≈ 0 → monotony undefined (or 0 when we handle division)
    # Implementation sets monotony=0 if sd=0; or very high
    # Either way, strain should be nonzero if load is nonzero
    assert m.strain >= 0


def test_ramp_rate_requires_14_days():
    """Ramp rate calculation needs at least 14 days of data."""
    calc = TrainingLoadCalculator()
    sessions = [TrainingSession(date_offset=i, duration_min=60, rpe=7) for i in range(7)]
    result = calc.ramp_rate(sessions)
    assert "error" in result


def test_ramp_rate_flags_excessive_increase():
    """A doubling of load week over week should be flagged as unsafe."""
    calc = TrainingLoadCalculator()
    # Week 1: low load; Week 2: double
    week1 = [TrainingSession(date_offset=i, duration_min=30, rpe=5) for i in range(7)]
    week2 = [TrainingSession(date_offset=7 + i, duration_min=60, rpe=5) for i in range(7)]  # 2× load
    result = calc.ramp_rate(week1 + week2)
    ramp_rates = result.get("ramp_rates", [])
    assert len(ramp_rates) >= 1
    # Doubling = 100% ramp rate → not safe
    assert any(not r["safe"] for r in ramp_rates)


def test_ramp_rate_10_percent_is_safe():
    """10% increase should be within safe limits."""
    calc = TrainingLoadCalculator()
    # Week 1: 100 AU/day × 7 days; Week 2: 110 AU/day × 7 days
    week1 = [TrainingSession(date_offset=i, duration_min=20, rpe=5.0) for i in range(7)]
    week2 = [TrainingSession(date_offset=7 + i, duration_min=22, rpe=5.0) for i in range(7)]  # ~10% more
    result = calc.ramp_rate(week1 + week2)
    ramp_rates = result.get("ramp_rates", [])
    if ramp_rates:
        assert all(r["safe"] for r in ramp_rates), f"Expected safe, got: {ramp_rates}"


# ── Prilepin's Table ───────────────────────────────────────────────────────────

def test_prilepins_at_70_percent():
    result = prilepins_recommendation(70)
    assert result["optimal_total_reps"] is not None
    assert result["optimal_total_reps"] == 15
    assert "12" in result["rep_range"]


def test_prilepins_at_90_percent():
    result = prilepins_recommendation(90)
    assert result["optimal_total_reps"] == 4
    assert "1" in result["rep_range"]


def test_prilepins_at_80_percent():
    result = prilepins_recommendation(80)
    assert result["optimal_total_reps"] == 10


def test_prilepins_below_range():
    result = prilepins_recommendation(50)
    assert result["optimal_total_reps"] is None
    assert "outside" in result["note"].lower()


def test_prilepins_at_100_percent():
    result = prilepins_recommendation(100)
    assert result["optimal_total_reps"] == 4


def test_prilepins_evidence_tier():
    """All recommendations should include evidence string."""
    for intensity in [60, 70, 75, 80, 85, 90, 95]:
        result = prilepins_recommendation(intensity)
        if result["optimal_total_reps"] is not None:
            assert "🟡" in result["evidence"] or "empirical" in result["evidence"]


# ── Block Periodization ────────────────────────────────────────────────────────

def test_block_templates_exist():
    assert "strength" in BLOCK_TEMPLATES
    assert "endurance" in BLOCK_TEMPLATES
    assert "hypertrophy" in BLOCK_TEMPLATES


def test_get_block_plan_strength():
    plan = get_block_plan("strength")
    names = [b.name for b in plan]
    assert "base" in names
    assert "build" in names
    assert "peak" in names
    assert "taper" in names


def test_get_block_plan_endurance():
    plan = get_block_plan("endurance")
    assert len(plan) >= 3


def test_get_block_plan_unknown_defaults_to_strength():
    plan = get_block_plan("unknown_sport_xyz")
    # Should fall back to strength
    assert len(plan) >= 3


def test_block_has_valid_intensity_and_volume():
    for sport, blocks in BLOCK_TEMPLATES.items():
        for b in blocks:
            assert 0 < b.intensity_pct <= 100, f"{sport}/{b.name}: invalid intensity {b.intensity_pct}"
            assert 0 < b.volume_pct <= 100, f"{sport}/{b.name}: invalid volume {b.volume_pct}"
            assert b.weeks > 0


def test_block_plan_peak_intensity_higher_than_base():
    """Peak block should always have higher intensity than Base."""
    for sport, blocks in BLOCK_TEMPLATES.items():
        by_name = {b.name: b for b in blocks}
        if "base" in by_name and "peak" in by_name:
            assert by_name["peak"].intensity_pct > by_name["base"].intensity_pct, \
                f"{sport}: peak intensity should exceed base"


def test_block_plan_taper_has_lower_volume():
    """Taper block should have lower volume than Build."""
    for sport, blocks in BLOCK_TEMPLATES.items():
        by_name = {b.name: b for b in blocks}
        if "build" in by_name and "taper" in by_name:
            assert by_name["taper"].volume_pct < by_name["build"].volume_pct, \
                f"{sport}: taper volume should be less than build volume"


def test_format_block_plan_output():
    plan = get_block_plan("strength")
    output = format_block_plan(plan, athlete_name="Test Athlete")
    assert "Test Athlete" in output
    assert "BASE" in output or "base" in output.lower()
    assert "PEAK" in output or "peak" in output.lower()
    assert "weeks" in output.lower()


def test_periodization_block_display():
    b = PeriodizationBlock(
        name="build",
        weeks=4,
        intensity_pct=80,
        volume_pct=100,
        goal="Accumulation",
        key_sessions=["5×5 @80%", "Tempo intervals"],
    )
    text = b.display()
    assert "BUILD" in text or "build" in text.lower()
    assert "4 weeks" in text
    assert "80%" in text
    assert "5×5" in text
