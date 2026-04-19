"""Tests for mental performance tool."""
import pytest

from tools.mental_performance import (
    VISUALIZATION_DB,
    AnxietyAssessment,
    BurnoutAssessment,
    MentalFatigueAssessment,
    PreCompetitionRoutine,
    assess_burnout,
    assess_competition_anxiety,
    assess_mental_fatigue,
    format_anxiety_report,
    format_burnout_report,
    format_visualization,
    generate_pre_competition_routine,
    get_visualization_protocol,
    list_visualization_protocols,
)


# ── Visualization Database Tests ─────────────────────────────────────────────

EXPECTED_PROTOCOLS = [
    "performance_rehearsal", "relaxation_imagery",
    "confidence_building", "injury_recovery",
]


class TestVisualizationDatabase:
    def test_all_protocols_present(self):
        for name in EXPECTED_PROTOCOLS:
            assert name in VISUALIZATION_DB

    @pytest.mark.parametrize("key", EXPECTED_PROTOCOLS)
    def test_protocol_has_required_fields(self, key):
        proto = VISUALIZATION_DB[key]
        assert proto.name
        assert proto.purpose
        assert len(proto.modalities) > 0
        assert len(proto.script) > 0
        assert proto.duration_minutes > 0
        assert proto.frequency
        assert proto.evidence

    @pytest.mark.parametrize("key", EXPECTED_PROTOCOLS)
    def test_protocol_has_evidence_tier(self, key):
        proto = VISUALIZATION_DB[key]
        assert any(tier in proto.evidence for tier in ["🟢", "🟡", "🟠", "🔵"])

    def test_protocol_lookup(self):
        proto = get_visualization_protocol("performance_rehearsal")
        assert proto is not None
        assert "Rehearsal" in proto.name

    def test_protocol_lookup_missing(self):
        assert get_visualization_protocol("nonexistent") is None

    def test_list_protocols(self):
        output = list_visualization_protocols()
        assert "performance_rehearsal" in output
        assert "Total:" in output


# ── Competition Anxiety Tests ────────────────────────────────────────────────

class TestCompetitionAnxiety:
    def test_optimal_profile(self):
        result = assess_competition_anxiety(1.5, 2.0, 3.5)
        assert isinstance(result, AnxietyAssessment)
        assert result.overall_profile == "optimal"

    def test_debilitative_profile(self):
        result = assess_competition_anxiety(3.5, 3.5, 1.5)
        assert result.overall_profile == "debilitative"

    def test_facilitative_profile(self):
        result = assess_competition_anxiety(1.5, 1.0, 3.5)
        assert result.overall_profile == "facilitative"

    def test_mixed_profile(self):
        result = assess_competition_anxiety(2.5, 2.5, 2.5)
        assert result.overall_profile == "mixed"

    def test_has_strategies(self):
        result = assess_competition_anxiety(3.0, 3.0, 1.5)
        assert len(result.strategies) > 0

    def test_high_cognitive_gets_restructuring(self):
        result = assess_competition_anxiety(3.5, 1.5, 3.0)
        strategies_text = " ".join(result.strategies).lower()
        assert "cognitive" in strategies_text or "self-talk" in strategies_text

    def test_high_somatic_gets_relaxation(self):
        result = assess_competition_anxiety(1.5, 3.5, 3.0)
        strategies_text = " ".join(result.strategies).lower()
        assert "relax" in strategies_text or "breathing" in strategies_text

    def test_low_confidence_gets_building(self):
        result = assess_competition_anxiety(2.0, 2.0, 1.5)
        strategies_text = " ".join(result.strategies).lower()
        assert "confidence" in strategies_text or "imagery" in strategies_text

    def test_invalid_score_raises(self):
        with pytest.raises(ValueError):
            assess_competition_anxiety(0.5, 2.0, 3.0)

    def test_invalid_score_high_raises(self):
        with pytest.raises(ValueError):
            assess_competition_anxiety(2.0, 5.0, 3.0)

    def test_has_evidence(self):
        result = assess_competition_anxiety(2.0, 2.0, 3.0)
        assert "CSAI" in result.evidence


# ── Mental Fatigue Tests ─────────────────────────────────────────────────────

class TestMentalFatigue:
    def test_low_fatigue(self):
        result = assess_mental_fatigue(2.0, 8.5, 5.0, life_stress=1.0, screen_time_hours=2.0)
        assert isinstance(result, MentalFatigueAssessment)
        assert result.fatigue_level == "low"
        assert result.performance_impact_pct == 0.0

    def test_moderate_fatigue(self):
        result = assess_mental_fatigue(3.0, 7.5, 5.0, life_stress=2.0, screen_time_hours=3.0)
        assert result.fatigue_level in ("low", "moderate")

    def test_high_fatigue(self):
        result = assess_mental_fatigue(7.0, 5.5, 8.0, life_stress=4.0, screen_time_hours=6.0)
        assert result.fatigue_level in ("high", "severe")
        assert result.performance_impact_pct > 5.0

    def test_sleep_deprivation_impact(self):
        good_sleep = assess_mental_fatigue(3.0, 8.0, 5.0)
        bad_sleep = assess_mental_fatigue(3.0, 4.5, 5.0)
        assert bad_sleep.fatigue_score > good_sleep.fatigue_score

    def test_has_contributing_factors(self):
        result = assess_mental_fatigue(7.0, 5.0, 8.0, life_stress=4.5, screen_time_hours=7.0)
        assert len(result.contributing_factors) >= 2

    def test_has_recovery_strategies(self):
        result = assess_mental_fatigue(6.0, 6.0, 5.0)
        assert len(result.recovery_strategies) >= 2

    def test_severe_has_rest_day(self):
        result = assess_mental_fatigue(9.0, 4.0, 8.0, life_stress=5.0, screen_time_hours=8.0)
        mods = " ".join(result.training_modifications).lower()
        assert "rest" in mods or "recovery" in mods

    def test_has_evidence(self):
        result = assess_mental_fatigue(5.0, 7.0, 5.0)
        assert "Van Cutsem" in result.evidence or "mental fatigue" in result.evidence.lower()


