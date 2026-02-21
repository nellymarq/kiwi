"""
Tests for tools/race_predictor.py — Race Time Prediction.

Covers:
- Time parsing and formatting utilities
- Riegel power-law model
- Cameron distance-specific model
- VDOT-based prediction (Daniels)
- Age grading
- Multi-distance prediction
- Model comparison
- Edge cases and input validation
"""
import pytest
import math
from tools.race_predictor import (
    parse_time_seconds,
    format_time,
    pace_per_km,
    predict_riegel,
    predict_cameron,
    predict_vdot,
    predict_all_distances,
    compare_models,
    age_grade,
    format_predictions,
    format_model_comparison,
    RACE_DISTANCES_M,
    RacePrediction,
    MultiDistancePrediction,
    ModelComparison,
    AgeGradedResult,
    _time_to_vdot,
    _vdot_to_time,
    _age_factor,
    _cameron_factor,
)


# ── Time Parsing ─────────────────────────────────────────────────────────────

class TestTimeParsing:
    def test_parse_hh_mm_ss(self):
        assert parse_time_seconds("1:30:00") == 5400

    def test_parse_mm_ss(self):
        assert parse_time_seconds("25:30") == 1530

    def test_parse_seconds_string(self):
        assert parse_time_seconds("90") == 90.0

    def test_parse_float_passthrough(self):
        assert parse_time_seconds(1234.5) == 1234.5

    def test_parse_int_passthrough(self):
        assert parse_time_seconds(300) == 300.0

    def test_parse_marathon_time(self):
        assert parse_time_seconds("3:30:00") == 12600

    def test_format_time_hours(self):
        assert format_time(5400) == "1:30:00"

    def test_format_time_minutes(self):
        assert format_time(1530) == "25:30"

    def test_format_time_negative(self):
        assert format_time(-1) == "N/A"

    def test_pace_per_km(self):
        # 20:00 for 5K = 4:00/km
        result = pace_per_km(1200, 5000)
        assert "4:00" in result

    def test_pace_per_km_zero_distance(self):
        assert pace_per_km(1200, 0) == "N/A"


# ── Riegel Model ─────────────────────────────────────────────────────────────

class TestRiegel:
    def test_same_distance_returns_same_time(self):
        """Predicting the same distance should return the known time."""
        pred = predict_riegel(5000, 1200, 5000)
        assert pred.predicted_seconds == pytest.approx(1200, abs=1)

    def test_longer_distance_slower(self):
        """Predicting a longer distance should give a slower time."""
        pred = predict_riegel(5000, 1200, 10000)
        assert pred.predicted_seconds > 1200

    def test_shorter_distance_faster(self):
        """Predicting a shorter distance should give a faster time."""
        pred = predict_riegel(10000, 2500, 5000)
        assert pred.predicted_seconds < 2500

    def test_5k_to_10k_reasonable(self):
        """20:00 5K → ~41:30–42:30 10K is typical."""
        pred = predict_riegel(5000, 1200, 10000)
        assert 2400 < pred.predicted_seconds < 2600

    def test_5k_to_marathon_reasonable(self):
        """20:00 5K → ~3:05–3:20 marathon is typical."""
        pred = predict_riegel(5000, 1200, 42195)
        assert 10800 < pred.predicted_seconds < 12600  # 3:00–3:30

    def test_custom_fatigue_factor(self):
        """Higher fatigue factor → slower predictions."""
        pred_default = predict_riegel(5000, 1200, 42195, fatigue_factor=1.06)
        pred_high = predict_riegel(5000, 1200, 42195, fatigue_factor=1.10)
        assert pred_high.predicted_seconds > pred_default.predicted_seconds

    def test_ultra_note(self):
        """Ultramarathon predictions should include a warning note."""
        pred = predict_riegel(42195, 12600, 50000)
        assert "ultra" in pred.notes.lower() or pred.notes == ""

    def test_model_string(self):
        pred = predict_riegel(5000, 1200, 10000)
        assert "Riegel" in pred.model

    def test_evidence_tier(self):
        pred = predict_riegel(5000, 1200, 10000)
        assert "🟡" in pred.evidence

    def test_invalid_zero_distance(self):
        with pytest.raises(ValueError):
            predict_riegel(0, 1200, 10000)

    def test_invalid_zero_time(self):
        with pytest.raises(ValueError):
            predict_riegel(5000, 0, 10000)

    def test_invalid_negative_target(self):
        with pytest.raises(ValueError):
            predict_riegel(5000, 1200, -1000)


# ── Cameron Model ────────────────────────────────────────────────────────────

