"""
Biomarker Interpreter — athlete blood panel analysis.

Interprets common blood test values in the context of athletic performance,
overtraining, nutritional deficiencies, and hormonal health.

Reference ranges sourced from:
  - Quest Diagnostics / LabCorp standard ranges
  - IOC Medical Commission athlete-specific adjustments
  - Hackney 2020 — Exercise Endocrinology (🟢)
  - Cadegiani & Kater 2017 — HPA axis in overtrained athletes (🟡)
  - Peeling et al. 2014 — Iron biomarkers in athletes (🟢)

Status codes: LOW / NORMAL / HIGH / ATHLETIC_LOW / ATHLETIC_NORM
  ATHLETIC_LOW = low in standard range but may be clinically relevant for athletes
  ATHLETIC_NORM = outside standard range but common/expected in high performers
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Status = Literal["LOW", "NORMAL", "HIGH", "ATHLETIC_LOW", "ATHLETIC_NORM", "CRITICAL_LOW", "CRITICAL_HIGH"]

STATUS_EMOJI = {
    "LOW": "🔵",
    "ATHLETIC_LOW": "🟡",
    "NORMAL": "✅",
    "ATHLETIC_NORM": "🟢",
    "HIGH": "🟠",
    "CRITICAL_LOW": "🚨",
    "CRITICAL_HIGH": "🚨",
}

IMPORTANCE = {
    "CRITICAL_LOW": 0,
    "CRITICAL_HIGH": 1,
    "LOW": 2,
    "HIGH": 3,
    "ATHLETIC_LOW": 4,
    "NORMAL": 5,
    "ATHLETIC_NORM": 6,
}


@dataclass
class BiomarkerRef:
    """Reference range and interpretation for a single biomarker."""
    name: str
    unit: str
    low: float
    high: float
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    athletic_low_adj: Optional[float] = None   # Athletes often run lower — below this is truly low
    athletic_high_adj: Optional[float] = None  # Athletes often run higher — above ref.high but ≤ this is ATHLETIC_NORM
    athlete_note: str = ""
    performance_impact: str = ""
    action_if_low: str = ""
    action_if_high: str = ""
    evidence: str = ""


@dataclass
class BiomarkerResult:
    """Interpreted result for a single test value."""
    name: str
    value: float
    unit: str
    status: Status
    ref: BiomarkerRef
    flag: str = ""
    recommendation: str = ""

    def display(self) -> str:
        emoji = STATUS_EMOJI[self.status]
        lines = [
            f"{emoji} {self.name}: {self.value} {self.unit}  [{self.status}]",
        ]
        if self.flag:
            lines.append(f"   ⚠  {self.flag}")
        if self.recommendation:
            lines.append(f"   →  {self.recommendation}")
        if self.ref.performance_impact:
            lines.append(f"   📊 Performance: {self.ref.performance_impact}")
        return "\n".join(lines)


# ── Reference Database ────────────────────────────────────────────────────────

BIOMARKER_DB: dict[str, BiomarkerRef] = {

    # ── Iron Status Panel ───────────────────────────────────────────────────
    "ferritin": BiomarkerRef(
        name="Ferritin",
        unit="ng/mL",
        low=12.0, high=300.0,
        critical_low=5.0,
        athletic_low_adj=30.0,
        athlete_note="Athletes should target >30 ng/mL; endurance athletes >50 ng/mL for optimal performance.",
        performance_impact="Iron deficiency impairs VO2max, endurance capacity, and fatigue resistance.",
        action_if_low="Iron supplementation 25–150mg elemental iron/day with vitamin C. Identify dietary causes.",
        action_if_high="Rule out hemochromatosis, chronic inflammation. Elevated CRP can falsely elevate ferritin.",
        evidence="Peeling et al. 2014 Am J Clin Nutr 🟢",
    ),
    "hemoglobin": BiomarkerRef(
        name="Hemoglobin",
        unit="g/dL",
        low=12.0, high=17.5,
        critical_low=7.0,
        athletic_low_adj=13.5,
        athletic_high_adj=18.5,
        athlete_note="Endurance athletes may have dilutional pseudoanemia (plasma expansion). Interpret with hematocrit.",
        performance_impact="Hemoglobin directly limits oxygen transport and VO2max.",
        action_if_low="Iron-deficiency anemia vs. dilutional: check ferritin + MCV. Altitude exposure may help.",
        action_if_high="Possible dehydration or EPO use. Hgb > 17 is WADA flag.",
        evidence="Malczewska-Lenczowska et al. 2016 IJSPP 🟡",
    ),
    "transferrin_saturation": BiomarkerRef(
        name="Transferrin Saturation",
        unit="%",
        low=15.0, high=50.0,
        critical_low=10.0,
        athlete_note="< 16% indicates functional iron deficiency even with normal ferritin.",
        performance_impact="Low transferrin saturation → impaired erythropoiesis → reduced oxygen carrying capacity.",
        action_if_low="Consider IV iron if oral unresponsive. Hepcidin assay useful.",
        action_if_high="Hemochromatosis screen. Cease iron supplementation.",
        evidence="Peeling et al. 2014 🟢",
    ),

    # ── Hormonal Panel ─────────────────────────────────────────────────────
    "testosterone_male": BiomarkerRef(
        name="Testosterone (Male)",
        unit="ng/dL",
        low=270.0, high=1070.0,
        critical_low=100.0,
        athletic_low_adj=400.0,
        athlete_note="Athletic performance impaired below 400 ng/dL. Relative Energy Deficiency (RED-S) key risk.",
        performance_impact="Testosterone drives muscle protein synthesis, recovery, bone density, motivation.",
        action_if_low="Rule out RED-S (energy availability <30 kcal/kg FFM). Check LH/FSH/prolactin. Sleep quality.",
        action_if_high="Rule out exogenous testosterone. Check hematocrit for polycythemia.",
        evidence="Hackney 2020 Endocrinology 🟢",
    ),
    "testosterone_female": BiomarkerRef(
        name="Testosterone (Female)",
        unit="ng/dL",
        low=15.0, high=70.0,
        critical_low=5.0,
        athlete_note="Female athletes often run mid-range. High (>70) with RED-S in some athletes.",
        performance_impact="Testosterone in females supports power, muscle mass, and recovery.",
        action_if_low="Low energy availability. Check estradiol and LH/FSH.",
        action_if_high="Polycystic ovary syndrome (PCOS), CAH. Rule out exogenous androgen use.",
        evidence="Hackney 2020 Endocrinology 🟢",
    ),
    "cortisol_morning": BiomarkerRef(
        name="Cortisol (Morning, 8am)",
        unit="mcg/dL",
        low=6.0, high=23.0,
        critical_low=2.0,
        critical_high=50.0,
        athletic_low_adj=10.0,
        athlete_note="Chronically low cortisol (<10) in athletes suggests HPA suppression / OTS.",
        performance_impact="Cortisol: protein catabolism, anti-inflammatory, energy mobilization.",
        action_if_low="OTS or secondary adrenal insufficiency. Consider ACTH stim test.",
        action_if_high="Overtraining, Cushing syndrome, psychological stress. Monitor with training load.",
        evidence="Cadegiani & Kater 2017 BMC Sports Sci 🟡",
    ),
    "testosterone_cortisol_ratio": BiomarkerRef(
        name="Testosterone:Cortisol Ratio",
        unit="ng/dL per mcg/dL",
        low=5.0, high=1000.0,
        critical_low=2.0,
        athlete_note=">30% decrease from baseline = overreaching marker. Calculate as T(ng/dL)/C(mcg/dL).",
        performance_impact="T:C ratio is the most sensitive hormonal marker for overtraining syndrome.",
        action_if_low="Reduce training volume immediately. 10–14 day deload. Optimize sleep and nutrition.",
        action_if_high="",
        evidence="Adlercreutz et al. 1986 IJSM 🟡",
    ),
    "igf1": BiomarkerRef(
        name="IGF-1",
        unit="ng/mL",
        low=88.0, high=246.0,
        athlete_note="GH/IGF-1 axis is anabolic; can be elevated with resistance training.",
        performance_impact="IGF-1 mediates GH anabolic effects on muscle, bone, and cartilage.",
        action_if_low="Poor sleep (GH pulsatile at night), high training stress, low carbohydrate intake.",
        action_if_high="Acromegaly (rare). IGF-1 >400 warrants endocrinology referral.",
        evidence="Nindl & Pierce 2010 Sports Med 🟡",
    ),

    # ── Metabolic Panel ────────────────────────────────────────────────────
    "glucose_fasting": BiomarkerRef(
        name="Fasting Glucose",
        unit="mg/dL",
        low=70.0, high=99.0,
        critical_low=55.0,
        critical_high=400.0,
        athlete_note="Athletes tend toward lower fasting glucose. Post-exercise may be transiently elevated.",
        performance_impact="Glucose is primary fuel for high-intensity exercise; ketosis can impair glycolytic performance.",
        action_if_low="Hypoglycemia — immediate carbohydrate. If fasting: rule out insulin excess.",
        action_if_high="Pre-diabetes threshold at 100–125. Impaired insulin sensitivity → impaired glycogen resynthesis.",
        evidence="ADA Standards of Medical Care 2024 🟢",
    ),
    "hba1c": BiomarkerRef(
        name="HbA1c",
        unit="%",
        low=4.0, high=5.6,
        critical_high=10.0,
        athlete_note="Athletes: HbA1c may run slightly lower due to faster red cell turnover.",
        performance_impact="Glycemic control directly affects aerobic metabolism, recovery, inflammation.",
        action_if_low="Possible accelerated RBC turnover or frequent hypoglycemia.",
        action_if_high="Pre-diabetes (5.7–6.4%), type 2 DM (≥6.5%). Dietary and lifestyle intervention.",
        evidence="ADA 2024 🟢",
    ),

    # ── Thyroid Panel ──────────────────────────────────────────────────────
    "tsh": BiomarkerRef(
        name="TSH",
        unit="mIU/L",
        low=0.4, high=4.0,
        critical_high=10.0,
        athletic_low_adj=0.5,
        athlete_note="Endurance athletes may have slightly suppressed TSH from training-induced T3 elevations.",
        performance_impact="Hypothyroidism → fatigue, reduced VO2max, cold intolerance, weight gain.",
        action_if_low="Possible hyperthyroidism or over-replacement if on levothyroxine. Check free T4/T3.",
        action_if_high="Subclinical (1–10): monitor, optimize iodine/selenium intake.",
        evidence="Dunn 2008 Clinics 🟡",
    ),
    "free_t3": BiomarkerRef(
        name="Free T3",
        unit="pg/mL",
        low=2.3, high=4.2,
        athletic_low_adj=2.8,
        athlete_note="T3 is the active thyroid hormone. Low T3 syndrome common in RED-S and severe caloric restriction.",
        performance_impact="T3 regulates metabolic rate, mitochondrial biogenesis, and substrate oxidation.",
        action_if_low="Euthyroid sick syndrome from energy restriction. Increase caloric intake.",
        action_if_high="Hyperthyroidism. Rule out T3 supplementation.",
        evidence="De Souza et al. 2003 Metabolism 🟡",
    ),

    # ── Kidney / Liver ─────────────────────────────────────────────────────
    "creatinine": BiomarkerRef(
        name="Creatinine",
        unit="mg/dL",
        low=0.6, high=1.2,
        critical_high=10.0,
        athletic_low_adj=0.8,
        athletic_high_adj=1.4,
        athlete_note="Athletes with high muscle mass often have creatinine 1.0–1.4 — not necessarily kidney disease.",
        performance_impact="Elevated post-exercise creatinine is normal (exercise-induced). Monitor trends.",
        action_if_low="Low muscle mass, possible malnutrition.",
        action_if_high="If persistent >2.0: nephrology referral. eGFR more sensitive.",
        evidence="Clarkson et al. 2006 MSSE 🟡",
    ),
    "alt": BiomarkerRef(
        name="ALT",
        unit="U/L",
        low=7.0, high=56.0,
        critical_high=500.0,
        athletic_high_adj=168.0,  # Up to 3× upper limit is expected post-DOMS
        athlete_note="Can be transiently elevated 2–3× after intense resistance training (from muscle damage, not liver).",
        performance_impact="Elevated ALT post-exercise: DOMS marker, not liver disease in athletes.",
        action_if_low="",
        action_if_high="If persistent >3× upper limit: hepatology referral. Rule out fatty liver (NAFLD).",
        evidence="Totsuka et al. 2002 J Sports Med Phys Fitness 🟠",
    ),

    # ── Inflammation & Recovery ────────────────────────────────────────────
    "crp": BiomarkerRef(
        name="hsCRP",
        unit="mg/L",
        low=0.0, high=1.0,
        critical_high=10.0,
        athlete_note="Acutely elevated post-hard training (up to 5 mg/L). Chronic > 3 mg/L = systemic inflammation.",
        performance_impact="Chronic inflammation impairs recovery, anabolic signaling, and immune function.",
        action_if_low="",
        action_if_high="Optimize sleep, reduce training monotony, anti-inflammatory diet (omega-3, polyphenols).",
        evidence="Kasapis & Thompson 2005 J Am Coll Cardiol 🟡",
    ),
    "vitamin_d": BiomarkerRef(
        name="25-OH Vitamin D",
        unit="ng/mL",
        low=30.0, high=80.0,
        critical_low=10.0,
        athletic_low_adj=40.0,
        athlete_note="Athletes should target 40–60 ng/mL for optimal immune function and bone density.",
        performance_impact="Vitamin D deficiency → reduced muscle power, higher injury risk, impaired immunity.",
        action_if_low="2000–4000 IU vitamin D3/day + K2 (MK-7) 100–200mcg. Retest in 3 months.",
        action_if_high="Toxicity rare but > 100 ng/mL: cease supplementation.",
        evidence="Larson-Meyer & Willis 2010 Sports Health 🟢",
    ),
    "magnesium": BiomarkerRef(
        name="Serum Magnesium",
        unit="mg/dL",
        low=1.7, high=2.2,
        critical_low=1.0,
        critical_high=4.5,
        athlete_note="Serum Mg poorly reflects total body Mg. Athletes can be deficient with 'normal' serum levels.",
        performance_impact="Magnesium cofactor for 300+ enzymes. Deficiency → cramps, poor sleep, reduced power.",
        action_if_low="Magnesium glycinate or malate 200–400mg/day. Avoid oxide form (poor absorption).",
        action_if_high="Excess supplementation or kidney disease.",
        evidence="Zhang et al. 2017 Nutrients 🟡",
    ),
}

# Aliases for common naming variants
_ALIASES = {
    "serum ferritin": "ferritin",
    "ferritin serum": "ferritin",
    "hgb": "hemoglobin",
    "hb": "hemoglobin",
    "tsat": "transferrin_saturation",
    "t sat": "transferrin_saturation",
    "testosterone": "testosterone_male",
    "total testosterone": "testosterone_male",
    "cortisol": "cortisol_morning",
    "morning cortisol": "cortisol_morning",
    "fasting glucose": "glucose_fasting",
    "glucose": "glucose_fasting",
    "igf-1": "igf1",
    "free t3": "free_t3",
    "ft3": "free_t3",
    "25-oh vitamin d": "vitamin_d",
    "vitamin d": "vitamin_d",
    "vit d": "vitamin_d",
    "crp": "crp",
    "hscrp": "crp",
    "hs-crp": "crp",
    "magnesium serum": "magnesium",
    "mg": "magnesium",
    "alt sgpt": "alt",
}


# ── Interpreter ───────────────────────────────────────────────────────────────

class BiomarkerInterpreter:
    """
    Interprets a blood panel in the context of athletic performance.
    Applies athlete-specific reference ranges where available.
    """

    def interpret(self, name: str, value: float, sex: str = "male") -> Optional[BiomarkerResult]:
        """
        Interpret a single biomarker value.
        sex: "male" or "female" (affects testosterone reference selection)
        """
        key = name.lower().strip()
        key = _ALIASES.get(key, key)

        # Sex-specific testosterone
        if key == "testosterone_male" and sex == "female":
            key = "testosterone_female"
        elif key == "testosterone_female" and sex == "male":
            key = "testosterone_male"

        ref = BIOMARKER_DB.get(key)
        if not ref:
            return None

        status = self._classify(value, ref)
        flag, recommendation = self._advise(value, status, ref)

        return BiomarkerResult(
            name=ref.name,
            value=value,
            unit=ref.unit,
            status=status,
            ref=ref,
            flag=flag,
            recommendation=recommendation,
        )

    def _classify(self, value: float, ref: BiomarkerRef) -> Status:
        if ref.critical_low and value <= ref.critical_low:
            return "CRITICAL_LOW"
        if ref.critical_high and value >= ref.critical_high:
            return "CRITICAL_HIGH"
        if value < ref.low:
            if ref.athletic_low_adj and value >= ref.athletic_low_adj:
                return "ATHLETIC_LOW"
            return "LOW"
        if value > ref.high:
            if ref.athletic_high_adj and value <= ref.athletic_high_adj:
                return "ATHLETIC_NORM"
            return "HIGH"
        return "NORMAL"

    def _advise(self, value: float, status: Status, ref: BiomarkerRef) -> tuple[str, str]:
        flag = ""
        recommendation = ""

        if status in ("CRITICAL_LOW", "CRITICAL_HIGH"):
            flag = "Seek immediate medical evaluation."
            recommendation = ref.action_if_low if status == "CRITICAL_LOW" else ref.action_if_high

        elif status == "LOW":
            flag = ref.athlete_note if ref.athlete_note else f"Below normal range ({ref.low} {ref.unit})"
            recommendation = ref.action_if_low

        elif status == "ATHLETIC_LOW":
            flag = f"Below standard but may be within athletic norm. {ref.athlete_note}"
            recommendation = ref.action_if_low

        elif status == "HIGH":
            flag = ref.athlete_note if ref.athlete_note and "high" in ref.athlete_note.lower() else (
                f"Above normal range ({ref.high} {ref.unit})"
            )
            recommendation = ref.action_if_high

        return flag, recommendation

    def interpret_panel(
        self,
        results: dict[str, float],
        sex: str = "male",
    ) -> list[BiomarkerResult]:
        """
        Interpret a full panel dict {biomarker_name: value}.
        Returns sorted by importance (critical first).
        """
        interpreted = []
        for name, value in results.items():
            result = self.interpret(name, value, sex=sex)
            if result:
                interpreted.append(result)

        return sorted(interpreted, key=lambda r: IMPORTANCE.get(r.status, 5))

    def format_panel_report(
        self,
        results: dict[str, float],
        sex: str = "male",
        athlete_name: str = "",
    ) -> str:
        """Generate a full formatted blood panel report."""
        interpreted = self.interpret_panel(results, sex=sex)

        lines = [
            f"Blood Panel Analysis{f' — {athlete_name}' if athlete_name else ''}",
            f"Sex: {sex.title()}  |  {len(interpreted)} markers interpreted",
            "=" * 60,
        ]

        if not interpreted:
            lines.append("\nNo recognizable biomarkers found in panel.")
            return "\n".join(lines)

        by_status: dict[str, list] = {}
        for r in interpreted:
            by_status.setdefault(r.status, []).append(r)

        for status in ["CRITICAL_LOW", "CRITICAL_HIGH", "LOW", "HIGH", "ATHLETIC_LOW", "NORMAL"]:
            group = by_status.get(status, [])
            if not group:
                continue
            emoji = STATUS_EMOJI[status]
            lines.append(f"\n{emoji} {status.replace('_', ' ')} ({len(group)})")
            lines.append("-" * 40)
            for r in group:
                lines.append(r.display())

        # Summary flags
        critical = [r for r in interpreted if r.status in ("CRITICAL_LOW", "CRITICAL_HIGH")]
        low = [r for r in interpreted if r.status == "LOW"]
        if critical:
            lines.append(f"\n🚨 {len(critical)} CRITICAL value(s) — immediate medical attention required.")
        if low:
            lines.append(f"\n⚠️  {len(low)} LOW value(s) — review with healthcare provider.")

        return "\n".join(lines)


# Module-level convenience instance
interpreter = BiomarkerInterpreter()


def interpret_panel(results: dict[str, float], sex: str = "male", athlete_name: str = "") -> str:
    """Convenience function: interpret a full panel and return formatted report."""
    return interpreter.format_panel_report(results, sex=sex, athlete_name=athlete_name)
