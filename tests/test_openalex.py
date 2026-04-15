"""
Tests for the OpenAlex client — scholarly literature retrieval.

Uses mocked data to avoid real API calls in tests.
"""

import pytest
from tools.openalex import (
    OpenAlexClient,
    OpenAlexWork,
    reconstruct_abstract,
    SPORTS_NUTRITION_JOURNALS,
    SPORTS_NUTRITION_ISSNS,
)


# ── Abstract Reconstruction ──────────────────────────────────────────────────

def test_reconstruct_abstract_basic():
    inverted = {"Creatine": [0], "supplementation": [1], "increases": [2], "strength": [3]}
    result = reconstruct_abstract(inverted)
    assert result == "Creatine supplementation increases strength"


def test_reconstruct_abstract_repeated_words():
    inverted = {"the": [0, 4], "study": [1], "showed": [2], "that": [3], "effect": [5]}
    result = reconstruct_abstract(inverted)
    assert result == "the study showed that the effect"


def test_reconstruct_abstract_empty():
    assert reconstruct_abstract(None) == ""
    assert reconstruct_abstract({}) == ""


# ── OpenAlexWork ─────────────────────────────────────────────────────────────

def test_work_context_block():
    work = OpenAlexWork(
        openalex_id="W123",
        title="Creatine and Performance",
        authors=["Kreider R", "Stout J", "Greenwood M", "Campbell B"],
        journal="JISSN",
        year=2022,
        abstract="This review examines creatine supplementation...",
        doi="10.1186/s12970-022-001",
        cited_by_count=150,
        open_access=True,
    )
    block = work.to_context_block()
    assert "Creatine and Performance" in block
    assert "Kreider R" in block
    assert "et al." in block
    assert "JISSN" in block
    assert "[Open Access]" in block
    assert "150" in block
    assert "10.1186" in block


def test_work_context_block_no_oa():
    work = OpenAlexWork(
        openalex_id="W456",
        title="Test",
        authors=["Author A"],
        journal="Test Journal",
        year=2023,
        abstract="Test abstract",
        doi="10.1000/test",
        open_access=False,
    )
    block = work.to_context_block()
    assert "[Open Access]" not in block


# ── Journal Constants ────────────────────────────────────────────────────────

def test_sports_nutrition_journals_present():
    assert "JISSN" in SPORTS_NUTRITION_JOURNALS
    assert "BJSM" in SPORTS_NUTRITION_JOURNALS
    assert "Sports Medicine" in SPORTS_NUTRITION_JOURNALS
    assert "Nutrients" in SPORTS_NUTRITION_JOURNALS
    assert "Frontiers in Nutrition" in SPORTS_NUTRITION_JOURNALS


def test_issns_list_matches_journals():
    assert len(SPORTS_NUTRITION_ISSNS) == len(SPORTS_NUTRITION_JOURNALS)
    for issn in SPORTS_NUTRITION_ISSNS:
        assert "-" in issn


# ── Client Instantiation ────────────────────────────────────────────────────

def test_client_creates():
    client = OpenAlexClient()
    assert client.email == "kiwi@scythene.com"


def test_client_custom_email():
    client = OpenAlexClient(email="test@example.com")
    assert client.email == "test@example.com"


# ── Build Context Block ─────────────────────────────────────────────────────

def test_build_context_block_empty():
    client = OpenAlexClient()
    assert client.build_context_block([]) == ""


def test_build_context_block_multiple():
    client = OpenAlexClient()
    works = [
        OpenAlexWork("W1", "Study A", ["Auth1"], "J1", 2023, "Abstract A", "10.1/a"),
        OpenAlexWork("W2", "Study B", ["Auth2"], "J2", 2024, "Abstract B", "10.1/b"),
    ]
    block = client.build_context_block(works)
    assert "OpenAlex Results (2 articles)" in block
    assert "Study A" in block
    assert "Study B" in block
    assert "[1]" in block
    assert "[2]" in block
