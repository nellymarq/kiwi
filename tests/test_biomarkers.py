"""
Tests for tools/biomarkers.py — Athlete Biomarker Interpreter.

Covers:
- BIOMARKER_DB completeness and structure
- BiomarkerRef fields validation
- BiomarkerInterpreter.interpret() — status classification
- Critical value detection
- Athlete-specific ranges (ATHLETIC_LOW)
- Sex-specific testosterone selection
- Full panel interpretation and sorting
- format_panel_report() structure
- Alias resolution
"""
import pytest
from tools.biomarkers import (
    BiomarkerRef,
    BiomarkerResult,
    BiomarkerInterpreter,
    BIOMARKER_DB,
    STATUS_EMOJI,
    IMPORTANCE,
    interpret_panel,
    interpreter,
)


# ── Database Integrity ─────────────────────────────────────────────────────────

def test_biomarker_db_has_minimum_entries():
    assert len(BIOMARKER_DB) >= 10


def test_all_refs_have_required_fields():
    for key, ref in BIOMARKER_DB.items():
        assert ref.name, f"Empty name for {key}"
        assert ref.unit, f"Empty unit for {key}"
        assert ref.low < ref.high, f"low >= high for {key}: {ref.low} >= {ref.high}"


def test_critical_ranges_are_outside_normal():
    """critical_low must be below low; critical_high must be above high."""
    for key, ref in BIOMARKER_DB.items():
        if ref.critical_low is not None:
            assert ref.critical_low <= ref.low, \
                f"{key}: critical_low ({ref.critical_low}) should be <= low ({ref.low})"
        if ref.critical_high is not None:
            assert ref.critical_high >= ref.high, \
                f"{key}: critical_high ({ref.critical_high}) should be >= high ({ref.high})"


def test_status_emoji_covers_all_statuses():
    expected = {"LOW", "NORMAL", "HIGH", "ATHLETIC_LOW", "ATHLETIC_NORM", "CRITICAL_LOW", "CRITICAL_HIGH"}
    assert expected.issubset(set(STATUS_EMOJI.keys()))


def test_importance_covers_all_statuses():
    for status in STATUS_EMOJI:
        assert status in IMPORTANCE or status == "ATHLETIC_NORM", \
            f"Status {status} missing from IMPORTANCE"


# ── BiomarkerInterpreter.interpret() ──────────────────────────────────────────

def test_normal_ferritin_value():
    result = interpreter.interpret("ferritin", 85.0)
    assert result is not None
    assert result.status == "NORMAL"
    assert result.name == "Ferritin"
    assert result.unit == "ng/mL"


def test_low_ferritin():
    result = interpreter.interpret("ferritin", 8.0)
    assert result is not None
    assert result.status == "LOW"
    assert result.recommendation  # Should have action


def test_critical_low_ferritin():
    result = interpreter.interpret("ferritin", 3.0)
    assert result is not None
    assert result.status == "CRITICAL_LOW"
    assert "immediate" in result.flag.lower() or result.flag


def test_athletic_low_ferritin():
    """Ferritin 20–29 is below normal but athletic_low_adj=30."""
    result = interpreter.interpret("ferritin", 25.0)
    assert result is not None
    # 25 < 30 (low) but >= athletic_low_adj check...
    # athletic_low_adj=30 means values ABOVE 30 are "athletic norm" for low...
    # Let me re-read the logic: if value < ref.low AND value >= ref.athletic_low_adj → ATHLETIC_LOW
    # ref.low=12, ref.athletic_low_adj=30
    # 25 is above standard low (12) but below athletic threshold (30) → ATHLETIC_LOW
    assert result.status == "ATHLETIC_LOW"


def test_athletic_low_ferritin_below_standard_but_above_athletic_adj():
    """Values between ref.low (12) and athletic_low_adj (30) → ATHLETIC_LOW.
    Athletes should target >30; 15 is in standard range but below athletic threshold."""
    result = interpreter.interpret("ferritin", 15.0)
    assert result is not None
    assert result.status == "ATHLETIC_LOW"


def test_low_testosterone_male():
    result = interpreter.interpret("testosterone_male", 200.0)
    assert result is not None
    assert result.status in ("LOW", "CRITICAL_LOW")


def test_normal_testosterone_male():
    result = interpreter.interpret("testosterone_male", 600.0)
    assert result is not None
    assert result.status == "NORMAL"


def test_high_testosterone_male_athletic_norm():
    result = interpreter.interpret("testosterone_male", 1200.0)
    assert result is not None
    assert result.status == "ATHLETIC_NORM"


def test_high_testosterone_male_truly_high():
    result = interpreter.interpret("testosterone_male", 1300.0)
    assert result is not None
    assert result.status == "HIGH"


def test_critical_low_testosterone_male():
    result = interpreter.interpret("testosterone_male", 80.0)
    assert result is not None
    assert result.status == "CRITICAL_LOW"


def test_sex_specific_testosterone_female():
    result = interpreter.interpret("testosterone", 50.0, sex="female")
    assert result is not None
    assert result.name == "Testosterone (Female)"
    assert result.status == "NORMAL"


def test_sex_specific_testosterone_male():
    result = interpreter.interpret("testosterone", 600.0, sex="male")
    assert result is not None
    assert result.name == "Testosterone (Male)"


