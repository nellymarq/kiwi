"""
Tests for tools/supplements.py — Supplement dosing protocols.

Covers:
- Supplement database integrity (all 10 supplements)
- DosingProtocol field validation
- Alias resolution (30+ aliases)
- Format output structure
- Category listing
- Edge cases (unknown supplements, empty inputs)
"""

import pytest
from tools.supplements import (
    SUPPLEMENT_DB, SUPPLEMENT_ALIASES,
    DosingProtocol, resolve_supplement,
    format_dosing_protocol, list_supplements_by_category,
)


# ── Database Integrity ────────────────────────────────────────────────────────

EXPECTED_SUPPLEMENTS = [
    "creatine", "caffeine", "beta_alanine", "nitrate", "vitamin_d",
    "omega_3", "magnesium", "hmb", "ashwagandha", "iron",
    "citrulline", "taurine", "tyrosine", "melatonin", "zinc", "l_carnitine",
    "glycerol", "collagen", "sodium_bicarbonate",
    "vitamin_c", "vitamin_b12", "folate", "probiotics", "curcumin", "quercetin",
]


def test_all_supplements_present():
    """All supplements must be in the database."""
    for name in EXPECTED_SUPPLEMENTS:
        assert name in SUPPLEMENT_DB, f"Missing supplement: {name}"
    assert len(SUPPLEMENT_DB) == len(EXPECTED_SUPPLEMENTS)


@pytest.mark.parametrize("key", EXPECTED_SUPPLEMENTS)
def test_supplement_has_required_fields(key):
    """Every supplement must have all DosingProtocol fields populated."""
    proto = SUPPLEMENT_DB[key]
    assert isinstance(proto, DosingProtocol)
    assert proto.name
    assert proto.category in ("ergogenic", "health", "recovery", "cognitive")
    assert proto.maintenance_dose
    assert proto.timing
    assert proto.duration
    assert len(proto.best_forms) >= 1
    assert proto.evidence
    assert proto.mechanism
    assert len(proto.key_references) >= 1


@pytest.mark.parametrize("key", EXPECTED_SUPPLEMENTS)
def test_supplement_has_evidence_tier(key):
    """Evidence field must contain a valid tier emoji."""
    proto = SUPPLEMENT_DB[key]
    assert any(t in proto.evidence for t in ["🟢", "🟡", "🟠", "🔵"])


@pytest.mark.parametrize("key", EXPECTED_SUPPLEMENTS)
def test_supplement_has_sport_notes(key):
    """Every supplement must have at least one sport-specific note."""
    proto = SUPPLEMENT_DB[key]
    assert len(proto.sport_specific_notes) >= 1


def test_creatine_specific_values():
    """Creatine dosing must match ISSN position stand."""
    cr = SUPPLEMENT_DB["creatine"]
    assert "20g" in cr.loading_dose
    assert "3–5g" in cr.maintenance_dose
    assert cr.category == "ergogenic"
    assert "🟢" in cr.evidence
    assert "ISSN" in cr.key_references[0]


def test_caffeine_specific_values():
    """Caffeine dosing must match IOC consensus."""
    caff = SUPPLEMENT_DB["caffeine"]
    assert caff.loading_dose is None  # Acute, no loading
    assert "3–6 mg/kg" in caff.maintenance_dose
    assert "🟢" in caff.evidence
    assert "CYP1A2" in caff.washout


def test_iron_specific_values():
    """Iron must include ferritin threshold and female athlete note."""
    fe = SUPPLEMENT_DB["iron"]
    assert "ferritin" in fe.loading_dose.lower()
    assert "female_athletes" in fe.sport_specific_notes


def test_vitamin_d_forms():
    """Vitamin D should recommend D3 (cholecalciferol), not D2."""
    vd = SUPPLEMENT_DB["vitamin_d"]
    assert any("D3" in f or "cholecalciferol" in f for f in vd.best_forms)


# ── Alias Resolution ─────────────────────────────────────────────────────────

def test_alias_count():
    """At least 25 aliases should be defined."""
    assert len(SUPPLEMENT_ALIASES) >= 25


