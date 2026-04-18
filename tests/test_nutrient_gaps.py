"""Tests for nutrient gap analyzer."""

import pytest
from tools.nutrient_gaps import analyze_gaps, format_gap_analysis, ATHLETE_TARGETS


def test_basic_analysis():
    gaps = analyze_gaps(sex="male", sport="strength")
    assert len(gaps) > 0
    assert all(hasattr(g, "gap_severity") for g in gaps)


def test_female_endurance_high_risk_iron():
    gaps = analyze_gaps(sex="female", sport="endurance")
    iron_gap = next((g for g in gaps if g.nutrient == "iron"), None)
    assert iron_gap is not None
    assert iron_gap.gap_severity == "high_risk"
    assert iron_gap.athlete_target > iron_gap.rda_ai


def test_vegetarian_b12_high_risk():
    gaps = analyze_gaps(
        sex="male",
        dietary_restrictions=["vegetarian"],
    )
    b12_gap = next((g for g in gaps if g.nutrient == "vitamin_b12"), None)
    assert b12_gap is not None
    assert b12_gap.gap_severity == "high_risk"


def test_supplemented_nutrient_covered():
    gaps = analyze_gaps(
        sex="male",
        current_supplements=["iron", "vitamin_d"],
    )
    iron_gap = next((g for g in gaps if g.nutrient == "iron"), None)
    vd_gap = next((g for g in gaps if g.nutrient == "vitamin_d"), None)
    assert iron_gap is not None
    assert iron_gap.gap_severity == "covered"
    assert vd_gap is not None
    assert vd_gap.gap_severity == "covered"


def test_combat_sports_high_risk_nutrients():
    gaps = analyze_gaps(sex="male", sport="combat_sports")
    magnesium = next((g for g in gaps if g.nutrient == "magnesium"), None)
    potassium = next((g for g in gaps if g.nutrient == "potassium"), None)
    assert magnesium is not None
    assert potassium is not None
    # Combat sports → high sweat → high risk for these
    assert magnesium.gap_severity == "high_risk"


def test_format_output():
    gaps = analyze_gaps(sex="female", sport="endurance")
    output = format_gap_analysis(gaps)
    assert "Nutrient Gap Analysis" in output
    assert "🔴" in output or "🟡" in output
    assert "Summary:" in output


def test_format_empty():
    output = format_gap_analysis([])
    assert "No gap" in output


def test_sorting_high_risk_first():
    gaps = analyze_gaps(sex="female", sport="endurance")
    severities = [g.gap_severity for g in gaps]
    # First entries should be high_risk
    first_non_high = next((i for i, s in enumerate(severities) if s != "high_risk"), len(severities))
    for i in range(first_non_high):
        assert severities[i] == "high_risk"


def test_athlete_targets_exist():
    assert "iron" in ATHLETE_TARGETS
    assert "calcium" in ATHLETE_TARGETS
    assert "vitamin_d" in ATHLETE_TARGETS
    assert len(ATHLETE_TARGETS) >= 10


def test_multivitamin_covers_multiple():
    gaps = analyze_gaps(
        sex="male",
        current_supplements=["multivitamin"],
    )
    covered = [g.nutrient for g in gaps if g.gap_severity == "covered"]
    assert "iron" in covered
    assert "vitamin_d" in covered
    assert "zinc" in covered
