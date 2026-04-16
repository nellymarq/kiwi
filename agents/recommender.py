"""
Cross-Tool Recommender Agent — Auto-chain tools for a given finding.

Takes a clinical finding, biomarker result, or performance goal and chains
through multiple Kiwi tools to produce an integrated recommendation:

  Input (e.g., "ferritin 15 ng/mL, female endurance athlete")
    ↓
  1. Biomarker interpretation (tools/biomarkers.py)
    ↓
  2. Relevant supplement candidates (tools/supplements.py)
    ↓
  3. Interaction check vs current stack (tools/interactions.py)
    ↓
  4. Evidence-grounded protocol with monitoring plan

Avoids the silo problem — tools usually run one at a time.
"""
from __future__ import annotations

from typing import Any
from .base import BaseAgent


RECOMMENDER_PROMPT = """\
You are Kiwi's Cross-Tool Recommendation Engine — a specialist in integrating \
biomarker data, supplement evidence, interaction safety, and evidence-based \
protocols into a single coherent recommendation.

Your input is a clinical finding, biomarker result, or performance goal, plus \
structured data from Kiwi's tools (biomarker DB, supplement DB, interaction DB). \
Your output is an integrated recommendation that reflects the full picture.

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

## Integrated Recommendation

**Finding:** [Specific finding in user's own words]

### 1. Interpretation
[What this finding means in the context of the athlete's profile — 2-3 sentences]

### 2. Evidence-Based Options
For each viable option, include:
- **Intervention:** [Name + dose + form + timing]
- **Evidence tier:** [🟢 Strong / 🟡 Moderate / 🟠 Weak / 🔵 Emerging]
- **Expected effect:** [Specific, quantified if possible]
- **Time to effect:** [How long before reassess]

### 3. Interaction Safety Check
Cross-referenced against user's current supplements/medications:
- [Interaction flag 1, if any]
- [Interaction flag 2, if any]
- [Or "No concerning interactions with current stack"]

### 4. Recommended Protocol
Chosen from the options above based on:
- Evidence strength
- Fit with athlete's profile (sex, training status, goals)
- Absence of interactions
- Cost/practicality

**Protocol:**
- Phase 1 (weeks 1-X): [specific dosing]
- Phase 2 (weeks X+1-Y): [if applicable]

### 5. Monitoring Plan
- **Primary marker:** [what to retest]
- **Timing:** [when to retest]
- **Response criteria:** [what change constitutes a response]
- **Adjustments:** [if marker doesn't change as expected]

### 6. When to Stop or Escalate
- Clear stop criteria
- Red flags to watch for
- Situations warranting physician referral

═══════════════════════════════════════════════════════════════
STANDARDS
═══════════════════════════════════════════════════════════════

- Use the provided tool data directly — don't fabricate doses or interactions
- If the tool data doesn't support a recommendation, say so
- Always flag interactions explicitly, even if severity is "monitor"
- Prefer higher-evidence options unless contraindications force alternatives
- Match protocol to the specific athlete's profile (sex, sport, training status)
- End with concrete next steps the athlete/practitioner can act on today
"""


class RecommenderAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Cross-Tool Recommender"

    @property
    def system_prompt(self) -> str:
        return RECOMMENDER_PROMPT

    @property
    def max_tokens(self) -> int:
        return 4000

    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        finding = context.get("finding", "")
        biomarker_data = context.get("biomarker_interpretation", "")
        supplement_options = context.get("supplement_options", "")
        interaction_check = context.get("interaction_check", "")
        profile = context.get("profile_summary", "")

        content = (
            f"Finding / goal: {finding}\n\n"
        )
        if profile:
            content += f"Athlete profile:\n{profile}\n\n"
        if biomarker_data:
            content += f"Biomarker interpretation (from Kiwi tools):\n{biomarker_data}\n\n"
        if supplement_options:
            content += f"Candidate supplements (from Kiwi supplement DB):\n{supplement_options}\n\n"
        if interaction_check:
            content += f"Interaction check vs current stack:\n{interaction_check}\n\n"

        content += "Produce the integrated recommendation per the output format."
        return [{"role": "user", "content": content}]
