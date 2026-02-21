"""
Tests for tools/body_composition.py — Body composition analysis.

Covers:
- Body fat classification (ACSM categories)
- Jackson-Pollock 3-site estimation
- Sport-specific BF targets
- FFMI calculation and interpretation
- Energy Availability (RED-S screening)
- Safe weight change rate
- Format report output
"""

import pytest
from tools.body_composition import (
    BF_CATEGORIES_MALE, BF_CATEGORIES_FEMALE,
    SPORT_BF_TARGETS,
    BodyFatResult, FFMIResult, EnergyAvailability, WeightChangeGuidance,
    classify_body_fat, estimate_body_fat_jackson_pollock_3,
    analyze_body_composition, calculate_ffmi,
    calculate_energy_availability, safe_weight_change_rate,
    format_composition_report,
)


# ── Body Fat Classification ──────────────────────────────────────────────────

def test_classify_bf_male_athletic():
    assert classify_body_fat(10, "male") == "athletic"

def test_classify_bf_male_essential():
    assert classify_body_fat(3, "male") == "essential"

def test_classify_bf_male_fitness():
    assert classify_body_fat(15, "male") == "fitness"

def test_classify_bf_male_average():
    assert classify_body_fat(20, "male") == "average"

def test_classify_bf_male_obese():
    assert classify_body_fat(30, "male") == "obese"

def test_classify_bf_female_athletic():
    assert classify_body_fat(15, "female") == "athletic"

def test_classify_bf_female_fitness():
    assert classify_body_fat(22, "female") == "fitness"

def test_classify_bf_female_average():
    assert classify_body_fat(28, "female") == "average"

def test_classify_bf_categories_male_coverage():
    """Male categories should cover 0–100% without gaps."""
    prev_high = 0
    for low, high, _ in BF_CATEGORIES_MALE:
        assert low == prev_high
        prev_high = high
    assert prev_high == 100

def test_classify_bf_categories_female_coverage():
    """Female categories should cover 0–100% without gaps."""
    prev_high = 0
    for low, high, _ in BF_CATEGORIES_FEMALE:
        assert low == prev_high
        prev_high = high
    assert prev_high == 100


# ── Jackson-Pollock 3-site ───────────────────────────────────────────────────

def test_jp3_male_typical():
    """Typical male skinfolds should give reasonable BF%."""
    bf = estimate_body_fat_jackson_pollock_3(
        sex="male", age=25,
        skinfold_chest_mm=10, skinfold_abdomen_mm=15, skinfold_thigh_mm=12,
    )
    assert 5 < bf < 20  # Reasonable range

def test_jp3_female_typical():
    """Typical female skinfolds should give reasonable BF%."""
    bf = estimate_body_fat_jackson_pollock_3(
        sex="female", age=28,
        skinfold_tricep_mm=15, skinfold_suprailiac_mm=12, skinfold_thigh_mm=18,
    )
    assert 10 < bf < 30

def test_jp3_male_age_effect():
    """Higher age should increase estimated BF% (all else equal)."""
    bf_young = estimate_body_fat_jackson_pollock_3(
        sex="male", age=20,
        skinfold_chest_mm=10, skinfold_abdomen_mm=15, skinfold_thigh_mm=12,
    )
    bf_old = estimate_body_fat_jackson_pollock_3(
        sex="male", age=50,
        skinfold_chest_mm=10, skinfold_abdomen_mm=15, skinfold_thigh_mm=12,
    )
    assert bf_old > bf_young

def test_jp3_never_negative():
    """BF% should never be negative even with very low skinfolds."""
    bf = estimate_body_fat_jackson_pollock_3(
        sex="male", age=20,
        skinfold_chest_mm=3, skinfold_abdomen_mm=3, skinfold_thigh_mm=3,
    )
    assert bf >= 0


# ── Sport-Specific BF Targets ───────────────────────────────────────────────

def test_sport_targets_count():
    """At least 10 sports should have BF targets."""
    assert len(SPORT_BF_TARGETS) >= 10

