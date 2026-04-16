"""
Automatic Quality Assessment Heuristics — Best-guess study design and quality
flags from abstract/title alone.

Not a replacement for full RoB 2 / ROBINS-I / AMSTAR 2 assessment, but provides
rapid triage flags when evaluating many papers. Identifies likely study design,
common methodology red flags, and evidence hierarchy tier.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


StudyDesign = Literal[
    "systematic_review", "meta_analysis", "rct", "crossover_rct",
    "cohort", "case_control", "cross_sectional", "case_series",
    "animal_study", "in_vitro", "narrative_review", "unknown",
]

DESIGN_TIER = {
    "meta_analysis": "🟢",
    "systematic_review": "🟢",
    "rct": "🟢",
    "crossover_rct": "🟢",
    "cohort": "🟡",
    "case_control": "🟡",
    "cross_sectional": "🟠",
    "case_series": "🟠",
    "narrative_review": "🟠",
    "animal_study": "🔵",
    "in_vitro": "🔵",
    "unknown": "⚪",
}


@dataclass
class AutoQualityFlag:
    study_design: StudyDesign
    evidence_tier: str
    concerns: list[str]
    strengths: list[str]
    confidence: float  # 0.0-1.0 — confidence in the auto-classification

    def display(self) -> str:
        lines = [
            f"{self.evidence_tier} Auto-classified: {self.study_design.replace('_', ' ')}",
            f"   Classification confidence: {self.confidence:.0%}",
        ]
        if self.strengths:
            lines.append("   Strengths:")
            for s in self.strengths:
                lines.append(f"     + {s}")
        if self.concerns:
            lines.append("   Concerns:")
            for c in self.concerns:
                lines.append(f"     - {c}")
        return "\n".join(lines)


def _pattern_match(patterns: list[str], text: str) -> int:
    """Count how many patterns match the text (case-insensitive)."""
    t = text.lower()
    return sum(1 for p in patterns if p.lower() in t)


def classify_design(title: str, abstract: str = "", journal: str = "") -> tuple[StudyDesign, float]:
    """
    Classify study design from title + abstract + journal using keyword heuristics.
    Returns (design, confidence).
    """
    text = f"{title} {abstract} {journal}".lower()

    # Meta-analysis (strongest signal if "meta-analysis" in title)
    if "meta-analysis" in title.lower() or "meta analysis" in title.lower():
        return "meta_analysis", 0.95

    # Systematic review
    if "systematic review" in title.lower():
        return "systematic_review", 0.95
    if _pattern_match(["systematic", "prisma", "search strategy", "inclusion criteria"], text) >= 3:
        return "systematic_review", 0.75

    # RCT
    rct_patterns = [
        "randomized controlled trial", "randomised controlled trial",
        "double-blind", "double blind", "placebo-controlled",
        "placebo controlled", "randomly assigned", "randomly allocated",
    ]
    rct_score = _pattern_match(rct_patterns, text)
    if "crossover" in text and rct_score >= 2:
        return "crossover_rct", 0.90
    if rct_score >= 2:
        return "rct", 0.85
    if rct_score >= 1 and "rct" in text:
        return "rct", 0.75

    # Observational
    if _pattern_match(["prospective cohort", "longitudinal cohort", "followed for"], text) >= 1:
        return "cohort", 0.80
    if _pattern_match(["case-control", "case control"], text) >= 1:
        return "case_control", 0.85
    if _pattern_match(["cross-sectional", "cross sectional", "survey of"], text) >= 1:
        return "cross_sectional", 0.80
    if "case series" in text or "case report" in text:
        return "case_series", 0.85

    # Preclinical
    if _pattern_match(["mice", "rats", "rodent", "murine", "mouse model"], text) >= 1:
        return "animal_study", 0.90
    if _pattern_match(["in vitro", "cell culture", "cell line", "petri"], text) >= 1:
        return "in_vitro", 0.90

    # Narrative review fallback
    if "review" in title.lower() or "overview" in title.lower():
        return "narrative_review", 0.60

    return "unknown", 0.30


def detect_concerns(title: str, abstract: str = "") -> list[str]:
    """Detect common methodology concerns from title/abstract."""
    text = f"{title} {abstract}".lower()
    concerns = []

    # Small sample size indicators
    small_n_patterns = re.findall(r"n\s*=\s*(\d+)", text)
    if small_n_patterns:
        try:
            n = min(int(x) for x in small_n_patterns)
            if n < 20:
                concerns.append(f"Small sample size (n={n})")
            elif n < 50 and "rct" in text:
                concerns.append(f"Modest sample size for RCT (n={n})")
        except ValueError:
            pass

    # Short duration
    if re.search(r"\b(single dose|acute|one[- ]?off|one[- ]?time)\b", text):
        concerns.append("Acute/single-dose study — limited chronic inference")

    # Industry funding hints
    if _pattern_match(["funded by the manufacturer", "manufacturer provided", "sponsored by"], text):
        concerns.append("Potential industry funding — check conflicts of interest")

    # Open-label (no blinding)
    if "open-label" in text or "open label" in text:
        concerns.append("Open-label design — no blinding (performance/detection bias risk)")

    # No control group
    if "single-arm" in text or "single arm" in text or "uncontrolled" in text:
        concerns.append("Single-arm / uncontrolled — cannot isolate intervention effect")

    # Surrogate endpoints
    if _pattern_match(["surrogate marker", "surrogate endpoint", "biomarker only"], text):
        concerns.append("Surrogate endpoint — clinical relevance uncertain")

    # Retracted or correction indicator
    if "retraction" in text or "correction" in text:
        concerns.append("Retraction or correction noted — verify current status")

    return concerns


def detect_strengths(title: str, abstract: str = "") -> list[str]:
    """Detect methodology strengths from title/abstract."""
    text = f"{title} {abstract}".lower()
    strengths = []

    if _pattern_match(["double-blind", "double blind", "triple-blind"], text):
        strengths.append("Blinded design (reduces performance/detection bias)")

    if _pattern_match(["pre-registered", "preregistered", "clinicaltrials.gov"], text):
        strengths.append("Pre-registered protocol (reduces selective reporting)")

    # Larger sample size
    large_n = re.findall(r"n\s*=\s*(\d+)", text)
    if large_n:
        try:
            n = max(int(x) for x in large_n)
            if n >= 200:
                strengths.append(f"Large sample size (n={n})")
            elif n >= 100:
                strengths.append(f"Adequate sample size (n={n})")
        except ValueError:
            pass

    if _pattern_match(["intention-to-treat", "intention to treat", "itt analysis"], text):
        strengths.append("Intention-to-treat analysis")

    if _pattern_match(["heterogeneity assessed", "i² =", "i2 ="], text):
        strengths.append("Heterogeneity statistically assessed")

    if _pattern_match(["grade assessment", "rob 2", "cochrane risk of bias"], text):
        strengths.append("Formal quality assessment used")

    return strengths


def auto_assess(title: str, abstract: str = "", journal: str = "") -> AutoQualityFlag:
    """
    Run full automatic quality assessment on a paper.
    Returns structured flag with design classification, strengths, concerns.
    """
    design, confidence = classify_design(title, abstract, journal)
    concerns = detect_concerns(title, abstract)
    strengths = detect_strengths(title, abstract)

    return AutoQualityFlag(
        study_design=design,
        evidence_tier=DESIGN_TIER.get(design, "⚪"),
        concerns=concerns,
        strengths=strengths,
        confidence=confidence,
    )
