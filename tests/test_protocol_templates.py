"""Tests for protocol templates."""

import pytest
from tools.protocol_templates import get_template, list_templates, TEMPLATES


def test_weight_cut_exists():
    t = get_template("weight_cut")
    assert t is not None
    assert "Combat Sports" in t.name
    assert "Day -7" in t.content


def test_muscle_gain_exists():
    t = get_template("muscle_gain")
    assert t is not None
    assert "12" in t.duration
    assert "creatine" in t.content.lower()


def test_iron_repletion_exists():
    t = get_template("iron_repletion")
    assert t is not None
    assert "ferritin" in t.content.lower()
    assert "bisglycinate" in t.content.lower()


def test_female_athlete_exists():
    t = get_template("female_athlete_health")
    assert t is not None
    assert "RED-S" in t.content
    assert "amenorrhea" in t.content


def test_endurance_build_exists():
    t = get_template("endurance_build")
    assert t is not None
    assert "Zone 2" in t.content


def test_all_templates_have_required_fields():
    for key, t in TEMPLATES.items():
        assert t.name, f"{key} missing name"
        assert t.category, f"{key} missing category"
        assert t.description, f"{key} missing description"
        assert t.duration, f"{key} missing duration"
        assert len(t.content) > 200, f"{key} content too short"
        assert len(t.related_commands) >= 1, f"{key} missing related commands"


def test_get_template_case_insensitive():
    assert get_template("Weight_Cut") is not None
    assert get_template("WEIGHT_CUT") is not None


def test_get_template_nonexistent():
    assert get_template("unicorn_protocol") is None


def test_list_templates_format():
    output = list_templates()
    assert "weight_cut" in output
    assert "muscle_gain" in output
    assert "iron_repletion" in output
    assert "Duration:" in output
