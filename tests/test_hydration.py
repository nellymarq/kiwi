"""
Tests for tools/hydration.py — sweat loss, electrolytes, rehydration, urine color.
"""
import pytest

from tools.hydration import (
    SweatLoss,
    RehydrationProtocol,
    SPORT_SWEAT_RATES,
    SWEAT_ELECTROLYTE_CONCENTRATION,
    URINE_COLOR_CHART,
    calculate_sweat_loss,
    estimate_sweat_loss_by_sport,
    design_rehydration_protocol,
    format_rehydration_report,
    urine_color_status,
    hyponatremia_risk,
    pre_exercise_hydration_plan,
)


# ── Sweat Loss Calculation ─────────────────────────────────────────────────────

class TestCalculateSweatLoss:
    def test_basic_weight_loss(self):
        """1 kg weight loss with no fluid = 1L sweat."""
        sl = calculate_sweat_loss(pre_weight_kg=75.0, post_weight_kg=74.0,
                                   fluid_consumed_L=0.0, duration_hours=1.0)
        assert sl.liters == pytest.approx(1.0, abs=0.05)

    def test_fluid_consumption_adds_to_sweat(self):
        """0.5 kg loss + 0.5L consumed = 1.0L sweat."""
        sl = calculate_sweat_loss(pre_weight_kg=75.0, post_weight_kg=74.5,
                                   fluid_consumed_L=0.5, duration_hours=1.0)
        assert sl.liters == pytest.approx(1.0, abs=0.05)

    def test_sweat_rate_correct(self):
        """2L sweat over 2h = 1.0 L/h."""
        sl = calculate_sweat_loss(pre_weight_kg=75.0, post_weight_kg=73.0,
                                   fluid_consumed_L=0.0, duration_hours=2.0)
        assert sl.sweat_rate_L_hr == pytest.approx(1.0, abs=0.05)

    def test_no_negative_sweat(self):
        """Post > pre weight (drank more than sweated) → 0 sweat loss."""
        sl = calculate_sweat_loss(pre_weight_kg=75.0, post_weight_kg=75.5,
                                   fluid_consumed_L=0.0, duration_hours=1.0)
        assert sl.liters == 0.0

    def test_sodium_positive(self):
        sl = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0)
        assert sl.sodium_mg > 0

    def test_potassium_positive(self):
        sl = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0)
        assert sl.potassium_mg > 0

    def test_heat_adjustment_increases_sweat(self):
        sl_cool = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0, ambient_temp_c=15.0)
        sl_hot  = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0, ambient_temp_c=35.0)
        # Hot adjusts upward from the same raw weight loss
        assert sl_hot.liters >= sl_cool.liters

    def test_heat_adjusted_flag(self):
        sl = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0, ambient_temp_c=30.0)
        assert sl.heat_adjusted is True

    def test_temperate_not_heat_adjusted(self):
        sl = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0, ambient_temp_c=20.0)
        assert sl.heat_adjusted is False

    def test_acclimatized_lower_sodium_concentration(self):
        sl_naive = calculate_sweat_loss(75.0, 73.0, 0.0, 1.0, acclimatized=False)
        sl_accl  = calculate_sweat_loss(75.0, 73.0, 0.0, 1.0, acclimatized=True)
        # Acclimatized: higher sweat rate but lower [Na+] → different mg totals
        # Acclimatized sweat more (heat_factor *= 1.1) so total might be higher, but [Na] lower
        na_per_L_naive = sl_naive.sodium_mg / sl_naive.liters if sl_naive.liters > 0 else 0
        na_per_L_accl  = sl_accl.sodium_mg / sl_accl.liters if sl_accl.liters > 0 else 0
        assert na_per_L_accl < na_per_L_naive

    def test_summary_string_contains_liters(self):
        sl = calculate_sweat_loss(75.0, 74.0, 0.0, 1.0)
        summary = sl.summary()
        assert "L" in summary
        assert "Sodium" in summary


