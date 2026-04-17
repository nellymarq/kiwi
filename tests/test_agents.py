"""
Comprehensive agent tests — verifies _build_messages structure, system prompts,
max_tokens, and agent names for ALL 14 agents.

Does NOT test actual Claude API calls (would require mocking or API key).
Tests the data preparation pipeline that feeds each agent.
"""

import pytest
from unittest.mock import MagicMock

from agents.base import BaseAgent, AGENT_MODEL, REFINEMENT_THRESHOLD
from agents.planning import PlanningAgent
from agents.critique import CritiqueAgent
from agents.protocol import ProtocolAgent
from agents.orchestrator import KiwiOrchestrator
from agents.sports_agent import SportsAgent
from agents.synthesis import SynthesisAgent
from agents.n_of_1 import NOf1Agent
from agents.meal_plan import MealPlanAgent
from agents.training_plan import TrainingPlanAgent
from agents.recommender import RecommenderAgent
from agents.systematic_review import SystematicReviewAgent
from agents.competition_prep import CompetitionPrepAgent
from agents.stack_optimizer import StackOptimizerAgent
from agents.risk_screen import RiskScreenAgent
from agents.question_gen import QuestionGenAgent


@pytest.fixture
def mock_client():
    return MagicMock()


# ── Agent Registry ──────────────────────────────────────────────────────────

ALL_AGENTS = [
    ("PlanningAgent", PlanningAgent),
    ("CritiqueAgent", CritiqueAgent),
    ("ProtocolAgent", ProtocolAgent),
    ("SportsAgent", SportsAgent),
    ("SynthesisAgent", SynthesisAgent),
    ("NOf1Agent", NOf1Agent),
    ("MealPlanAgent", MealPlanAgent),
    ("TrainingPlanAgent", TrainingPlanAgent),
    ("RecommenderAgent", RecommenderAgent),
    ("SystematicReviewAgent", SystematicReviewAgent),
    ("CompetitionPrepAgent", CompetitionPrepAgent),
    ("StackOptimizerAgent", StackOptimizerAgent),
    ("RiskScreenAgent", RiskScreenAgent),
    ("QuestionGenAgent", QuestionGenAgent),
]


@pytest.mark.parametrize("class_name,agent_cls", ALL_AGENTS)
def test_agent_inherits_base(class_name, agent_cls):
    assert issubclass(agent_cls, BaseAgent)


@pytest.mark.parametrize("class_name,agent_cls", ALL_AGENTS)
def test_agent_has_name(class_name, agent_cls, mock_client):
    agent = agent_cls(mock_client)
    assert agent.name
    assert isinstance(agent.name, str)
    assert len(agent.name) > 0


@pytest.mark.parametrize("class_name,agent_cls", ALL_AGENTS)
def test_agent_has_system_prompt(class_name, agent_cls, mock_client):
    agent = agent_cls(mock_client)
    prompt = agent.system_prompt
    assert prompt
    assert isinstance(prompt, str)
    assert len(prompt) > 100


@pytest.mark.parametrize("class_name,agent_cls", ALL_AGENTS)
def test_agent_max_tokens_reasonable(class_name, agent_cls, mock_client):
    agent = agent_cls(mock_client)
    assert 1000 <= agent.max_tokens <= 16000


# ── Build Messages Tests ────────────────────────────────────────────────────

def test_planning_build_messages(mock_client):
    agent = PlanningAgent(mock_client)
    msgs = agent._build_messages({
        "query": "creatine timing",
        "history_summary": "recent history",
        "profile_summary": "male 80kg",
        "pubmed_hits": "3 articles",
    })
    assert len(msgs) == 1
    assert "creatine" in msgs[0]["content"]


def test_critique_build_messages(mock_client):
    agent = CritiqueAgent(mock_client)
    msgs = agent._build_messages({
        "query": "beta-alanine dosing",
        "response_text": "Beta-alanine at 3.2g/d...",
    })
    assert len(msgs) == 1
    assert "beta-alanine" in msgs[0]["content"].lower()
    assert "RESEARCH RESPONSE" in msgs[0]["content"]


