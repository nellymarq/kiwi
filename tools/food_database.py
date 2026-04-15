"""
USDA FoodData Central API integration.

API: https://api.nal.usda.gov/fdc/v1/
Key: DEMO_KEY (limited to 30 req/hour, 50 req/day) or personal key via env var
Documentation: https://fdc.nal.usda.gov/api-guide.html

Provides:
- Food search by name
- Full nutrient breakdown per 100g / custom portion
- Foundation Foods, Survey (FNDDS), and SR Legacy databases
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

FDC_BASE = "https://api.nal.usda.gov/fdc/v1"
FDC_API_KEY = os.getenv("FDC_API_KEY", "DEMO_KEY")

# Key nutrient IDs (FDC nutrient IDs — stable across databases)
NUTRIENT_IDS = {
    1008: "Energy (kcal)",
    1003: "Protein (g)",
    1004: "Total Fat (g)",
    1005: "Total Carbs (g)",
    1079: "Dietary Fiber (g)",
    2000: "Total Sugars (g)",
    1087: "Calcium (mg)",
    1089: "Iron (mg)",
    1090: "Magnesium (mg)",
    1091: "Phosphorus (mg)",
    1092: "Potassium (mg)",
    1093: "Sodium (mg)",
    1095: "Zinc (mg)",
    1175: "Vitamin B6 (mg)",
    1177: "Folate (mcg DFE)",
    1178: "Vitamin B12 (mcg)",
    1162: "Vitamin C (mg)",
    1114: "Vitamin D (IU)",
    1109: "Vitamin E (mg)",
    1185: "Vitamin K (mcg)",
    1292: "Monounsaturated Fat (g)",
    1293: "Polyunsaturated Fat (g)",
    1258: "Saturated Fat (g)",
    1096: "Selenium (mcg)",
    1100: "Iodine (mcg)",
}

# Amino acid IDs
AMINO_ACID_IDS = {
    1210: "Tryptophan (g)",
    1211: "Threonine (g)",
    1212: "Isoleucine (g)",
    1213: "Leucine (g)",
    1214: "Lysine (g)",
    1215: "Methionine (g)",
    1216: "Cysteine (g)",
    1217: "Phenylalanine (g)",
    1218: "Tyrosine (g)",
    1219: "Valine (g)",
    1220: "Arginine (g)",
    1221: "Histidine (g)",
    1222: "Alanine (g)",
    1223: "Aspartic Acid (g)",
    1224: "Glutamic Acid (g)",
    1226: "Glycine (g)",
    1227: "Proline (g)",
    1228: "Serine (g)",
}


@dataclass
class FoodNutrients:
    fdc_id: int
    description: str
    brand: str
    data_type: str
    serving_size_g: float = 100.0
    nutrients: dict[str, float] = field(default_factory=dict)  # name → value
    amino_acids: dict[str, float] = field(default_factory=dict)

    def get(self, nutrient_name: str, default: float = 0.0) -> float:
        """Get nutrient value (per 100g unless scaled)."""
        return self.nutrients.get(nutrient_name, default)

    def scale_to(self, grams: float) -> "FoodNutrients":
        """Return a copy with nutrients scaled to a custom serving size."""
        factor = grams / 100.0
        scaled_nutrients = {k: round(v * factor, 3) for k, v in self.nutrients.items()}
        scaled_aa = {k: round(v * factor, 3) for k, v in self.amino_acids.items()}
        return FoodNutrients(
            fdc_id=self.fdc_id,
            description=self.description,
            brand=self.brand,
            data_type=self.data_type,
            serving_size_g=grams,
            nutrients=scaled_nutrients,
            amino_acids=scaled_aa,
        )

    def macro_summary(self) -> str:
        n = self.nutrients
        return (
            f"Per {self.serving_size_g:.0f}g: "
            f"{n.get('Energy (kcal)', 0):.0f} kcal | "
            f"{n.get('Protein (g)', 0):.1f}g protein | "
            f"{n.get('Total Carbs (g)', 0):.1f}g carbs | "
            f"{n.get('Total Fat (g)', 0):.1f}g fat | "
            f"{n.get('Dietary Fiber (g)', 0):.1f}g fiber"
        )

    def full_report(self, include_aminos: bool = False) -> str:
        lines = [
            f"## {self.description}",
            f"   FDC ID: {self.fdc_id}  |  Type: {self.data_type}",
            f"   {self.brand or 'Foundation Food'}",
            "",
            "### Macros & Energy",
            self.macro_summary(),
            "",
            "### Micronutrients",
        ]
        micro_keys = [k for k in self.nutrients if k not in {
            "Energy (kcal)", "Protein (g)", "Total Fat (g)", "Total Carbs (g)",
            "Dietary Fiber (g)", "Total Sugars (g)",
            "Saturated Fat (g)", "Monounsaturated Fat (g)", "Polyunsaturated Fat (g)",
        }]
        for k in sorted(micro_keys):
            v = self.nutrients[k]
            if v > 0:
                lines.append(f"   {k}: {v:.2f}")

        if include_aminos and self.amino_acids:
            lines += ["", "### Amino Acid Profile"]
            for aa, val in sorted(self.amino_acids.items()):
                if val > 0:
                    lines.append(f"   {aa}: {val:.3f}g")

        return "\n".join(lines)


class FDCClient:
    """USDA FoodData Central API client with bounded LRU cache and rate limiting."""

    MAX_CACHE_SIZE = 200

    def __init__(self, api_key: str = FDC_API_KEY):
        self.api_key = api_key
        self._cache: dict[str, tuple[float, any]] = {}
        self._last_request = 0.0
        self._min_interval = 0.5

    def _cache_get(self, key: str):
        entry = self._cache.get(key)
        return entry[1] if entry else None

    def _cache_set(self, key: str, value):
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), value)

    def _throttle(self):
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def search(
        self,
        query: str,
        max_results: int = 5,
        data_types: list[str] | None = None,
    ) -> list[dict]:
        """
        Search for foods by name.
        data_types: ["Foundation", "SR Legacy", "Survey (FNDDS)", "Branded Food"]
        Returns raw search result items.
        """
        cache_key = f"search:{query}:{max_results}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        self._throttle()
        params: dict = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": max_results,
        }
        if data_types:
            params["dataType"] = ",".join(data_types)

        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(f"{FDC_BASE}/foods/search", params=params)
                response.raise_for_status()
                data = response.json()
                items = data.get("foods", [])
                self._cache_set(cache_key, items)
                return items
        except httpx.TimeoutException:
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                time.sleep(2)
            return []
        except httpx.HTTPError:
            return []

    def get_food(
        self,
        fdc_id: int,
        serving_g: float = 100.0,
        include_aminos: bool = False,
    ) -> Optional[FoodNutrients]:
        """
        Fetch full nutrient data for a specific FDC ID.
        Returns FoodNutrients scaled to serving_g (default 100g).
        """
        cache_key = f"food:{fdc_id}"
        raw = self._cache_get(cache_key)

        if not raw:
            self._throttle()
            try:
                with httpx.Client(timeout=15) as client:
                    response = client.get(
                        f"{FDC_BASE}/food/{fdc_id}",
                        params={"api_key": self.api_key},
                    )
                    response.raise_for_status()
                    raw = response.json()
                    self._cache_set(cache_key, raw)
            except httpx.TimeoutException:
                return None
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    time.sleep(2)
                return None
            except httpx.HTTPError:
                return None

        nutrients: dict[str, float] = {}
        amino_acids: dict[str, float] = {}

        for nutrient in raw.get("foodNutrients", []):
            n_id = nutrient.get("nutrient", {}).get("id")
            value = nutrient.get("amount", 0.0) or 0.0

            if n_id in NUTRIENT_IDS:
                nutrients[NUTRIENT_IDS[n_id]] = round(float(value), 4)
            elif include_aminos and n_id in AMINO_ACID_IDS:
                amino_acids[AMINO_ACID_IDS[n_id]] = round(float(value), 4)

        food = FoodNutrients(
            fdc_id=fdc_id,
            description=raw.get("description", "Unknown"),
            brand=raw.get("brandOwner", "") or raw.get("brandName", ""),
            data_type=raw.get("dataType", ""),
            serving_size_g=100.0,
            nutrients=nutrients,
            amino_acids=amino_acids,
        )

        return food.scale_to(serving_g) if serving_g != 100.0 else food

    def search_and_get(
        self,
        query: str,
        serving_g: float = 100.0,
        include_aminos: bool = False,
        data_types: list[str] | None = None,
    ) -> Optional[FoodNutrients]:
        """
        Convenience: search and return full nutrient data for the top result.
        Prefers Foundation Foods > SR Legacy > Survey > Branded.
        """
        results = self.search(query, max_results=10, data_types=data_types)
        if not results:
            return None

        # Prefer Foundation Food data type
        priority_order = ["Foundation", "SR Legacy", "Survey (FNDDS)"]
        for ptype in priority_order:
            for r in results:
                if r.get("dataType") == ptype:
                    return self.get_food(r["fdcId"], serving_g, include_aminos)

        # Fall back to first result
        return self.get_food(results[0]["fdcId"], serving_g, include_aminos)

    def compare_foods(
        self,
        queries: list[str],
        serving_g: float = 100.0,
        nutrient_keys: list[str] | None = None,
    ) -> str:
        """Compare multiple foods side-by-side for specified nutrients."""
        default_keys = ["Energy (kcal)", "Protein (g)", "Total Carbs (g)", "Total Fat (g)", "Dietary Fiber (g)"]
        keys = nutrient_keys or default_keys

        foods = []
        for q in queries:
            food = self.search_and_get(q, serving_g)
            if food:
                foods.append(food)

        if not foods:
            return "No foods found."

        # Header
        header = f"{'Nutrient':<30}" + "".join(f"{f.description[:18]:<20}" for f in foods)
        lines = [f"Food Comparison (per {serving_g:.0f}g)", header, "-" * (30 + 20 * len(foods))]

        for key in keys:
            row = f"{key:<30}"
            for food in foods:
                val = food.nutrients.get(key, 0)
                row += f"{val:<20.2f}"
            lines.append(row)

        return "\n".join(lines)
