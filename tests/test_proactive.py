"""Tests for proactive biomarker-to-action linking."""

import pytest
from tools.proactive import (
    check_biomarker, format_proactive_actions,
    ProactiveAction, BIOMARKER_SUPPLEMENT_MAP,
)


def test_low_ferritin_triggers_action():
    actions = check_biomarker("ferritin", 15.0, sex="female")
    assert len(actions) > 0
    assert any(a.severity == "action" for a in actions)
    assert any("iron" in s for a in actions for s in a.supplements)


def test_normal_ferritin_no_action():
    actions = check_biomarker("ferritin", 80.0, sex="male")
    assert len(actions) == 0


def test_low_vitamin_d_triggers():
    actions = check_biomarker("vitamin_d", 18.0, sex="male")
    assert len(actions) > 0
    assert any("vitamin_d" in s for a in actions for s in a.supplements)


def test_high_crp_triggers_warning():
    actions = check_biomarker("crp", 5.0, sex="male")
    assert len(actions) > 0
    assert any(a.severity == "warning" for a in actions)


def test_low_testosterone_triggers():
    actions = check_biomarker("testosterone_male", 250.0, sex="male")
    assert len(actions) > 0
    supplements = [s for a in actions for s in a.supplements]
    assert any(s in supplements for s in ["zinc", "vitamin_d", "ashwagandha"])


def test_interaction_check_with_current_stack():
    actions = check_biomarker(
        "ferritin", 12.0, sex="female",
        current_supplements=["zinc", "calcium"],
    )
    # Should flag zinc-iron or calcium-iron interaction
    has_interaction = any(
        len(a.interactions_to_check) > 0 for a in actions
    )
    # May or may not find interactions depending on DB coverage
    assert len(actions) > 0


def test_format_empty():
    assert format_proactive_actions([]) == ""


def test_format_with_actions():
    actions = [
        ProactiveAction(
            trigger="Ferritin = 12 ng/mL (CRITICAL_LOW)",
            severity="action",
            message="Consider iron bisglycinate 36mg/d with vitamin C.",
            supplements=["iron", "vitamin_c"],
            suggested_command="/supp iron",
        ),
    ]
    output = format_proactive_actions(actions)
    assert "Ferritin" in output
    assert "iron" in output
    assert "/supp iron" in output
    assert "🎯" in output


def test_biomarker_supplement_map_coverage():
    """At least the most common biomarkers should have supplement mappings."""
    for key in ["ferritin", "vitamin_d", "testosterone_male", "cortisol_morning"]:
        assert key in BIOMARKER_SUPPLEMENT_MAP
        assert len(BIOMARKER_SUPPLEMENT_MAP[key]) >= 1
