"""
Tests for Kiwi — Performance Research Architect.

Covers:
- All module imports
- Sports science calculations (evidence-based formulas)
- PubMed client query building
- Memory store operations
- User profile management
- Critique agent JSON parsing
- Agent class structure
- Ralph Wiggum Loop score validation
"""

import json
import re
import pytest
from pathlib import Path


# ── Module Imports ─────────────────────────────────────────────────────────────

def test_all_module_imports():
    """All Kiwi modules must import without errors."""
    from agents.base import BaseAgent, AGENT_MODEL, REFINEMENT_THRESHOLD
    from agents.planning import PlanningAgent
    from agents.critique import CritiqueAgent
    from agents.protocol import ProtocolAgent
    from agents.orchestrator import KiwiOrchestrator, KIWI_SYSTEM
    from tools.pubmed import PubMedClient, Article
    from tools.calculations import SportsCalc, AthleteMetrics, ACTIVITY_FACTORS
    from tools.exporter import ResearchExporter
    from tools.interactions import INTERACTION_DB, lookup_interactions, format_interaction_report, has_novel_compounds, analyze_novel_interactions
    from tools.food_database import FDCClient, FoodNutrients, NUTRIENT_IDS
    from tools.periodization import TrainingLoadCalculator, get_block_plan, prilepins_recommendation
    from tools.biomarkers import BiomarkerInterpreter, BIOMARKER_DB, interpret_panel
    from tools.sleep_optimizer import (
        classify_chronotype, optimal_wake_times, caffeine_clearance,
        sleep_debt_report, CHRONOTYPE_PROFILES, ATHLETE_SLEEP_TARGETS,
    )
    from tools.recovery import (
        compute_readiness, estimate_doms, assess_deload_need,
        recovery_modality_guide, mps_timing_guide,
        EXERCISE_DAMAGE_COEFFICIENTS, RECOVERY_MODALITIES,
    )
    from tools.hydration import (
        calculate_sweat_loss, estimate_sweat_loss_by_sport,
        design_rehydration_protocol, urine_color_status,
        SPORT_SWEAT_RATES, SWEAT_ELECTROLYTE_CONCENTRATION,
    )
    from agents.sports_agent import SportsAgent, run_sports_assessment
    from tools.supplements import SUPPLEMENT_DB, resolve_supplement, format_dosing_protocol
    from tools.body_composition import (
        classify_body_fat, estimate_body_fat_jackson_pollock_3,
        analyze_body_composition, calculate_ffmi,
        calculate_energy_availability, safe_weight_change_rate,
    )
    from tools.training_zones import (
        estimate_vo2max_cooper, predict_hr_max,
        calculate_hr_zones_karvonen, calculate_power_zones,
        calculate_pace_zones, recommend_intensity_distribution,
    )
    from memory.store import KiwiMemory
    from memory.profile import UserProfile

    assert AGENT_MODEL == "claude-opus-4-6"
    assert REFINEMENT_THRESHOLD == 0.72
    assert isinstance(KIWI_SYSTEM, str) and len(KIWI_SYSTEM) > 500


# ── Sports Science Calculations ────────────────────────────────────────────────

def test_bmr_mifflin_male():
    """Mifflin-St Jeor for 80kg, 180cm, 25yo male."""
    from tools.calculations import SportsCalc
    bmr = SportsCalc.bmr_mifflin(80, 180, 25, "male")
    # Expected: (10*80) + (6.25*180) - (5*25) + 5 = 800 + 1125 - 125 + 5 = 1805
    assert abs(bmr - 1805) < 1


def test_bmr_mifflin_female():
    """Mifflin-St Jeor for 60kg, 165cm, 28yo female."""
    from tools.calculations import SportsCalc
    bmr = SportsCalc.bmr_mifflin(60, 165, 28, "female")
    # Expected: (10*60) + (6.25*165) - (5*28) - 161 = 600 + 1031.25 - 140 - 161 = 1330.25
    assert abs(bmr - 1330.25) < 1


def test_bmr_katch_mcardle():
    """Katch-McArdle for 70kg LBM."""
    from tools.calculations import SportsCalc
    bmr = SportsCalc.bmr_katch_mcardle(70)
    # Expected: 370 + (21.6 * 70) = 370 + 1512 = 1882
    assert abs(bmr - 1882) < 1


