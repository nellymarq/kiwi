"""
Tests for tools/training_zones.py — Training zone calculations.

Covers:
- VO2max estimation (Cooper test, HR-based)
- HRmax prediction (Tanaka, Fox, Gulati)
- Heart rate zones (Karvonen HRR)
- Power zones (Coggan/Allen FTP model)
- Running pace zones (Daniels' VDOT)
- Training intensity distribution (polarized, pyramidal, threshold)
- Formatting functions
"""

import pytest
from tools.training_zones import (
    VO2MAX_CATEGORIES_MALE, VO2MAX_CATEGORIES_FEMALE,
    VO2maxEstimate, HRZone, PowerZone, PaceZone, IntensityDistribution,
    classify_vo2max, estimate_vo2max_cooper, estimate_vo2max_hr_based,
    predict_hr_max,
    calculate_hr_zones_karvonen,
    calculate_power_zones,
    calculate_pace_zones,
    recommend_intensity_distribution,
    format_hr_zones, format_power_zones, format_pace_zones,
    format_intensity_distribution,
)


# ── VO2max Estimation ────────────────────────────────────────────────────────

def test_classify_vo2max_male_good():
    assert classify_vo2max(48, "male") == "good"

def test_classify_vo2max_male_superior():
    assert classify_vo2max(65, "male") == "superior"

def test_classify_vo2max_female_excellent():
    assert classify_vo2max(50, "female") == "excellent"

def test_classify_vo2max_female_poor():
    assert classify_vo2max(26, "female") == "poor"

def test_vo2max_categories_male_coverage():
    """Male VO2max categories should be contiguous."""
    prev = 0
    for low, high, _ in VO2MAX_CATEGORIES_MALE:
        assert low == prev
        prev = high

def test_vo2max_categories_female_coverage():
    """Female VO2max categories should be contiguous."""
    prev = 0
    for low, high, _ in VO2MAX_CATEGORIES_FEMALE:
        assert low == prev
        prev = high


def test_cooper_test_average():
    """Cooper 12min: 2400m ≈ VO2max 42.3 (good fitness)."""
    result = estimate_vo2max_cooper(2400)
    # (2400 - 504.9) / 44.73 ≈ 42.3
    assert result.vo2max == pytest.approx(42.3, abs=0.5)
    assert result.method == "Cooper 12-min test"

def test_cooper_test_elite():
    """Cooper 12min: 3200m ≈ VO2max 60.2 (superior)."""
    result = estimate_vo2max_cooper(3200)
    assert result.vo2max == pytest.approx(60.3, abs=0.5)
    assert result.fitness_category == "superior"

def test_cooper_test_low():
    """Very short distance should still give positive VO2max."""
    result = estimate_vo2max_cooper(1000)
    assert result.vo2max >= 10.0  # Clamped minimum

def test_hr_based_vo2max():
    """HR ratio estimate: HRmax=190, HRrest=55 → VO2max ≈ 52.8."""
    result = estimate_vo2max_hr_based(55, 190, 25, "male")
    # 15.3 × (190/55) ≈ 52.8
    assert result.vo2max == pytest.approx(52.8, abs=0.5)
    assert "Uth" in result.method

def test_hr_based_vo2max_zero_rest_guard():
    """HRrest=0 should not crash (division guard)."""
    result = estimate_vo2max_hr_based(0, 190, 25)
    assert result.vo2max > 0


# ── HRmax Prediction ────────────────────────────────────────────────────────

def test_hrmax_tanaka():
    """Tanaka: 208 - 0.7 × 30 = 187."""
    assert predict_hr_max(30, "tanaka") == 187

def test_hrmax_fox():
    """Fox: 220 - 30 = 190."""
    assert predict_hr_max(30, "fox") == 190

def test_hrmax_gulati():
    """Gulati (female): 206 - 0.88 × 30 = 180."""
    assert predict_hr_max(30, "gulati") == 180

def test_hrmax_default_is_tanaka():
    assert predict_hr_max(25) == predict_hr_max(25, "tanaka")


# ── Heart Rate Zones ─────────────────────────────────────────────────────────