def test_protocol_build_messages(mock_client):
    agent = ProtocolAgent(mock_client)
    msgs = agent._build_messages({
        "query": "iron repletion protocol",
        "synthesis": "Iron bisglycinate 36mg/d...",
        "profile_summary": "female endurance athlete",
    })
    assert len(msgs) == 1
    assert "iron" in msgs[0]["content"].lower()
    assert "female" in msgs[0]["content"].lower()


def test_protocol_includes_interaction_warnings(mock_client):
    agent = ProtocolAgent(mock_client)
    msgs = agent._build_messages({
        "query": "supplement stack",
        "synthesis": "...",
        "profile_summary": "...",
        "interaction_warnings": "⚠️ zinc + iron: separate by 2h",
    })
    assert "interaction" in msgs[0]["content"].lower()
    assert "zinc" in msgs[0]["content"]


def test_synthesis_build_messages(mock_client):
    agent = SynthesisAgent(mock_client)
    msgs = agent._build_messages({
        "claim": "creatine improves strength in trained athletes",
        "papers_context": "PubMed: 10 articles...",
        "profile_summary": "male powerlifter",
    })
    assert len(msgs) == 1
    assert "creatine" in msgs[0]["content"]
    assert "papers" in msgs[0]["content"].lower() or "literature" in msgs[0]["content"].lower()


def test_n_of_1_build_messages(mock_client):
    agent = NOf1Agent(mock_client)
    msgs = agent._build_messages({
        "question": "Does ashwagandha reduce my cortisol?",
        "research_context": "Some studies show...",
        "profile_summary": "28M MMA fighter",
    })
    assert len(msgs) == 1
    assert "ashwagandha" in msgs[0]["content"]
    assert "n-of-1" in msgs[0]["content"].lower() or "protocol" in msgs[0]["content"].lower()


def test_meal_plan_build_messages(mock_client):
    agent = MealPlanAgent(mock_client)
    msgs = agent._build_messages({
        "profile_summary": "77kg male MMA",
        "macro_targets": "Protein: 180g, Carbs: 350g, Fat: 70g",
        "days": 5,
        "training_schedule": "MMA 5x/week",
        "dietary_restrictions": "none",
        "goal": "performance",
    })
    assert len(msgs) == 1
    assert "5-day" in msgs[0]["content"] or "5 day" in msgs[0]["content"]
    assert "180g" in msgs[0]["content"] or "macro" in msgs[0]["content"].lower()


def test_training_plan_build_messages(mock_client):
    agent = TrainingPlanAgent(mock_client)
    msgs = agent._build_messages({
        "profile_summary": "advanced lifter",
        "sport": "powerlifting",
        "weeks": 12,
        "goal": "peaking for competition",
        "current_maxes": "Squat: 200kg",
        "current_load": "CTL: 350",
        "frequency": 4,
    })
    assert len(msgs) == 1
    assert "12-week" in msgs[0]["content"] or "12 week" in msgs[0]["content"]
    assert "powerlifting" in msgs[0]["content"]


def test_recommender_build_messages(mock_client):
    agent = RecommenderAgent(mock_client)
    msgs = agent._build_messages({
        "finding": "low ferritin 18 ng/mL",
        "profile_summary": "female runner",
        "biomarker_interpretation": "ATHLETIC_LOW",
        "supplement_options": "iron, vitamin C",
        "interaction_check": "No interactions with current stack",
    })
    assert len(msgs) == 1
    assert "ferritin" in msgs[0]["content"]
    assert "iron" in msgs[0]["content"]


def test_systematic_review_build_messages(mock_client):
    agent = SystematicReviewAgent(mock_client)
    msgs = agent._build_messages({
        "question": "caffeine and endurance performance",
        "papers_context": "20 articles retrieved...",
        "population": "trained endurance athletes",
        "profile_summary": "",
    })
    assert len(msgs) == 1
    assert "caffeine" in msgs[0]["content"]
    assert "trained" in msgs[0]["content"]


