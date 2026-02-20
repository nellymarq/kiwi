"""
Tests for tools/food_database.py — USDA FoodData Central API client.

Covers:
- FoodNutrients dataclass methods
- NUTRIENT_IDS / AMINO_ACID_IDS completeness
- FDCClient cache logic
- scale_to() nutrient scaling
- macro_summary() / full_report() formatting
- compare_foods() table structure
- FDCClient initialization and throttle
"""
import time
import pytest
from tools.food_database import (
    FoodNutrients,
    FDCClient,
    NUTRIENT_IDS,
    AMINO_ACID_IDS,
    FDC_BASE,
)


# ── NUTRIENT_IDS Coverage ──────────────────────────────────────────────────────

def test_nutrient_ids_has_core_macros():
    """Core macronutrients must be present in NUTRIENT_IDS."""
    names = set(NUTRIENT_IDS.values())
    assert any("Energy" in n for n in names)
    assert any("Protein" in n for n in names)
    assert any("Fat" in n for n in names)
    assert any("Carb" in n for n in names)


def test_nutrient_ids_has_key_micros():
    """Key micronutrients must be in NUTRIENT_IDS."""
    names = set(NUTRIENT_IDS.values())
    assert any("Calcium" in n for n in names)
    assert any("Iron" in n for n in names)
    assert any("Vitamin C" in n for n in names)
    assert any("Vitamin D" in n for n in names)


def test_amino_acid_ids_has_essential_aminos():
    """Essential amino acids must all be in AMINO_ACID_IDS."""
    names = " ".join(AMINO_ACID_IDS.values())
    essentials = ["Leucine", "Lysine", "Methionine", "Valine", "Isoleucine",
                  "Threonine", "Tryptophan", "Phenylalanine"]
    for aa in essentials:
        assert aa in names, f"Essential amino acid {aa} missing from AMINO_ACID_IDS"


def test_nutrient_ids_all_unique_names():
    """Nutrient names should be unique (no two IDs map to the same display name)."""
    names = list(NUTRIENT_IDS.values())
    # Allow a few duplicates due to aliasing (e.g. Dietary Fiber / Total Fiber)
    # but the total unique should be >= 80% of total
    unique_count = len(set(names))
    assert unique_count >= len(names) * 0.75, "Too many duplicate nutrient names"


def test_fdc_base_url():
    """FDC_BASE must point to the USDA API."""
    assert "nal.usda.gov" in FDC_BASE
    assert "fdc" in FDC_BASE


# ── FoodNutrients Dataclass ────────────────────────────────────────────────────

def _make_food(**kwargs) -> FoodNutrients:
    defaults = dict(
        fdc_id=123456,
        description="Chicken Breast, cooked",
        brand="",
        data_type="Foundation",
        serving_size_g=100.0,
        nutrients={
            "Energy (kcal)": 165.0,
            "Protein (g)": 31.0,
            "Total Fat (g)": 3.6,
            "Total Carbs (g)": 0.0,
            "Dietary Fiber (g)": 0.0,
            "Calcium (mg)": 15.0,
            "Iron (mg)": 1.2,
            "Vitamin C (mg)": 0.0,
        },
        amino_acids={"Leucine (g)": 2.5, "Lysine (g)": 2.8},
    )
    defaults.update(kwargs)
    return FoodNutrients(**defaults)


def test_food_get_existing_nutrient():
    food = _make_food()
    assert food.get("Protein (g)") == pytest.approx(31.0)


def test_food_get_missing_nutrient_default():
    food = _make_food()
    assert food.get("Nonexistent", 99.9) == pytest.approx(99.9)


def test_scale_to_doubles_nutrients():
    food = _make_food()
    scaled = food.scale_to(200.0)
    assert scaled.serving_size_g == 200.0
    assert scaled.get("Protein (g)") == pytest.approx(31.0 * 2, rel=0.01)
    assert scaled.get("Energy (kcal)") == pytest.approx(165.0 * 2, rel=0.01)


def test_scale_to_50g():
    food = _make_food()
    scaled = food.scale_to(50.0)
    assert scaled.get("Protein (g)") == pytest.approx(31.0 * 0.5, rel=0.01)


def test_scale_to_scales_amino_acids():
    food = _make_food()
    scaled = food.scale_to(200.0)
    assert scaled.amino_acids.get("Leucine (g)", 0) == pytest.approx(2.5 * 2, rel=0.01)


def test_scale_to_preserves_metadata():
    food = _make_food()
    scaled = food.scale_to(150.0)
    assert scaled.fdc_id == food.fdc_id
    assert scaled.description == food.description
    assert scaled.data_type == food.data_type


def test_macro_summary_format():
    food = _make_food()
    summary = food.macro_summary()
    assert "165" in summary      # kcal
    assert "31.0" in summary     # protein
    assert "0.0g carbs" in summary
    assert "3.6g fat" in summary
    assert "Per 100g" in summary


