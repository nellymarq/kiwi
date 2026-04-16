"""Tests for Semantic Scholar client."""

import pytest
from tools.semantic_scholar import SemanticScholarClient, SemanticScholarPaper


def test_paper_context_block():
    paper = SemanticScholarPaper(
        paper_id="SS123",
        title="Creatine Meta-Analysis",
        authors=["Kreider R", "Stout J"],
        journal="JISSN",
        year=2022,
        abstract="This review examines creatine...",
        doi="10.1186/s12970",
        tldr="Creatine consistently improves strength in trained individuals.",
        citation_count=500,
        influential_citation_count=50,
        is_open_access=True,
    )
    block = paper.to_context_block()
    assert "Creatine Meta-Analysis" in block
    assert "Kreider R" in block
    assert "TLDR:" in block
    assert "consistently improves" in block
    assert "500" in block
    assert "50" in block
    assert "[OA]" in block


def test_paper_without_tldr():
    paper = SemanticScholarPaper(
        paper_id="SS456",
        title="T",
        authors=["A"],
        journal="J",
        year=2023,
        abstract="a",
        doi="10.1/x",
        tldr="",
    )
    block = paper.to_context_block()
    assert "TLDR:" not in block


def test_client_creates():
    client = SemanticScholarClient()
    assert client is not None


def test_build_context_block_empty():
    client = SemanticScholarClient()
    assert client.build_context_block([]) == ""


def test_build_context_block_multiple():
    client = SemanticScholarClient()
    papers = [
        SemanticScholarPaper("1", "A", ["X"], "J1", 2023, "ab1", "10.1/a", tldr="TLDR A"),
        SemanticScholarPaper("2", "B", ["Y"], "J2", 2024, "ab2", "10.1/b", tldr="TLDR B"),
    ]
    block = client.build_context_block(papers)
    assert "Semantic Scholar Results (2 papers" in block
    assert "[1]" in block
    assert "[2]" in block


def test_fields_of_study_default():
    paper = SemanticScholarPaper(
        paper_id="1", title="T", authors=[], journal="J", year=2023,
        abstract="", doi="",
    )
    assert paper.fields_of_study == []