@pytest.mark.parametrize("sport", SPORT_BF_TARGETS.keys())
def test_sport_target_has_male_female(sport):
    """Each sport target must have male and female ranges."""
    targets = SPORT_BF_TARGETS[sport]
    assert "male" in targets
    assert "female" in targets
    assert "notes" in targets
    male_lo, male_hi = targets["male"]
    female_lo, female_hi = targets["female"]
    assert male_lo < male_hi
    assert female_lo < female_hi

def test_bodybuilding_targets_extreme():
    """Bodybuilding competition targets should be very low."""
    bb = SPORT_BF_TARGETS["bodybuilding"]
    assert bb["male"][0] <= 5
    assert bb["female"][0] <= 12


# ── Analyze Body Composition ────────────────────────────────────────────────

def test_analyze_within_range():
    """80kg male at 12% BF should be athletic and within cycling range."""
    result = analyze_body_composition(80, 12, "male", sport="cycling")
    assert result.category == "athletic"
    assert result.fat_mass_kg == pytest.approx(9.6, abs=0.1)
    assert result.lean_mass_kg == pytest.approx(70.4, abs=0.1)
    assert "Within" in result.sport_context

def test_analyze_above_range():
    """80kg male at 20% BF should be above cycling range."""
    result = analyze_body_composition(80, 20, "male", sport="cycling")
    assert "ABOVE" in result.sport_context

def test_analyze_below_range():
    """60kg female at 10% BF should be below running range."""
    result = analyze_body_composition(60, 10, "female", sport="running_distance")
    assert "BELOW" in result.sport_context
    assert "RED-S" in result.sport_context


# ── FFMI ─────────────────────────────────────────────────────────────────────

def test_ffmi_typical_athletic_male():
    """80kg male, 12% BF, 180cm → FFMI should be ~21–22 (athletic)."""
    result = calculate_ffmi(80, 12, 180)
    lean = 80 * 0.88
    expected_ffmi = lean / (1.80 ** 2)
    assert result.ffmi == pytest.approx(expected_ffmi, abs=0.5)
    assert "athletic" in result.interpretation.lower() or "Above average" in result.interpretation

def test_ffmi_adjusted_at_180cm():
    """At 180cm, adjusted FFMI should equal raw FFMI (correction = 0)."""
    result = calculate_ffmi(80, 12, 180)
    assert result.ffmi == result.adjusted_ffmi

def test_ffmi_height_adjustment():
    """Shorter person should get positive FFMI adjustment."""
    result = calculate_ffmi(70, 12, 170)
    assert result.adjusted_ffmi > result.ffmi  # 1.80 - 1.70 > 0

def test_ffmi_natural_ceiling():
    """Very muscular individual: FFMI > 25 should flag natural limit."""
    # 100kg at 5% BF, 175cm → lean = 95kg, FFMI = 95 / 1.75² ≈ 31
    result = calculate_ffmi(100, 5, 175)
    assert result.adjusted_ffmi > 25
    assert "natural" in result.natural_limit_note.lower()
    assert "Above" in result.natural_limit_note

def test_ffmi_below_average():
    """Low muscle mass should classify as below average."""
    result = calculate_ffmi(55, 20, 180)
    assert "below" in result.interpretation.lower() or "Average" in result.interpretation


# ── Energy Availability (RED-S) ──────────────────────────────────────────────

def test_ea_optimal():
    """EA ≥ 45 kcal/kg FFM/d = optimal."""
    ea = calculate_energy_availability(3000, 800, 50)
    # EA = (3000 - 800) / 50 = 44
    assert ea.ea_kcal_per_kg_ffm == pytest.approx(44, abs=0.5)
    # Borderline — let's use a clearer case
    ea = calculate_energy_availability(3500, 800, 50)
    # EA = (3500 - 800) / 50 = 54
    assert ea.status == "optimal"
    assert ea.risk_level == "none"

def test_ea_reduced():
    """EA 30–45 = reduced, moderate risk."""
    ea = calculate_energy_availability(2500, 800, 50)
    # EA = (2500 - 800) / 50 = 34
    assert ea.status == "reduced"
    assert ea.risk_level == "moderate"
    assert len(ea.recommendations) >= 1

