"""Tests for evidence freshness checking."""

import pytest
from tools.freshness import (
    check_supplement_freshness, check_biomarker_freshness,
    format_freshness_report, _extract_years, _newest_year,
    FreshnessFlag, FRESHNESS_THRESHOLD_YEARS,
)


def test_extract_years():
    assert _extract_years("Kreider et al. (2017) JISSN") == [2017]
    assert _extract_years("Smith 2023, Jones 2024") == [2023, 2024]
    assert _extract_years("No year here") == []


def test_newest_year():
    assert _newest_year(["Smith 2019", "Jones 2023"]) == 2023
    assert _newest_year(["No year"]) is None
    assert _newest_year([]) is None


def test_supplement_freshness_returns_list():
    flags = check_supplement_freshness()
    assert isinstance(flags, list)
    for f in flags:
        assert isinstance(f, FreshnessFlag)
        assert f.source == "supplement"
        assert f.severity in ("stale", "aging")


def test_biomarker_freshness_returns_list():
    flags = check_biomarker_freshness()
    assert isinstance(flags, list)
    for f in flags:
        assert isinstance(f, FreshnessFlag)
        assert f.source == "biomarker"


def test_freshness_flags_sorted_by_age():
    flags = check_supplement_freshness()
    if len(flags) >= 2:
        for i in range(len(flags) - 1):
            assert flags[i].age_years >= flags[i + 1].age_years


def test_format_report():
    output = format_freshness_report()
    assert isinstance(output, str)
    # Should contain either "current" message or report sections
    assert len(output) > 10


def test_threshold_constant():
    assert FRESHNESS_THRESHOLD_YEARS == 5
