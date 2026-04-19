"""Tier 33 profile schema tests — menstrual_status + injury_history.

Isolation via the shared `clean_client` fixture in tests/conftest.py.
"""
import pytest

from memory.profile import UserProfile, VALID_MENSTRUAL_STATUS


# ── menstrual_status ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("value", sorted(VALID_MENSTRUAL_STATUS))
def test_menstrual_status_valid_values(clean_client, value):
    p = UserProfile(client=clean_client)
    assert p.set("menstrual_status", value) is True
    assert p.get("menstrual_status") == value


@pytest.mark.parametrize("value", ["oligo", "regular", "post", "random", "abnormal", "none"])
def test_menstrual_status_rejects_invalid(clean_client, value):
    p = UserProfile(client=clean_client)
    result = p.set("menstrual_status", value)
    # Must be a string error message, NOT False
    assert isinstance(result, str)
    assert "Invalid menstrual_status" in result
    assert p.get("menstrual_status") is None  # not saved


def test_menstrual_status_normalizes_case(clean_client):
    p = UserProfile(client=clean_client)
    assert p.set("menstrual_status", "NORMAL") is True
    assert p.get("menstrual_status") == "normal"

    assert p.set("menstrual_status", "  Amenorrheic  ") is True
    assert p.get("menstrual_status") == "amenorrheic"


# ── injury_history ───────────────────────────────────────────────────────────

def test_injury_history_comma_parsing(clean_client):
    p = UserProfile(client=clean_client)
    assert p.set("injury_history", "acl, ankle sprain, shin splints") is True
    assert p.get("injury_history") == ["acl", "ankle sprain", "shin splints"]


def test_injury_history_empty_input(clean_client):
    p = UserProfile(client=clean_client)
    # Empty string → empty list (consistent with existing list-field behavior)
    assert p.set("injury_history", "") is True
    assert p.get("injury_history") == []


def test_injury_history_accepts_list_directly(clean_client):
    p = UserProfile(client=clean_client)
    assert p.set("injury_history", ["ACL tear 2023", "stress fracture tibia"]) is True
    assert p.get("injury_history") == ["ACL tear 2023", "stress fracture tibia"]


# ── to_summary() ─────────────────────────────────────────────────────────────

def test_to_summary_skips_menstrual_status_for_male(clean_client):
    p = UserProfile(client=clean_client)
    p.set("sex", "male")
    p.set("menstrual_status", "normal")  # nonsensical but allowed
    summary = p.to_summary()
    assert "Menstrual status" not in summary


def test_to_summary_includes_menstrual_status_for_female(clean_client):
    p = UserProfile(client=clean_client)
    p.set("sex", "female")
    p.set("menstrual_status", "amenorrheic")
    summary = p.to_summary()
    assert "Menstrual status: amenorrheic" in summary


def test_to_summary_includes_injury_history_when_non_empty(clean_client):
    p = UserProfile(client=clean_client)
    p.set("injury_history", "hamstring strain, knee tendinopathy")
    summary = p.to_summary()
    assert "Injury history: hamstring strain, knee tendinopathy" in summary


def test_to_summary_skips_injury_history_when_empty(clean_client):
    p = UserProfile(client=clean_client)
    p.set("injury_history", "")
    summary = p.to_summary()
    assert "Injury history" not in summary


# ── Backwards-compat ─────────────────────────────────────────────────────────

def test_backward_compat_missing_fields(clean_client):
    p = UserProfile(client=clean_client)
    # Before any set: new fields should return None / be absent
    assert p.get("menstrual_status") is None
    assert p.get("injury_history") is None
    # to_summary() must not crash with the new fields unset
    summary = p.to_summary()
    assert "Menstrual status" not in summary
    assert "Injury history" not in summary


def test_fields_contains_new_schema(clean_client):
    p = UserProfile(client=clean_client)
    assert "menstrual_status" in p.FIELDS
    assert "injury_history" in p.FIELDS
    assert p.FIELDS["menstrual_status"] is str
    assert p.FIELDS["injury_history"] is list