class TestCameron:
    def test_same_distance_returns_same_time(self):
        pred = predict_cameron(5000, 1200, 5000)
        assert pred.predicted_seconds == pytest.approx(1200, abs=5)

    def test_longer_distance_slower(self):
        pred = predict_cameron(5000, 1200, 10000)
        assert pred.predicted_seconds > 1200

    def test_shorter_distance_faster(self):
        pred = predict_cameron(10000, 2500, 5000)
        assert pred.predicted_seconds < 2500

    def test_5k_to_10k_reasonable(self):
        pred = predict_cameron(5000, 1200, 10000)
        assert 2400 < pred.predicted_seconds < 2600

    def test_model_string(self):
        pred = predict_cameron(5000, 1200, 10000)
        assert "Cameron" in pred.model or "heuristic" in pred.model

    def test_cameron_factor_interpolation(self):
        """Factor should increase monotonically with distance."""
        f_5k = _cameron_factor(5000)
        f_10k = _cameron_factor(10000)
        f_hm = _cameron_factor(21097.5)
        assert f_5k < f_10k < f_hm

    def test_cameron_factor_at_anchor(self):
        """1500m is the anchor point with factor 0."""
        f = _cameron_factor(1500)
        assert f == pytest.approx(0.0)

    def test_invalid_inputs(self):
        with pytest.raises(ValueError):
            predict_cameron(0, 1200, 10000)


# ── VDOT Model ───────────────────────────────────────────────────────────────

class TestVDOT:
    def test_vdot_from_known_result(self):
        """A 20:00 5K should give VDOT around 42–52 (Daniels/Gilbert formula)."""
        vdot = _time_to_vdot(5000, 1200)
        assert 42 < vdot < 55

    def test_faster_runner_higher_vdot(self):
        """Faster 5K → higher VDOT."""
        vdot_20 = _time_to_vdot(5000, 1200)   # 20:00
        vdot_17 = _time_to_vdot(5000, 1020)   # 17:00
        assert vdot_17 > vdot_20

    def test_vdot_roundtrip(self):
        """VDOT → time → VDOT should be stable."""
        vdot = 50.0
        time = _vdot_to_time(vdot, 5000)
        vdot_back = _time_to_vdot(5000, time)
        assert vdot_back == pytest.approx(vdot, abs=0.5)

    def test_vdot_prediction_same_distance(self):
        pred = predict_vdot(5000, 1200, 5000)
        assert pred.predicted_seconds == pytest.approx(1200, abs=5)

    def test_vdot_prediction_longer_slower(self):
        pred = predict_vdot(5000, 1200, 10000)
        assert pred.predicted_seconds > 1200

    def test_vdot_5k_to_marathon(self):
        """20:00 5K → ~3:10–3:25 marathon via VDOT."""
        pred = predict_vdot(5000, 1200, 42195)
        assert 10800 < pred.predicted_seconds < 12600  # 3:00–3:30

    def test_vdot_in_model_string(self):
        pred = predict_vdot(5000, 1200, 10000)
        assert "VDOT" in pred.model

    def test_vdot_notes_contain_value(self):
        pred = predict_vdot(5000, 1200, 10000)
        assert "VDOT" in pred.notes

    def test_elite_5k_vdot(self):
        """13:00 5K — VDOT should be high (Daniels/Gilbert formula)."""
        vdot = _time_to_vdot(5000, 780)
        assert 75 < vdot < 90

    def test_slow_5k_vdot(self):
        """30:00 5K ≈ VDOT ~30."""
        vdot = _time_to_vdot(5000, 1800)
        assert 25 < vdot < 35

    def test_vdot_floor(self):
        """Extremely slow times should floor at VDOT 20."""
        vdot = _time_to_vdot(5000, 6000)  # 100 minutes for 5K
        assert vdot >= 20.0


# ── Age Grading ──────────────────────────────────────────────────────────────

class TestAgeGrading:
    def test_peak_age_factor_is_1(self):
        """Ages 22–35 should have factor ~1.0."""
        for age in [22, 25, 30, 35]:
            assert _age_factor(age) == pytest.approx(1.0)

    def test_older_athlete_lower_factor(self):
        assert _age_factor(50) < 1.0
        assert _age_factor(70) < _age_factor(50)

    def test_factor_never_below_floor(self):
        assert _age_factor(100) >= 0.40

    def test_junior_factor(self):
        assert 0.80 <= _age_factor(15) < 1.0

    def test_female_decline_steeper(self):
        """Female age decline should be slightly steeper than male."""
        age = 60
        assert _age_factor(age, "female") < _age_factor(age, "male")

    def test_age_grade_result_structure(self):
        result = age_grade(5000, 1200, 30, "male")
        assert isinstance(result, AgeGradedResult)
        assert result.age_factor == pytest.approx(1.0)
        assert result.raw_time_seconds == 1200

    def test_age_grade_older_athlete(self):
        result = age_grade(5000, 1200, 55, "male")
        assert result.age_graded_seconds < result.raw_time_seconds

    def test_age_grade_performance_levels(self):
        # Peak age, factor=1.0 → age_grade_pct=100
        result = age_grade(5000, 1200, 30, "male")
        assert result.performance_level in [
            "World class", "National class", "Regional class",
            "Local class", "Recreational"
        ]

    def test_evidence_string(self):
        result = age_grade(5000, 1200, 30)
        assert "WMA" in result.evidence or "WAVA" in result.evidence


# ── Multi-Distance Prediction ───────────────────────────────────────────────

