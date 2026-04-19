"""
Daily Brief Agent — One-page daily summary for the active client.

Synthesizes: today's training recommendation, biomarker status, active
interventions, flagged risks, and suggested next steps.
"""
from __future__ import annotations

from typing import Any
from .base import BaseAgent


DAILY_BRIEF_PROMPT = """\
You are Kiwi's Daily Brief Agent — you produce a concise, actionable daily \
summary for a specific athlete based on their current data.

Your output is a single-page brief that the practitioner can review in 60 seconds \
and know exactly what to focus on today.

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

# Daily Brief: [Athlete Name] — [Date]

## 📊 Status at a Glance
| Metric | Latest | Trend | Flag |
|--------|--------|-------|------|
| Weight | 77.0 kg | ↓ 0.5 this week | ✅ On track |
| HRV | 52 ms | → Stable | ✅ |
| Sleep | 7.2 hrs | ↓ Below target | ⚠️ |

## 🏋️ Today's Training Recommendation
[Based on HRV readiness, training load trends, and active interventions]
- **Suggested:** [session type + intensity]
- **Rationale:** [why this, based on data]

## 💊 Active Interventions
- Iron 36mg/d (started 3 weeks ago) — ferritin trending ↑ (15 → 25 ng/mL)
- Creatine 5g/d — ongoing

## ⚠️ Watch Items
- [Any biomarker due for retest]
- [Any risk flag from last screening]
- [Any intervention needing outcome check]

## 📋 Suggested Actions
1. [Most important action for today]
2. [Secondary]
3. [If time allows]

═══════════════════════════════════════════════════════════════
STANDARDS
═══════════════════════════════════════════════════════════════

- Keep it to ONE PAGE (under 500 words)
- Lead with actionable items, not data
- Only flag items that need attention TODAY
- Use the data provided — don't fabricate trends
- If data is insufficient, say "Insufficient data for X"
"""


class DailyBriefAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Daily Brief"

    @property
    def system_prompt(self) -> str:
        return DAILY_BRIEF_PROMPT

    @property
    def max_tokens(self) -> int:
        return 3000

    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        profile = context.get("profile_summary", "")
        progress = context.get("progress_data", "")
        interventions = context.get("interventions", "")
        risk_flags = context.get("risk_flags", "")
        research_gaps = context.get("research_gaps", "")
        biomarker_due = context.get("biomarker_due", "")
        training_load = context.get("training_load", "")
        reds_screening = context.get("reds_screening", "")
        cycle_phase_context = context.get("cycle_phase_context", "")

        content = "Generate today's daily brief.\n\n"
        if profile:
            content += f"Athlete profile:\n{profile}\n\n"
        if progress:
            content += f"Recent progress data:\n{progress}\n\n"
        if training_load:
            content += f"Training load analysis (Kiwi ACWR tool):\n{training_load}\n\n"
        if reds_screening:
            content += f"RED-S structured screening (from Kiwi profile data):\n{reds_screening}\n\n"
        if cycle_phase_context:
            content += f"{cycle_phase_context}\n\n"
        if interventions:
            content += f"Active interventions:\n{interventions}\n\n"
        if risk_flags:
            content += f"Risk flags:\n{risk_flags}\n\n"
        if research_gaps:
            content += f"Research gaps:\n{research_gaps}\n\n"
        if biomarker_due:
            content += f"Biomarkers due for retest:\n{biomarker_due}\n\n"
        content += "Produce the daily brief."
        return [{"role": "user", "content": content}]
