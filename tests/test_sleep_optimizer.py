"""
Tests for tools/sleep_optimizer.py — Sleep Architecture & Chronotype.

Covers:
- Chronotype classification (MEQ score + bedtime)
- Sleep cycle wake time calculation
- Caffeine clearance (fast/slow metabolizer)
- Sleep debt tracker
- Athlete sleep targets
- Hormonal window table
- Pre-sleep protocol generation
"""
import pytest
from tools.sleep_optimizer import (
    classify_chronotype,
    optimal_wake_times,
    caffeine_clearance,
    sleep_debt_report,
    athlete_sleep_target,
    format_hormonal_windows,
    pre_sleep_protocol,
    CHRONOTYPE_PROFILES,
    ATHLETE_SLEEP_TARGETS,
    HORMONAL_WINDOWS,
    SLEEP_CYCLE_MINUTES,
    SleepDebt,
)


# ── CHRONOTYPE_PROFILES completeness ──────────────────────────────────────────

def test_all_chronotypes_have_profiles():
    for ct in ["lion", "bear", "wolf", "dolphin"]:
        assert ct in CHRONOTYPE_PROFILES
        p = CHRONOTYPE_PROFILES[ct]
        assert p["label"]
        assert p["sleep_window"]
        assert p["peak_physical"]
        assert p["description"]


def test_all_athlete_sleep_targets_present():
    for sport in ["endurance", "strength", "team_sport", "weight_class", "general"]:
        assert sport in ATHLETE_SLEEP_TARGETS
        t = ATHLETE_SLEEP_TARGETS[sport]
        assert t["min_hours"] > 0
        assert t["optimal_hours"] >= t["min_hours"]


# ── classify_chronotype() ─────────────────────────────────────────────────────

def test_classify_high_meq_score_is_lion():
    result = classify_chronotype(meq_score=75)
    assert result["chronotype"] == "lion"


def test_classify_low_meq_score_is_wolf():
    result = classify_chronotype(meq_score=25)
    assert result["chronotype"] == "wolf"


def test_classify_middle_meq_is_bear():
    result = classify_chronotype(meq_score=55)
    assert result["chronotype"] == "bear"


def test_classify_bedtime_early_is_lion():
    # Bedtime 21:00 → before 11:30pm → lion
    result = classify_chronotype(bedtime_wfree="21:00")
    assert result["chronotype"] == "lion"


def test_classify_bedtime_midnight_is_bear():
    # Bedtime 23:30 → 11:30pm range → bear or wolf (boundary)
    result = classify_chronotype(bedtime_wfree="23:30")
    assert result["chronotype"] in ("bear", "wolf")


def test_classify_bedtime_late_is_wolf():
    result = classify_chronotype(bedtime_wfree="01:30")
    assert result["chronotype"] == "wolf"


def test_classify_no_input_returns_error():
    result = classify_chronotype()
    assert "error" in result


def test_classify_returns_peak_physical():
    result = classify_chronotype(meq_score=55)
    assert "peak_physical" in result or "training_window" in result


def test_classify_includes_evidence():
    result = classify_chronotype(meq_score=55)
    assert "evidence" in result
    assert "🟢" in result["evidence"]


# ── optimal_wake_times() ──────────────────────────────────────────────────────

def test_wake_times_returns_4_options():
    result = optimal_wake_times("23:00", num_options=4)
    assert len(result.wake_times) == 4


def test_wake_times_all_valid_format():
    result = optimal_wake_times("22:30", num_options=4)
    for t in result.wake_times:
        h, m = map(int, t.split(":"))
        assert 0 <= h <= 23
        assert 0 <= m <= 59


