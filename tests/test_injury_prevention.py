"""Tests for injury prevention tool."""
import pytest

from tools.injury_prevention import (
    PROTOCOL_DB,
    PROTOCOL_ALIASES,
    ACWRResult,
    FMSScore,
    InjuryRiskAssessment,
    calculate_acwr,
    calculate_fms_composite,
    check_ten_percent_rule,
    format_acwr_report,
    format_prevention_protocol,
    get_prevention_protocol,
    list_prevention_protocols,
    return_to_sport_decision,
    score_fms_movement,
    screen_overuse_risk,
)

PREVENTION_DB = PROTOCOL_DB
PREVENTION_ALIASES = PROTOCOL_ALIASES

# ── Expected items ─────────────────────────────────────────────────────────────

EXPECTED_PROTOCOLS = [
    "acl", "ankle_sprain", "hamstring", "shoulder",
    "shin_splints", "stress_fracture", "groin", "tennis_elbow",
]

FMS_MOVEMENTS = [
    "deep_squat", "hurdle_step", "inline_lunge", "shoulder_mobility",
    "active_straight_leg_raise", "trunk_stability_pushup", "rotary_stability",
]


# ── Prevention Protocol Database Tests ────────────────────────────────────────

class TestPreventionDatabase:
    def test_all_protocols_present(self):
        for name in EXPECTED_PROTOCOLS:
            assert name in PREVENTION_DB, f"Missing protocol: {name}"

    @pytest.mark.parametrize("key", EXPECTED_PROTOCOLS)
    def test_protocol_has_required_fields(self, key):
        proto = PREVENTION_DB[key]
        assert proto.name
        assert proto.target_injury
        assert len(proto.exercises) > 0
        assert proto.frequency
        assert proto.duration
        assert proto.evidence
        assert proto.key_references

    @pytest.mark.parametrize("key", EXPECTED_PROTOCOLS)
    def test_protocol_has_evidence_tier(self, key):
        proto = PREVENTION_DB[key]
        assert any(tier in proto.evidence for tier in ["🟢", "🟡", "🟠", "🔵"])

    def test_protocol_lookup(self):
        proto = get_prevention_protocol("acl")
        assert proto is not None
        assert "ACL" in proto.name or "acl" in proto.target_injury.lower()

    def test_protocol_lookup_missing(self):
        assert get_prevention_protocol("nonexistent_injury") is None


# ── Prevention Protocol Alias Tests ──────────────────────────────────────────

class TestPreventionAliases:
    @pytest.mark.parametrize("alias,expected", [
        ("anterior cruciate ligament", "acl"),
        ("lateral ankle sprain", "ankle_sprain"),
        ("hamstring strain", "hamstring"),
        ("rotator cuff", "shoulder"),
        ("medial tibial stress syndrome", "shin_splints"),
        ("bone stress injury", "stress_fracture"),
        ("adductor strain", "groin"),
        ("lateral epicondylitis", "tennis_elbow"),
    ])
    def test_alias_resolves(self, alias, expected):
        assert alias in PREVENTION_ALIASES
        assert PREVENTION_ALIASES[alias] == expected


# ── ACWR Tests ───────────────────────────────────────────────────────────────

class TestACWR:
    def test_sweet_spot(self):
        # Steady training → ratio ~1.0
        loads = [100.0] * 28
        result = calculate_acwr(loads)
        assert isinstance(result, ACWRResult)
        assert 0.8 <= result.ratio <= 1.3
        assert result.risk_zone == "sweet spot"

    def test_danger_zone(self):
        # Low chronic + high acute spike
        loads = [50.0] * 21 + [200.0] * 7
        result = calculate_acwr(loads)
        assert result.ratio > 1.3
        assert result.risk_zone in ("caution", "danger")

    def test_undertraining(self):
        # High chronic + low acute (deload)
        loads = [150.0] * 21 + [30.0] * 7
        result = calculate_acwr(loads)
        assert result.ratio < 0.8
        assert result.risk_zone == "undertraining"

    def test_acwr_has_evidence(self):
        loads = [100.0] * 28
        result = calculate_acwr(loads)
        assert "Gabbett" in result.evidence

    def test_acwr_short_data(self):
        # Less than chronic window — should still work
        loads = [100.0] * 10
        result = calculate_acwr(loads)
        assert result.ratio > 0

    def test_acwr_minimum_data(self):
        loads = [100.0] * 7
        result = calculate_acwr(loads)
        assert result.acute_load > 0

    def test_acwr_zero_chronic(self):
        # All zeros then spike — should handle gracefully
        loads = [0.0] * 21 + [100.0] * 7
        result = calculate_acwr(loads)
        assert result.ratio > 1.5 or result.risk_zone == "danger"

    def test_acwr_custom_windows(self):
        loads = [100.0] * 35
        result = calculate_acwr(loads, acute_window=7, chronic_window=35)
        assert 0.8 <= result.ratio <= 1.3


