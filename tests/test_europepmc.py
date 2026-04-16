"""Tests for Europe PMC client."""

import pytest
from tools.europepmc import EuropePMCClient, EuropePMCArticle


def test_article_context_block():
    art = EuropePMCArticle(
        pmid="12345",
        pmcid="PMC67890",
        title="Creatine in Athletes",
        authors=["Smith J", "Jones K", "Brown L", "White M"],
        journal="JISSN",
        year="2023",
        abstract="Background: creatine supplementation...",
        doi="10.1186/s12970-023-001",
        is_open_access=True,
        has_fulltext=True,
    )
    block = art.to_context_block()
    assert "PMID: 12345" in block
    assert "PMC67890" in block
    assert "Creatine in Athletes" in block
    assert "et al." in block
    assert "[Open Access]" in block
    assert "[Full Text Available]" in block


def test_article_no_oa():
    art = EuropePMCArticle(
        pmid="1", pmcid="", title="T", authors=["A"], journal="J", year="2022",
        abstract="a", doi="10.1/x", is_open_access=False, has_fulltext=False,
    )
    block = art.to_context_block()
    assert "[Open Access]" not in block
    assert "[Full Text Available]" not in block


def test_client_creates():
    client = EuropePMCClient()
    assert client is not None


def test_build_context_block_empty():
    client = EuropePMCClient()
    assert client.build_context_block([]) == ""


def test_build_context_block_multiple():
    client = EuropePMCClient()
    articles = [
        EuropePMCArticle("1", "PMC1", "A", ["X"], "J1", "2023", "ab1", "10.1/a"),
        EuropePMCArticle("2", "PMC2", "B", ["Y"], "J2", "2024", "ab2", "10.1/b"),
    ]
    block = client.build_context_block(articles)
    assert "Europe PMC Results (2 articles)" in block
    assert "[1]" in block
    assert "[2]" in block