def test_wake_times_spacing_90min():
    """Each option should be exactly 90 minutes apart."""
    result = optimal_wake_times("22:00", num_options=4)
    times_in_minutes = []
    for t in result.wake_times:
        h, m = map(int, t.split(":"))
        times_in_minutes.append(h * 60 + m)
    for i in range(1, len(times_in_minutes)):
        diff = (times_in_minutes[i] - times_in_minutes[i - 1]) % (24 * 60)
        assert diff == 90, f"Expected 90min gap, got {diff}min between {result.wake_times[i-1]} and {result.wake_times[i]}"


def test_wake_times_accounts_for_onset_latency():
    """First wake time should be ~4 cycles × 90min + 15min onset after bedtime."""
    result = optimal_wake_times("23:00", num_options=4)
    # Bed: 23:00 + 15min onset = 23:15 sleep start
    # 4 cycles × 90min = 360min = 6h → wake at 05:15
    first = result.wake_times[0]
    h, m = map(int, first.split(":"))
    total = h * 60 + m
    expected = (23 * 60 + 15 + 360) % (24 * 60)  # 5:15 = 315
    assert total == expected, f"Expected {expected}min (05:15), got {total}min ({first})"


def test_optimal_wake_is_in_wake_times():
    result = optimal_wake_times("22:00")
    assert result.optimal_wake in result.wake_times


def test_wake_times_display_works():
    result = optimal_wake_times("23:00")
    text = result.display()
    assert "Bedtime" in text
    assert "OPTIMAL" in text


# ── caffeine_clearance() ──────────────────────────────────────────────────────

def test_caffeine_full_clearance_fast_metabolizer():
    """After 24 hours, virtually all caffeine should be gone."""
    result = caffeine_clearance(200, hours_elapsed=24, fast_metabolizer=True)
    assert result.remaining_mg < 5
    assert result.sleep_safe is True


def test_caffeine_clearance_fast_vs_slow():
    """Slow metabolizer should have more caffeine remaining at same time point."""
    fast = caffeine_clearance(200, hours_elapsed=8, fast_metabolizer=True)
    slow = caffeine_clearance(200, hours_elapsed=8, fast_metabolizer=False)
    assert slow.remaining_mg > fast.remaining_mg


def test_caffeine_half_life_fast():
    """After exactly 4 hours (one fast half-life), should be ~50% remaining."""
    result = caffeine_clearance(200, hours_elapsed=4, fast_metabolizer=True)
    assert 45 <= result.pct_remaining <= 55


def test_caffeine_half_life_slow():
    """After exactly 7 hours (one slow half-life), should be ~50% remaining."""
    result = caffeine_clearance(200, hours_elapsed=7, fast_metabolizer=False)
    assert 45 <= result.pct_remaining <= 55


def test_caffeine_sleep_unsafe_high_dose():
    result = caffeine_clearance(400, hours_elapsed=2, fast_metabolizer=True)
    assert result.sleep_safe is False
    assert "wait" in result.recommendation.lower() or "avoid" in result.recommendation.lower() or "significant" in result.recommendation.lower()


def test_caffeine_clearance_display():
    result = caffeine_clearance(200, hours_elapsed=5, fast_metabolizer=True)
    text = result.display()
    assert "200" in text
    assert "CYP1A2" in text


def test_caffeine_zero_hours():
    result = caffeine_clearance(200, hours_elapsed=0, fast_metabolizer=True)
    assert result.pct_remaining == pytest.approx(100.0, abs=0.1)
    assert result.sleep_safe is False


# ── SleepDebt ─────────────────────────────────────────────────────────────────

def test_sleep_debt_no_deficit():
    debt = sleep_debt_report([8.0, 8.0, 8.0, 8.0, 8.0], target_hours=8.0)
    assert debt.total_debt_hours == 0.0


def test_sleep_debt_partial_deficit():
    # Each night 1h short → 5 nights → 5h total debt
    debt = sleep_debt_report([7.0, 7.0, 7.0, 7.0, 7.0], target_hours=8.0)
    assert debt.total_debt_hours == pytest.approx(5.0)


