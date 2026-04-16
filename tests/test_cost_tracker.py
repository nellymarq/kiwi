"""Tests for session cost tracking."""

import pytest
from tools.cost_tracker import (
    SessionCostTracker, CostEntry,
    PRICING_PER_1M, DEFAULT_MODEL_PRICING,
)


def test_empty_tracker():
    t = SessionCostTracker()
    assert t.call_count() == 0
    assert t.total_cost_usd() == 0.0
    assert "No API calls" in t.summary()


def test_record_single_call():
    t = SessionCostTracker()
    t.record("claude-opus-4-6", input_tokens=1000, output_tokens=500)
    assert t.call_count() == 1
    # $15/M input + $75/M output → 1000*15/1M + 500*75/1M = 0.015 + 0.0375 = 0.0525
    assert abs(t.total_cost_usd() - 0.0525) < 1e-6


def test_sonnet_is_cheaper():
    t = SessionCostTracker()
    t.record("claude-sonnet-4-6", input_tokens=10000, output_tokens=5000)
    # $3/M input + $15/M output → 0.03 + 0.075 = 0.105
    assert abs(t.total_cost_usd() - 0.105) < 1e-6


def test_haiku_is_cheapest():
    t = SessionCostTracker()
    t.record("claude-haiku-4-5-20251001", input_tokens=10000, output_tokens=5000)
    # $1/M input + $5/M output → 0.01 + 0.025 = 0.035
    assert abs(t.total_cost_usd() - 0.035) < 1e-6


def test_cache_pricing():
    t = SessionCostTracker()
    t.record(
        "claude-opus-4-6",
        input_tokens=100,
        output_tokens=100,
        cache_read_tokens=10000,
        cache_write_tokens=1000,
    )
    # 100*15 + 100*75 + 10000*1.5 + 1000*18.75 (all /1M)
    expected = (100 * 15 + 100 * 75 + 10000 * 1.5 + 1000 * 18.75) / 1_000_000
    assert abs(t.total_cost_usd() - expected) < 1e-6


def test_totals():
    t = SessionCostTracker()
    t.record("claude-opus-4-6", 1000, 500)
    t.record("claude-sonnet-4-6", 2000, 1000)
    assert t.total_input_tokens() == 3000
    assert t.total_output_tokens() == 1500
    assert t.call_count() == 2


def test_by_model():
    t = SessionCostTracker()
    t.record("claude-opus-4-6", 1000, 500)
    t.record("claude-opus-4-6", 2000, 1000)
    t.record("claude-sonnet-4-6", 500, 200)
    by_model = t.by_model()
    assert by_model["claude-opus-4-6"]["calls"] == 2
    assert by_model["claude-opus-4-6"]["input"] == 3000
    assert by_model["claude-sonnet-4-6"]["calls"] == 1


def test_by_purpose():
    t = SessionCostTracker()
    t.record("claude-opus-4-6", 1000, 500, purpose="synthesis")
    t.record("claude-opus-4-6", 1000, 500, purpose="synthesis")
    t.record("claude-sonnet-4-6", 500, 200, purpose="critique")
    bp = t.by_purpose()
    assert bp["synthesis"]["calls"] == 2
    assert bp["critique"]["calls"] == 1


def test_summary_format():
    t = SessionCostTracker()
    t.record("claude-opus-4-6", 1000, 500, purpose="patch")
    s = t.summary()
    assert "Total calls: 1" in s
    assert "claude-opus-4-6" in s
    assert "$" in s


def test_reset():
    t = SessionCostTracker()
    t.record("claude-opus-4-6", 100, 50)
    assert t.call_count() == 1
    t.reset()
    assert t.call_count() == 0


def test_unknown_model_uses_default():
    t = SessionCostTracker()
    t.record("some-unknown-model", 1000, 500)
    # Should use DEFAULT_MODEL_PRICING (opus rates)
    assert t.total_cost_usd() > 0


def test_pricing_constants():
    assert "claude-opus-4-6" in PRICING_PER_1M
    assert PRICING_PER_1M["claude-opus-4-6"]["output"] > PRICING_PER_1M["claude-opus-4-6"]["input"]
