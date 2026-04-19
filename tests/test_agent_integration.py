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
    """Simulates the /recommend keyword-match logic for a real finding."""
    from tools.injury_prevention import (
        PROTOCOL_ALIASES, PROTOCOL_DB, get_prevention_protocol,
        format_prevention_protocol,
    )

    finding_lower = "ACL tear rehab for a soccer midfielder".lower()
    candidates: list = []
    for key in PROTOCOL_DB.keys():
        if len(key) >= 4:
            candidates.append((key, key))
    for alias, target in PROTOCOL_ALIASES.items():
        if len(alias) >= 4:
            candidates.append((alias, target))
    candidates.sort(key=lambda kv: -len(kv[0]))

    matched = None
    for alias, target_key in candidates:
        idx = finding_lower.find(alias)
        if idx == -1:
            continue
        left_ok = idx == 0 or not finding_lower[idx - 1].isalnum()
        end = idx + len(alias)
        right_ok = end == len(finding_lower) or not finding_lower[end].isalnum()
        if left_ok or right_ok:
            matched = target_key
            break

    assert matched == "acl"
    proto = get_prevention_protocol(matched)
    assert proto is not None
    rendered = format_prevention_protocol(proto, "soccer")
    assert "FIFA 11+" in rendered


def test_prevention_no_match_on_unrelated_finding():
    """A biomarker finding should not trigger prevention-protocol injection."""
    from tools.injury_prevention import PROTOCOL_ALIASES, PROTOCOL_DB

    finding_lower = "ferritin 15 ng/ml female endurance athlete".lower()
    candidates: list = []
    for key in PROTOCOL_DB.keys():
        if len(key) >= 4:
            candidates.append((key, key))
    for alias, target in PROTOCOL_ALIASES.items():
        if len(alias) >= 4:
            candidates.append((alias, target))
    candidates.sort(key=lambda kv: -len(kv[0]))

    matched = None
    for alias, target_key in candidates:
        idx = finding_lower.find(alias)
        if idx == -1:
            continue
        left_ok = idx == 0 or not finding_lower[idx - 1].isalnum()
        end = idx + len(alias)
        right_ok = end == len(finding_lower) or not finding_lower[end].isalnum()
        if left_ok or right_ok:
            matched = target_key
            break

    assert matched is None