def test_tdee_multipliers():
    """TDEE activity multipliers match literature values."""
    from tools.calculations import SportsCalc, ACTIVITY_FACTORS
    assert ACTIVITY_FACTORS["sedentary"] == 1.2
    assert ACTIVITY_FACTORS["active"] == 1.725
    assert ACTIVITY_FACTORS["very_active"] == 1.9

    bmr = 1800
    tdee = SportsCalc.tdee(bmr, "active")
    assert abs(tdee - 1800 * 1.725) < 0.01


def test_energy_availability_reds_threshold():
    """Energy availability < 30 kcal/kg FFM/day = RED-S risk (IOC 2023)."""
    from tools.calculations import SportsCalc
    # Scenario: 2000 kcal intake, 1200 kcal exercise, 55kg FFM
    ea = SportsCalc.energy_availability(2000, 1200, 55)
    # EA = (2000 - 1200) / 55 = 14.5 kcal/kg FFM/day (below RED-S threshold)
    assert abs(ea - 800 / 55) < 0.01
    assert ea < 30  # RED-S risk


def test_protein_targets_strength():
    """ISSN protein targets for 80kg strength athlete."""
    from tools.calculations import SportsCalc
    targets = SportsCalc.protein_targets(80, "strength")
    # 1.6–2.2 g/kg → 128–176g
    assert targets["min_g"] == 128.0
    assert targets["max_g"] == 176.0
    assert "ISSN" in targets["evidence"]
    assert "🟢" in targets["evidence"]


def test_protein_targets_hypocaloric():
    """Hypocaloric protein targets are higher (Helms et al. 2014)."""
    from tools.calculations import SportsCalc
    targets = SportsCalc.protein_targets(80, "hypocaloric")
    # 2.3–3.1 g/kg
    assert targets["min_g"] == pytest.approx(2.3 * 80, abs=0.1)
    assert targets["max_g"] == pytest.approx(3.1 * 80, abs=0.1)


def test_creatine_dosing():
    """Creatine dosing per ISSN 2017 Position Stand."""
    from tools.calculations import SportsCalc
    dosing = SportsCalc.creatine_dosing(80)
    # Maintenance: max(3.0, 0.03 * 80) = max(3.0, 2.4) = 3.0g
    assert "3.0" in dosing["maintenance_g_per_day"]
    assert "🟢" in dosing["evidence"]
    assert "ISSN" in dosing["evidence"]


def test_caffeine_dosing():
    """Caffeine dosing: 3–6 mg/kg for 80kg athlete = 240–480mg."""
    from tools.calculations import SportsCalc
    dosing = SportsCalc.caffeine_dosing(80)
    assert "240" in dosing["dose_range_mg"]
    assert "480" in dosing["dose_range_mg"]
    assert "CYP1A2" in dosing["half_life"]


def test_compute_full_metrics():
    """Full metrics computation with body composition."""
    from tools.calculations import SportsCalc
    m = SportsCalc.compute_full_metrics(
        weight_kg=80,
        height_cm=180,
        age=25,
        sex="male",
        activity_level="active",
        body_fat_pct=12,
    )
    assert m.bmr_mifflin == pytest.approx(1805, abs=1)
    assert m.tdee == pytest.approx(1805 * 1.725, abs=2)
    assert m.ffm_kg == pytest.approx(80 * 0.88, abs=0.1)
    assert m.bmr_katch is not None
    assert m.protein_target_g > 0
    assert m.summary()  # Non-empty string


# ── PubMed Client ──────────────────────────────────────────────────────────────

def test_pubmed_search_string_basic():
    from tools.pubmed import PubMedClient
    pb = PubMedClient()
    s = pb.build_search_string("magnesium sleep quality")
    assert "magnesium sleep quality" in s.lower()


def test_pubmed_search_string_with_study_types():
    from tools.pubmed import PubMedClient
    pb = PubMedClient()
    s = pb.build_search_string("creatine", ["randomized controlled trial", "meta-analysis"])
    assert "randomized controlled trial" in s
    assert "meta-analysis" in s
    assert "[pt]" in s


