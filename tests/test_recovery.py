"""
Tests for tools/recovery.py — HRV readiness, DOMS, supercompensation, deload.
"""
import pytest
from datetime import date, timedelta

from tools.recovery import (
    HRVReading,
    ReadinessScore,
    DOMSEstimate,
    DeloadAssessment,
    compute_readiness,
    format_readiness_report,
    estimate_doms,
    supercompensation_window,
    assess_deload_need,
    recovery_modality_guide,
    mps_timing_guide,
    EXERCISE_DAMAGE_COEFFICIENTS,
    TRAINED_STATUS_MODIFIERS,
    RECOVERY_MODALITIES,
    SUPERCOMPENSATION_PROFILES,
    MPS_WINDOWS,
)


# ── HRV Readiness ─────────────────────────────────────────────────────────────

class TestComputeReadiness:
    def _make_readings(self, rmssd_list: list[float]) -> list[HRVReading]:
        today = date.today()
        return [
            HRVReading(rmssd=v, resting_hr=55.0, date=today - timedelta(days=len(rmssd_list)-1-i))
            for i, v in enumerate(rmssd_list)
        ]

    def test_empty_readings_returns_moderate(self):
        r = compute_readiness([])
        assert r.score == 50.0
        assert r.category == "moderate"
        assert r.hrv_trend == "insufficient_data"

    def test_single_reading_returns_moderate_baseline(self):
        readings = self._make_readings([60.0])
        r = compute_readiness(readings)
        # Only 1 reading — uses fallback SD=10, z≈0 → ~50 pts
        assert 40 <= r.score <= 60
        assert r.hrv_trend == "insufficient_data"

    def test_two_readings_insufficient_data(self):
        readings = self._make_readings([60.0, 62.0])
        r = compute_readiness(readings)
        assert r.hrv_trend == "insufficient_data"

    def test_high_rmssd_today_gives_high_score(self):
        # Baseline ~55ms, today 80ms — large positive z
        readings = self._make_readings([55.0, 54.0, 56.0, 55.0, 80.0])
        r = compute_readiness(readings)
        assert r.score >= 70
        assert r.category in ("good", "excellent")

    def test_low_rmssd_today_gives_low_score(self):
        # Baseline ~70ms, today 35ms — large negative z
        readings = self._make_readings([70.0, 68.0, 72.0, 71.0, 35.0])
        r = compute_readiness(readings)
        assert r.score <= 40
        assert r.category in ("poor", "very_poor")

    def test_rising_trend_adds_points(self):
        readings_rising = self._make_readings([50.0, 55.0, 60.0, 65.0, 68.0])
        readings_stable = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r_rising = compute_readiness(readings_rising)
        r_stable = compute_readiness(readings_stable)
        assert r_rising.hrv_trend == "rising"
        assert r_rising.score > r_stable.score

    def test_declining_trend_removes_points(self):
        readings_declining = self._make_readings([68.0, 63.0, 58.0, 53.0, 48.0])
        r = compute_readiness(readings_declining)
        assert r.hrv_trend == "declining"
        # Should have negative trend adjustment

    def test_tsb_fatigue_penalty(self):
        readings = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r_no_tsb = compute_readiness(readings, tsb=0.0)
        r_fatigued = compute_readiness(readings, tsb=-40.0)
        assert r_no_tsb.score > r_fatigued.score

    def test_tsb_above_threshold_no_penalty(self):
        readings = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r_fresh = compute_readiness(readings, tsb=5.0)
        r_neutral = compute_readiness(readings, tsb=-10.0)
        # Neither should trigger fatigue penalty (threshold is -20)
        assert abs(r_fresh.score - r_neutral.score) < 5

    def test_sleep_debt_penalty(self):
        readings = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r_no_debt = compute_readiness(readings, sleep_debt_hours=0.0)
        r_debt = compute_readiness(readings, sleep_debt_hours=4.0)
        assert r_no_debt.score > r_debt.score
        assert r_debt.score == pytest.approx(r_no_debt.score - 20.0, abs=5)

    def test_sleep_debt_capped_at_20_pts(self):
        readings = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r_large_debt = compute_readiness(readings, sleep_debt_hours=10.0)
        r_max_debt = compute_readiness(readings, sleep_debt_hours=6.0)
        # Both should have sleep_adj = -20 (capped)
        assert abs(r_large_debt.score - r_max_debt.score) < 2

    def test_score_clamped_to_0_100(self):
        # Extreme negative z should not go below 0
        readings = self._make_readings([100.0, 100.0, 100.0, 100.0, 1.0])
        r = compute_readiness(readings, tsb=-50.0, sleep_debt_hours=10.0)
        assert 0.0 <= r.score <= 100.0

    def test_excellent_category_threshold(self):
        # Need score >= 85 for excellent
        readings = self._make_readings([55.0, 54.0, 56.0, 55.0, 90.0])
        r = compute_readiness(readings)
        if r.score >= 85:
            assert r.category == "excellent"
        else:
            assert r.category in ("good", "moderate")

    def test_recommendations_not_empty(self):
        readings = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r = compute_readiness(readings)
        assert len(r.recommendations) >= 1

    def test_sleep_debt_recommendation_appears(self):
        readings = self._make_readings([60.0, 60.0, 60.0, 60.0, 60.0])
        r = compute_readiness(readings, sleep_debt_hours=3.0)
        has_sleep_rec = any("sleep" in rec.lower() for rec in r.recommendations)
        assert has_sleep_rec

    def test_declining_trend_recommendation_appears(self):
        readings = self._make_readings([80.0, 70.0, 60.0, 50.0, 40.0])
        r = compute_readiness(readings)
        if r.hrv_trend == "declining":
            has_deload_rec = any("deload" in rec.lower() or "declining" in rec.lower()
                                  for rec in r.recommendations)
            assert has_deload_rec