# ── Ten Percent Rule Tests ───────────────────────────────────────────────────

class TestTenPercentRule:
    def test_safe_increase(self):
        result = check_ten_percent_rule(105.0, 100.0)
        assert result["safe"] is True
        assert result["increase_pct"] == pytest.approx(5.0)

    def test_unsafe_increase(self):
        result = check_ten_percent_rule(115.0, 100.0)
        assert result["safe"] is False
        assert result["increase_pct"] == pytest.approx(15.0)

    def test_exact_ten_percent(self):
        result = check_ten_percent_rule(110.0, 100.0)
        assert result["safe"] is True

    def test_decrease_is_safe(self):
        result = check_ten_percent_rule(80.0, 100.0)
        assert result["safe"] is True

    def test_zero_previous(self):
        result = check_ten_percent_rule(50.0, 0.0)
        assert "recommendation" in result


# ── FMS Tests ────────────────────────────────────────────────────────────────

class TestFMS:
    @pytest.mark.parametrize("movement", FMS_MOVEMENTS)
    def test_score_movement_valid(self, movement):
        result = score_fms_movement(movement, 2)
        assert isinstance(result, FMSScore)
        assert result.movement == movement
        assert result.score == 2

    def test_score_movement_perfect(self):
        result = score_fms_movement("deep_squat", 3)
        assert result.score == 3

    def test_score_movement_pain(self):
        result = score_fms_movement("deep_squat", 0)
        assert result.score == 0

    def test_score_movement_has_correctives(self):
        result = score_fms_movement("deep_squat", 1)
        assert len(result.corrective_exercises) > 0

    def test_composite_high_risk(self):
        scores = {m: 1 for m in FMS_MOVEMENTS}
        result = calculate_fms_composite(scores)
        assert result["composite_score"] == 7
        assert result["risk_level"] == "high injury risk"

    def test_composite_moderate_risk(self):
        scores = {m: 2 for m in FMS_MOVEMENTS}
        result = calculate_fms_composite(scores)
        assert result["composite_score"] == 14
        assert result["risk_level"] == "moderate"

    def test_composite_low_risk(self):
        scores = {m: 3 for m in FMS_MOVEMENTS}
        result = calculate_fms_composite(scores)
        assert result["composite_score"] == 21
        assert result["risk_level"] == "low"

    def test_composite_asymmetry_detection(self):
        scores = {m: 3 for m in FMS_MOVEMENTS}
        # Asymmetries detected when bilateral movements differ
        result = calculate_fms_composite(scores)
        assert "asymmetries" in result

    def test_composite_priority_movements(self):
        scores = {m: 3 for m in FMS_MOVEMENTS}
        scores["deep_squat"] = 1
        result = calculate_fms_composite(scores)
        assert len(result["priority_movements"]) > 0


# ── Overuse Risk Screening Tests ─────────────────────────────────────────────

class TestOveruseRisk:
    def test_youth_excessive_hours(self):
        # 10-year-old training 15 hours/week (exceeds age)
        result = screen_overuse_risk("tennis", age=10, weekly_hours=15)
        assert isinstance(result, InjuryRiskAssessment)
        assert result.risk_level in ("moderate", "high")
        assert any("hour" in f.lower() or "exceed" in f.lower() for f in result.risk_factors)

    def test_youth_safe_hours(self):
        result = screen_overuse_risk("soccer", age=14, weekly_hours=10)
        assert result.risk_level in ("low", "moderate")

    def test_early_specialization_risk(self):
        result = screen_overuse_risk("gymnastics", age=12, weekly_hours=10, specialization_age=8)
        assert any("specializ" in f.lower() for f in result.risk_factors)

    def test_adult_with_injury_history(self):
        result = screen_overuse_risk(
            "running", age=30, weekly_hours=12,
            injury_history=["shin splints", "stress fracture"]
        )
        assert result.risk_level in ("moderate", "high")

    def test_low_risk_adult(self):
        result = screen_overuse_risk("swimming", age=25, weekly_hours=8)
        assert result.risk_level in ("low", "moderate")