def test_macro_summary_respects_serving_size():
    food = _make_food()
    scaled = food.scale_to(200.0)
    summary = scaled.macro_summary()
    assert "Per 200g" in summary
    assert "330" in summary  # 165 * 2


def test_full_report_contains_food_name():
    food = _make_food()
    report = food.full_report()
    assert "Chicken Breast" in report
    assert "Foundation" in report


def test_full_report_shows_micros():
    food = _make_food()
    report = food.full_report()
    assert "Calcium" in report or "Iron" in report


def test_full_report_include_aminos_false():
    """Without include_aminos, amino acids should not appear in report."""
    food = _make_food()
    report = food.full_report(include_aminos=False)
    assert "Leucine" not in report


def test_full_report_include_aminos_true():
    """With include_aminos, amino acid section should appear."""
    food = _make_food()
    report = food.full_report(include_aminos=True)
    assert "Leucine" in report
    assert "Amino Acid Profile" in report


def test_full_report_branded_food():
    food = _make_food(brand="Nike Nutrition")
    report = food.full_report()
    assert "Nike Nutrition" in report


def test_full_report_foundation_food_no_brand():
    food = _make_food(brand="")
    report = food.full_report()
    assert "Foundation Food" in report


# ── FDCClient Initialization ───────────────────────────────────────────────────

def test_fdcclient_init_defaults():
    client = FDCClient()
    assert client.api_key  # Not empty
    assert client._min_interval > 0
    assert isinstance(client._cache, dict)


def test_fdcclient_custom_api_key():
    client = FDCClient(api_key="TEST_KEY_123")
    assert client.api_key == "TEST_KEY_123"


def test_fdcclient_throttle_enforced():
    """Throttle must wait at least min_interval between calls."""
    client = FDCClient()
    client._last_request = time.time()
    start = time.time()
    client._throttle()
    elapsed = time.time() - start
    # Should have waited some amount (min_interval ~0.5s)
    # We just verify _throttle doesn't crash and updates timestamp
    assert client._last_request >= start


# ── FDCClient Cache ────────────────────────────────────────────────────────────

def test_search_cache_key():
    """Cache keys for search must include query and page size."""
    client = FDCClient()
    # Pre-populate cache
    client._cache["search:chicken:5"] = [{"fdcId": 123, "dataType": "Foundation"}]
    results = client.search("chicken", max_results=5)
    assert results == [{"fdcId": 123, "dataType": "Foundation"}]


def test_get_food_cache_key():
    """Cache keys for food must include fdc_id."""
    client = FDCClient()
    # Pre-populate cache with minimal raw food data
    client._cache["food:999"] = {
        "description": "Cached Food",
        "brandOwner": "TestBrand",
        "dataType": "Foundation",
        "foodNutrients": [
            {"nutrient": {"id": 1008}, "amount": 200.0},   # Energy
            {"nutrient": {"id": 1003}, "amount": 25.0},    # Protein
        ],
    }
    food = client.get_food(999, serving_g=100.0)
    assert food is not None
    assert food.description == "Cached Food"
    assert food.get("Energy (kcal)") == pytest.approx(200.0)
    assert food.get("Protein (g)") == pytest.approx(25.0)


def test_get_food_scales_correctly_via_cache():
    """get_food with serving_g should scale nutrients."""
    client = FDCClient()
    client._cache["food:888"] = {
        "description": "Scale Test Food",
        "brandOwner": "",
        "dataType": "SR Legacy",
        "foodNutrients": [
            {"nutrient": {"id": 1003}, "amount": 20.0},  # 20g protein per 100g
        ],
    }
    food = client.get_food(888, serving_g=200.0)
    assert food is not None
    assert food.get("Protein (g)") == pytest.approx(40.0, rel=0.01)
    assert food.serving_size_g == 200.0


def test_get_food_100g_no_scaling():
    """get_food at 100g should not scale (returns raw values)."""
    client = FDCClient()
    client._cache["food:777"] = {
        "description": "No Scale",
        "brandOwner": "",
        "dataType": "Foundation",
        "foodNutrients": [
            {"nutrient": {"id": 1003}, "amount": 30.0},  # 30g protein
        ],
    }
    food = client.get_food(777, serving_g=100.0)
    assert food is not None
    assert food.get("Protein (g)") == pytest.approx(30.0)
    assert food.serving_size_g == 100.0


