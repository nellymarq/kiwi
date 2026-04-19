"""Tests for environmental factors tool."""
import pytest

from tools.environmental import (
    AirQualityAdjustment,
    AltitudeProtocol,
    ColdExposureProtocol,
    HeatAcclimatization,
    JetLagProtocol,
    air_quality_adjustment,
    altitude_training_protocol,
    cold_exposure_protocol,
    format_air_quality,
    format_altitude_protocol,
    format_heat_protocol,
    format_jet_lag,
    heat_acclimatization_protocol,
    jet_lag_protocol,
)


# ── Altitude Tests ───────────────────────────────────────────────────────────

class TestAltitude:
    def test_moderate_altitude(self):
        result = altitude_training_protocol(2000)
        assert isinstance(result, AltitudeProtocol)
        assert result.target_altitude_m == 2000
        assert result.acclimatization_days >= 3

    def test_high_altitude(self):
        result = altitude_training_protocol(3500)
        assert result.acclimatization_days > 7

    def test_very_high_altitude(self):
        result = altitude_training_protocol(4500)
        assert result.acclimatization_days > 14
        assert any("AMS" in r or "HAPE" in r for r in result.risks)

    def test_lhtl_model(self):
        result = altitude_training_protocol(2500)
        assert result.optimal_living_altitude_m >= 2000
        assert result.optimal_training_altitude_m <= 1500

    def test_hemoglobin_increase(self):
        result = altitude_training_protocol(2500, duration_weeks=4)
        assert result.expected_hb_increase_pct > 0

    def test_low_altitude_no_hb(self):
        result = altitude_training_protocol(1000)
        assert result.expected_hb_increase_pct == 0.0

    def test_nutrition_includes_iron(self):
        result = altitude_training_protocol(2500)
        assert any("iron" in n.lower() for n in result.nutrition_adjustments)

    def test_has_evidence(self):
        result = altitude_training_protocol(2000)
        assert "Chapman" in result.evidence

    def test_has_references(self):
        result = altitude_training_protocol(2000)
        assert len(result.key_references) >= 2


# ── Heat Acclimatization Tests ───────────────────────────────────────────────

class TestHeat:
    @pytest.mark.parametrize("wbgt,expected_cat", [
        (15, "low"),
        (20, "moderate"),
        (25, "high"),
        (30, "very_high"),
        (35, "extreme"),
    ])
    def test_risk_categories(self, wbgt, expected_cat):
        result = heat_acclimatization_protocol(wbgt)
        assert isinstance(result, HeatAcclimatization)
        assert result.risk_category == expected_cat

    def test_extreme_cancels_training(self):
        result = heat_acclimatization_protocol(35)
        combined = " ".join(result.training_modifications).lower()
        assert "cancel" in combined or "postpone" in combined

    def test_non_acclimatized_extra_caution(self):
        acc = heat_acclimatization_protocol(25, acclimatized=True)
        nonacc = heat_acclimatization_protocol(25, acclimatized=False)
        assert len(nonacc.training_modifications) >= len(acc.training_modifications)

    def test_hydration_protocol(self):
        result = heat_acclimatization_protocol(28)
        assert len(result.hydration_protocol) >= 2

    def test_cooling_strategies_high_heat(self):
        result = heat_acclimatization_protocol(30)
        assert len(result.cooling_strategies) > 0

    def test_warning_signs(self):
        result = heat_acclimatization_protocol(25)
        assert len(result.warning_signs) >= 3

    def test_has_evidence(self):
        result = heat_acclimatization_protocol(25)
        assert "Racinais" in result.evidence


# ── Air Quality Tests ────────────────────────────────────────────────────────

class TestAirQuality:
    @pytest.mark.parametrize("aqi,expected_cat", [
        (25, "good"),
        (75, "moderate"),
        (125, "unhealthy_sensitive"),
        (175, "unhealthy"),
        (250, "very_unhealthy"),
        (400, "hazardous"),
    ])
    def test_aqi_categories(self, aqi, expected_cat):
        result = air_quality_adjustment(aqi)
        assert isinstance(result, AirQualityAdjustment)
        assert result.category == expected_cat

    def test_good_no_modifications(self):
        result = air_quality_adjustment(30)
        assert len(result.modifications) == 0

    def test_unhealthy_has_modifications(self):
        result = air_quality_adjustment(160)
        assert len(result.modifications) > 0

    def test_hazardous_cancels_exercise(self):
        result = air_quality_adjustment(350)
        assert "cancel" in result.training_recommendation.lower() or "no exercise" in result.training_recommendation.lower()

    def test_has_evidence(self):
        result = air_quality_adjustment(100)
        assert "EPA" in result.evidence or "AQI" in result.evidence