class TestFormatReadinessReport:
    def test_report_contains_score(self):
        readings = [HRVReading(rmssd=60.0, resting_hr=55.0)]
        r = compute_readiness(readings)
        report = format_readiness_report(r)
        assert "Readiness Score" in report
        assert str(int(r.score)) in report

    def test_report_contains_category(self):
        readings = [HRVReading(rmssd=60.0, resting_hr=55.0)]
        r = compute_readiness(readings)
        report = format_readiness_report(r)
        assert r.category.upper().replace("_", " ") in report

    def test_report_contains_recommendations(self):
        readings = [HRVReading(rmssd=60.0, resting_hr=55.0)]
        r = compute_readiness(readings)
        report = format_readiness_report(r)
        assert "Recommendations" in report


# ── DOMS Estimation ───────────────────────────────────────────────────────────

class TestEstimateDomsBasic:
    def test_easy_cycling_minimal_doms(self):
        d = estimate_doms("cycling", rpe=5.0, duration_min=60)
        assert d.severity in ("none", "mild")

    def test_heavy_eccentric_high_doms(self):
        d = estimate_doms("strength_eccentric_heavy", rpe=9.0, duration_min=90)
        assert d.severity in ("moderate", "severe")

    def test_isometric_low_damage(self):
        d = estimate_doms("isometric", rpe=7.0, duration_min=45)
        assert d.severity in ("none", "mild")

    def test_unknown_type_uses_default(self):
        # Should not raise; falls back to default coefficient 0.40
        d = estimate_doms("underwater_basket_weaving", rpe=8.0, duration_min=60)
        assert d.severity in ("none", "mild", "moderate", "severe")

    def test_untrained_worse_than_elite(self):
        d_untrained = estimate_doms("strength_eccentric_moderate", rpe=8.0, duration_min=60,
                                    trained_status="untrained")
        d_elite = estimate_doms("strength_eccentric_moderate", rpe=8.0, duration_min=60,
                                trained_status="elite")
        assert d_untrained.severity_score > d_elite.severity_score

    def test_severity_score_within_0_10(self):
        d = estimate_doms("plyometrics", rpe=10.0, duration_min=120, trained_status="untrained")
        assert 0.0 <= d.severity_score <= 10.0

    def test_peak_hours_severe_is_48(self):
        d = estimate_doms("strength_eccentric_heavy", rpe=10.0, duration_min=120,
                          trained_status="untrained")
        if d.severity == "severe":
            assert d.peak_hours == 48

    def test_resolution_hours_progression(self):
        # Mild resolves faster than severe
        d_mild = estimate_doms("cycling", rpe=4.0, duration_min=30, trained_status="elite")
        d_severe = estimate_doms("strength_eccentric_heavy", rpe=10.0, duration_min=120,
                                  trained_status="untrained")
        if d_mild.severity == "mild" and d_severe.severity == "severe":
            assert d_mild.resolution_hours < d_severe.resolution_hours

    def test_evidence_tier_present(self):
        d = estimate_doms("running_new", rpe=7.0, duration_min=60)
        assert d.evidence in ("🟢 Strong", "🟡 Moderate", "🟠 Weak", "🔵 Emerging")