class TestEstimateSweatLossBySport:
    def test_returns_sweat_loss_object(self):
        sl = estimate_sweat_loss_by_sport("running", duration_hours=1.0)
        assert isinstance(sl, SweatLoss)

    def test_running_higher_rate_than_swimming(self):
        sl_run = estimate_sweat_loss_by_sport("running", duration_hours=1.0)
        sl_swim = estimate_sweat_loss_by_sport("swimming", duration_hours=1.0)
        assert sl_run.liters > sl_swim.liters

    def test_hard_intensity_more_than_easy(self):
        sl_easy = estimate_sweat_loss_by_sport("running", duration_hours=1.0, intensity="easy")
        sl_hard = estimate_sweat_loss_by_sport("running", duration_hours=1.0, intensity="hard")
        assert sl_hard.liters > sl_easy.liters

    def test_longer_duration_more_sweat(self):
        sl_1h = estimate_sweat_loss_by_sport("cycling", duration_hours=1.0)
        sl_2h = estimate_sweat_loss_by_sport("cycling", duration_hours=2.0)
        assert sl_2h.liters == pytest.approx(sl_1h.liters * 2, rel=0.1)

    def test_heavier_athlete_more_sweat(self):
        sl_70 = estimate_sweat_loss_by_sport("running", 1.0, body_weight_kg=70.0)
        sl_90 = estimate_sweat_loss_by_sport("running", 1.0, body_weight_kg=90.0)
        assert sl_90.liters > sl_70.liters

    def test_unknown_sport_uses_general(self):
        sl = estimate_sweat_loss_by_sport("curling", duration_hours=1.0)
        assert sl.liters > 0

    def test_hot_conditions_increase_sweat(self):
        sl_cool = estimate_sweat_loss_by_sport("running", 1.0, ambient_temp_c=15.0)
        sl_hot  = estimate_sweat_loss_by_sport("running", 1.0, ambient_temp_c=35.0)
        assert sl_hot.liters > sl_cool.liters

    def test_all_listed_sports_work(self):
        for sport in SPORT_SWEAT_RATES:
            sl = estimate_sweat_loss_by_sport(sport, duration_hours=1.0)
            assert sl.liters > 0


# ── Sport Sweat Rate Database ──────────────────────────────────────────────────

class TestSweatRateDatabase:
    def test_all_sports_have_required_keys(self):
        required = {"min_L_hr", "typical_L_hr", "max_L_hr", "notes"}
        for sport, data in SPORT_SWEAT_RATES.items():
            missing = required - set(data.keys())
            assert not missing, f"{sport} missing: {missing}"

    def test_min_less_than_typical(self):
        for sport, data in SPORT_SWEAT_RATES.items():
            assert data["min_L_hr"] < data["typical_L_hr"], f"{sport} min >= typical"

    def test_typical_less_than_max(self):
        for sport, data in SPORT_SWEAT_RATES.items():
            assert data["typical_L_hr"] < data["max_L_hr"], f"{sport} typical >= max"

    def test_all_rates_positive(self):
        for sport, data in SPORT_SWEAT_RATES.items():
            assert data["min_L_hr"] > 0, f"{sport} min rate ≤ 0"


# ── Rehydration Protocol ───────────────────────────────────────────────────────

