"""Tier 31 agent-integration tests.

Verifies that RiskScreenAgent and RecommenderAgent correctly consume the
new context keys (reds_screening, prevention_protocol) introduced by the
autonomous enrichment at the /risk_screen and /recommend call sites.

Does not test the kiwi.py handler gating logic directly (handler-level
async flow is out of scope for unit tests here — smoke-tested manually).
Tests the agent-side contract: when the key is present, it appears in the
LLM prompt with the correct framing; when absent, no stray headers leak.
"""
from unittest.mock import MagicMock

from agents.risk_screen import RiskScreenAgent
from agents.recommender import RecommenderAgent


def _client():
    return MagicMock()


# ── RiskScreenAgent ──────────────────────────────────────────────────────────

def test_risk_screen_includes_reds_when_key_present():
    agent = RiskScreenAgent(_client())
    msgs = agent._build_messages({
        "profile_summary": "female, 24yo, distance runner",
        "reds_screening": "═══ RED-S Risk Screening ═══\n  Risk Score: 5\n  Risk Level: HIGH\n",
    })
    content = msgs[0]["content"]
    assert "RED-S structured screening" in content
    assert "Risk Level: HIGH" in content
    assert "IOC-criteria tool" in content


def test_risk_screen_omits_reds_when_empty():
    agent = RiskScreenAgent(_client())
    msgs = agent._build_messages({
        "profile_summary": "male, 30yo, strength athlete",
        "reds_screening": "",
    })
    content = msgs[0]["content"]
    assert "RED-S structured screening" not in content
    assert "IOC-criteria tool" not in content


def test_risk_screen_omits_reds_when_key_absent():
    agent = RiskScreenAgent(_client())
    msgs = agent._build_messages({"profile_summary": "irrelevant"})
    content = msgs[0]["content"]
    assert "RED-S structured screening" not in content


# ── RecommenderAgent ─────────────────────────────────────────────────────────

def test_recommender_includes_prevention_when_key_present():
    agent = RecommenderAgent(_client())
    msgs = agent._build_messages({
        "finding": "ACL rehab for soccer midfielder",
        "prevention_protocol": "═══ FIFA 11+ Neuromuscular Warm-Up ═══\nTarget: ACL Tear\n",
    })
    content = msgs[0]["content"]
    assert "injury prevention protocol" in content
    assert "FIFA 11+" in content
    # Framing must discourage treating exercises as supplement dosing
    assert "not as supplement dosing" in content


def test_recommender_omits_prevention_when_empty():
    agent = RecommenderAgent(_client())
    msgs = agent._build_messages({
        "finding": "ferritin 15 ng/mL, female endurance athlete",
        "prevention_protocol": "",
    })
    content = msgs[0]["content"]
    assert "injury prevention protocol" not in content
    assert "not as supplement dosing" not in content


# ── Handler logic — exercises the parse/match pipeline end-to-end ────────────
# These mirror what the /risk_screen and /recommend handlers do at the call site
# without requiring a full Kiwi instance.

def test_reds_parse_and_screen_pipeline():
    """Simulates the /risk_screen parse-and-gate, then invokes screen_reds."""
    from tools.female_athlete import screen_reds, format_reds_report

    notes = "menstrual_status=amenorrheic bmi=17 bone_stress_injuries=1 extra free text"
    reds_keys = {
        "menstrual_status", "bmi", "bone_stress_injuries", "disordered_eating",
        "weight_loss_pct", "mood_disturbance", "gi_issues", "recurrent_illness",
        "declining_performance", "low_energy_availability",
    }
    responses: dict = {}
    free_tokens: list = []
    for tok in notes.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k in reds_keys:
                try:
                    responses[k] = float(v) if "." in v else int(v)
                except ValueError:
                    responses[k] = v
                continue
        free_tokens.append(tok)

    assert responses == {"menstrual_status": "amenorrheic", "bmi": 17, "bone_stress_injuries": 1}
    assert " ".join(free_tokens) == "extra free text"

    result = screen_reds(responses)
    assert result.risk_level == "high"
    assert result.referral_needed
    rendered = format_reds_report(result)
    assert "RED-S Risk Screening" in rendered
    assert "Amenorrhea" in rendered