def test_hr_zones_count():
    """Should produce exactly 5 HR zones."""
    zones = calculate_hr_zones_karvonen(60, 190)
    assert len(zones) == 5

def test_hr_zones_ascending_order():
    """Zones should have ascending HR values."""
    zones = calculate_hr_zones_karvonen(60, 190)
    for i in range(len(zones) - 1):
        assert zones[i].hr_high <= zones[i + 1].hr_high

def test_hr_zones_zone1_start():
    """Zone 1 should start at 50% HRR."""
    zones = calculate_hr_zones_karvonen(60, 190)
    hrr = 190 - 60
    expected_low = round(60 + 0.50 * hrr)  # 60 + 65 = 125
    assert zones[0].hr_low == expected_low

def test_hr_zones_zone5_ceiling():
    """Zone 5 should reach HRmax."""
    zones = calculate_hr_zones_karvonen(60, 190)
    assert zones[4].hr_high == 190

def test_hr_zones_have_names():
    """All zones must have names and purposes."""
    zones = calculate_hr_zones_karvonen(55, 185)
    for z in zones:
        assert z.name
        assert z.purpose
        assert z.physiological_target

def test_hr_zones_karvonen_math():
    """Verify Karvonen formula: HR = HRrest + %HRR × (HRmax - HRrest)."""
    zones = calculate_hr_zones_karvonen(50, 200)
    hrr = 150
    # Zone 2 low = 50 + 0.60 × 150 = 140
    assert zones[1].hr_low == round(50 + 0.60 * hrr)
    # Zone 3 high = 50 + 0.80 × 150 = 170
    assert zones[2].hr_high == round(50 + 0.80 * hrr)


# ── Power Zones ──────────────────────────────────────────────────────────────

def test_power_zones_count():
    """Should produce exactly 7 power zones."""
    zones = calculate_power_zones(250)
    assert len(zones) == 7

def test_power_zones_ftp_in_zone4():
    """FTP should fall within Zone 4 (91–105% FTP)."""
    ftp = 250
    zones = calculate_power_zones(ftp)
    z4 = zones[3]
    assert z4.power_low <= ftp <= z4.power_high

def test_power_zones_zone1_ceiling():
    """Zone 1 ceiling should be 55% FTP."""
    zones = calculate_power_zones(300)
    assert zones[0].power_high == round(300 * 0.55)

def test_power_zones_zone7_no_ceiling():
    """Zone 7 should have no power ceiling (0 = max)."""
    zones = calculate_power_zones(250)
    assert zones[6].power_high == 0

def test_power_zones_ascending():
    """Power zones should have ascending power values."""
    zones = calculate_power_zones(280)
    for i in range(len(zones) - 2):  # Skip Z7 (no ceiling)
        assert zones[i].power_high <= zones[i + 1].power_high or zones[i + 1].power_high == 0

def test_power_zones_names():
    """All 7 zones should have descriptive names."""
    zones = calculate_power_zones(200)
    names = [z.name for z in zones]
    assert "Active Recovery" in names
    assert "Endurance" in names
    assert "Lactate Threshold" in names
    assert "VO2max" in names
    assert "Neuromuscular Power" in names


# ── Pace Zones ───────────────────────────────────────────────────────────────

def test_pace_zones_count():
    """Should produce exactly 5 pace zones (E, M, T, I, R)."""
    zones = calculate_pace_zones(50)
    assert len(zones) == 5

def test_pace_zones_identifiers():
    """Zones should be labeled E, M, T, I, R."""
    zones = calculate_pace_zones(50)
    ids = [z.zone for z in zones]
    assert ids == ["E", "M", "T", "I", "R"]

def test_pace_zones_easy_slowest():
    """Easy pace should be the slowest (highest min/km)."""
    zones = calculate_pace_zones(50)
    easy_slow = zones[0].pace_max_per_km
    rep_fast = zones[4].pace_min_per_km
    assert easy_slow > rep_fast  # Slower pace = higher number