def test_sleep_debt_recovery_nights():
    debt = sleep_debt_report([6.0, 6.0, 6.0], target_hours=8.0)
    assert debt.total_debt_hours == 6.0
    assert debt.recovery_nights_needed == 6  # 6 nights of +1h recovery


def test_sleep_debt_average_actual():
    debt = sleep_debt_report([7.0, 8.0, 9.0], target_hours=8.0)
    assert debt.average_actual == pytest.approx(8.0)


def test_sleep_debt_performance_impact_severe():
    debt = sleep_debt_report([5.0, 5.0, 5.0, 5.0, 5.0], target_hours=8.0)
    impact = debt.performance_impact
    assert "significant" in impact.lower() or "severe" in impact.lower()


def test_sleep_debt_display():
    debt = sleep_debt_report([7.0, 7.5, 6.5], target_hours=8.0)
    text = debt.display()
    assert "Total debt" in text
    assert "8.0h" in text or "8h" in text


# ── athlete_sleep_target() ────────────────────────────────────────────────────

def test_sleep_target_endurance():
    result = athlete_sleep_target("endurance")
    assert result["optimal_hours"] >= 8.5
    assert result["evidence"]


def test_sleep_target_strength():
    result = athlete_sleep_target("strength")
    assert result["optimal_hours"] >= 8.5
    assert "GH" in result["rationale"] or "testosterone" in result["rationale"].lower()


def test_sleep_target_unknown_defaults_to_general():
    result = athlete_sleep_target("unknown_sport")
    assert result["sport"] == "unknown_sport"
    assert result["optimal_hours"] > 0


def test_sleep_target_all_have_evidence():
    valid_tiers = {"🟢", "🟡", "🟠", "🔵"}
    for sport in ATHLETE_SLEEP_TARGETS:
        result = athlete_sleep_target(sport)
        assert result["evidence"]
        assert any(t in result["evidence"] for t in valid_tiers), \
            f"{sport}: evidence missing evidence tier emoji: {result['evidence']}"


# ── format_hormonal_windows() ─────────────────────────────────────────────────

def test_hormonal_windows_format():
    text = format_hormonal_windows()
    assert "Growth" in text or "growth_hormone" in text.lower() or "GH" in text
    assert "Melatonin" in text or "melatonin" in text
    assert "Cortisol" in text or "cortisol" in text


def test_hormonal_windows_has_evidence_tiers():
    text = format_hormonal_windows()
    assert "🟢" in text


def test_all_hormonal_windows_have_required_fields():
    for key, w in HORMONAL_WINDOWS.items():
        assert "window" in w, f"{key} missing 'window'"
        assert "description" in w, f"{key} missing 'description'"
        assert "protocol" in w, f"{key} missing 'protocol'"
        assert "evidence" in w, f"{key} missing 'evidence'"


# ── pre_sleep_protocol() ──────────────────────────────────────────────────────

def test_pre_sleep_protocol_contains_timing_blocks():
    protocol = pre_sleep_protocol(chronotype="bear", sport="strength", sleep_time="23:00")
    assert "T-120" in protocol or "T-90" in protocol or "T-60" in protocol


def test_pre_sleep_protocol_includes_supplements():
    protocol = pre_sleep_protocol(sleep_time="23:00")
    assert "Magnesium" in protocol or "magnesium" in protocol


def test_pre_sleep_protocol_includes_wake_time():
    protocol = pre_sleep_protocol(sleep_time="23:00")
    assert "wake" in protocol.lower() or "Target wake" in protocol


def test_pre_sleep_protocol_different_chronotypes():
    """Protocol should generate for all chronotypes without error."""
    for ct in ["lion", "bear", "wolf", "dolphin"]:
        protocol = pre_sleep_protocol(chronotype=ct, sleep_time="23:00")
        assert len(protocol) > 200


def test_pre_sleep_protocol_evidence():
    protocol = pre_sleep_protocol()
    assert "🟢" in protocol or "🟡" in protocol
