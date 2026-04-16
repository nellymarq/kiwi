"""Tests for Unpaywall client."""

import pytest
from tools.unpaywall import UnpaywallClient, UnpaywallResult, OALocation


def test_client_creates():
    client = UnpaywallClient()
    assert client.email == "kiwi@scythene.com"


def test_custom_email():
    client = UnpaywallClient(email="test@example.com")
    assert client.email == "test@example.com"


def test_result_summary_with_oa():
    result = UnpaywallResult(
        doi="10.1/test",
        title="Test Paper",
        is_oa=True,
        oa_status="gold",
        best_oa_location=OALocation(
            url="https://publisher.com/paper",
            url_for_pdf="https://publisher.com/paper.pdf",
            license="cc-by",
            version="publishedVersion",
            host_type="publisher",
            is_best=True,
        ),
        all_oa_locations=[
            OALocation("https://publisher.com/paper", "https://publisher.com/paper.pdf",
                       "cc-by", "publishedVersion", "publisher", True),
        ],
    )
    summary = result.summary()
    assert "10.1/test" in summary
    assert "Test Paper" in summary
    assert "gold" in summary
    assert ".pdf" in summary


def test_result_summary_no_oa():
    result = UnpaywallResult(
        doi="10.1/closed",
        title="Closed Paper",
        is_oa=False,
        oa_status="closed",
        best_oa_location=None,
        all_oa_locations=[],
    )
    summary = result.summary()
    assert "No open access" in summary


def test_lookup_empty_doi():
    client = UnpaywallClient()
    assert client.lookup("") is None


def test_oa_location_dataclass():
    loc = OALocation(
        url="https://example.com",
        url_for_pdf="https://example.com/pdf",
        license="cc-by",
        version="publishedVersion",
        host_type="publisher",
    )
    assert loc.license == "cc-by"
    assert not loc.is_best