# ── Return to Sport Tests ────────────────────────────────────────────────────

class TestReturnToSport:
    def test_acute_phase(self):
        result = return_to_sport_decision("acl", weeks_since=1, pain_level=7, strength_deficit_pct=50.0)
        assert result["cleared"] is False
        assert result["phase"] == "acute"

    def test_rehab_phase(self):
        result = return_to_sport_decision("hamstring", weeks_since=4, pain_level=3, strength_deficit_pct=25.0)
        assert result["cleared"] is False
        assert result["phase"] == "rehabilitation"

    def test_return_to_training(self):
        result = return_to_sport_decision("ankle_sprain", weeks_since=8, pain_level=1, strength_deficit_pct=8.0)
        assert result["cleared"] is False or result["phase"] in ("return_to_training", "return_to_competition")

    def test_full_clearance(self):
        result = return_to_sport_decision("ankle_sprain", weeks_since=12, pain_level=0, strength_deficit_pct=5.0)
        assert result["cleared"] is True
        assert result["phase"] == "return_to_competition"

    def test_has_criteria(self):
        result = return_to_sport_decision("acl", weeks_since=6, pain_level=2, strength_deficit_pct=30.0)
        assert "criteria_met" in result
        assert "criteria_remaining" in result


# ── Formatting Tests ─────────────────────────────────────────────────────────

class TestFormatting:
    def test_format_acwr_report(self):
        result = calculate_acwr([100.0] * 28)
        report = format_acwr_report(result)
        assert "ACWR" in report or "Workload" in report
        assert "sweet spot" in report.lower() or "ratio" in report.lower()

    def test_format_prevention_protocol(self):
        proto = get_prevention_protocol("acl")
        assert proto is not None
        output = format_prevention_protocol(proto)
        assert proto.name in output
        assert "Exercise" in output or "exercise" in output

    def test_format_prevention_protocol_sport(self):
        proto = get_prevention_protocol("hamstring")
        assert proto is not None
        output = format_prevention_protocol(proto, sport="soccer")
        assert proto.name in output

    def test_list_prevention_protocols(self):
        output = list_prevention_protocols()
        assert "ACL" in output or "acl" in output.lower()
        assert "hamstring" in output.lower()


# ── Tier 36: match_prevention_protocol helper ──────────────────────────────

class TestMatchPreventionProtocol:
    def test_empty_list_returns_none(self):
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol([]) is None

    def test_empty_string_returns_none(self):
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol("") is None

    def test_no_alias_in_text_returns_none(self):
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol("random unrelated text about nutrition") is None

    def test_single_string_returns_key(self):
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol("hamstring strain during sprints") == "hamstring"

    def test_list_first_entry_match_wins(self):
        from tools.injury_prevention import match_prevention_protocol
        entries = ["ACL tear 2023", "groin strain 2022"]
        assert match_prevention_protocol(entries) == "acl"

    def test_respects_min_alias_length_bare_key_rejected(self):
        """Bare 'acl' (len 3) is below default min_alias_length=4, so the bare
        DB key is skipped. Only aliases of len ≥ 4 like 'acl tear' can match."""
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol("acl") is None
        assert match_prevention_protocol("acl tear diagnosed today") == "acl"

    def test_word_boundary_prevents_midword_match(self):
        """Alias fully surrounded by alphanumerics on both sides should not match."""
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol("transhamstringreally continues on") is None

    def test_none_entry_does_not_crash(self):
        """str(None) = 'None', matches nothing; next valid entry wins."""
        from tools.injury_prevention import match_prevention_protocol
        assert match_prevention_protocol([None, "ACL tear"]) == "acl"
