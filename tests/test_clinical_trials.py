"""
Tests for the ClinicalTrials.gov client.

Uses dataclass construction and mocked data to avoid real API calls.
"""

import pytest
from tools.clinical_trials import (
    ClinicalTrial,
    ClinicalTrialsClient,
)


def test_trial_context_block():
    trial = ClinicalTrial(
        nct_id="NCT01234567",
        title="Creatine Loading in Elite Athletes",
        status="RECRUITING",
        phase="PHASE3",
        study_type="INTERVENTIONAL",
        conditions=["Muscle Performance", "Creatine Deficiency"],
        interventions=["Creatine monohydrate 5g/d", "Placebo"],
        primary_outcomes=["Change in lean mass", "Change in 1RM"],
        enrollment=120,
        sponsor="University of Example",
        brief_summary="This RCT examines creatine loading protocols in elite strength athletes...",
    )
    block = trial.to_context_block()
    assert "NCT01234567" in block
    assert "RECRUITING" in block
    assert "PHASE3" in block
    assert "N=120" in block
    assert "Creatine monohydrate" in block
    assert "lean mass" in block
    assert "University of Example" in block


def test_trial_truncates_summary():
    long_summary = "A" * 2000
    trial = ClinicalTrial(
        nct_id="NCT9", title="T", status="", phase="NA",
        study_type="", conditions=[], interventions=[],
        primary_outcomes=[], brief_summary=long_summary,
    )
    block = trial.to_context_block()
    assert len(block) < 1200


def test_client_creates():
    client = ClinicalTrialsClient()
    assert client is not None


def test_build_context_block_empty():
    client = ClinicalTrialsClient()
    assert client.build_context_block([]) == ""


def test_build_context_block_multiple():
    client = ClinicalTrialsClient()
    trials = [
        ClinicalTrial(
            nct_id="NCT1", title="Trial A", status="RECRUITING", phase="PHASE2",
            study_type="INTERVENTIONAL", conditions=["X"], interventions=["Y"],
            primary_outcomes=["Z"], enrollment=50,
        ),
        ClinicalTrial(
            nct_id="NCT2", title="Trial B", status="COMPLETED", phase="PHASE3",
            study_type="INTERVENTIONAL", conditions=["X2"], interventions=["Y2"],
            primary_outcomes=["Z2"], enrollment=200,
        ),
    ]
    block = client.build_context_block(trials)
    assert "ClinicalTrials.gov Results (2 trials)" in block
    assert "Trial A" in block
    assert "Trial B" in block
    assert "[1]" in block
    assert "[2]" in block
