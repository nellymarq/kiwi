"""
Sports Science Calculator — Evidence-based physiological calculations.

All formulas reference peer-reviewed sources. Used for personalized context
injection into Kiwi research responses.
"""

from dataclasses import dataclass
from typing import Literal


Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
BMRMethod = Literal["mifflin", "harris_benedict", "katch_mcardle"]

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


@dataclass
class AthleteMetrics:
    """Complete computed metrics for an athlete profile."""
    bmr_mifflin: float
    bmr_harris: float
    bmr_katch: float | None
    tdee: float
    protein_target_g: float       # 1.6–2.2 g/kg (ISSN 2017 position stand)
    protein_max_g: float          # 2.2 g/kg upper practical bound
    carb_target_g: float          # 45–65% of TDEE
    fat_target_g: float           # 20–35% of TDEE
    ea_kcal_per_kg_ffm: float | None   # Energy availability (IOC 2023 RED-S threshold: 30)
    bmi: float | None
    ffm_kg: float | None          # Fat-free mass
    lean_mass_ratio: float | None

    def summary(self) -> str:
        lines = [
            f"BMR (Mifflin-St Jeor): {self.bmr_mifflin:.0f} kcal/day",
            f"BMR (Harris-Benedict): {self.bmr_harris:.0f} kcal/day",
        ]
        if self.bmr_katch is not None:
            lines.append(f"BMR (Katch-McArdle): {self.bmr_katch:.0f} kcal/day")
        lines.append(f"TDEE: {self.tdee:.0f} kcal/day")
        lines.append(f"Protein target: {self.protein_target_g:.0f}–{self.protein_max_g:.0f} g/day")
        lines.append(f"Carbohydrate target: {self.carb_target_g:.0f} g/day")
        lines.append(f"Fat target: {self.fat_target_g:.0f} g/day")
        if self.ea_kcal_per_kg_ffm is not None:
            reds_status = "⚠ Below RED-S threshold" if self.ea_kcal_per_kg_ffm < 30 else "OK"
            lines.append(f"Energy availability: {self.ea_kcal_per_kg_ffm:.1f} kcal/kg FFM/day ({reds_status})")
        if self.bmi is not None:
            lines.append(f"BMI: {self.bmi:.1f}")
        return "\n".join(lines)