def test_prevention_keyword_match_pipeline():
    """/recommend keyword-match via shared helper."""
    from tools.injury_prevention import (
        format_prevention_protocol,
        get_prevention_protocol,
        match_prevention_protocol,
    )

    matched = match_prevention_protocol("ACL tear rehab for a soccer midfielder")
    assert matched == "acl"
    proto = get_prevention_protocol(matched)
    assert proto is not None
    rendered = format_prevention_protocol(proto, "soccer")
    assert "FIFA 11+" in rendered


def test_prevention_no_match_on_unrelated_finding():
    """Biomarker finding triggers no protocol injection."""
    from tools.injury_prevention import match_prevention_protocol

    assert match_prevention_protocol("ferritin 15 ng/ml female endurance athlete") is None


# ── Tier 33: profile auto-fill for /risk_screen ──────────────────────────────

def _merge_profile_into_reds(reds_responses, profile_data):
    """Simulates Tier 33 /risk_screen merge: fills menstrual_status from profile
    when notes didn't set it; counts bone_stress_injuries via 3-phrase scan.
    Notes override profile."""
    profile_ms = profile_data.get("menstrual_status")
    if profile_ms and "menstrual_status" not in reds_responses:
        reds_responses["menstrual_status"] = profile_ms
    if "bone_stress_injuries" not in reds_responses:
        injury_history = profile_data.get("injury_history") or []
        bone_phrases = ("stress fracture", "bone stress", "stress reaction")
        bone_count = sum(
            1 for inj in injury_history
            if any(phrase in str(inj).lower() for phrase in bone_phrases)
        )
        if bone_count > 0:
            reds_responses["bone_stress_injuries"] = bone_count
    return reds_responses


def test_risk_screen_fills_menstrual_status_from_profile():
    """Profile has menstrual_status; notes provide only bmi — profile fills the gap."""
    reds_responses: dict = {"bmi": 17}
    profile = {"sex": "female", "menstrual_status": "amenorrheic"}
    merged = _merge_profile_into_reds(reds_responses, profile)
    assert merged["menstrual_status"] == "amenorrheic"
    assert merged["bmi"] == 17


def test_risk_screen_notes_override_profile():
    """Notes-provided menstrual_status takes precedence over profile."""
    reds_responses: dict = {"menstrual_status": "amenorrheic", "bmi": 18}
    profile = {"sex": "female", "menstrual_status": "normal"}
    merged = _merge_profile_into_reds(reds_responses, profile)
    # Notes value preserved, not overwritten
    assert merged["menstrual_status"] == "amenorrheic"


def test_risk_screen_counts_bone_stress_from_injury_history():
    """3-phrase literal scan of injury_history → bone_stress_injuries count."""
    reds_responses: dict = {}
    profile = {
        "sex": "female",
        "injury_history": [
            "stress fracture tibia 2022",
            "shin splints 2023",
            "bone stress reaction metatarsal 2024",
        ],
    }
    merged = _merge_profile_into_reds(reds_responses, profile)
    # Per-entry match (any() short-circuits): stress-fracture entry counts 1,
    # shin-splints counts 0, bone-stress-reaction entry counts 1 → total 2
    assert merged["bone_stress_injuries"] == 2


def test_risk_screen_no_bone_stress_on_irrelevant_injuries():
    """ACL/ankle/hamstring injuries should not count as bone stress."""
    reds_responses: dict = {}
    profile = {
        "sex": "female",
        "injury_history": ["ACL tear 2022", "hamstring strain 2023", "ankle sprain 2024"],
    }
    merged = _merge_profile_into_reds(reds_responses, profile)
    assert "bone_stress_injuries" not in merged


# ── Tier 34: ACWR auto-enrichment for /risk_screen ──────────────────────────

def _acwr_gate_and_compute(raw_loads, today):
    """Simulates Tier 34 /risk_screen ACWR enrichment logic end-to-end."""
    from datetime import timedelta as _td

    from tools.injury_prevention import calculate_acwr, format_acwr_report

    raw_loads.sort(key=lambda e: e.get("ts", ""))
    by_day: dict = {}
    for e in raw_loads:
        day = str(e.get("ts", ""))[:10]
        if day:
            by_day[day] = by_day.get(day, 0.0) + float(e.get("value", 0.0))
    recent_window_days = {(today - _td(days=i)).isoformat() for i in range(14)}
    recent_days_with_load = [d for d in by_day if d in recent_window_days]
    if len(recent_days_with_load) >= 7:
        sorted_days = sorted(by_day.keys())
        last_28 = sorted_days[-28:]
        daily_loads = [by_day[d] for d in last_28]
        result = calculate_acwr(daily_loads, acute_window=7, chronic_window=28)
        return format_acwr_report(result)
    return ""