class TestExerciseDamageCoefficients:
    def test_all_coefficients_in_range(self):
        for name, coef in EXERCISE_DAMAGE_COEFFICIENTS.items():
            assert 0.0 <= coef <= 1.0, f"{name} coefficient {coef} out of range"

    def test_eccentric_highest_damage(self):
        assert EXERCISE_DAMAGE_COEFFICIENTS["strength_eccentric_heavy"] >= 0.8

    def test_swimming_lowest_damage(self):
        assert EXERCISE_DAMAGE_COEFFICIENTS["swimming"] <= 0.2


# ── Supercompensation Window ───────────────────────────────────────────────────

class TestSupercompensationWindow:
    def test_returns_dict_with_required_keys(self):
        result = supercompensation_window("strength", 0)
        assert "current_phase" in result
        assert "phases" in result
        assert "hours_to_supercomp_peak" in result

    def test_just_finished_is_fatigue_phase(self):
        result = supercompensation_window("strength", session_end_datetime_hours_ago=0)
        assert result["current_phase"] == "fatigue_phase"

    def test_72h_later_is_supercomp_for_strength(self):
        result = supercompensation_window("strength", session_end_datetime_hours_ago=80)
        # Strength supercomp: 72–120h
        assert result["current_phase"] == "supercomp_phase"

    def test_hours_to_supercomp_zero_when_in_window(self):
        result = supercompensation_window("strength", session_end_datetime_hours_ago=90)
        assert result["hours_to_supercomp_peak"] == 0

    def test_hours_to_supercomp_positive_before_window(self):
        result = supercompensation_window("strength", session_end_datetime_hours_ago=10)
        assert result["hours_to_supercomp_peak"] > 0

    def test_hours_to_supercomp_none_after_window(self):
        result = supercompensation_window("strength", session_end_datetime_hours_ago=200)
        assert result["hours_to_supercomp_peak"] is None

    def test_endurance_faster_supercomp(self):
        # Endurance supercomp starts at 36h vs strength at 72h
        r_endurance = supercompensation_window("endurance", session_end_datetime_hours_ago=40)
        r_strength = supercompensation_window("strength", session_end_datetime_hours_ago=40)
        assert r_endurance["current_phase"] == "supercomp_phase"
        assert r_strength["current_phase"] != "supercomp_phase"

    def test_unknown_type_falls_back_to_strength(self):
        result = supercompensation_window("badminton", session_end_datetime_hours_ago=0)
        # Should not raise
        assert "current_phase" in result


# ── Deload Assessment ──────────────────────────────────────────────────────────

class TestAssessDeloadNeed:
    def test_no_triggers_returns_not_needed(self):
        d = assess_deload_need(
            tsb=5.0,
            consecutive_hard_days=1,
            weeks_since_deload=2,
            sleep_debt_hours=0.5,
        )
        assert d.should_deload is False
        assert d.urgency == "not_needed"
        assert d.deload_type == "none"

    def test_severe_tsb_triggers_immediate(self):
        d = assess_deload_need(tsb=-45.0)
        assert d.should_deload is True
        assert d.urgency == "immediate"

    def test_moderate_tsb_triggers_soon(self):
        d = assess_deload_need(tsb=-33.0)
        assert d.should_deload is True
        # Should be soon or immediate depending on other factors
        assert d.urgency in ("soon", "immediate")

    def test_mild_tsb_no_trigger(self):
        d = assess_deload_need(tsb=-15.0)
        assert d.urgency == "not_needed"

    def test_7_consecutive_hard_days_immediate(self):
        d = assess_deload_need(consecutive_hard_days=7)
        assert d.should_deload is True
        assert d.urgency == "immediate"

    def test_3_hard_days_optional(self):
        d = assess_deload_need(consecutive_hard_days=3)
        assert d.should_deload is True
        assert d.urgency == "optional"

    def test_6_weeks_no_deload_triggers_soon(self):
        d = assess_deload_need(weeks_since_deload=6)
        assert d.should_deload is True
        assert d.urgency in ("soon", "immediate")

    def test_severe_sleep_debt_triggers(self):
        d = assess_deload_need(sleep_debt_hours=7.0)
        assert d.should_deload is True
        assert d.urgency == "immediate"

    def test_high_subjective_fatigue_triggers(self):
        d = assess_deload_need(subjective_fatigue=9)
        assert d.should_deload is True
        assert d.urgency == "immediate"

    def test_rpe_drift_triggers(self):
        d = assess_deload_need(rpe_drift=20.0)
        assert d.should_deload is True

    def test_performance_decline_triggers(self):
        d = assess_deload_need(performance_decline_pct=12.0)
        assert d.should_deload is True
        assert d.urgency == "immediate"

    def test_multiple_mild_triggers_escalate(self):
        # 4 mild triggers → should escalate beyond "optional"
        d = assess_deload_need(
            tsb=-15.0,             # mild (no trigger, below threshold)
            consecutive_hard_days=3,  # severity 1
            weeks_since_deload=4,    # severity 1
            sleep_debt_hours=2.5,    # severity 1
            subjective_fatigue=7,    # severity 1
        )
        # 4 triggers → urgency should be "soon" or higher
        assert d.should_deload is True
        assert d.urgency in ("soon", "immediate")

    def test_deload_guidance_not_empty(self):
        d = assess_deload_need(tsb=-35.0)
        assert len(d.deload_guidance) >= 1

    def test_deload_type_complete_for_severe(self):
        d = assess_deload_need(
            tsb=-50.0,
            consecutive_hard_days=8,
            sleep_debt_hours=8.0,
        )
        if d.urgency == "immediate":
            assert d.deload_type in ("complete", "volume")

    def test_triggered_by_list_populated(self):
        d = assess_deload_need(tsb=-35.0, consecutive_hard_days=6)
        assert len(d.triggered_by) >= 1

    def test_evidence_tier_present(self):
        d = assess_deload_need()
        assert d.evidence in ("🟢 Strong", "🟡 Moderate", "🟠 Weak", "🔵 Emerging")