# ── Tier 40: cycle_day persistence + extrapolation ───────────────────────────

def test_cycle_day_field_registered(clean_client):
    p = UserProfile(client=clean_client)
    assert "cycle_day" in p.FIELDS
    assert p.FIELDS["cycle_day"] is int


def test_cycle_day_range_validation(clean_client):
    p = UserProfile(client=clean_client)
    # Valid
    assert p.set("cycle_day", 14) is True
    # Too low
    result = p.set("cycle_day", 0)
    assert isinstance(result, str)
    # Too high
    result = p.set("cycle_day", 29)
    assert isinstance(result, str)


def test_cycle_day_auto_stamps_date(clean_client):
    from datetime import datetime, timezone
    p = UserProfile(client=clean_client)
    p.set("cycle_day", 7)
    assert p.get("cycle_day_set_at") == datetime.now(timezone.utc).date().isoformat()


def test_get_current_cycle_day_same_day(clean_client):
    """Set today, retrieve today → same value."""
    p = UserProfile(client=clean_client)
    p.set("cycle_day", 14)
    assert p.get_current_cycle_day() == 14


def test_get_current_cycle_day_with_elapsed_days(clean_client):
    """Manually set an old anchor date; extrapolation adds days with modulo 28."""
    from datetime import date, timedelta
    p = UserProfile(client=clean_client)
    p.data["cycle_day"] = 14
    # Pretend it was set 10 days ago
    past = (date.today() - timedelta(days=10)).isoformat()
    p.data["cycle_day_set_at"] = past
    # Day 14 + 10 = day 24
    assert p.get_current_cycle_day() == 24


def test_get_current_cycle_day_wraps_past_28(clean_client):
    """Extrapolation wraps at 28 via modulo."""
    from datetime import date, timedelta
    p = UserProfile(client=clean_client)
    p.data["cycle_day"] = 20
    # 10 days after day 20 → (20 + 10 - 1) % 28 + 1 = 30 % 28 + 1 = 3
    past = (date.today() - timedelta(days=10)).isoformat()
    p.data["cycle_day_set_at"] = past
    assert p.get_current_cycle_day() == 2  # 20+10=30, (30-1)%28+1 = 29%28+1 = 1+1 = 2


def test_get_current_cycle_day_full_cycle(clean_client):
    """Day N + 28 days = day N again."""
    from datetime import date, timedelta
    p = UserProfile(client=clean_client)
    p.data["cycle_day"] = 7
    past = (date.today() - timedelta(days=28)).isoformat()
    p.data["cycle_day_set_at"] = past
    assert p.get_current_cycle_day() == 7


def test_get_current_cycle_day_returns_none_when_unset(clean_client):
    p = UserProfile(client=clean_client)
    assert p.get_current_cycle_day() is None


def test_get_current_cycle_day_returns_none_on_malformed_date(clean_client):
    p = UserProfile(client=clean_client)
    p.data["cycle_day"] = 14
    p.data["cycle_day_set_at"] = "not-a-date"
    assert p.get_current_cycle_day() is None


def test_get_current_cycle_day_clock_skew_negative_elapsed(clean_client):
    """If anchor date is in the future (clock skew), return raw anchor."""
    from datetime import date, timedelta
    p = UserProfile(client=clean_client)
    p.data["cycle_day"] = 14
    # Future date — should return raw anchor, not negative math
    future = (date.today() + timedelta(days=5)).isoformat()
    p.data["cycle_day_set_at"] = future
    assert p.get_current_cycle_day() == 14


def test_to_summary_includes_extrapolated_cycle_day_for_female(clean_client):
    p = UserProfile(client=clean_client)
    p.set("sex", "female")
    p.set("cycle_day", 10)
    summary = p.to_summary()
    assert "Cycle day (today, extrapolated): 10" in summary


def test_to_summary_skips_cycle_day_for_male(clean_client):
    p = UserProfile(client=clean_client)
    p.set("sex", "male")
    p.set("cycle_day", 10)  # permissive set, but hidden in summary
    summary = p.to_summary()
    assert "Cycle day" not in summary
