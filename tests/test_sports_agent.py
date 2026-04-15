"""
Tests for the Sports Intelligence Agent — context building and data synthesis.

Note: actual Claude API calls are not tested (would require mock or API key).
These tests cover the data preparation pipeline that feeds the agent.
"""

import pytest
from agents.sports_agent import SportsAgent, run_sports_assessment
from agents.base import BaseAgent


def test_sports_agent_is_base_agent():
    """SportsAgent must inherit from BaseAgent."""
    assert issubclass(SportsAgent, BaseAgent)


def test_sports_agent_name():
    """Agent must identify itself correctly."""
    # Can't instantiate without client, but can check class properties
    assert SportsAgent.name.fget is not None


def test_build_messages_minimal_context():
    """Messages should build with minimal context (no HRV, no load)."""

    class FakeClient:
        pass

    agent = SportsAgent(FakeClient())
    messages = agent._build_messages({
        "athlete_name": "Test Athlete",
        "sport": "cycling",
        "training_phase": "base",
    })

    assert len(messages) == 1
    content = messages[0]["content"]
    assert "Test Athlete" in content
    assert "cycling" in content
    assert "base" in content


def test_build_messages_full_context():
    """Messages should include all data sections when provided."""

    class FakeClient:
        pass

    agent = SportsAgent(FakeClient())
    messages = agent._build_messages({
        "athlete_name": "Nelson",
        "sport": "MMA",
        "training_phase": "build",
        "readiness_report": "Readiness: 72/100 — moderate",
        "deload_assessment": "No deload needed",
        "load_data": "ATL: 350, CTL: 280, TSB: -70",
        "biomarker_summary": "Ferritin: 45 ng/mL, Testosterone: 620 ng/dL",
        "sleep_data": "7.2 hours, 2 awakenings",
        "hydration_data": "Pre: 82kg, Post: 80.5kg",
        "planned_session": "Sparring 60min RPE 8",
        "notes": "Left knee slightly sore from yesterday",
    })

    content = messages[0]["content"]
    assert "Nelson" in content
    assert "MMA" in content
    assert "HRV Readiness Report" in content
    assert "Deload Assessment" in content
    assert "Training Load Data" in content
    assert "Biomarker Summary" in content
    assert "Sleep Data" in content
    assert "Hydration" in content
    assert "Planned Session" in content
    assert "Athlete Notes" in content
    assert "Left knee" in content


def test_build_messages_omits_empty_sections():
    """Empty data sections should not appear in the message."""

    class FakeClient:
        pass

    agent = SportsAgent(FakeClient())
    messages = agent._build_messages({
        "athlete_name": "Test",
        "sport": "running",
        "training_phase": "taper",
        "readiness_report": "",
        "load_data": "",
        "sleep_data": "8 hours, good quality",
    })

    content = messages[0]["content"]
    assert "HRV Readiness" not in content
    assert "Training Load" not in content
    assert "Sleep Data" in content


def test_sports_agent_system_prompt():
    """System prompt must contain key coaching directives."""

    class FakeClient:
        pass

    agent = SportsAgent(FakeClient())
    prompt = agent.system_prompt
    assert "Today's Readiness" in prompt
    assert "Training Prescription" in prompt
    assert "Recovery Priority" in prompt
    assert "Watch Flags" in prompt


def test_readiness_import():
    """Recovery tools used by sports agent must be importable."""
    from tools.recovery import compute_readiness, assess_deload_need, HRVReading
    assert callable(compute_readiness)
    assert callable(assess_deload_need)


def test_readiness_computation():
    """Readiness score should compute from HRV readings."""
    from tools.recovery import compute_readiness, HRVReading
    from datetime import date

    readings = [
        HRVReading(rmssd=45.0, resting_hr=55.0, date=date(2026, 4, 14)),
        HRVReading(rmssd=50.0, resting_hr=53.0, date=date(2026, 4, 15)),
    ]
    result = compute_readiness(readings)
    assert hasattr(result, "score")
    assert 0 <= result.score <= 100


def test_deload_assessment():
    """Deload assessment should return structured result."""
    from tools.recovery import assess_deload_need

    result = assess_deload_need(
        tsb=-15.0,
        consecutive_hard_days=3,
        weeks_since_deload=6,
        subjective_fatigue=7,
    )
    assert hasattr(result, "should_deload")
    assert isinstance(result.should_deload, bool)