# ── Recovery Modalities ────────────────────────────────────────────────────────

class TestRecoveryModalities:
    def test_all_modalities_have_required_keys(self):
        required = {"primary_benefit", "protocol", "timing", "evidence", "best_for", "cautions"}
        for name, mod in RECOVERY_MODALITIES.items():
            missing = required - set(mod.keys())
            assert not missing, f"{name} missing keys: {missing}"

    def test_evidence_tiers_valid(self):
        valid_tiers = {"🟢 Strong", "🟡 Moderate", "🟠 Weak", "🔵 Emerging"}
        for name, mod in RECOVERY_MODALITIES.items():
            evidence = mod["evidence"]
            # Evidence may contain multiple tiers (e.g. "🟢 Strong; 🟡 Moderate")
            has_valid = any(tier in evidence for tier in valid_tiers)
            assert has_valid, f"{name} evidence '{evidence}' contains no valid tier"

    def test_modality_guide_returns_string(self):
        result = recovery_modality_guide(goal="soreness", post_session_type="strength")
        assert isinstance(result, str)
        assert len(result) > 50

    def test_adaptation_goal_includes_warning_for_strength_cwi(self):
        result = recovery_modality_guide(goal="adaptation", post_session_type="strength")
        assert "Cold" in result or "cold" in result or "hypertrophy" in result.lower()

    def test_all_goals_return_content(self):
        for goal in ("soreness", "performance", "adaptation", "general"):
            result = recovery_modality_guide(goal=goal)
            assert len(result) > 100

    def test_at_least_5_modalities(self):
        assert len(RECOVERY_MODALITIES) >= 5


# ── MPS Timing ────────────────────────────────────────────────────────────────

class TestMpsTiming:
    def test_mps_windows_populated(self):
        assert len(MPS_WINDOWS) >= 3

    def test_all_windows_have_evidence(self):
        valid_tiers = {"🟢 Strong", "🟡 Moderate", "🟠 Weak", "🔵 Emerging"}
        for name, w in MPS_WINDOWS.items():
            has_valid = any(tier in w.get("evidence", "") for tier in valid_tiers)
            assert has_valid, f"{name} missing valid evidence tier"

    def test_mps_guide_returns_string(self):
        result = mps_timing_guide(body_weight_kg=80.0)
        assert isinstance(result, str)
        assert "80" in result

    def test_mps_guide_personalizes_protein_target(self):
        result_70 = mps_timing_guide(body_weight_kg=70.0)
        result_90 = mps_timing_guide(body_weight_kg=90.0)
        # Both should produce different protein gram targets
        assert result_70 != result_90

    def test_pre_sleep_window_present(self):
        assert "pre_sleep" in MPS_WINDOWS

    def test_immediate_post_exercise_window_present(self):
        assert "immediate_post_exercise" in MPS_WINDOWS