def test_ea_low():
    """EA < 30 = low, high risk (clinical RED-S threshold)."""
    ea = calculate_energy_availability(2000, 1200, 55)
    # EA = (2000 - 1200) / 55 ≈ 14.5
    assert ea.status in ("low", "clinical")
    assert ea.risk_level in ("high", "critical")

def test_ea_clinical():
    """EA < 20 = clinical, critical risk."""
    ea = calculate_energy_availability(1500, 1200, 55)
    # EA = (1500 - 1200) / 55 ≈ 5.5
    assert ea.status == "clinical"
    assert ea.risk_level == "critical"
    assert "MEDICAL" in " ".join(ea.recommendations).upper()

def test_ea_zero_lean_mass_safety():
    """Zero lean mass should not crash (division by zero guard)."""
    ea = calculate_energy_availability(2000, 500, 0)
    assert ea.ea_kcal_per_kg_ffm > 0  # Default lean mass used


# ── Weight Change Rate ───────────────────────────────────────────────────────

def test_fat_loss_rate_moderate():
    """Standard fat loss for 80kg male at 18% BF."""
    wc = safe_weight_change_rate(80, 75, 18, "male", "fat_loss")
    assert wc.direction == "loss"
    assert 0.3 <= wc.rate_kg_per_week <= 1.0
    assert wc.safe is True
    assert "protein" in " ".join(wc.lean_mass_preservation_notes).lower()

def test_fat_loss_rate_lean_individual():
    """Lean individual (10% BF) should get slower rate."""
    wc = safe_weight_change_rate(75, 72, 10, "male", "fat_loss")
    assert wc.rate_pct_bw_per_week <= 0.5

def test_muscle_gain_rate():
    """Muscle gain should recommend ~0.35% BW/week."""
    wc = safe_weight_change_rate(70, 75, 15, "male", "muscle_gain")
    assert wc.direction == "gain"
    assert wc.rate_pct_bw_per_week == pytest.approx(0.35, abs=0.1)
    assert "surplus" in " ".join(wc.lean_mass_preservation_notes).lower()

def test_contest_prep_rate():
    """Contest prep should have specific notes about refeeds."""
    wc = safe_weight_change_rate(80, 72, 12, "male", "contest_prep")
    assert wc.direction == "loss"
    notes_text = " ".join(wc.lean_mass_preservation_notes).lower()
    assert "refeed" in notes_text or "contest" in notes_text

def test_maintain_weight():
    """Same target weight = maintain."""
    wc = safe_weight_change_rate(80, 80, 15, "male", "fat_loss")
    assert wc.direction == "maintain"

def test_timeline_estimation():
    """Weight change should include timeline estimate."""
    wc = safe_weight_change_rate(80, 75, 18, "male", "fat_loss")
    notes_text = " ".join(wc.lean_mass_preservation_notes)
    assert "weeks" in notes_text.lower()


# ── Format Report ────────────────────────────────────────────────────────────

def test_format_report_basic():
    """Report must include all main sections."""
    result = analyze_body_composition(80, 12, "male", 180, "cycling")
    report = format_composition_report(result)
    assert "BODY COMPOSITION REPORT" in report
    assert "12.0%" in report
    assert "ATHLETIC" in report

def test_format_report_with_ffmi():
    """Report with FFMI section."""
    result = analyze_body_composition(80, 12, "male", 180)
    ffmi = calculate_ffmi(80, 12, 180)
    report = format_composition_report(result, ffmi=ffmi)
    assert "Fat-Free Mass Index" in report
    assert "FFMI" in report

def test_format_report_with_ea():
    """Report with EA/RED-S section."""
    result = analyze_body_composition(60, 18, "female", 165)
    ea = calculate_energy_availability(1800, 600, 49.2)
    report = format_composition_report(result, ea=ea)
    assert "Energy Availability" in report or "RED-S" in report

def test_format_report_with_weight_plan():
    """Report with weight change plan."""
    result = analyze_body_composition(80, 18, "male", 180)
    wc = safe_weight_change_rate(80, 75, 18, "male", "fat_loss")
    report = format_composition_report(result, weight_plan=wc)
    assert "Weight Change Plan" in report
    assert "Loss" in report