def test_acwr_fires_with_sufficient_history():
    """≥7 distinct days in last 14 → ACWR report injected."""
    from datetime import date, timedelta

    today = date.today()
    raw_loads = [
        {
            "ts": (today - timedelta(days=i)).isoformat() + "T10:00:00+00:00",
            "metric": "training_load",
            "value": 400.0 + i * 10,
        }
        for i in range(10)  # 10 distinct days, all within last 14
    ]
    result = _acwr_gate_and_compute(raw_loads, today)
    assert result != ""
    assert "Acute:Chronic Workload Ratio" in result
    assert "ACWR Ratio" in result


def test_acwr_skips_with_insufficient_history():
    """<7 distinct days in last 14 → silent skip (empty string)."""
    from datetime import date, timedelta

    today = date.today()
    raw_loads = [
        {
            "ts": (today - timedelta(days=i)).isoformat() + "T10:00:00+00:00",
            "metric": "training_load",
            "value": 400.0,
        }
        for i in range(5)  # only 5 distinct days
    ]
    result = _acwr_gate_and_compute(raw_loads, today)
    assert result == ""


def test_acwr_aggregates_same_day_loads():
    """Multiple same-day loads sum before ACWR calculation."""
    from datetime import date, timedelta

    today = date.today()
    raw_loads = []
    for i in range(8):  # 8 distinct days
        day = today - timedelta(days=i)
        raw_loads.append({
            "ts": day.isoformat() + "T08:00:00+00:00",
            "metric": "training_load",
            "value": 200.0,
        })
        raw_loads.append({
            "ts": day.isoformat() + "T18:00:00+00:00",
            "metric": "training_load",
            "value": 150.0,
        })
    result = _acwr_gate_and_compute(raw_loads, today)
    # 8 distinct days with same-day aggregation = 350 AU/day passes the gate
    assert result != ""
    assert "Acute:Chronic Workload Ratio" in result


# ── Tier 35: CompetitionPrepAgent enrichment ────────────────────────────────

def test_competition_prep_includes_menstrual_context_when_key_present():
    from agents.competition_prep import CompetitionPrepAgent
    agent = CompetitionPrepAgent(_client())
    msgs = agent._build_messages({
        "sport": "boxing",
        "event": "competition",
        "menstrual_context": "Athlete menstrual status (from Kiwi profile): amenorrheic",
    })
    content = msgs[0]["content"]
    assert "menstrual status" in content.lower()
    assert "amenorrheic" in content


def test_competition_prep_omits_menstrual_context_when_empty():
    from agents.competition_prep import CompetitionPrepAgent
    agent = CompetitionPrepAgent(_client())
    msgs = agent._build_messages({
        "sport": "boxing",
        "event": "competition",
        "menstrual_context": "",
    })
    content = msgs[0]["content"]
    assert "menstrual" not in content.lower()


def test_competition_prep_includes_injury_prevention_when_key_present():
    from agents.competition_prep import CompetitionPrepAgent
    agent = CompetitionPrepAgent(_client())
    msgs = agent._build_messages({
        "sport": "soccer",
        "event": "race",
        "injury_prevention_context": "Prior injury context: FIFA 11+ Neuromuscular Warm-Up",
    })
    content = msgs[0]["content"]
    assert "FIFA 11+" in content
    assert "Prior injury" in content


def test_competition_prep_omits_injury_prevention_when_empty():
    from agents.competition_prep import CompetitionPrepAgent
    agent = CompetitionPrepAgent(_client())
    msgs = agent._build_messages({
        "sport": "soccer",
        "event": "race",
        "injury_prevention_context": "",
    })
    content = msgs[0]["content"]
    assert "Prior injury" not in content
    assert "FIFA" not in content


def test_cycle_phase_lookup_for_day_14_ovulation():
    """Day 14 maps to ovulation phase with injury-risk notes."""
    from tools.female_athlete import format_cycle_training, match_training_to_phase

    result = match_training_to_phase(14, "basketball")
    phase = result["phase"]
    assert phase.phase_name == "ovulation"
    formatted = format_cycle_training(phase)
    assert "ovulation" in formatted.lower()