@pytest.mark.parametrize("alias,expected", [
    ("creatine monohydrate", "creatine"),
    ("cm", "creatine"),
    ("coffee", "caffeine"),
    ("beta alanine", "beta_alanine"),
    ("beetroot", "nitrate"),
    ("beet juice", "nitrate"),
    ("vit d", "vitamin_d"),
    ("d3", "vitamin_d"),
    ("fish oil", "omega_3"),
    ("epa", "omega_3"),
    ("dha", "omega_3"),
    ("mag", "magnesium"),
    ("ksm-66", "ashwagandha"),
    ("ferrous sulfate", "iron"),
    ("fe", "iron"),
    ("hmb-fa", "hmb"),
])
def test_alias_resolves_correctly(alias, expected):
    """Known aliases must resolve to correct supplement."""
    result = resolve_supplement(alias)
    assert result is not None
    assert result.name == SUPPLEMENT_DB[expected].name


def test_resolve_by_canonical_name():
    """Resolving by canonical key must work."""
    for key in EXPECTED_SUPPLEMENTS:
        result = resolve_supplement(key)
        assert result is not None
        assert result.name == SUPPLEMENT_DB[key].name


def test_resolve_unknown_supplement():
    """Unknown supplement name returns None."""
    assert resolve_supplement("unicorn_dust") is None
    assert resolve_supplement("") is None
    assert resolve_supplement("   ") is None


def test_resolve_case_insensitive():
    """Resolution should be case-insensitive."""
    result = resolve_supplement("CREATINE")
    assert result is not None
    assert result.name == "Creatine Monohydrate"


def test_resolve_with_hyphens():
    """Hyphens should be converted to underscores."""
    result = resolve_supplement("beta-alanine")
    assert result is not None
    assert result.name == "Beta-Alanine"


# ── Formatting ───────────────────────────────────────────────────────────────

def test_format_dosing_protocol_basic():
    """Formatted protocol must contain all key sections."""
    proto = SUPPLEMENT_DB["creatine"]
    output = format_dosing_protocol(proto)
    assert "Creatine Monohydrate" in output
    assert "Dosing" in output
    assert "Forms" in output
    assert "Absorption" in output
    assert "Mechanism" in output
    assert "References" in output


def test_format_dosing_protocol_with_sport():
    """Sport-specific note should appear when sport matches."""
    proto = SUPPLEMENT_DB["caffeine"]
    output = format_dosing_protocol(proto, sport="endurance")
    assert "endurance" in output.lower()
    assert "time trial" in output.lower()


def test_format_dosing_protocol_loading_shown():
    """Loading dose should appear when present."""
    cr = format_dosing_protocol(SUPPLEMENT_DB["creatine"])
    assert "Loading" in cr
    # Caffeine has no loading dose
    caff = format_dosing_protocol(SUPPLEMENT_DB["caffeine"])
    assert "Loading" not in caff


def test_format_dosing_protocol_safety():
    """Safety section with UL/NOAEL and contraindications."""
    output = format_dosing_protocol(SUPPLEMENT_DB["iron"])
    assert "Safety" in output or "UL" in output
    assert "Hemochromatosis" in output


# ── Category Listing ─────────────────────────────────────────────────────────

def test_list_all_supplements():
    """Listing all supplements should show all entries."""
    output = list_supplements_by_category()
    assert f"Total: {len(SUPPLEMENT_DB)}" in output
    assert "ERGOGENIC" in output
    assert "HEALTH" in output


def test_list_by_category_ergogenic():
    """Filtering by ergogenic should show only ergogenic supplements."""
    output = list_supplements_by_category("ergogenic")
    assert "ERGOGENIC" in output
    assert "HEALTH" not in output
    assert "creatine" in output.lower()


def test_list_by_category_health():
    """Health category should include vitamin D, omega-3, magnesium, iron."""
    output = list_supplements_by_category("health")
    assert "Vitamin D3" in output
    assert "Omega-3" in output
    assert "Magnesium" in output
    assert "Iron" in output


def test_list_by_nonexistent_category():
    """Listing a nonexistent category returns empty-ish output."""
    output = list_supplements_by_category("fake_category")
    assert "Total: 0" in output