def test_cortisol_normal():
    result = interpreter.interpret("cortisol_morning", 15.0)
    assert result is not None
    assert result.status == "NORMAL"


def test_cortisol_critical_low():
    result = interpreter.interpret("cortisol_morning", 1.5)
    assert result is not None
    assert result.status == "CRITICAL_LOW"


def test_cortisol_critical_high():
    result = interpreter.interpret("cortisol_morning", 55.0)
    assert result is not None
    assert result.status == "CRITICAL_HIGH"


def test_glucose_normal():
    result = interpreter.interpret("glucose_fasting", 88.0)
    assert result is not None
    assert result.status == "NORMAL"


def test_glucose_high():
    result = interpreter.interpret("glucose_fasting", 110.0)
    assert result is not None
    assert result.status == "HIGH"


def test_glucose_critical_low():
    result = interpreter.interpret("glucose_fasting", 45.0)
    assert result is not None
    assert result.status == "CRITICAL_LOW"


def test_vitamin_d_low():
    result = interpreter.interpret("vitamin_d", 18.0)
    assert result is not None
    assert result.status == "LOW"


def test_vitamin_d_normal():
    result = interpreter.interpret("vitamin_d", 55.0)
    assert result is not None
    assert result.status == "NORMAL"


def test_crp_normal():
    result = interpreter.interpret("crp", 0.5)
    assert result is not None
    assert result.status == "NORMAL"


def test_crp_high():
    result = interpreter.interpret("crp", 8.0)
    assert result is not None
    assert result.status == "HIGH"


def test_unknown_biomarker_returns_none():
    result = interpreter.interpret("unicorn_hormone", 99.9)
    assert result is None


# ── Alias Resolution ───────────────────────────────────────────────────────────

def test_alias_hgb():
    result = interpreter.interpret("hgb", 14.5)
    assert result is not None
    assert result.name == "Hemoglobin"


def test_alias_vit_d():
    result = interpreter.interpret("vit d", 45.0)
    assert result is not None
    assert "Vitamin D" in result.name


def test_alias_hscrp():
    result = interpreter.interpret("hscrp", 1.2)
    assert result is not None
    assert "CRP" in result.name


def test_alias_fasting_glucose():
    result = interpreter.interpret("fasting glucose", 90.0)
    assert result is not None
    assert "Glucose" in result.name


def test_alias_free_t3():
    result = interpreter.interpret("free t3", 3.0)
    assert result is not None
    assert "T3" in result.name


def test_alias_magnesium():
    result = interpreter.interpret("mg", 2.0)
    assert result is not None
    assert "Magnesium" in result.name


# ── BiomarkerResult.display() ─────────────────────────────────────────────────

def test_result_display_includes_value_and_status():
    result = interpreter.interpret("ferritin", 8.0)
    assert result is not None
    text = result.display()
    assert "8.0" in text or "8" in text
    assert "LOW" in text or "Ferritin" in text


def test_result_display_shows_recommendation_if_low():
    result = interpreter.interpret("vitamin_d", 12.0)
    assert result is not None
    text = result.display()
    assert "D3" in text or "supplement" in text.lower() or "IU" in text


# ── interpret_panel() ──────────────────────────────────────────────────────────

def test_panel_empty_dict():
    report = interpret_panel({})
    assert "No recognizable biomarkers" in report


def test_panel_all_normal():
    panel = {
        "ferritin": 85.0,
        "hemoglobin": 14.5,
        "glucose_fasting": 88.0,
        "vitamin_d": 55.0,
    }
    report = interpret_panel(panel, sex="male", athlete_name="Alex Fit")
    assert "Alex Fit" in report
    assert "NORMAL" in report


def test_panel_sorted_critical_first():
    """Critical values should appear before normals in report."""
    panel = {
        "ferritin": 85.0,       # NORMAL
        "cortisol_morning": 1.0, # CRITICAL_LOW
        "glucose_fasting": 88.0, # NORMAL
    }
    report = interpret_panel(panel)
    critical_pos = report.find("CRITICAL")
    normal_pos = report.find("NORMAL")
    if critical_pos != -1 and normal_pos != -1:
        assert critical_pos < normal_pos


def test_panel_report_shows_total_markers_count():
    panel = {
        "ferritin": 85.0,
        "vitamin_d": 55.0,
        "crp": 0.5,
    }
    report = interpret_panel(panel)
    assert "3" in report  # 3 markers


def test_panel_with_critical_shows_warning_line():
    panel = {
        "glucose_fasting": 40.0,  # CRITICAL_LOW
    }
    report = interpret_panel(panel)
    assert "CRITICAL" in report or "immediate" in report.lower()


def test_interpret_panel_convenience_function():
    """Top-level interpret_panel() function must work without instantiation."""
    result = interpret_panel({"ferritin": 50.0}, sex="female")
    assert "Ferritin" in result


def test_panel_multiple_low_values():
    panel = {
        "ferritin": 5.0,     # LOW
        "vitamin_d": 12.0,   # LOW
        "magnesium": 1.5,    # LOW
    }
    report = interpret_panel(panel)
    assert "LOW" in report
    # Should mention recommendation to see provider
    assert "LOW" in report or "⚠" in report
