"""
Methodology Quality Assessment — Risk of Bias tools for evidence appraisal.

Implements checklists for the three most common study-quality tools:
- RoB 2 (Risk of Bias 2) for randomized trials (Cochrane 2019)
- ROBINS-I (Risk Of Bias In Non-randomized Studies of Interventions, 2016)
- AMSTAR 2 (A MeaSurement Tool to Assess systematic Reviews, 2017)

These are domain-specific question checklists. Each domain gets a judgment:
LOW / SOME_CONCERNS / HIGH risk of bias. Overall rating follows the worst domain.

References:
- Sterne et al. BMJ 2019 (RoB 2)
- Sterne et al. BMJ 2016 (ROBINS-I)
- Shea et al. BMJ 2017 (AMSTAR 2)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Judgment = Literal["LOW", "SOME_CONCERNS", "HIGH", "NO_INFORMATION"]

JUDGMENT_EMOJI = {
    "LOW": "🟢",
    "SOME_CONCERNS": "🟡",
    "HIGH": "🔴",
    "NO_INFORMATION": "⚪",
}

JUDGMENT_ORDER = {"LOW": 0, "SOME_CONCERNS": 1, "HIGH": 2, "NO_INFORMATION": 3}


@dataclass
class QualityDomain:
    name: str
    questions: list[str]
    judgment: Judgment = "NO_INFORMATION"
    rationale: str = ""


@dataclass
class QualityAssessment:
    tool: str                  # "RoB 2", "ROBINS-I", "AMSTAR 2"
    study_title: str
    domains: list[QualityDomain]
    overall: Judgment = "NO_INFORMATION"
    notes: str = ""

    def worst_domain(self) -> QualityDomain | None:
        if not self.domains:
            return None
        return max(self.domains, key=lambda d: JUDGMENT_ORDER[d.judgment])

    def compute_overall(self) -> Judgment:
        """Overall rating = worst single domain (standard RoB 2 rule)."""
        worst = self.worst_domain()
        if not worst or worst.judgment == "NO_INFORMATION":
            return "NO_INFORMATION"
        return worst.judgment

    def display(self) -> str:
        self.overall = self.compute_overall()
        emoji = JUDGMENT_EMOJI.get(self.overall, "⚪")
        lines = [
            f"{emoji} {self.tool} Quality Assessment",
            f"   Study: {self.study_title}",
            f"   Overall: {self.overall}",
            "",
        ]
        for d in self.domains:
            d_emoji = JUDGMENT_EMOJI.get(d.judgment, "⚪")
            lines.append(f"   {d_emoji} {d.name}: {d.judgment}")
            if d.rationale:
                lines.append(f"      {d.rationale[:200]}")
        if self.notes:
            lines.append(f"\n   Notes: {self.notes}")
        return "\n".join(lines)


# ── RoB 2 (Randomized Trials) ─────────────────────────────────────────────────

ROB2_DOMAINS = [
    QualityDomain(
        name="1. Randomization process",
        questions=[
            "Was the allocation sequence random?",
            "Was the allocation sequence concealed until participants were enrolled?",
            "Did baseline differences between groups suggest a problem with the randomization process?",
        ],
    ),
    QualityDomain(
        name="2. Deviations from intended interventions",
        questions=[
            "Were participants aware of their assigned intervention?",
            "Were carers and people delivering the interventions aware of participants' assigned intervention?",
            "Were there deviations from the intended intervention that arose because of the trial context?",
            "Was an appropriate analysis used to estimate the effect of assignment to intervention?",
        ],
    ),
    QualityDomain(
        name="3. Missing outcome data",
        questions=[
            "Were data for this outcome available for all, or nearly all, participants randomized?",
            "Is there evidence that the result was not biased by missing outcome data?",
            "Could missingness in the outcome depend on its true value?",
        ],
    ),
    QualityDomain(
        name="4. Measurement of the outcome",
        questions=[
            "Was the method of measuring the outcome inappropriate?",
            "Could measurement or ascertainment of the outcome have differed between intervention groups?",
            "Were outcome assessors aware of the intervention received by study participants?",
        ],
    ),
    QualityDomain(
        name="5. Selection of the reported result",
        questions=[
            "Were the data that produced this result analysed in accordance with a pre-specified analysis plan?",
            "Is the numerical result being assessed likely to have been selected from multiple outcome measurements within the outcome domain?",
            "Is the numerical result being assessed likely to have been selected from multiple analyses of the data?",
        ],
    ),
]


# ── ROBINS-I (Non-randomized Studies) ─────────────────────────────────────────

ROBINS_I_DOMAINS = [
    QualityDomain(
        name="1. Confounding",
        questions=[
            "Is there potential for confounding of the effect of intervention?",
            "Were participants analysed according to their initial intervention group?",
            "Were confounding variables adjusted for appropriately?",
        ],
    ),
    QualityDomain(
        name="2. Selection of participants",
        questions=[
            "Was selection of participants into the study related to intervention and outcome?",
            "Does the analysis control for all the important prognostic variables?",
        ],
    ),
    QualityDomain(
        name="3. Classification of interventions",
        questions=[
            "Were intervention groups clearly defined?",
            "Was information on intervention status recorded at the start of the intervention?",
            "Could classification of intervention status have been affected by knowledge of the outcome?",
        ],
    ),
    QualityDomain(
        name="4. Deviations from intended interventions",
        questions=[
            "Were there deviations from the intended intervention beyond what would be expected in usual practice?",
            "Were these deviations likely to affect the outcome?",
        ],
    ),
    QualityDomain(
        name="5. Missing data",
        questions=[
            "Were outcome data reasonably complete?",
            "Was the analysis appropriate to the pattern of missing data?",
        ],
    ),
    QualityDomain(
        name="6. Measurement of outcomes",
        questions=[
            "Could the outcome measure have been influenced by knowledge of intervention received?",
            "Were outcome assessors blinded to intervention status?",
            "Were methods of outcome assessment comparable across intervention groups?",
        ],
    ),
    QualityDomain(
        name="7. Selection of the reported result",
        questions=[
            "Is the reported effect estimate likely to be selected from multiple measurements?",
            "Is the reported effect estimate likely to be selected from multiple analyses?",
            "Is the reported effect estimate likely to be selected from multiple subgroups?",
        ],
    ),
]


# ── AMSTAR 2 (Systematic Reviews) ─────────────────────────────────────────────

AMSTAR2_DOMAINS = [
    QualityDomain(
        name="1. PICO in research question",
        questions=["Did the research question include PICO components?"],
    ),
    QualityDomain(
        name="2. Pre-registered protocol",
        questions=["Was the review protocol established prior to conduct?"],
    ),
    QualityDomain(
        name="3. Study design justified",
        questions=["Did review authors explain their study design selection?"],
    ),
    QualityDomain(
        name="4. Comprehensive literature search",
        questions=[
            "Did review authors use a comprehensive literature search strategy?",
            "At least 2 databases searched, keywords and/or MeSH terms provided.",
        ],
    ),
    QualityDomain(
        name="5. Duplicate study selection",
        questions=["Did review authors perform study selection in duplicate?"],
    ),
    QualityDomain(
        name="6. Duplicate data extraction",
        questions=["Did review authors perform data extraction in duplicate?"],
    ),
    QualityDomain(
        name="7. Excluded studies list",
        questions=["Did authors provide a list of excluded studies and justify exclusions?"],
    ),
    QualityDomain(
        name="8. Included studies detail",
        questions=["Did authors describe included studies in adequate detail?"],
    ),
    QualityDomain(
        name="9. Risk of bias in individual studies",
        questions=["Did authors use a satisfactory technique for assessing RoB in individual studies?"],
    ),
    QualityDomain(
        name="10. Funding sources",
        questions=["Did authors report sources of funding for studies included in the review?"],
    ),
    QualityDomain(
        name="11. Appropriate meta-analysis methods",
        questions=["If meta-analysis performed, did authors use appropriate methods for statistical combination?"],
    ),
    QualityDomain(
        name="12. RoB impact on meta-analysis",
        questions=["Did authors assess potential impact of RoB in individual studies on the results?"],
    ),
    QualityDomain(
        name="13. RoB discussion in interpretation",
        questions=["Did authors account for RoB when interpreting/discussing results?"],
    ),
    QualityDomain(
        name="14. Heterogeneity discussion",
        questions=["Did authors provide satisfactory explanation for any heterogeneity?"],
    ),
    QualityDomain(
        name="15. Publication bias",
        questions=["If quantitative synthesis was performed, did authors investigate publication bias?"],
    ),
    QualityDomain(
        name="16. Conflicts of interest",
        questions=["Did authors report potential conflicts of interest?"],
    ),
]


def get_checklist(tool: str) -> list[QualityDomain]:
    """Return a fresh checklist for the specified quality tool."""
    tool_upper = tool.upper().replace(" ", "").replace("-", "")
    if tool_upper in ("ROB2", "ROB", "RCT"):
        return [QualityDomain(name=d.name, questions=list(d.questions)) for d in ROB2_DOMAINS]
    if tool_upper in ("ROBINSI", "OBSERVATIONAL", "COHORT", "CASECONTROL"):
        return [QualityDomain(name=d.name, questions=list(d.questions)) for d in ROBINS_I_DOMAINS]
    if tool_upper in ("AMSTAR2", "AMSTAR", "SYSTEMATICREVIEW", "METAANALYSIS"):
        return [QualityDomain(name=d.name, questions=list(d.questions)) for d in AMSTAR2_DOMAINS]
    raise ValueError(f"Unknown quality tool: {tool}. Use 'RoB2', 'ROBINS-I', or 'AMSTAR 2'.")


def format_checklist(tool: str) -> str:
    """Return a formatted checklist for manual completion."""
    domains = get_checklist(tool)
    tool_name = {
        "ROB2": "RoB 2 (Randomized Trials)",
        "ROBINSI": "ROBINS-I (Non-randomized Studies)",
        "AMSTAR2": "AMSTAR 2 (Systematic Reviews)",
    }.get(tool.upper().replace(" ", "").replace("-", ""), tool)

    lines = [f"=== {tool_name} ===", ""]
    for d in domains:
        lines.append(f"{d.name}")
        for q in d.questions:
            lines.append(f"  □ {q}")
        lines.append("  Judgment: [ ] LOW  [ ] SOME_CONCERNS  [ ] HIGH")
        lines.append("")
    return "\n".join(lines)
