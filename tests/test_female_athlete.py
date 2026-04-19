"""Tests for female athlete health tool."""
import pytest

from tools.female_athlete import (
    CYCLE_PHASES,
    CyclePhase,
    EnergyAvailability,
    PostpartumProtocol,
    REDSScreening,
    calculate_energy_availability,
    calculate_iron_needs,
    format_cycle_training,
    format_ea_report,
    format_reds_report,
    get_cycle_phase,
    match_training_to_phase,
    postpartum_return_protocol,
    screen_reds,
)


# ── Energy Availability Tests ────────────────────────────────────────────────

class TestEnergyAvailability:
    def test_optimal_ea(self):
        # 2500 intake - 500 EEE = 2000, / 40 FFM = 50 kcal/kg
        result = calculate_energy_availability(2500, 500, 40.0)
        assert isinstance(result, EnergyAvailability)
        assert result.ea_value == 50.0
        assert result.classification == "optimal"
        assert result.risk_level == "low"

    def test_reduced_ea(self):
        # 2000 - 500 = 1500, / 40 = 37.5
        result = calculate_energy_availability(2000, 500, 40.0)
        assert result.ea_value == 37.5
        assert result.classification == "reduced"
        assert result.risk_level == "moderate"

    def test_low_ea(self):
        # 1700 - 500 = 1200, / 40 = 30 → boundary
        # Try 1600 - 500 = 1100, / 40 = 27.5
        result = calculate_energy_availability(1600, 500, 40.0)
        assert result.ea_value == 27.5
        assert result.classification == "low"
        assert result.risk_level == "high"

    def test_severe_ea(self):
        # 1200 - 500 = 700, / 40 = 17.5
        result = calculate_energy_availability(1200, 500, 40.0)
        assert result.ea_value == 17.5
        assert result.classification == "severe"
        assert result.risk_level == "critical"

    def test_boundary_45(self):
        # Exactly 45: 2300 - 500 = 1800, / 40 = 45.0
        result = calculate_energy_availability(2300, 500, 40.0)
        assert result.ea_value == 45.0
        assert result.classification == "optimal"

    def test_boundary_30(self):
        # Exactly 30: 1700 - 500 = 1200, / 40 = 30.0
        result = calculate_energy_availability(1700, 500, 40.0)
        assert result.ea_value == 30.0
        assert result.classification == "reduced"

    def test_zero_ffm_raises(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_energy_availability(2000, 500, 0.0)

    def test_negative_ffm_raises(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_energy_availability(2000, 500, -10.0)

    def test_has_evidence(self):
        result = calculate_energy_availability(2500, 500, 40.0)
        assert "Loucks" in result.evidence

    def test_has_recommendations(self):
        result = calculate_energy_availability(1200, 500, 40.0)
        assert len(result.recommendations) >= 3


# ── Cycle Phase Tests ────────────────────────────────────────────────────────

class TestCyclePhase:
    def test_all_phases_defined(self):
        assert len(CYCLE_PHASES) == 5

    @pytest.mark.parametrize("day,expected_phase", [
        (1, "early_follicular"),
        (3, "early_follicular"),
        (5, "early_follicular"),
        (6, "late_follicular"),
        (10, "late_follicular"),
        (13, "late_follicular"),
        (14, "ovulation"),
        (15, "early_luteal"),
        (18, "early_luteal"),
        (21, "early_luteal"),
        (22, "late_luteal"),
        (25, "late_luteal"),
        (28, "late_luteal"),
    ])
    def test_cycle_phase_identification(self, day, expected_phase):
        phase = get_cycle_phase(day)
        assert isinstance(phase, CyclePhase)
        assert phase.phase_name == expected_phase

    def test_invalid_day_zero(self):
        with pytest.raises(ValueError):
            get_cycle_phase(0)

    def test_invalid_day_29(self):
        with pytest.raises(ValueError):
            get_cycle_phase(29)

    @pytest.mark.parametrize("day", range(1, 29))
    def test_all_days_have_phase(self, day):
        phase = get_cycle_phase(day)
        assert phase.phase_name in (
            "early_follicular", "late_follicular", "ovulation",
            "early_luteal", "late_luteal",
        )

    def test_phase_has_hormonal_profile(self):
        for phase in CYCLE_PHASES:
            assert phase.hormonal_profile

    def test_phase_has_training_recommendations(self):
        for phase in CYCLE_PHASES:
            assert phase.training_recommendations

    def test_phase_has_nutrition_notes(self):
        for phase in CYCLE_PHASES:
            assert phase.nutrition_notes


# ── Training Matching Tests ──────────────────────────────────────────────────

class TestTrainingMatching:
    def test_late_follicular_high_intensity(self):
        result = match_training_to_phase(10)
        assert result["intensity_modifier"] > 1.0
        assert "high-intensity" in result["recommended_focus"].lower() or "PR" in result["recommended_focus"]

    def test_ovulation_injury_risk(self):
        result = match_training_to_phase(14)
        assert "ACL" in result["injury_risk_notes"]
        assert result["intensity_modifier"] < 1.0

    def test_late_luteal_reduced(self):
        result = match_training_to_phase(25)
        assert result["intensity_modifier"] < 1.0

    def test_has_key_nutrients(self):
        result = match_training_to_phase(1)
        assert len(result["key_nutrients"]) > 0
        assert any("iron" in n.lower() for n in result["key_nutrients"])

    def test_returns_phase(self):
        result = match_training_to_phase(14)
        assert isinstance(result["phase"], CyclePhase)


# ── RED-S Screening Tests ────────────────────────────────────────────────────

class TestREDSScreening:
    def test_low_risk(self):
        result = screen_reds({"bmi": 22, "menstrual_status": "regular"})
        assert isinstance(result, REDSScreening)
        assert result.risk_level == "low"
        assert result.referral_needed is False

    def test_moderate_risk(self):
        result = screen_reds({
            "bmi": 20,
            "menstrual_status": "irregular",
            "declining_performance": True,
            "mood_disturbance": True,
            "weight_loss_pct": 6,
        })
        assert result.risk_level in ("moderate", "high")
        assert result.risk_score >= 3

    def test_high_risk(self):
        result = screen_reds({
            "bmi": 17,
            "menstrual_status": "amenorrheic",
            "disordered_eating": True,
            "bone_stress_injuries": 2,
        })
        assert result.risk_level == "high"
        assert result.referral_needed is True

    def test_red_flag_amenorrhea(self):
        result = screen_reds({"menstrual_status": "amenorrheic"})
        assert result.risk_level == "high"
        assert any("menorrhea" in s.lower() or "amenorrhea" in s.lower() for s in result.clinical_signs)

    def test_red_flag_low_bmi(self):
        result = screen_reds({"bmi": 16.5})
        assert result.risk_level == "high"
        assert any("bmi" in s.lower() for s in result.clinical_signs)

    def test_red_flag_multiple_bsi(self):
        result = screen_reds({"bone_stress_injuries": 3})
        assert result.risk_level == "high"

    def test_has_evidence(self):
        result = screen_reds({})
        assert "Mountjoy" in result.evidence

    def test_has_recommendations(self):
        result = screen_reds({"menstrual_status": "amenorrheic"})
        assert len(result.recommendations) >= 3


# ── Postpartum Protocol Tests ────────────────────────────────────────────────

class TestPostpartum:
    def test_immediate_recovery(self):
        result = postpartum_return_protocol(1)
        assert isinstance(result, PostpartumProtocol)
        assert result.phase == "immediate_recovery"

    def test_early_return(self):
        result = postpartum_return_protocol(4)
        assert result.phase == "early_return"

    def test_progressive_loading(self):
        result = postpartum_return_protocol(8)
        assert result.phase == "progressive_loading"

    def test_return_to_sport(self):
        result = postpartum_return_protocol(16)
        assert result.phase == "return_to_sport"

    def test_full_return(self):
        result = postpartum_return_protocol(30)
        assert result.phase == "full_return"

    def test_csection_delays_phase(self):
        csection = postpartum_return_protocol(5, delivery_type="c-section")
        # C-section at 5 weeks → effective 3 weeks → early_return
        assert csection.phase in ("immediate_recovery", "early_return")

    def test_diastasis_recti_modification(self):
        result = postpartum_return_protocol(8, complications=["diastasis_recti"])
        combined = " ".join(result.exercise_guidelines + result.contraindications)
        assert "diastasis" in combined.lower()

    def test_pelvic_floor_modification(self):
        result = postpartum_return_protocol(8, complications=["pelvic_floor_dysfunction"])
        combined = " ".join(result.exercise_guidelines + result.contraindications)
        assert "pelvic floor" in combined.lower()

    def test_has_references(self):
        result = postpartum_return_protocol(1)
        assert len(result.key_references) >= 2


# ── Iron Needs Tests ─────────────────────────────────────────────────────────

class TestIronNeeds:
    def test_baseline(self):
        result = calculate_iron_needs("regular", 3.0)
        assert result["rda_mg"] == 18.0
        assert result["recommended_mg"] == 18.0

    def test_high_volume(self):
        result = calculate_iron_needs("regular", 15.0)
        assert result["recommended_mg"] > 25.0

    def test_vegetarian_multiplier(self):
        omni = calculate_iron_needs("regular", 10.0)
        veg = calculate_iron_needs("regular", 10.0, dietary_pattern="vegetarian")
        assert veg["recommended_mg"] > omni["recommended_mg"]

    def test_amenorrheic_lower_needs(self):
        regular = calculate_iron_needs("regular", 5.0)
        amenorrheic = calculate_iron_needs("amenorrheic", 5.0)
        assert amenorrheic["recommended_mg"] < regular["recommended_mg"]

    def test_has_monitoring_advice(self):
        result = calculate_iron_needs("regular", 10.0)
        assert "ferritin" in result["monitoring"].lower()

    def test_has_rationale(self):
        result = calculate_iron_needs("regular", 15.0, "vegan")
        assert "multiplier" in result["rationale"].lower()


# ── Formatting Tests ─────────────────────────────────────────────────────────

class TestFormatting:
    def test_format_ea_report(self):
        ea = calculate_energy_availability(2500, 500, 40.0)
        report = format_ea_report(ea)
        assert "Energy Availability" in report
        assert "50.0" in report
        assert "OPTIMAL" in report

    def test_format_reds_report(self):
        screening = screen_reds({"menstrual_status": "amenorrheic"})
        report = format_reds_report(screening)
        assert "RED-S" in report
        assert "HIGH" in report

    def test_format_cycle_training(self):
        phase = get_cycle_phase(10)
        report = format_cycle_training(phase)
        assert "Late Follicular" in report
        assert "Training" in report