class SportsCalc:
    """Evidence-based sports science calculations."""

    @staticmethod
    def bmr_mifflin(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
        """
        Mifflin-St Jeor equation (1990) — most accurate for general population.
        Mifflin MD et al. J Am Diet Assoc. 1990.
        """
        base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        return base + 5 if sex == "male" else base - 161

    @staticmethod
    def bmr_harris_benedict(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
        """
        Harris-Benedict equation (revised 1984, Roza & Shizgal).
        Roza AM, Shizgal HM. Am J Clin Nutr. 1984.
        """
        if sex == "male":
            return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    @staticmethod
    def bmr_katch_mcardle(lean_mass_kg: float) -> float:
        """
        Katch-McArdle equation — most accurate for lean athletes with known body composition.
        Katch FI, McArdle WD. Nutrition, Weight Control, and Exercise. 1977.
        """
        return 370 + (21.6 * lean_mass_kg)

    @staticmethod
    def tdee(bmr: float, activity_level: ActivityLevel) -> float:
        """Total Daily Energy Expenditure via activity multiplier (Harris & Benedict, 1919)."""
        return bmr * ACTIVITY_FACTORS[activity_level]

    @staticmethod
    def energy_availability(
        energy_intake_kcal: float,
        exercise_energy_expenditure_kcal: float,
        ffm_kg: float,
    ) -> float:
        """
        Energy Availability = (EI - EEE) / FFM
        IOC consensus 2023: RED-S threshold < 30 kcal/kg FFM/day.
        Mountjoy M et al. Br J Sports Med. 2023.
        """
        return (energy_intake_kcal - exercise_energy_expenditure_kcal) / ffm_kg

    @staticmethod
    def protein_targets(weight_kg: float, sport_type: str = "strength") -> dict[str, float]:
        """
        Evidence-based protein targets from ISSN Position Stand (Stokes et al. 2018).

        sport_type: "strength", "endurance", "mixed", "hypocaloric"
        """
        targets = {
            "strength": (1.6, 2.2),       # Morton et al. 2018 meta-analysis
            "endurance": (1.4, 1.7),       # ISSN 2009 position stand
            "mixed": (1.6, 2.0),
            "hypocaloric": (2.3, 3.1),     # Helms et al. 2014 — lean mass preservation
        }
        low, high = targets.get(sport_type, (1.6, 2.2))
        return {
            "min_g": round(low * weight_kg, 1),
            "max_g": round(high * weight_kg, 1),
            "optimal_g": round(((low + high) / 2) * weight_kg, 1),
            "per_kg_min": low,
            "per_kg_max": high,
            "evidence": "🟢 Strong (ISSN 2018 Position Stand, Morton et al. 2018 meta-analysis)",
        }

    @staticmethod
    def carbohydrate_targets(
        weight_kg: float,
        training_intensity: str = "moderate",
    ) -> dict[str, float]:
        """
        Carbohydrate targets from Burke et al. (2011) and Thomas et al. (2016).
        training_intensity: "rest", "low", "moderate", "high", "very_high"
        """
        g_per_kg = {
            "rest": (3.0, 5.0),
            "low": (3.0, 5.0),
            "moderate": (5.0, 7.0),
            "high": (6.0, 10.0),
            "very_high": (8.0, 12.0),
        }
        low_ratio, high_ratio = g_per_kg.get(training_intensity, (5.0, 7.0))
        return {
            "min_g": round(low_ratio * weight_kg, 1),
            "max_g": round(high_ratio * weight_kg, 1),
            "g_per_kg_range": f"{low_ratio}–{high_ratio}",
            "evidence": "🟢 Strong (Burke et al. 2011; Thomas et al. Nutrients 2016)",
        }

    @staticmethod
    def creatine_dosing(weight_kg: float) -> dict[str, str]:
        """
        Creatine monohydrate dosing per ISSN Position Stand (Kreider et al. 2017).
        """
        loading_daily = round(0.3 * weight_kg, 1)  # 0.3 g/kg/day for 5-7 days
        maintenance = round(0.03 * weight_kg, 1)   # 0.03 g/kg/day or 3-5g flat
        return {
            "loading_g_per_day": f"{loading_daily}g for 5–7 days (optional)",
            "maintenance_g_per_day": f"{max(3.0, maintenance):.1f}–5.0g daily",
            "timing": "Post-exercise or with meal (carbohydrate + protein co-ingestion enhances uptake)",
            "form": "Creatine monohydrate (most researched form)",
            "evidence": "🟢 Strong (ISSN 2017 Position Stand; >500 RCTs)",
        }

    @staticmethod
    def caffeine_dosing(weight_kg: float) -> dict[str, str]:
        """
        Caffeine dosing per ISSN Position Stand (Goldstein et al. 2010).
        """
        low_dose = round(3 * weight_kg, 0)
        high_dose = round(6 * weight_kg, 0)
        return {
            "dose_range_mg": f"{low_dose:.0f}–{high_dose:.0f}mg (3–6 mg/kg)",
            "timing": "45–60 min pre-exercise",
            "half_life": "~5–6 hours (significant individual variation via CYP1A2 genotype)",
            "tolerance": "Tolerance develops with habitual use; consider 10–14 day washout for peak effect",
            "evidence": "🟢 Strong (ISSN 2010 Position Stand; Grgic et al. 2019 meta-analysis)",
        }

    @staticmethod
    def compute_full_metrics(
        weight_kg: float,
        height_cm: float,
        age: int,
        sex: Sex,
        activity_level: ActivityLevel,
        body_fat_pct: float | None = None,
        energy_intake_kcal: float | None = None,
        exercise_kcal: float | None = None,
    ) -> AthleteMetrics:
        """Compute complete athlete metrics package."""
        bmr_m = SportsCalc.bmr_mifflin(weight_kg, height_cm, age, sex)
        bmr_h = SportsCalc.bmr_harris_benedict(weight_kg, height_cm, age, sex)
        tdee_val = SportsCalc.tdee(bmr_m, activity_level)

        ffm_kg = None
        bmr_k = None
        bmi = height_cm and round(weight_kg / (height_cm / 100) ** 2, 1)
        ea = None
        lean_ratio = None

        if body_fat_pct is not None and 0 < body_fat_pct < 100:
            ffm_kg = weight_kg * (1 - body_fat_pct / 100)
            bmr_k = SportsCalc.bmr_katch_mcardle(ffm_kg)
            lean_ratio = round(ffm_kg / weight_kg, 3)

            if energy_intake_kcal and exercise_kcal:
                ea = SportsCalc.energy_availability(energy_intake_kcal, exercise_kcal, ffm_kg)

        protein = SportsCalc.protein_targets(weight_kg)
        carbs = SportsCalc.carbohydrate_targets(weight_kg)

        fat_target_g = round((tdee_val * 0.25) / 9, 1)  # 25% of TDEE from fat

        return AthleteMetrics(
            bmr_mifflin=round(bmr_m, 1),
            bmr_harris=round(bmr_h, 1),
            bmr_katch=round(bmr_k, 1) if bmr_k else None,
            tdee=round(tdee_val, 1),
            protein_target_g=protein["min_g"],
            protein_max_g=protein["max_g"],
            carb_target_g=carbs["min_g"],
            fat_target_g=fat_target_g,
            ea_kcal_per_kg_ffm=round(ea, 1) if ea else None,
            bmi=bmi,
            ffm_kg=round(ffm_kg, 1) if ffm_kg else None,
            lean_mass_ratio=lean_ratio,
        )
