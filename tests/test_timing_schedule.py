"""Tests for supplement timing schedule."""

import pytest
from tools.timing_schedule import (
    generate_timing_schedule, check_separation_conflicts,
    format_timing_schedule, _classify_timing,
    TimingSlot, SLOT_ORDER,
)


def test_classify_pre_workout():
    assert _classify_timing("30-60 min pre-workout") == "pre_workout"
    assert _classify_timing("60 min before exercise") == "pre_workout"


def test_classify_morning():
    assert _classify_timing("Morning with breakfast") == "morning"
    assert _classify_timing("AM on empty stomach") == "morning"


def test_classify_bedtime():
    assert _classify_timing("30 min before bed") == "bedtime"
    assert _classify_timing("Evening before sleep") == "bedtime"


def test_classify_any_time():
    assert _classify_timing("Any time of day") == "morning"


def test_classify_with_food():
    assert _classify_timing("With fat-containing meal") == "with_dinner"


def test_generate_schedule_empty():
    schedule = generate_timing_schedule([])
    assert schedule == []


def test_generate_schedule_creatine():
    schedule = generate_timing_schedule(["creatine"])
    assert len(schedule) >= 1
    all_supps = [name for slot in schedule for name, dose in slot.supplements]
    assert any("Creatine" in s for s in all_supps)


def test_generate_schedule_multi():
    schedule = generate_timing_schedule(["creatine", "caffeine", "melatonin", "magnesium"])
    assert len(schedule) >= 2
    slot_times = [s.time_of_day for s in schedule]
    assert len(slot_times) >= 2


def test_separation_conflicts_iron_zinc():
    conflicts = check_separation_conflicts(["iron", "zinc"])
    assert len(conflicts) >= 1
    assert any("iron" in c.lower() and "zinc" in c.lower() for c in conflicts)


def test_separation_no_conflicts():
    conflicts = check_separation_conflicts(["creatine", "caffeine"])
    assert len(conflicts) == 0


def test_format_empty():
    output = format_timing_schedule([])
    assert "No supplements" in output


def test_format_with_schedule():
    schedule = generate_timing_schedule(["creatine", "caffeine", "magnesium"])
    output = format_timing_schedule(schedule)
    assert "Daily Supplement Timing" in output
    assert "☀️" in output or "💪" in output or "🌙" in output


def test_unknown_supplement_defaults_to_morning():
    schedule = generate_timing_schedule(["mystery_supp_xyz"])
    assert len(schedule) >= 1
    assert schedule[0].time_of_day == "morning"
