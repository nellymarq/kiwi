"""
Critique Agent — Ralph Wiggum Loop for evidence integrity and logical quality.

The Ralph Wiggum Loop is Kiwi's internal self-critique system. It evaluates every
research response on 5 evidence dimensions and returns a structured JSON score.
When the score falls below REFINEMENT_THRESHOLD (0.72), the refinement agent
rewrites the response targeting the specific critical issues.

Why "Ralph Wiggum"? The loop embodies innocent, unbiased critique — no agenda,
no favoritism, just honest evaluation of what the evidence actually shows.
"""

import json
import re
from typing import Any
from .base import BaseAgent, AGENT_MODEL, REFINEMENT_THRESHOLD

CRITIQUE_PROMPT = """\
You are Kiwi's internal critic — the Ralph Wiggum Loop.

Your sole purpose: evaluate research output quality with rigorous, unbiased standards.
You have no stake in the content — only in its accuracy, evidence integrity, and intellectual honesty.

═══════════════════════════════════════════════════════════════
EVALUATION DIMENSIONS
═══════════════════════════════════════════════════════════════

Score each dimension from 0.0 to 1.0:

1. Evidence Grounding (weight: 0.30)
   — Are all claims traceable to actual peer-reviewed literature?
   — Are study types, sample sizes, and populations mentioned?
   — Any fabricated citations, effect sizes, or authors?

2. Evidence Hierarchy (weight: 0.20)
   — Is evidence quality explicitly labeled (🟢/🟡/🟠/🔵)?
   — Are RCTs and meta-analyses distinguished from case reports or animal data?
   — Is the overall evidence grade appropriate for the certainty expressed?

3. Mechanistic Accuracy (weight: 0.20)
   — Are biochemical pathways and physiological principles correctly described?
   — Are molecular mechanisms (enzyme kinetics, receptor pharmacology, signaling) accurate?
   — Any oversimplifications that would mislead a knowledgeable reader?

4. Logical Consistency (weight: 0.20)
   — Any internal contradictions between sections?
   — Unsupported inferential leaps from mechanism to practical recommendation?
   — Does the conclusion follow from the evidence presented?

5. Uncertainty Handling (weight: 0.10)
   — Is uncertainty appropriately acknowledged where the evidence is limited?
   — Are population-specific limitations noted (sex, training status, age, genetics)?
   — Any overconfident claims that outrun the evidence?

═══════════════════════════════════════════════════════════════
SCORING
═══════════════════════════════════════════════════════════════

Composite score = (grounding×0.30) + (hierarchy×0.20) + (mechanistic×0.20) + (logic×0.20) + (uncertainty×0.10)

Threshold for auto-refinement: 0.72
If score < 0.72 OR any dimension score < 0.50, set needs_refinement: true

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

Return ONLY valid JSON. No preamble. No markdown fences. No explanation outside the JSON.

{
  "score": <weighted composite float 0.0–1.0>,
  "dimension_scores": {
    "evidence_grounding": <0.0–1.0>,
    "evidence_hierarchy": <0.0–1.0>,
    "mechanistic_accuracy": <0.0–1.0>,
    "logical_consistency": <0.0–1.0>,
    "uncertainty_handling": <0.0–1.0>
  },
  "critical_issues": [
    "<Specific, actionable problem — cite the exact claim or section where the issue occurs>",
    ...
  ],
  "minor_issues": [
    "<Small concern that doesn't invalidate the response>",
    ...
  ],
  "strengths": [
    "<What the response does exceptionally well>",
    ...
  ],
  "needs_refinement": <true if score < 0.72 or any dimension < 0.50, else false>,
  "refinement_priority": "<evidence_grounding|mechanistic_accuracy|logical_consistency|evidence_hierarchy|uncertainty_handling — the single most important dimension to fix>"
}\
"""


class CritiqueAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Ralph Wiggum Loop"

    @property
    def system_prompt(self) -> str:
        return CRITIQUE_PROMPT

    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        query = context.get("query", "")
        response_text = context.get("response_text", "")
        return [{
            "role": "user",
            "content": (
                f"ORIGINAL QUERY:\n{query}\n\n"
                f"RESEARCH RESPONSE TO EVALUATE:\n{response_text[:8000]}"
            ),
        }]

    async def critique(
        self,
        query: str,
        response_text: str,
    ) -> tuple[dict, float]:
        """
        Run the Ralph Wiggum critique loop.
        Returns (critique_data dict, composite score float).
        Retries once on parse failure. Falls back to score=0.5 (not 1.0)
        to trigger refinement rather than silently passing bad research.
        """
        messages = self._build_messages({
            "query": query,
            "response_text": response_text,
        })

        for attempt in range(2):
            response = await self.client.messages.create(
                model=AGENT_MODEL,
                max_tokens=3000,
                system=self.system_prompt,
                messages=messages,
            )

            critique_text = next(
                (b.text for b in response.content if hasattr(b, "text")), "{}"
            )

            try:
                m = re.search(r"\{.*\}", critique_text, re.DOTALL)
                if m:
                    parsed = json.loads(m.group())
                    score = float(parsed.get("score", 0.5))
                    dim_scores = parsed.get("dimension_scores", {})
                    any_low_dim = any(float(v) < 0.50 for v in dim_scores.values())
                    if score < REFINEMENT_THRESHOLD or any_low_dim:
                        parsed["needs_refinement"] = True
                    return parsed, score
            except (json.JSONDecodeError, AttributeError, ValueError):
                if attempt == 0:
                    continue

        fallback = {
            "score": 0.5,
            "dimension_scores": {},
            "critical_issues": ["Critique parse failed — flagging for manual review"],
            "minor_issues": [],
            "strengths": [],
            "needs_refinement": True,
            "refinement_priority": "evidence_grounding",
        }
        return fallback, 0.5