class TestDesignRehydrationProtocol:
    def _make_sweat_loss(self, liters: float = 1.5) -> SweatLoss:
        # Build a SweatLoss manually for testing
        from tools.hydration import SWEAT_ELECTROLYTE_CONCENTRATION as SEC
        na = SEC["sodium"]["mean_mmol_L"]
        k  = SEC["potassium"]["mean_mmol_L"]
        cl = SEC["chloride"]["mean_mmol_L"]
        mg = SEC["magnesium"]["mean_mmol_L"]
        return SweatLoss(
            liters=liters,
            duration_hours=1.5,
            sweat_rate_L_hr=liters / 1.5,
            sodium_mg=liters * na * 23.0,
            potassium_mg=liters * k * 39.1,
            chloride_mg=liters * cl * 35.5,
            magnesium_mg=liters * mg * 24.3,
        )

    def test_fluid_target_1_5x_for_near_term(self):
        sl = self._make_sweat_loss(1.0)
        p = design_rehydration_protocol(sl, time_to_next_activity_hours=6)
        assert p.total_fluid_target_L == pytest.approx(1.5, abs=0.05)

    def test_fluid_target_1_25x_for_long_term(self):
        sl = self._make_sweat_loss(1.0)
        p = design_rehydration_protocol(sl, time_to_next_activity_hours=48)
        assert p.total_fluid_target_L == pytest.approx(1.25, abs=0.05)

    def test_sodium_target_80_pct_of_loss(self):
        sl = self._make_sweat_loss(1.0)
        p = design_rehydration_protocol(sl)
        assert p.sodium_target_mg == pytest.approx(sl.sodium_mg * 0.80, abs=50)

    def test_immediate_urgency_for_soon_event(self):
        sl = self._make_sweat_loss(1.0)
        p = design_rehydration_protocol(sl, time_to_next_activity_hours=2)
        assert p.urgency == "immediate"

    def test_gradual_urgency_for_long_recovery(self):
        sl = self._make_sweat_loss(1.0)
        p = design_rehydration_protocol(sl, time_to_next_activity_hours=48)
        assert p.urgency == "gradual"

    def test_large_sweat_loss_triggers_warning(self):
        sl = self._make_sweat_loss(3.0)
        p = design_rehydration_protocol(sl)
        assert len(p.warnings) >= 1

    def test_high_sodium_loss_triggers_warning(self):
        sl = self._make_sweat_loss(4.0)  # Large loss → high Na loss
        p = design_rehydration_protocol(sl)
        # Should warn about high sodium loss
        warnings_text = " ".join(p.warnings).lower()
        assert "sodium" in warnings_text or "electrolyte" in warnings_text or len(p.warnings) >= 1

    def test_first_hour_target_not_exceed_total(self):
        sl = self._make_sweat_loss(1.0)
        p = design_rehydration_protocol(sl)
        assert p.first_hour_target_L <= p.total_fluid_target_L

    def test_first_hour_capped_at_800ml(self):
        sl = self._make_sweat_loss(5.0)  # Large loss
        p = design_rehydration_protocol(sl)
        assert p.first_hour_target_L <= 0.8

    def test_ors_sodium_in_reasonable_range(self):
        sl = self._make_sweat_loss(1.5)
        p = design_rehydration_protocol(sl)
        assert 300 <= p.ors_concentration_mg_per_L["sodium_mg_per_L"] <= 1500

    def test_format_rehydration_report_returns_string(self):
        sl = self._make_sweat_loss(1.5)
        p = design_rehydration_protocol(sl)
        report = format_rehydration_report(p, sl)
        assert isinstance(report, str)
        assert "REHYDRATION" in report


# ── Urine Color Chart ──────────────────────────────────────────────────────────

class TestUrineColorStatus:
    def test_color_1_well_hydrated(self):
        result = urine_color_status(1)
        assert result["dehydrated"] is False
        assert "hydrated" in result["status"].lower()

    def test_color_4_adequately_hydrated(self):
        result = urine_color_status(4)
        assert result["dehydrated"] is False

    def test_color_5_mild_dehydration(self):
        result = urine_color_status(5)
        assert result["dehydrated"] is True
        assert result["urgent"] is False

    def test_color_7_urgent(self):
        result = urine_color_status(7)
        assert result["urgent"] is True

    def test_color_8_most_severe(self):
        result = urine_color_status(8)
        assert result["urgent"] is True
        assert "medical" in result["action"].lower() or "rhabdomyolysis" in result["action"].lower()

    def test_color_out_of_range_clamped(self):
        result_low = urine_color_status(0)  # Below 1 → clamped to 1
        result_high = urine_color_status(10)  # Above 8 → clamped to 8
        assert result_low["color_number"] == 1
        assert result_high["color_number"] == 8

    def test_all_chart_entries_have_required_fields(self):
        for num, color, status, action in URINE_COLOR_CHART:
            assert isinstance(num, int)
            assert isinstance(status, str)
            assert isinstance(action, str)
            assert len(action) > 5

    def test_chart_has_8_entries(self):
        assert len(URINE_COLOR_CHART) == 8

    def test_evidence_tier_present(self):
        result = urine_color_status(3)
        assert "🟢" in result["evidence"] or "🟡" in result["evidence"]


