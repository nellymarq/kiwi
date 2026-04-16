"""Tests for effect size calculator."""

import math
import pytest
from tools.effect_size import (
    cohens_d, hedges_g, mean_difference,
    relative_risk, odds_ratio, number_needed_to_treat,
    EffectSizeResult,
)


def test_cohens_d_no_difference():
    result = cohens_d(100, 10, 30, 100, 10, 30)
    assert abs(result.estimate) < 0.01
    assert "Trivial" in result.interpretation


def test_cohens_d_medium_effect():
    # Mean difference of 5, pooled SD 10 → d = 0.5
    result = cohens_d(105, 10, 30, 100, 10, 30)
    assert 0.45 <= result.estimate <= 0.55
    assert "Small" in result.interpretation or "Medium" in result.interpretation


def test_cohens_d_large_effect():
    # Mean difference of 10, pooled SD 10 → d = 1.0
    result = cohens_d(110, 10, 30, 100, 10, 30)
    assert result.estimate > 0.9
    assert "Large" in result.interpretation


def test_cohens_d_negative():
    result = cohens_d(95, 10, 30, 100, 10, 30)
    assert result.estimate < 0


def test_hedges_g_small_sample_correction():
    # Hedges g should be smaller in magnitude than Cohen's d for small samples
    d = cohens_d(105, 10, 10, 100, 10, 10).estimate
    g = hedges_g(105, 10, 10, 100, 10, 10).estimate
    assert abs(g) < abs(d)


def test_hedges_g_converges_with_large_n():
    # Correction factor approaches 1 as n grows
    d = cohens_d(105, 10, 500, 100, 10, 500).estimate
    g = hedges_g(105, 10, 500, 100, 10, 500).estimate
    assert abs(d - g) < 0.001


def test_mean_difference():
    result = mean_difference(105, 10, 30, 100, 10, 30)
    assert result.estimate == 5.0
    # CI should include positive values
    assert result.ci_lower < result.ci_upper


def test_mean_difference_no_effect():
    result = mean_difference(100, 10, 30, 100, 10, 30)
    assert abs(result.estimate) < 0.01


def test_relative_risk_protective():
    # 10 of 100 vs 20 of 100 → RR = 0.5 (protective)
    result = relative_risk(10, 100, 20, 100)
    assert 0.45 <= result.estimate <= 0.55
    assert "reduces" in result.interpretation


def test_relative_risk_harmful():
    # 20 of 100 vs 10 of 100 → RR = 2.0
    result = relative_risk(20, 100, 10, 100)
    assert 1.9 <= result.estimate <= 2.1
    assert "increases" in result.interpretation


def test_relative_risk_zero_cell():
    result = relative_risk(0, 100, 10, 100)
    # Haldane correction should prevent division errors
    assert result.estimate > 0
    assert result.estimate < 1


def test_odds_ratio():
    # 10/90 vs 20/80 → OR ~ 0.44
    result = odds_ratio(10, 100, 20, 100)
    assert 0.40 <= result.estimate <= 0.50


def test_odds_ratio_no_effect():
    result = odds_ratio(10, 100, 10, 100)
    assert abs(result.estimate - 1.0) < 0.01


def test_nnt_protective():
    # Treatment: 10%; Control: 20% → ARR 0.10, NNT = 10
    result = number_needed_to_treat(10, 100, 20, 100)
    assert abs(result["arr"] - 0.10) < 0.01
    assert 9 <= result["nnt_or_nnh"] <= 11
    assert "prevent" in result["interpretation"]


def test_nnt_harmful():
    # Treatment: 20%; Control: 10% → NNH = 10
    result = number_needed_to_treat(20, 100, 10, 100)
    assert "extra event" in result["interpretation"] or "NNH" in result["interpretation"]


def test_nnt_no_effect():
    result = number_needed_to_treat(10, 100, 10, 100)
    assert "No difference" in result["interpretation"]


def test_result_display():
    result = cohens_d(105, 10, 30, 100, 10, 30)
    display = result.display()
    assert "Cohen's d" in display
    assert "95% CI" in display
