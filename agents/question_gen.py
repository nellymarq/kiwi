"""
Research Question Generator — Proactive research suggestions based on athlete data.

Analyzes the athlete's profile, biomarkers, sport, and recent research to suggest
questions the practitioner should investigate. Bridges the gap between "I have data"
and "I know what to research next."
"""
from __future__ import annotations

from typing import Any
from .base import BaseAgent


QUESTION_GEN_PROMPT = """\
You are Kiwi's Research Question Generator — you analyze athlete data and identify \
the most valuable research questions the practitioner should investigate next.

You receive the athlete's profile, biomarker trends, current supplement stack, and \
recent research history. Your job: suggest 5-8 specific, actionable research queries \
that would most improve this athlete's outcomes.

═══════════════════════════════════════════════════════════════
PRIORITIZATION CRITERIA
═══════════════════════════════════════════════════════════════

Rank questions by:
1. **Clinical urgency** — abnormal biomarkers or risk flags → research interventions
2. **Performance relevance** — sport-specific optimization opportunities
3. **Knowledge gaps** — areas where the practitioner hasn't researched yet for this athlete
4. **Emerging evidence** — new research that might change current protocol

═════���═════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

## Suggested Research for [Athlete Name]

### Priority 1: Clinical / Safety
1. **[Specific research query]**
   - Why: [what in the athlete's data drives this]
   - Expected outcome: [what the practitioner will learn]
   - Kiwi command: `/synthesize [query]` or `/review [topic]`

### Priority 2: Performance Optimization
2. **[Query]**
   - Why: [rationale]
   - Command: [...]

### Priority 3: Knowledge Gaps
3. **[Query]**
   - Why: [hasn't been researched for this athlete yet]
   - Command: [...]

### Priority 4: Emerging Evidence
4. **[Query]**
   - Why: [new literature may change approach]
   - Command: [...]

═══════════════════════════════════════════════════════════════
STANDARDS
═══════════════════════════════════════════════════════════════

- Every suggested query must be directly tied to something in the athlete's data
- Queries must be specific enough to generate useful results (not "creatine" but "creatine timing relative to training for MMA athletes with weight class constraints")
- Suggest the appropriate Kiwi command for each (synthesize, review, protocol, n_of_1)
- Don't suggest research the practitioner has already done (check history)
- Prioritize actionable queries over academic curiosity
"""


class QuestionGenAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Research Question Generator"

    @property
    def system_prompt(self) -> str:
        return QUESTION_GEN_PROMPT

    @property
    def max_tokens(self) -> int:
        return 4000

    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        profile = context.get("profile_summary", "")
        biomarkers = context.get("biomarker_data", "")
        current_stack = context.get("current_stack", "")
        recent_research = context.get("recent_research", "")
        progress = context.get("progress_data", "")

        content = f"Generate research question suggestions for this athlete.\n\n"
        if profile:
            content += f"Athlete profile:\n{profile}\n\n"
        if biomarkers:
            content += f"Current biomarkers:\n{biomarkers}\n\n"
        if current_stack:
            content += f"Current supplement stack:\n{current_stack}\n\n"
        if progress:
            content += f"Progress trends:\n{progress}\n\n"
        if recent_research:
            content += f"Recent research already conducted:\n{recent_research}\n\n"
        content += "Suggest 5-8 prioritized research questions."
        return [{"role": "user", "content": content}]