def test_article_context_block():
    from tools.pubmed import Article
    art = Article(
        pmid="12345678",
        title="Effects of creatine on strength",
        authors=["Smith J", "Jones A", "Brown K", "White L"],
        journal="J Strength Cond Res",
        year="2023",
        abstract="This RCT examined creatine effects on maximal strength...",
        doi="10.1234/test",
    )
    block = art.to_context_block()
    assert "12345678" in block
    assert "et al." in block   # >3 authors → et al.
    assert "10.1234/test" in block
    assert "This RCT" in block


# ── Memory Store ───────────────────────────────────────────────────────────────

def test_memory_default_structure():
    from memory.store import KiwiMemory
    mem = KiwiMemory()
    assert "episodic" in mem.data
    assert "semantic" in mem.data
    assert "threads" in mem.data
    assert "user_notes" in mem.data


def test_memory_semantic_store_retrieve():
    from memory.store import KiwiMemory
    mem = KiwiMemory()
    mem.add_semantic("creatine monohydrate", "Evidence shows 3–5g/day maintenance dose...")
    result = mem.get_semantic("creatine monohydrate")
    assert "3–5g" in result


def test_memory_semantic_case_insensitive():
    from memory.store import KiwiMemory
    mem = KiwiMemory()
    mem.add_semantic("Magnesium", "Critical role in 300+ enzyme reactions")
    assert mem.get_semantic("magnesium")  # lowercase lookup
    assert mem.get_semantic("MAGNESIUM")  # uppercase lookup


def test_memory_thread_lifecycle():
    import uuid
    from memory.store import KiwiMemory
    mem = KiwiMemory()
    # Use UUID to avoid conflicts with previously persisted test data
    thread_name = f"test_thread_{uuid.uuid4().hex[:8]}"
    ok = mem.create_thread(thread_name, "Testing thread creation")
    assert ok is True
    duplicate = mem.create_thread(thread_name)
    assert duplicate is False  # Can't create duplicate
    threads = mem.list_threads()
    names = [t["name"] for t in threads]
    assert thread_name in names


def test_memory_history_summary_empty():
    from memory.store import KiwiMemory
    mem = KiwiMemory()
    # Fresh memory with no history
    mem.data["episodic"] = []
    summary = mem.get_history_summary()
    assert "No prior" in summary


# ── User Profile ───────────────────────────────────────────────────────────────

def test_profile_set_and_get():
    from memory.profile import UserProfile
    p = UserProfile()
    p.set("weight_kg", "80.5")
    assert p.get("weight_kg") == pytest.approx(80.5)


def test_profile_set_invalid_field():
    from memory.profile import UserProfile
    p = UserProfile()
    ok = p.set("nonexistent_field", "value")
    assert ok is False


def test_profile_list_field():
    from memory.profile import UserProfile
    p = UserProfile()
    p.set("dietary_restrictions", "gluten-free, lactose intolerance, shellfish")
    restrictions = p.get("dietary_restrictions")
    assert isinstance(restrictions, list)
    assert len(restrictions) == 3
    assert "gluten-free" in restrictions


def test_profile_completeness_check():
    from memory.profile import UserProfile
    p = UserProfile()
    p.data = {}  # Reset
    assert not p.is_complete()

    p.set("weight_kg", "80")
    p.set("sex", "male")
    p.set("age", "25")
    p.set("activity_level", "active")
    assert p.is_complete()


def test_profile_to_summary():
    from memory.profile import UserProfile
    p = UserProfile()
    p.data = {
        "name": "Test Athlete",
        "weight_kg": 80.0,
        "sex": "male",
        "age": 25,
        "sport": "cycling",
    }
    summary = p.to_summary()
    assert "Test Athlete" in summary
    assert "80.0" in summary
    assert "cycling" in summary


# ── Critique (Ralph Wiggum Loop) JSON Parsing ──────────────────────────────────

def test_rwl_json_parsing_clean():
    """Test that clean JSON from Claude is parsed correctly."""
    raw = """{
  "score": 0.81,
  "dimension_scores": {
    "evidence_grounding": 0.85,
    "evidence_hierarchy": 0.80,
    "mechanistic_accuracy": 0.80,
    "logical_consistency": 0.78,
    "uncertainty_handling": 0.85
  },
  "critical_issues": [],
  "minor_issues": ["Could specify study population more clearly"],
  "strengths": ["Strong evidence hierarchy labeling", "Mechanistic accuracy excellent"],
  "needs_refinement": false,
  "refinement_priority": null
}"""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    assert m is not None
    data = json.loads(m.group())
    assert data["score"] == 0.81
    assert data["needs_refinement"] is False
    assert len(data["strengths"]) == 2