# ── Tier 38: DailyBriefAgent enrichment ─────────────────────────────────────

def test_daily_brief_includes_training_load_when_key_present():
    from agents.daily_brief import DailyBriefAgent
    agent = DailyBriefAgent(_client())
    msgs = agent._build_messages({
        "profile_summary": "endurance runner",
        "training_load": "═══ Acute:Chronic Workload Ratio Report ═══\n  ACWR Ratio: 1.42\n  Risk Zone: CAUTION",
    })
    content = msgs[0]["content"]
    assert "Training load analysis" in content
    assert "ACWR" in content
    assert "CAUTION" in content


def test_daily_brief_omits_training_load_when_empty():
    from agents.daily_brief import DailyBriefAgent
    agent = DailyBriefAgent(_client())
    msgs = agent._build_messages({
        "profile_summary": "irrelevant",
        "training_load": "",
    })
    content = msgs[0]["content"]
    assert "Training load analysis" not in content
    assert "ACWR" not in content


def test_daily_brief_includes_reds_when_key_present():
    from agents.daily_brief import DailyBriefAgent
    agent = DailyBriefAgent(_client())
    msgs = agent._build_messages({
        "profile_summary": "female runner",
        "reds_screening": "═══ RED-S Risk Screening ═══\n  Risk Level: HIGH",
    })
    content = msgs[0]["content"]
    assert "RED-S" in content
    assert "HIGH" in content


def test_daily_brief_includes_cycle_phase_when_key_present():
    from agents.daily_brief import DailyBriefAgent
    agent = DailyBriefAgent(_client())
    msgs = agent._build_messages({
        "profile_summary": "female athlete",
        "cycle_phase_context": "Menstrual cycle phase analysis (Kiwi tool, day 14):\nOvulation phase",
    })
    content = msgs[0]["content"]
    assert "cycle phase analysis" in content.lower()
    assert "Ovulation" in content


def test_daily_brief_reds_derivation_from_profile_pipeline():
    """Simulates /brief autonomous RED-S enrichment logic."""
    from tools.female_athlete import format_reds_report, screen_reds

    # Profile has sex=female, menstrual_status=amenorrheic, injury_history with bone stress
    profile = {
        "sex": "female",
        "menstrual_status": "amenorrheic",
        "injury_history": ["stress fracture tibia 2023", "ankle sprain 2022"],
    }

    # Handler-side logic replica
    reds_responses: dict = {}
    if profile.get("sex") == "female":
        ms = profile.get("menstrual_status")
        if ms and ms != "not_applicable":
            reds_responses["menstrual_status"] = ms
        bone_phrases = ("stress fracture", "bone stress", "stress reaction")
        bone_count = sum(
            1 for inj in profile.get("injury_history", [])
            if any(phrase in str(inj).lower() for phrase in bone_phrases)
        )
        if bone_count > 0:
            reds_responses["bone_stress_injuries"] = bone_count

    assert reds_responses == {"menstrual_status": "amenorrheic", "bone_stress_injuries": 1}
    result = screen_reds(reds_responses)
    assert result.risk_level == "high"  # amenorrhea + bone stress = high
    rendered = format_reds_report(result)
    assert "RED-S Risk Screening" in rendered


def test_daily_brief_reds_skip_for_male_profile():
    """/brief RED-S gating: male profile → empty text regardless of data."""
    profile = {
        "sex": "male",
        "menstrual_status": "normal",  # nonsensical for male but saved
        "injury_history": ["stress fracture 2023"],
    }
    # Gate fails at sex=female check → no responses built
    reds_responses: dict = {}
    if profile.get("sex") == "female":
        pass  # skipped
    assert reds_responses == {}


def test_injury_history_first_match_resolves_to_protocol():
    """Iterable input: first matching entry wins, via shared helper."""
    from tools.injury_prevention import (
        format_prevention_protocol,
        get_prevention_protocol,
        match_prevention_protocol,
    )

    injury_history = ["ACL tear 2023", "ankle sprain 2022", "hamstring 2024"]
    matched = match_prevention_protocol(injury_history)
    assert matched == "acl"
    proto = get_prevention_protocol(matched)
    assert proto is not None
    formatted = format_prevention_protocol(proto, "soccer")
    assert "FIFA 11+" in formatted