# ── Hyponatremia Risk ──────────────────────────────────────────────────────────

class TestHyponatremiaRisk:
    def test_overconsumption_high_risk(self):
        # Drinking 1.5 L/h when sweat rate is ~1.2 L/h
        result = hyponatremia_risk(
            event_duration_hours=6,
            fluid_intake_L_hr=1.5,
            event_type="endurance",
        )
        assert result["risk_level"] == "HIGH"

    def test_drink_to_thirst_low_risk(self):
        result = hyponatremia_risk(
            event_duration_hours=1.5,
            fluid_intake_L_hr=0.5,
            event_type="endurance",
        )
        assert result["risk_level"] == "LOW"

    def test_long_event_increases_risk(self):
        r_short = hyponatremia_risk(event_duration_hours=1, fluid_intake_L_hr=0.8)
        r_long  = hyponatremia_risk(event_duration_hours=8, fluid_intake_L_hr=0.8)
        assert r_long["risk_score"] >= r_short["risk_score"]

    def test_drivers_list_populated_for_high_risk(self):
        result = hyponatremia_risk(6, 1.5)
        assert len(result["drivers"]) >= 1

    def test_key_warning_present(self):
        result = hyponatremia_risk(6, 1.5)
        assert "key_warning" in result
        assert len(result["key_warning"]) > 20

    def test_evidence_tier_strong(self):
        result = hyponatremia_risk(6, 1.5)
        assert "🟢" in result["evidence"]

    def test_low_body_weight_increases_risk(self):
        r_heavy = hyponatremia_risk(5, 1.0, body_weight_kg=90)
        r_light = hyponatremia_risk(5, 1.0, body_weight_kg=50)
        assert r_light["risk_score"] >= r_heavy["risk_score"]


# ── Pre-Exercise Hydration Plan ────────────────────────────────────────────────

class TestPreExerciseHydrationPlan:
    def test_returns_dict_with_required_keys(self):
        plan = pre_exercise_hydration_plan(75.0, 1.5)
        assert "pre_exercise_target_mL" in plan
        assert "intra_exercise_L_hr" in plan
        assert "schedule" in plan
        assert "urine_target" in plan

    def test_schedule_has_steps(self):
        plan = pre_exercise_hydration_plan(75.0, 1.5, start_hours_from_now=4.0)
        assert len(plan["schedule"]) >= 2

    def test_short_lead_time_has_schedule(self):
        plan = pre_exercise_hydration_plan(75.0, 1.5, start_hours_from_now=1.0)
        assert len(plan["schedule"]) >= 1

    def test_heavier_athlete_higher_target(self):
        plan_60 = pre_exercise_hydration_plan(60.0, 1.5)
        plan_90 = pre_exercise_hydration_plan(90.0, 1.5)
        # Parse the lower bound from "300-600" format
        low_60 = int(plan_60["pre_exercise_target_mL"].split("–")[0])
        low_90 = int(plan_90["pre_exercise_target_mL"].split("–")[0])
        assert low_90 > low_60

    def test_evidence_tier_present(self):
        plan = pre_exercise_hydration_plan(75.0, 1.5)
        assert "🟢" in plan["evidence"]

    def test_urine_color_target_mentioned(self):
        plan = pre_exercise_hydration_plan(75.0, 1.5)
        assert "colour" in plan["urine_target"].lower() or "color" in plan["urine_target"].lower()
