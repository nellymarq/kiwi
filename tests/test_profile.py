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
