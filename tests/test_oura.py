"""Tests for Oura Ring client (mocked — no real API calls)."""

import pytest
from tools.oura import OuraClient, OuraDaySummary


def test_day_summary_to_metrics():
    s = OuraDaySummary(
        date="2026-04-17",
        sleep_hours=7.5,
        resting_hr=55.0,
        hrv_rmssd=48.0,
        readiness_score=82,
        steps=8500,
    )
    metrics = s.to_metrics()
    assert metrics["sleep_hours"] == 7.5
    assert metrics["rhr"] == 55.0
    assert metrics["hrv_rmssd"] == 48.0
    assert metrics["readiness_score"] == 82.0
    assert metrics["steps"] == 8500.0


def test_day_summary_empty():
    s = OuraDaySummary(date="2026-04-17")
    metrics = s.to_metrics()
    assert metrics == {}


def test_day_summary_partial():
    s = OuraDaySummary(date="2026-04-17", sleep_hours=8.0)
    metrics = s.to_metrics()
    assert "sleep_hours" in metrics
    assert "rhr" not in metrics


def test_client_creates():
    client = OuraClient(token="test_token")
    assert client.token == "test_token"


def test_format_report_empty():
    client = OuraClient(token="test")
    output = client.format_sync_report([])
    assert "No data" in output


def test_format_report_with_data():
    client = OuraClient(token="test")
    summaries = [
        OuraDaySummary("2026-04-15", sleep_hours=7.0, resting_hr=56, readiness_score=78, steps=9000),
        OuraDaySummary("2026-04-16", sleep_hours=8.2, resting_hr=53, readiness_score=85, steps=7500),
    ]
    output = client.format_sync_report(summaries)
    assert "2026-04-15" in output
    assert "2026-04-16" in output
    assert "7.0" in output
    assert "8.2" in output