# ── Burnout Assessment Tests ─────────────────────────────────────────────────

class TestBurnout:
    def test_low_risk(self):
        stress = {"general_stress": 1.5, "training_stress": 1.0, "emotional_stress": 1.5}
        recovery = {"sleep_quality": 5.0, "social_recovery": 4.5, "physical_recovery": 5.0}
        result = assess_burnout(stress, recovery)
        assert isinstance(result, BurnoutAssessment)
        assert result.risk_level == "low"

    def test_high_risk(self):
        stress = {"general_stress": 4.5, "training_stress": 5.0, "emotional_stress": 4.0}
        recovery = {"sleep_quality": 2.0, "social_recovery": 1.5, "physical_recovery": 2.5}
        result = assess_burnout(stress, recovery)
        assert result.risk_level in ("high", "critical")

    def test_critical_risk(self):
        stress = {"general_stress": 5.5, "training_stress": 5.5, "emotional_stress": 5.0}
        recovery = {"sleep_quality": 1.0, "social_recovery": 1.0, "physical_recovery": 1.5}
        result = assess_burnout(stress, recovery)
        assert result.risk_level == "critical"

    def test_balance_ratio(self):
        stress = {"training_stress": 2.0}
        recovery = {"sleep_quality": 4.0}
        result = assess_burnout(stress, recovery)
        assert result.balance_ratio == 2.0

    def test_identifies_risk_factors(self):
        stress = {"training_stress": 5.0, "general_stress": 2.0}
        recovery = {"sleep_quality": 1.5, "physical_recovery": 4.0}
        result = assess_burnout(stress, recovery)
        factor_text = " ".join(result.risk_factors).lower()
        assert "training" in factor_text or "sleep" in factor_text

    def test_has_interventions(self):
        stress = {"training_stress": 4.0}
        recovery = {"sleep_quality": 2.0}
        result = assess_burnout(stress, recovery)
        assert len(result.intervention_strategies) >= 2

    def test_has_evidence(self):
        result = assess_burnout({"stress": 2.0}, {"recovery": 4.0})
        assert "REST-Q" in result.evidence or "Kellmann" in result.evidence


# ── Pre-Competition Routine Tests ────────────────────────────────────────────

class TestPreCompetitionRoutine:
    def test_basic_routine(self):
        result = generate_pre_competition_routine(3.0)
        assert isinstance(result, PreCompetitionRoutine)
        assert len(result.physical_actions) >= 3
        assert len(result.mental_actions) >= 2

    def test_high_anxiety_routine(self):
        result = generate_pre_competition_routine(3.0, anxiety_level="high")
        mental = " ".join(result.mental_actions).lower()
        assert "relax" in mental or "breathing" in mental

    def test_low_anxiety_routine(self):
        result = generate_pre_competition_routine(3.0, anxiety_level="low")
        mental = " ".join(result.mental_actions).lower()
        assert "energi" in mental or "activat" in mental

    def test_has_cue_words(self):
        result = generate_pre_competition_routine()
        assert len(result.cue_words) >= 3

    def test_has_contingency_plans(self):
        result = generate_pre_competition_routine()
        assert len(result.contingency_plans) >= 3

    def test_has_nutrition_timing(self):
        result = generate_pre_competition_routine(3.0)
        assert len(result.nutrition_timing) >= 2

    def test_has_evidence(self):
        result = generate_pre_competition_routine()
        assert "Weinberg" in result.evidence or "routine" in result.evidence.lower()


# ── Formatting Tests ─────────────────────────────────────────────────────────

class TestFormatting:
    def test_format_anxiety_report(self):
        assessment = assess_competition_anxiety(2.0, 2.5, 3.0)
        report = format_anxiety_report(assessment)
        assert "Anxiety" in report
        assert "Cognitive" in report

    def test_format_burnout_report(self):
        assessment = assess_burnout({"stress": 3.0}, {"recovery": 3.0})
        report = format_burnout_report(assessment)
        assert "Burnout" in report
        assert "Stress" in report

    def test_format_visualization(self):
        proto = get_visualization_protocol("performance_rehearsal")
        assert proto is not None
        report = format_visualization(proto)
        assert proto.name in report
        assert "Script" in report