def test_pace_zones_rep_fastest():
    """Repetition pace should be the fastest."""
    zones = calculate_pace_zones(55)
    rep = zones[4]
    for z in zones[:4]:
        assert z.pace_min_per_km > rep.pace_min_per_km

def test_pace_zones_higher_vdot_faster():
    """Higher VDOT = faster paces (lower min/km)."""
    slow = calculate_pace_zones(40)
    fast = calculate_pace_zones(60)
    # Threshold pace should be faster for VDOT 60
    assert fast[2].pace_min_per_km < slow[2].pace_min_per_km

def test_pace_zones_realistic_vdot50():
    """VDOT 50 threshold pace should be ~4:00–4:30 min/km range."""
    zones = calculate_pace_zones(50)
    t_pace = zones[2].pace_min_per_km  # Threshold fast end
    assert 3.5 < t_pace < 5.0  # Reasonable range


# ── Intensity Distribution ──────────────────────────────────────────────────

def test_polarized_for_elite_endurance():
    """Elite endurance athletes should get polarized model."""
    dist = recommend_intensity_distribution("endurance", "elite")
    assert dist.model == "polarized"
    assert dist.zone_1_pct == 80
    assert dist.zone_3_pct == 20

def test_pyramidal_for_intermediate():
    """Intermediate recreational athletes should get pyramidal."""
    dist = recommend_intensity_distribution("endurance", "intermediate")
    assert dist.model == "pyramidal"
    assert dist.zone_1_pct >= 70

def test_threshold_for_strength():
    """Strength athletes should get threshold model."""
    dist = recommend_intensity_distribution("strength", "intermediate")
    assert dist.model == "threshold"
    assert dist.zone_2_pct >= 30

def test_distribution_sums_to_100():
    """Zone percentages should sum to 100%."""
    for sport in ("endurance", "team_sport", "strength", "hybrid"):
        for level in ("beginner", "intermediate", "advanced", "elite"):
            dist = recommend_intensity_distribution(sport, level)
            total = dist.zone_1_pct + dist.zone_2_pct + dist.zone_3_pct
            assert total == 100, f"{sport}/{level}: {total}% != 100%"

def test_distribution_has_weekly_example():
    """All distributions should include a weekly example."""
    dist = recommend_intensity_distribution("endurance", "advanced")
    assert len(dist.weekly_example) >= 5

def test_distribution_has_evidence():
    """All distributions should cite evidence."""
    for model_args in [("endurance", "elite"), ("strength", "intermediate"), ("team_sport", "beginner")]:
        dist = recommend_intensity_distribution(*model_args)
        assert any(t in dist.evidence for t in ["🟢", "🟡", "🟠"])

def test_build_phase_more_intensity():
    """Build/peak phase should allocate more high-intensity work."""
    base = recommend_intensity_distribution("endurance", "intermediate", "base")
    build = recommend_intensity_distribution("endurance", "intermediate", "build")
    assert build.zone_3_pct >= base.zone_3_pct


# ── Formatting ───────────────────────────────────────────────────────────────

def test_format_hr_zones_output():
    """HR zone formatter produces readable table."""
    zones = calculate_hr_zones_karvonen(60, 185)
    output = format_hr_zones(zones)
    assert "Heart Rate Training Zones" in output
    assert "Z1" in output
    assert "Z5" in output
    assert "bpm" in output

def test_format_power_zones_output():
    """Power zone formatter produces readable table."""
    zones = calculate_power_zones(250)
    output = format_power_zones(zones)
    assert "Power Training Zones" in output
    assert "FTP" in output
    assert "Z4" in output

def test_format_pace_zones_output():
    """Pace zone formatter produces readable table."""
    zones = calculate_pace_zones(50)
    output = format_pace_zones(zones)
    assert "Running Pace Zones" in output
    assert "VDOT" in output
    assert "min/km" in output

def test_format_intensity_distribution_output():
    """Distribution formatter includes model name and percentages."""
    dist = recommend_intensity_distribution("endurance", "elite")
    output = format_intensity_distribution(dist)
    assert "POLARIZED" in output
    assert "80%" in output
    assert "20%" in output
    assert "Weekly Example" in output