def test_competition_prep_build_messages(mock_client):
    agent = CompetitionPrepAgent(mock_client)
    msgs = agent._build_messages({
        "profile_summary": "77kg male MMA fighter",
        "sport": "MMA",
        "event": "competition",
        "current_weight": "79 kg",
        "target_weight": "77 kg",
        "current_supplements": "creatine, caffeine, beta-alanine",
        "notes": "Last fight was 3 months ago",
    })
    assert len(msgs) == 1
    assert "MMA" in msgs[0]["content"]
    assert "79" in msgs[0]["content"]
    assert "creatine" in msgs[0]["content"]


def test_stack_optimizer_build_messages(mock_client):
    agent = StackOptimizerAgent(mock_client)
    msgs = agent._build_messages({
        "profile_summary": "male powerlifter",
        "goals": "strength + recovery",
        "biomarker_data": "ferritin: 25 ng/mL",
        "current_stack": "creatine, protein",
        "supplement_db_summary": "35 supplements available...",
        "interaction_data": "",
    })
    assert len(msgs) == 1
    assert "strength" in msgs[0]["content"]
    assert "ferritin" in msgs[0]["content"]


def test_risk_screen_build_messages(mock_client):
    agent = RiskScreenAgent(mock_client)
    msgs = agent._build_messages({
        "profile_summary": "female distance runner, 52kg",
        "biomarker_data": "ferritin: 12, estradiol: 25",
        "progress_data": "weight: 54 → 52 → 51",
        "training_load": "ATL: 450",
        "notes": "Missed period 2 months",
    })
    assert len(msgs) == 1
    assert "52kg" in msgs[0]["content"] or "52" in msgs[0]["content"]
    assert "period" in msgs[0]["content"] or "Missed" in msgs[0]["content"]


def test_question_gen_build_messages(mock_client):
    agent = QuestionGenAgent(mock_client)
    msgs = agent._build_messages({
        "profile_summary": "male MMA fighter",
        "biomarker_data": "cortisol: 28",
        "current_stack": "creatine, ashwagandha",
        "recent_research": "Researched creatine timing last week",
        "progress_data": "weight: 79 → 78",
    })
    assert len(msgs) == 1
    assert "cortisol" in msgs[0]["content"]
    assert "creatine" in msgs[0]["content"]


# ── System Prompt Content Checks ────────────────────────────────────────────

def test_critique_prompt_mentions_grade(mock_client):
    agent = CritiqueAgent(mock_client)
    prompt = agent.system_prompt
    assert "0.72" in prompt or "threshold" in prompt.lower()
    assert "evidence" in prompt.lower()


def test_synthesis_prompt_mentions_grade(mock_client):
    agent = SynthesisAgent(mock_client)
    prompt = agent.system_prompt
    assert "GRADE" in prompt
    assert "contradiction" in prompt.lower() or "Contradictions" in prompt


def test_meal_plan_prompt_mentions_issn(mock_client):
    agent = MealPlanAgent(mock_client)
    prompt = agent.system_prompt
    assert "ISSN" in prompt or "protein" in prompt.lower()


def test_training_plan_prompt_mentions_prilepin(mock_client):
    agent = TrainingPlanAgent(mock_client)
    prompt = agent.system_prompt
    assert "Prilepin" in prompt


def test_competition_prep_prompt_mentions_safety(mock_client):
    agent = CompetitionPrepAgent(mock_client)
    prompt = agent.system_prompt
    assert "safety" in prompt.lower() or "RED FLAG" in prompt.upper() or "stop" in prompt.lower()


def test_risk_screen_covers_reds(mock_client):
    agent = RiskScreenAgent(mock_client)
    prompt = agent.system_prompt
    assert "RED-S" in prompt
    assert "overtraining" in prompt.lower() or "OTS" in prompt


def test_stack_optimizer_limits_stack_size(mock_client):
    agent = StackOptimizerAgent(mock_client)
    prompt = agent.system_prompt
    assert "6-8" in prompt or "limit" in prompt.lower()


# ── Constants ────────────────────────────────────────────────────────────────

def test_agent_model_is_opus():
    assert "opus" in AGENT_MODEL.lower()


def test_refinement_threshold():
    assert REFINEMENT_THRESHOLD == 0.72


def test_orchestrator_creates(mock_client):
    orch = KiwiOrchestrator(mock_client)
    assert orch.planning_agent is not None
    assert orch.critique_agent is not None
    assert orch.protocol_agent is not None
