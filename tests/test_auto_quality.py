"""Tests for automatic quality assessment heuristics."""

import pytest
from tools.auto_quality import (
    classify_design, detect_concerns, detect_strengths, auto_assess,
    AutoQualityFlag, DESIGN_TIER,
)


def test_classify_meta_analysis():
    design, conf = classify_design(
        "A Meta-Analysis of Creatine Supplementation in Strength Athletes",
        "This meta-analysis examined 50 RCTs...",
    )
    assert design == "meta_analysis"
    assert conf >= 0.9


def test_classify_systematic_review():
    design, conf = classify_design(
        "Systematic Review of Vitamin D and Athletic Performance",
        "PRISMA methodology was used...",
    )
    assert design == "systematic_review"


def test_classify_rct():
    design, conf = classify_design(
        "Effects of Beta-Alanine on 800m Performance",
        "Thirty athletes were randomly assigned in a double-blind, placebo-controlled trial.",
    )
    assert design == "rct"


def test_classify_crossover():
    design, conf = classify_design(
        "Caffeine and Endurance Performance",
        "This randomized, double-blind, placebo-controlled crossover study examined...",
    )
    assert design == "crossover_rct"


def test_classify_cohort():
    design, conf = classify_design(
        "Iron Status in Elite Runners",
        "In this prospective cohort study, 200 athletes were followed for 24 months.",
    )
    assert design == "cohort"


def test_classify_animal():
    design, conf = classify_design(
        "Curcumin Reduces Muscle Inflammation in Mice",
        "Male C57BL/6 mice were treated with curcumin after downhill running.",
    )
    assert design == "animal_study"


def test_classify_in_vitro():
    design, conf = classify_design(
        "Quercetin Modulates NF-kB in Cell Culture",
        "Human macrophage cell line was treated...",
    )
    assert design == "in_vitro"


def test_classify_unknown():
    design, conf = classify_design("A paper about something", "")
    assert design in ("unknown", "narrative_review")


def test_detect_small_sample():
    concerns = detect_concerns(
        "Small RCT of supplement X",
        "Fifteen participants (n=15) were randomized...",
    )
    assert any("Small sample" in c for c in concerns)


def test_detect_large_sample_strength():
    strengths = detect_strengths(
        "Large RCT",
        "Two hundred and fifty athletes (n=250) were randomized...",
    )
    assert any("Large sample" in s for s in strengths)


def test_detect_blinding_strength():
    strengths = detect_strengths(
        "Blinded RCT",
        "This double-blind study...",
    )
    assert any("Blinded" in s for s in strengths)


def test_detect_open_label_concern():
    concerns = detect_concerns(
        "Open-label study of intervention X",
        "This open-label trial...",
    )
    assert any("Open-label" in c for c in concerns)


def test_detect_industry_funding():
    concerns = detect_concerns(
        "Sports drink study",
        "This study was funded by the manufacturer of Product X.",
    )
    assert any("industry" in c.lower() or "funding" in c.lower() for c in concerns)


def test_auto_assess_full():
    flag = auto_assess(
        title="A Meta-Analysis of Creatine in Strength Athletes",
        abstract="This systematic review and meta-analysis of 30 RCTs (n=850) used GRADE assessment.",
    )
    assert flag.study_design == "meta_analysis"
    assert flag.evidence_tier == "🟢"
    assert flag.confidence >= 0.9
    assert len(flag.strengths) > 0


def test_auto_assess_weak_study():
    flag = auto_assess(
        title="Case Report: Creatine Use in One Athlete",
        abstract="We report a single open-label case of one athlete using creatine (n=1).",
    )
    assert flag.study_design in ("case_series", "unknown")
    assert len(flag.concerns) > 0


def test_display_format():
    flag = AutoQualityFlag(
        study_design="rct",
        evidence_tier="🟢",
        concerns=["Modest sample size"],
        strengths=["Double-blind design", "ITT analysis"],
        confidence=0.85,
    )
    output = flag.display()
    assert "rct" in output.lower()
    assert "85%" in output
    assert "Double-blind" in output
    assert "Modest sample" in output


def test_design_tier_coverage():
    # Every design type should have a tier emoji
    from tools.auto_quality import classify_design
    for design_key in DESIGN_TIER:
        assert DESIGN_TIER[design_key] in ("🟢", "🟡", "🟠", "🔵", "⚪")
