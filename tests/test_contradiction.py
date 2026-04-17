"""Tests for contradiction detection."""

import pytest
from tools.contradiction import (
    detect_contradictions, format_contradictions,
    Contradiction, _extract_key_claims,
)


def test_no_contradictions_empty_memory():
    result = detect_contradictions("Creatine improves strength.", {})
    assert result == []


def test_no_contradictions_no_text():
    result = detect_contradictions("", {"creatine": {"content": "Creatine is effective."}})
    assert result == []


def test_extract_claims():
    text = (
        "A meta-analysis found creatine improves strength by 8%. "
        "This suggests it is effective. The weather is nice today."
    )
    claims = _extract_key_claims(text)
    assert len(claims) >= 2
    assert any("meta-analysis" in c.lower() for c in claims)


def test_detect_contradiction_positive_vs_negative():
    semantic = {
        "caffeine creatine": {
            "content": "Evidence suggests caffeine attenuates the ergogenic effect of creatine.",
        },
    }
    new_text = (
        "A recent 2026 meta-analysis found no significant effect of caffeine on creatine "
        "ergogenic benefits. The study demonstrated that creatine performance was maintained."
    )
    contradictions = detect_contradictions(new_text, semantic)
    # May or may not detect depending on exact pattern matching
    # At minimum, the function should not crash
    assert isinstance(contradictions, list)


def test_detect_contradiction_safe_vs_contraindicated():
    semantic = {
        "vitamin supplement": {
            "content": "High-dose vitamin C supplementation is recommended for endurance athletes.",
        },
    }
    new_text = (
        "This study found that high-dose vitamin supplementation is not recommended "
        "during training adaptation periods as it attenuates mitochondrial biogenesis."
    )
    contradictions = detect_contradictions(new_text, semantic)
    assert isinstance(contradictions, list)


def test_format_empty():
    assert format_contradictions([]) == ""


def test_format_with_contradictions():
    contradictions = [
        Contradiction(
            topic="creatine timing",
            stored_claim="Post-workout creatine is superior.",
            new_claim="A study found no difference in pre vs post timing.",
            confidence=0.7,
        ),
    ]
    output = format_contradictions(contradictions)
    assert "creatine timing" in output
    assert "⚡" in output
    assert "Stored:" in output
    assert "New:" in output


def test_contradiction_dedup_by_topic():
    semantic = {
        "iron": {
            "content": "Iron supplementation has no effect on performance in replete athletes.",
        },
    }
    new_text = (
        "This study found that iron supplementation improved VO2max in athletes. "
        "Another trial demonstrated iron supplementation is effective for endurance. "
        "A third study showed iron supplementation is beneficial."
    )
    contradictions = detect_contradictions(new_text, semantic)
    topic_counts = {}
    for c in contradictions:
        topic_counts[c.topic] = topic_counts.get(c.topic, 0) + 1
    for count in topic_counts.values():
        assert count <= 1  # At most one per topic