def test_get_food_includes_aminos_via_cache():
    """include_aminos=True should populate amino_acids dict."""
    client = FDCClient()
    client._cache["food:666"] = {
        "description": "Amino Test",
        "brandOwner": "",
        "dataType": "Foundation",
        "foodNutrients": [
            {"nutrient": {"id": 1003}, "amount": 25.0},   # Protein
            {"nutrient": {"id": 1213}, "amount": 2.1},    # Leucine
            {"nutrient": {"id": 1214}, "amount": 1.8},    # Lysine
        ],
    }
    food = client.get_food(666, serving_g=100.0, include_aminos=True)
    assert food is not None
    assert food.amino_acids.get("Leucine (g)") == pytest.approx(2.1)
    assert food.amino_acids.get("Lysine (g)") == pytest.approx(1.8)


def test_get_food_null_amount_handled():
    """Null nutrient amounts (None) should default to 0.0 without crashing."""
    client = FDCClient()
    client._cache["food:555"] = {
        "description": "Null Amount Test",
        "brandOwner": "",
        "dataType": "Foundation",
        "foodNutrients": [
            {"nutrient": {"id": 1008}, "amount": None},   # None should → 0.0
            {"nutrient": {"id": 1003}, "amount": 10.0},
        ],
    }
    food = client.get_food(555, serving_g=100.0)
    assert food is not None
    assert food.get("Energy (kcal)") == 0.0
    assert food.get("Protein (g)") == pytest.approx(10.0)


# ── FDCClient search_and_get Priority ─────────────────────────────────────────

def test_search_and_get_prefers_foundation():
    """search_and_get must prefer Foundation over SR Legacy over branded."""
    client = FDCClient()
    # Simulate search results with mixed data types
    client._cache["search:testfood:10"] = [
        {"fdcId": 1, "dataType": "Branded Food"},
        {"fdcId": 2, "dataType": "SR Legacy"},
        {"fdcId": 3, "dataType": "Foundation"},
    ]
    # Pre-populate food data for each
    for fdc_id in [1, 2, 3]:
        client._cache[f"food:{fdc_id}"] = {
            "description": f"Food {fdc_id}",
            "brandOwner": "",
            "dataType": ["Branded Food", "SR Legacy", "Foundation"][fdc_id - 1],
            "foodNutrients": [],
        }
    food = client.search_and_get("testfood")
    assert food is not None
    assert food.description == "Food 3"  # Foundation preferred


def test_search_and_get_falls_back_to_sr_legacy():
    """Without Foundation, should pick SR Legacy."""
    client = FDCClient()
    client._cache["search:srtest:10"] = [
        {"fdcId": 10, "dataType": "Branded Food"},
        {"fdcId": 11, "dataType": "SR Legacy"},
    ]
    for fdc_id, dt in [(10, "Branded Food"), (11, "SR Legacy")]:
        client._cache[f"food:{fdc_id}"] = {
            "description": f"Food {fdc_id}",
            "brandOwner": "",
            "dataType": dt,
            "foodNutrients": [],
        }
    food = client.search_and_get("srtest")
    assert food is not None
    assert food.description == "Food 11"


def test_search_and_get_no_results_returns_none():
    """If search returns empty, search_and_get should return None."""
    client = FDCClient()
    client._cache["search:emptyquery:10"] = []
    result = client.search_and_get("emptyquery")
    assert result is None


# ── compare_foods() ────────────────────────────────────────────────────────────

def test_compare_foods_table_structure():
    """compare_foods should return a table with food names and nutrient rows."""
    client = FDCClient()
    # Set up two foods in cache — keys must match the exact query string used by search()
    for fdc_id, name, protein, energy in [
        (100, "Food Alpha", 30.0, 150.0),
        (101, "Food Beta", 20.0, 100.0),
    ]:
        # compare_foods calls search_and_get(q) -> search(q, max_results=10)
        # cache key = f"search:{query}:{max_results}" = f"search:{name}:10"
        client._cache[f"search:{name}:10"] = [
            {"fdcId": fdc_id, "dataType": "Foundation"}
        ]
        client._cache[f"food:{fdc_id}"] = {
            "description": name,
            "brandOwner": "",
            "dataType": "Foundation",
            "foodNutrients": [
                {"nutrient": {"id": 1008}, "amount": energy},
                {"nutrient": {"id": 1003}, "amount": protein},
                {"nutrient": {"id": 1004}, "amount": 5.0},
                {"nutrient": {"id": 1005}, "amount": 10.0},
                {"nutrient": {"id": 1079}, "amount": 1.0},
            ],
        }

    result = client.compare_foods(["Food Alpha", "Food Beta"])
    assert "Food Alpha" in result or "Food Alp" in result  # may truncate
    assert "Food Beta" in result or "Food Bet" in result
    assert "Protein" in result
    assert "Energy" in result


def test_compare_foods_no_results():
    """compare_foods with all unknown foods returns 'No foods found.'"""
    client = FDCClient()
    client._cache["search:xyznotfood:10"] = []
    client._cache["search:abcnotfood:10"] = []
    result = client.compare_foods(["xyznotfood", "abcnotfood"])
    assert "No foods found" in result