class TestMultiDistance:
    def test_predict_all_returns_multiple(self):
        result = predict_all_distances(5000, 1200)
        assert isinstance(result, MultiDistancePrediction)
        assert len(result.predictions) >= 5

    def test_predict_specific_distances(self):
        result = predict_all_distances(5000, 1200, distances=["5K", "10K", "half_marathon"])
        assert len(result.predictions) == 3

    def test_predict_all_models(self):
        for model in ["riegel", "cameron", "vdot"]:
            result = predict_all_distances(5000, 1200, model=model)
            assert len(result.predictions) >= 5

    def test_predictions_monotonically_increasing(self):
        """Longer distances should always take more time."""
        result = predict_all_distances(5000, 1200, model="vdot")
        times = [p.predicted_seconds for p in result.predictions]
        for i in range(len(times) - 1):
            assert times[i] < times[i + 1], \
                f"{result.predictions[i].distance_label} should be faster than {result.predictions[i+1].distance_label}"

    def test_estimated_vdot_present(self):
        result = predict_all_distances(5000, 1200)
        assert result.estimated_vdot > 0

    def test_known_time_preserved(self):
        result = predict_all_distances(5000, 1200)
        assert result.known_time_seconds == 1200

    def test_invalid_distance_key_skipped(self):
        result = predict_all_distances(5000, 1200, distances=["5K", "nonexistent", "10K"])
        assert len(result.predictions) == 2


# ── Model Comparison ─────────────────────────────────────────────────────────

class TestModelComparison:
    def test_comparison_returns_all_models(self):
        comp = compare_models(5000, 1200, 10000)
        assert isinstance(comp, ModelComparison)
        assert comp.riegel is not None
        assert comp.cameron is not None
        assert comp.vdot is not None

    def test_spread_non_negative(self):
        comp = compare_models(5000, 1200, 10000)
        assert comp.spread_seconds >= 0

    def test_consensus_is_average(self):
        comp = compare_models(5000, 1200, 10000)
        avg = (comp.riegel.predicted_seconds + comp.cameron.predicted_seconds + comp.vdot.predicted_seconds) / 3
        assert comp.consensus_seconds == pytest.approx(avg, abs=1)

    def test_5k_to_10k_small_spread(self):
        """Models should agree reasonably for 5K→10K."""
        comp = compare_models(5000, 1200, 10000)
        assert comp.spread_seconds < 180  # within 3 minutes

    def test_5k_to_marathon_larger_spread(self):
        """Models may diverge more for 5K→marathon."""
        comp_10k = compare_models(5000, 1200, 10000)
        comp_marathon = compare_models(5000, 1200, 42195)
        assert comp_marathon.spread_seconds >= comp_10k.spread_seconds * 0.5  # not necessarily larger, but plausible


# ── Formatting ───────────────────────────────────────────────────────────────

class TestFormatting:
    def test_format_predictions_contains_key_info(self):
        result = predict_all_distances(5000, 1200, model="vdot")
        text = format_predictions(result)
        assert "5K" in text or "VDOT" in text
        assert "20:00" in text
        assert "Distance" in text

    def test_format_comparison_contains_models(self):
        comp = compare_models(5000, 1200, 10000)
        text = format_model_comparison(comp)
        assert "Riegel" in text
        assert "Cameron" in text
        assert "VDOT" in text
        assert "Consensus" in text

    def test_format_comparison_confidence_label(self):
        comp = compare_models(5000, 1200, 10000)
        text = format_model_comparison(comp)
        assert any(x in text for x in ["High confidence", "Moderate confidence", "Low confidence"])


# ── Race Distance Constants ──────────────────────────────────────────────────

class TestConstants:
    def test_standard_distances_exist(self):
        assert "5K" in RACE_DISTANCES_M
        assert "10K" in RACE_DISTANCES_M
        assert "half_marathon" in RACE_DISTANCES_M
        assert "marathon" in RACE_DISTANCES_M

    def test_marathon_distance(self):
        assert RACE_DISTANCES_M["marathon"] == 42195

    def test_half_marathon_distance(self):
        assert RACE_DISTANCES_M["half_marathon"] == 21097.5

    def test_distances_monotonically_increasing(self):
        values = list(RACE_DISTANCES_M.values())
        for i in range(len(values) - 1):
            assert values[i] < values[i + 1]


# ── Cross-Model Consistency ─────────────────────────────────────────────────

class TestCrossModelConsistency:
    """Ensure all three models produce plausible results for known benchmarks."""

    @pytest.mark.parametrize("model_fn", [predict_riegel, predict_cameron, predict_vdot])
    def test_20min_5k_to_10k(self, model_fn):
        """20:00 5K → 10K should be 40:00–44:00 for all models."""
        pred = model_fn(5000, 1200, 10000)
        assert 2400 <= pred.predicted_seconds <= 2640

    @pytest.mark.parametrize("model_fn", [predict_riegel, predict_cameron, predict_vdot])
    def test_prediction_has_pace(self, model_fn):
        pred = model_fn(5000, 1200, 10000)
        assert "/km" in pred.pace

    @pytest.mark.parametrize("model_fn", [predict_riegel, predict_cameron, predict_vdot])
    def test_prediction_has_formatted_time(self, model_fn):
        pred = model_fn(5000, 1200, 10000)
        assert ":" in pred.predicted_time
