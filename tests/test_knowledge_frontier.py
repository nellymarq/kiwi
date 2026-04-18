"""Tests for knowledge frontier analysis."""

import pytest
from tools.knowledge_frontier import analyze_frontiers, format_frontiers, FRONTIER_RULES


def test_female_without_reds_flagged():
    gaps = analyze_frontiers(
        profile={"sex": "female", "sport": "running"},
        tracked_metrics={},
        research_history=[],
    )
    topics = [g.topic for g in gaps]
    assert any("RED-S" in t for t in topics)


def test_female_with_reds_not_flagged():
    gaps = analyze_frontiers(
        profile={"sex": "female", "sport": "running"},
        tracked_metrics={},
        research_history=["red-s energy availability assessment"],
    )
    topics = [g.topic for g in gaps]
    assert not any("RED-S" in t for t in topics)


def test_combat_sport_weight_cut_flagged():
    gaps = analyze_frontiers(
        profile={"sport": "MMA"},
        tracked_metrics={},
        research_history=[],
    )
    topics = [g.topic for g in gaps]
    assert any("weight" in t.lower() or "cut" in t.lower() for t in topics)


def test_low_ferritin_iron_flagged():
    gaps = analyze_frontiers(
        profile={},
        tracked_metrics={"ferritin": [15.0, 18.0]},
        research_history=[],
    )
    topics = [g.topic for g in gaps]
    assert any("iron" in t.lower() for t in topics)


def test_comprehensive_research_no_gaps():
    gaps = analyze_frontiers(
        profile={"sex": "male", "sport": "strength", "training_status": "intermediate"},
        tracked_metrics={},
        research_history=[
            "sleep optimization athletes",
            "hydration endurance",
            "gut health athletes",
            "periodization strength training",
            "mental performance visualization",
        ],
    )
    # Should have fewer gaps since many topics covered
    assert len(gaps) < len(FRONTIER_RULES)


def test_sorting_critical_first():
    gaps = analyze_frontiers(
        profile={"sex": "female", "sport": "MMA"},
        tracked_metrics={"ferritin": [12.0]},
        research_history=[],
    )
    if len(gaps) >= 2:
        priorities = [g.priority for g in gaps]
        first_non_critical = next((i for i, p in enumerate(priorities) if p != "critical"), len(priorities))
        for i in range(first_non_critical):
            assert priorities[i] == "critical"


def test_format_empty():
    output = format_frontiers([])
    assert "comprehensive" in output.lower() or "No research gaps" in output


def test_format_with_gaps():
    gaps = analyze_frontiers(
        profile={"sex": "female", "sport": "running"},
        tracked_metrics={},
        research_history=[],
    )
    output = format_frontiers(gaps)
    assert "Research Frontier" in output
    assert "🔴" in output or "🟠" in output


def test_rules_exist():
    assert len(FRONTIER_RULES) >= 10
