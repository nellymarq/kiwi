"""Tests for natural language command routing."""

import pytest
from tools.command_router import route_natural_language, RouteMatch, format_route_suggestion


def test_import_labs():
    r = route_natural_language("import my labs: ferritin 25 testosterone 580")
    assert r is not None
    assert r.command == "/import_labs"


def test_optimize_stack():
    r = route_natural_language("optimize my supplement stack")
    assert r is not None
    assert r.command == "/optimize_stack"


def test_risk_screen():
    r = route_natural_language("screen for overtraining risks")
    assert r is not None
    assert r.command == "/risk_screen"


def test_fight_prep():
    r = route_natural_language("fight prep for next week")
    assert r is not None
    assert r.command == "/fight_prep"


def test_race_prep():
    r = route_natural_language("race preparation protocol")
    assert r is not None
    assert r.command == "/race_prep"


def test_meal_plan():
    r = route_natural_language("create a 5-day meal plan")
    assert r is not None
    assert r.command == "/meal_plan"


def test_snapshot():
    r = route_natural_language("show me a snapshot")
    assert r is not None
    assert r.command == "/snapshot"


def test_suggest_research():
    r = route_natural_language("what should I research next")
    assert r is not None
    assert r.command == "/suggest_research"


def test_export_pdf():
    r = route_natural_language("export a pdf report")
    assert r is not None
    assert r.command == "/pdf"


def test_save_session():
    r = route_natural_language("save this session")
    assert r is not None
    assert r.command == "/save_session"


def test_help():
    r = route_natural_language("what can you do")
    assert r is not None
    assert r.command == "/help"


def test_slash_commands_ignored():
    r = route_natural_language("/track weight 80")
    assert r is None


def test_short_inputs_ignored():
    r = route_natural_language("ok")
    assert r is None
    r = route_natural_language("yes")
    assert r is None


def test_research_query_not_routed():
    r = route_natural_language("what is the mechanism of creatine")
    assert r is None


def test_format_suggestion():
    match = RouteMatch(command="/optimize_stack", confidence=0.9)
    output = format_route_suggestion(match)
    assert "/optimize_stack" in output
    assert "90%" in output


def test_compare_clients():
    r = route_natural_language("compare alice and bob")
    assert r is not None
    assert r.command == "/compare_clients"


def test_team_summary():
    r = route_natural_language("show team analytics")
    assert r is not None
    assert r.command == "/team"


def test_onboard():
    r = route_natural_language("onboard new athlete")
    assert r is not None
    assert r.command == "/onboard"
