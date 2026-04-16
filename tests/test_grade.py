"""Tests for GRADE evidence grading."""

import pytest
from tools.grade import (
    GradeInputs, GradeAssessment, assess, assess_from_evidence_tier,
    DESIGN_STARTING_LEVEL, CERTAINTY_LABELS,
)


def test_rct_starts_at_high():
    result = assess(GradeInputs(study_design="rct"))
    assert result.certainty_label == "HIGH"
    assert result.starting_level == 4


def test_cohort_starts_at_low():
    result = assess(GradeInputs(study_design="cohort"))
    assert result.starting_level == 2


def test_serious_risk_of_bias_downgrades():
    result = assess(GradeInputs(
        study_design="rct",
        risk_of_bias="serious",
    ))
    assert result.certainty_level == 3
    assert result.certainty_label == "MODERATE"
    assert len(result.downgrades) == 1


def test_very_serious_downgrades_by_2():
    result = assess(GradeInputs(
        study_design="rct",
        risk_of_bias="very_serious",
    ))
    assert result.certainty_level == 2
    assert result.certainty_label == "LOW"


def test_multiple_downgrades_stack():
    result = assess(GradeInputs(
        study_design="rct",
        risk_of_bias="serious",
        inconsistency="serious",
    ))
    assert result.certainty_level == 2
    assert len(result.downgrades) == 2


def test_cannot_go_below_very_low():
    result = assess(GradeInputs(
        study_design="rct",
        risk_of_bias="very_serious",
        inconsistency="very_serious",
        indirectness="very_serious",
    ))
    assert result.certainty_level == 1


def test_observational_upgrade_for_large_effect():
    result = assess(GradeInputs(
        study_design="cohort",
        large_effect=True,
    ))
    assert result.certainty_level == 3  # LOW (2) + 1


def test_rct_does_not_upgrade():
    """Upgrades only apply to observational evidence."""
    result = assess(GradeInputs(
        study_design="rct",
        large_effect=True,
        dose_response=True,
    ))
    assert result.certainty_level == 4  # Already HIGH, no upgrade


def test_assess_from_emoji_tier():
    green = assess_from_evidence_tier("🟢")
    assert green.certainty_label == "HIGH"

    yellow = assess_from_evidence_tier("🟡")
    assert yellow.certainty_label == "MODERATE"

    orange = assess_from_evidence_tier("🟠")
    assert orange.certainty_label == "LOW"

    blue = assess_from_evidence_tier("🔵")
    assert blue.certainty_label == "VERY LOW"


def test_display_output():
    result = assess(GradeInputs(
        study_design="rct",
        risk_of_bias="serious",
    ))
    output = result.display()
    assert "MODERATE" in output
    assert "Starting level" in output
    assert "Downgrades" in output