# ── Cold Exposure Tests ──────────────────────────────────────────────────────

class TestColdExposure:
    def test_mild_cold(self):
        result = cold_exposure_protocol(3.0)
        assert isinstance(result, ColdExposureProtocol)
        assert result.risk_level in ("low", "moderate")

    def test_moderate_cold(self):
        result = cold_exposure_protocol(-3.0)
        assert result.risk_level == "moderate"

    def test_severe_cold(self):
        result = cold_exposure_protocol(-20.0)
        assert result.risk_level in ("high", "very_high")

    def test_extreme_cold(self):
        result = cold_exposure_protocol(-30.0)
        assert result.risk_level in ("very_high", "extreme")

    def test_wind_chill_calculated(self):
        result = cold_exposure_protocol(-5.0, wind_speed_kmh=30)
        assert result.wind_chill_c is not None
        assert result.wind_chill_c < -5.0

    def test_no_wind_chill_warm(self):
        result = cold_exposure_protocol(15.0, wind_speed_kmh=10)
        assert result.wind_chill_c is None

    def test_precipitation_adds_layer(self):
        dry = cold_exposure_protocol(-5.0)
        wet = cold_exposure_protocol(-5.0, precipitation=True)
        assert len(wet.clothing_layers) > len(dry.clothing_layers)

    def test_clothing_layers(self):
        result = cold_exposure_protocol(-10.0)
        assert len(result.clothing_layers) >= 3

    def test_nutrition_adjustments(self):
        result = cold_exposure_protocol(-10.0)
        assert any("caloric" in n.lower() or "carbohydrate" in n.lower() for n in result.nutrition_adjustments)

    def test_warning_signs(self):
        result = cold_exposure_protocol(-5.0)
        assert len(result.warning_signs) >= 3

    def test_has_evidence(self):
        result = cold_exposure_protocol(0.0)
        assert "Castellani" in result.evidence or "🟡" in result.evidence


# ── Jet Lag Tests ────────────────────────────────────────────────────────────

class TestJetLag:
    def test_eastward_travel(self):
        result = jet_lag_protocol(6, "east")
        assert isinstance(result, JetLagProtocol)
        assert result.direction == "east"
        assert result.time_zones_crossed == 6

    def test_westward_travel(self):
        result = jet_lag_protocol(6, "west")
        assert result.direction == "west"

    def test_eastward_harder(self):
        east = jet_lag_protocol(8, "east")
        west = jet_lag_protocol(8, "west")
        assert east.adjustment_days >= west.adjustment_days

    def test_small_crossing(self):
        result = jet_lag_protocol(2, "east")
        assert result.adjustment_days >= 1
        assert result.adjustment_days <= 5

    def test_large_crossing(self):
        result = jet_lag_protocol(12, "east")
        assert result.adjustment_days >= 10

    def test_light_exposure_east(self):
        result = jet_lag_protocol(6, "east")
        assert "morning" in result.light_exposure.lower()

    def test_light_exposure_west(self):
        result = jet_lag_protocol(6, "west")
        assert "evening" in result.light_exposure.lower() or "afternoon" in result.light_exposure.lower()

    def test_melatonin_for_large_crossing(self):
        result = jet_lag_protocol(6, "east")
        assert "melatonin" in result.melatonin_protocol.lower()

    def test_pre_travel_strategies(self):
        result = jet_lag_protocol(8, "east")
        assert len(result.pre_travel) >= 2

    def test_training_modifications(self):
        result = jet_lag_protocol(6, "east")
        assert len(result.training_modifications) >= 2

    def test_negative_zones_handled(self):
        result = jet_lag_protocol(-5, "east")
        assert result.time_zones_crossed == 5

    def test_has_evidence(self):
        result = jet_lag_protocol(6, "east")
        assert "Waterhouse" in result.evidence


# ── Formatting Tests ─────────────────────────────────────────────────────────

class TestFormatting:
    def test_format_altitude(self):
        proto = altitude_training_protocol(2500)
        output = format_altitude_protocol(proto)
        assert "Altitude" in output
        assert "2500" in output

    def test_format_heat(self):
        proto = heat_acclimatization_protocol(28)
        output = format_heat_protocol(proto)
        assert "Heat" in output or "WBGT" in output

    def test_format_air_quality(self):
        aq = air_quality_adjustment(150)
        output = format_air_quality(aq)
        assert "Air Quality" in output
        assert "150" in output

    def test_format_jet_lag(self):
        proto = jet_lag_protocol(8, "east")
        output = format_jet_lag(proto)
        assert "Jet Lag" in output
        assert "east" in output.lower()
