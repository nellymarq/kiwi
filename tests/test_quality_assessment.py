"""Tests for methodology quality assessment tools (RoB 2, ROBINS-I, AMSTAR 2)."""

import pytest
from tools.quality_assessment import (
    QualityDomain, QualityAssessment,
    get_checklist, format_checklist,
    ROB2_DOMAINS, ROBINS_I_DOMAINS, AMSTAR2_DOMAINS,
    JUDGMENT_EMOJI, JUDGMENT_ORDER,
)


def test_rob2_has_5_domains():
    assert len(ROB2_DOMAINS) == 5
    assert "Randomization" in ROB2_DOMAINS[0].name


def test_robins_i_has_7_domains():
    assert len(ROBINS_I_DOMAINS) == 7
    assert "Confounding" in ROBINS_I_DOMAINS[0].name


def test_amstar2_has_16_items():
    assert len(AMSTAR2_DOMAINS) == 16


def test_get_checklist_rob2():
    domains = get_checklist("RoB2")
    assert len(domains) == 5
    # Fresh copy, not shared reference
    domains[0].judgment = "HIGH"
    fresh = get_checklist("RoB2")
    assert fresh[0].judgment == "NO_INFORMATION"


def test_get_checklist_robins_i():
    domains = get_checklist("ROBINS-I")
    assert len(domains) == 7


def test_get_checklist_amstar2():
    domains = get_checklist("AMSTAR2")
    assert len(domains) == 16


def test_get_checklist_aliases():
    assert len(get_checklist("rct")) == 5
    assert len(get_checklist("observational")) == 7
    assert len(get_checklist("systematic review")) == 16
    assert len(get_checklist("meta-analysis")) == 16


def test_get_checklist_invalid():
    with pytest.raises(ValueError):
        get_checklist("unknown_tool")


def test_assessment_worst_domain():
    assessment = QualityAssessment(
        tool="RoB 2",
        study_title="Test",
        domains=[
            QualityDomain(name="D1", questions=[], judgment="LOW"),
            QualityDomain(name="D2", questions=[], judgment="SOME_CONCERNS"),
            QualityDomain(name="D3", questions=[], judgment="HIGH"),
        ],
    )
    worst = assessment.worst_domain()
    assert worst.name == "D3"
    assert assessment.compute_overall() == "HIGH"


def test_assessment_no_information():
    assessment = QualityAssessment(
        tool="RoB 2", study_title="T",
        domains=[QualityDomain(name="D1", questions=[])],
    )
    assert assessment.compute_overall() == "NO_INFORMATION"


def test_assessment_display():
    assessment = QualityAssessment(
        tool="RoB 2",
        study_title="Creatine RCT 2023",
        domains=[
            QualityDomain(name="Randomization", questions=["Q1"], judgment="LOW"),
            QualityDomain(name="Blinding", questions=["Q2"], judgment="SOME_CONCERNS",
                          rationale="Open-label design"),
        ],
    )
    output = assessment.display()
    assert "RoB 2" in output
    assert "Creatine RCT 2023" in output
    assert "Randomization" in output
    assert "LOW" in output
    assert "SOME_CONCERNS" in output
    assert "Open-label" in output


def test_format_checklist_rob2():
    output = format_checklist("RoB2")
    assert "RoB 2" in output
    assert "Randomization" in output
    assert "LOW" in output
    assert "□" in output  # Checkbox character


def test_format_checklist_amstar2():
    output = format_checklist("AMSTAR2")
    assert "AMSTAR 2" in output
    assert "PICO" in output


def test_judgment_emoji_map():
    assert JUDGMENT_EMOJI["LOW"] == "🟢"
    assert JUDGMENT_EMOJI["HIGH"] == "🔴"


def test_judgment_order():
    # HIGH should be "worst" (highest order value for sorting)
    assert JUDGMENT_ORDER["HIGH"] > JUDGMENT_ORDER["SOME_CONCERNS"]
    assert JUDGMENT_ORDER["SOME_CONCERNS"] > JUDGMENT_ORDER["LOW"]
