"""
Effect Size Calculator — Standardized effect sizes for research synthesis.

Converts raw study data (means, SDs, sample sizes, event counts) into
standardized effect sizes used in meta-analysis and clinical interpretation:

- Cohen's d / Hedges' g — standardized mean difference
- Mean difference (MD) — for continuous outcomes on same scale
- Relative Risk (RR) / Odds Ratio (OR) — for dichotomous outcomes
- Number Needed to Treat (NNT) — clinical interpretation

References:
- Cohen (1988) — small d=0.2, medium=0.5, large=0.8
- Hedges (1985) — small-sample correction
- Cochrane Handbook Ch 15
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class EffectSizeResult:
    estimate: float
    ci_lower: float
    ci_upper: float
    interpretation: str
    method: str

    def display(self) -> str:
        return (
            f"{self.method}: {self.estimate:.3f} "
            f"(95% CI: {self.ci_lower:.3f}, {self.ci_upper:.3f})\n"
            f"Interpretation: {self.interpretation}"
        )


def _interpret_cohens_d(d: float) -> str:
    a = abs(d)
    if a < 0.2:
        return "Trivial effect"
    elif a < 0.5:
        return "Small effect (Cohen: 0.2–0.5)"
    elif a < 0.8:
        return "Medium effect (Cohen: 0.5–0.8)"
    elif a < 1.2:
        return "Large effect (Cohen: 0.8–1.2)"
    else:
        return "Very large effect (d > 1.2)"


def cohens_d(
    mean1: float, sd1: float, n1: int,
    mean2: float, sd2: float, n2: int,
) -> EffectSizeResult:
    """
    Compute Cohen's d (standardized mean difference) with 95% CI.
    Uses pooled SD (Cohen's original formulation).
    """
    pooled_sd = math.sqrt(((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return EffectSizeResult(0.0, 0.0, 0.0, "Zero variance", "Cohen's d")

    d = (mean1 - mean2) / pooled_sd
    # SE of d (Hedges & Olkin 1985)
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2)))
    ci_half = 1.96 * se

    return EffectSizeResult(
        estimate=d,
        ci_lower=d - ci_half,
        ci_upper=d + ci_half,
        interpretation=_interpret_cohens_d(d),
        method="Cohen's d",
    )


def hedges_g(
    mean1: float, sd1: float, n1: int,
    mean2: float, sd2: float, n2: int,
) -> EffectSizeResult:
    """
    Compute Hedges' g — Cohen's d with small-sample bias correction.
    More accurate than Cohen's d for n < 20 per group.
    """
    d_result = cohens_d(mean1, sd1, n1, mean2, sd2, n2)
    df = n1 + n2 - 2
    # Hedges correction factor J
    j = 1 - (3 / (4 * df - 1)) if df > 0 else 1
    g = d_result.estimate * j

    return EffectSizeResult(
        estimate=g,
        ci_lower=d_result.ci_lower * j,
        ci_upper=d_result.ci_upper * j,
        interpretation=_interpret_cohens_d(g),
        method="Hedges' g (small-sample corrected)",
    )


def mean_difference(
    mean1: float, sd1: float, n1: int,
    mean2: float, sd2: float, n2: int,
) -> EffectSizeResult:
    """
    Raw mean difference with 95% CI. Use when outcome is on a meaningful scale
    (e.g., kg lean mass, seconds off a 5k time).
    """
    md = mean1 - mean2
    se = math.sqrt(sd1**2 / n1 + sd2**2 / n2)
    ci_half = 1.96 * se

    return EffectSizeResult(
        estimate=md,
        ci_lower=md - ci_half,
        ci_upper=md + ci_half,
        interpretation=f"Group 1 exceeds group 2 by {md:.2f} units" if md > 0 else f"Group 1 is below group 2 by {abs(md):.2f} units",
        method="Mean difference",
    )


def relative_risk(
    events_a: int, total_a: int,
    events_b: int, total_b: int,
) -> EffectSizeResult:
    """
    Relative risk (RR) with 95% CI. For dichotomous outcomes.
    RR = 1: no effect; RR > 1: intervention increases event rate; RR < 1: decreases.
    """
    if events_a == 0 or events_b == 0:
        # Haldane correction for zero cells
        events_a += 0.5
        events_b += 0.5
        total_a += 0.5
        total_b += 0.5
    risk_a = events_a / total_a
    risk_b = events_b / total_b
    if risk_b == 0:
        return EffectSizeResult(float("inf"), 0, 0, "Division by zero", "Relative risk")
    rr = risk_a / risk_b
    se_ln = math.sqrt((1 / events_a) - (1 / total_a) + (1 / events_b) - (1 / total_b))
    ln_rr = math.log(rr)
    ci_lower = math.exp(ln_rr - 1.96 * se_ln)
    ci_upper = math.exp(ln_rr + 1.96 * se_ln)

    interpretation = "No effect"
    if rr > 1:
        interpretation = f"Intervention increases event rate by {(rr - 1) * 100:.1f}%"
    elif rr < 1:
        interpretation = f"Intervention reduces event rate by {(1 - rr) * 100:.1f}%"

    return EffectSizeResult(
        estimate=rr,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=interpretation,
        method="Relative risk",
    )


def odds_ratio(
    events_a: int, total_a: int,
    events_b: int, total_b: int,
) -> EffectSizeResult:
    """
    Odds ratio (OR) with 95% CI. For dichotomous outcomes, especially case-control.
    OR = 1: no effect; OR > 1: higher odds in group A; OR < 1: lower.
    """
    non_events_a = total_a - events_a
    non_events_b = total_b - events_b

    # Haldane correction for zero cells
    if min(events_a, events_b, non_events_a, non_events_b) == 0:
        events_a += 0.5
        non_events_a += 0.5
        events_b += 0.5
        non_events_b += 0.5

    odds_a = events_a / non_events_a
    odds_b = events_b / non_events_b
    if odds_b == 0:
        return EffectSizeResult(float("inf"), 0, 0, "Division by zero", "Odds ratio")
    or_val = odds_a / odds_b
    se_ln = math.sqrt(1 / events_a + 1 / non_events_a + 1 / events_b + 1 / non_events_b)
    ln_or = math.log(or_val)
    ci_lower = math.exp(ln_or - 1.96 * se_ln)
    ci_upper = math.exp(ln_or + 1.96 * se_ln)

    return EffectSizeResult(
        estimate=or_val,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=f"Odds in group A are {or_val:.2f}x group B",
        method="Odds ratio",
    )


def number_needed_to_treat(
    events_treatment: int, total_treatment: int,
    events_control: int, total_control: int,
) -> dict:
    """
    NNT for beneficial outcomes = 1 / ARR where ARR = event_rate_control - event_rate_treatment.
    For harmful outcomes, returns NNH (number needed to harm).

    Example: Protocol reduces injury from 20% (control) to 10% (treatment)
    ARR = 0.20 - 0.10 = 0.10; NNT = 1/0.10 = 10 (treat 10 to prevent 1 injury)
    """
    risk_treatment = events_treatment / total_treatment if total_treatment else 0
    risk_control = events_control / total_control if total_control else 0
    arr = risk_control - risk_treatment

    if abs(arr) < 1e-9:
        return {
            "arr": arr,
            "nnt_or_nnh": float("inf"),
            "interpretation": "No difference between groups (ARR ≈ 0)",
        }

    nnt = 1 / abs(arr)
    if arr > 0:
        interpretation = (
            f"Treat {math.ceil(nnt)} to prevent 1 event (NNT = {nnt:.1f}). "
            f"Absolute risk reduction: {arr * 100:.1f}%"
        )
    else:
        interpretation = (
            f"Treat {math.ceil(nnt)} to cause 1 extra event (NNH = {nnt:.1f}). "
            f"Absolute risk increase: {abs(arr) * 100:.1f}%"
        )

    return {
        "arr": arr,
        "nnt_or_nnh": nnt,
        "interpretation": interpretation,
    }