def test_rwl_json_parsing_with_preamble():
    """Test JSON extraction from Claude response with text preamble."""
    raw = """Here is my critique evaluation:

{
  "score": 0.58,
  "dimension_scores": {
    "evidence_grounding": 0.45,
    "evidence_hierarchy": 0.60,
    "mechanistic_accuracy": 0.70,
    "logical_consistency": 0.65,
    "uncertainty_handling": 0.50
  },
  "critical_issues": ["Unsupported claim about ATP synthesis pathway", "Missing evidence tier labels"],
  "minor_issues": [],
  "strengths": ["Good structure"],
  "needs_refinement": true,
  "refinement_priority": "evidence_grounding"
}"""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    assert m is not None
    data = json.loads(m.group())
    assert data["score"] == 0.58
    assert data["needs_refinement"] is True
    assert data["refinement_priority"] == "evidence_grounding"
    assert len(data["critical_issues"]) == 2
    # Verify weighted score math
    dims = data["dimension_scores"]
    computed = (
        dims["evidence_grounding"] * 0.30 +
        dims["evidence_hierarchy"] * 0.20 +
        dims["mechanistic_accuracy"] * 0.20 +
        dims["logical_consistency"] * 0.20 +
        dims["uncertainty_handling"] * 0.10
    )
    assert abs(computed - 0.58) < 0.05


def test_rwl_threshold():
    """Verify REFINEMENT_THRESHOLD is 0.72 and enforced correctly."""
    from agents.base import REFINEMENT_THRESHOLD
    assert REFINEMENT_THRESHOLD == 0.72
    # A score of 0.71 is below threshold
    assert 0.71 < REFINEMENT_THRESHOLD
    # A score of 0.73 is above threshold
    assert 0.73 > REFINEMENT_THRESHOLD


# ── Agent Structure Tests ──────────────────────────────────────────────────────

def test_planning_agent_builds_messages():
    """Planning agent must build valid message list from context."""
    import anthropic
    from agents.planning import PlanningAgent

    client = anthropic.AsyncAnthropic.__new__(anthropic.AsyncAnthropic)
    agent = PlanningAgent(client)

    messages = agent._build_messages({
        "query": "What is the optimal creatine loading protocol?",
        "history_summary": "Prior research on creatine kinetics.",
        "profile_summary": "Male, 80kg, strength athlete.",
        "pubmed_hits": "PMID: 12345 — Creatine meta-analysis",
    })

    assert isinstance(messages, list)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    assert "creatine loading" in content.lower()
    assert "80kg" in content


def test_critique_agent_builds_messages():
    """Critique agent builds messages from query + response."""
    import anthropic
    from agents.critique import CritiqueAgent

    client = anthropic.AsyncAnthropic.__new__(anthropic.AsyncAnthropic)
    agent = CritiqueAgent(client)

    messages = agent._build_messages({
        "query": "Effects of beta-alanine on muscular endurance",
        "response_text": "Beta-alanine increases carnosine... 🟢 Strong evidence...",
    })

    assert messages[0]["role"] == "user"
    assert "beta-alanine" in messages[0]["content"].lower()
    assert "Strong evidence" in messages[0]["content"]


def test_protocol_agent_builds_messages():
    """Protocol agent injects synthesis and profile into messages."""
    import anthropic
    from agents.protocol import ProtocolAgent

    client = anthropic.AsyncAnthropic.__new__(anthropic.AsyncAnthropic)
    agent = ProtocolAgent(client)

    messages = agent._build_messages({
        "query": "Creatine protocol for strength athlete",
        "synthesis": "Creatine monohydrate: 🟢 Strong evidence...",
        "profile_summary": "Male, 25y, 80kg, strength training",
    })

    assert "Creatine protocol" in messages[0]["content"]
    assert "🟢 Strong evidence" in messages[0]["content"]
    assert "strength training" in messages[0]["content"]
