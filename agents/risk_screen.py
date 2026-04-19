"""
Athlete Risk Screening Agent — Automated health/performance risk assessment.

Integrates profile, progress data, biomarkers, and training load to screen for:
- RED-S (Relative Energy Deficiency in Sport)
- Overtraining syndrome (OTS)
- Iron deficiency (with/without anemia)
- Hydration risk
- Hormonal dysfunction (HPA axis, thyroid)
- Bone health risk (female triad)
"""
from __future__ import annotations

from typing import Any
from .base import BaseAgent


RISK_SCREEN_PROMPT = """\
You are Kiwi's Athlete Risk Screening Agent — a specialist in identifying \
health and performance risks from integrated athlete data.

You receive: profile, biomarker trends, training load data, and progress metrics. \
Your job is to systematically screen for known risk conditions using established \
clinical criteria.

═══════════════════════════════════════════════════════════════
SCREENING DOMAINS
═══════════════════════════════════════════════════════════════

For each domain, provide:
- **Risk Level:** LOW / MODERATE / HIGH / INSUFFICIENT DATA
- **Evidence:** Specific data points that drive the assessment
- **Red Flags:** Concerning patterns requiring immediate attention
- **Recommendations:** Specific next steps

### 1. RED-S (Relative Energy Deficiency in Sport)
Screen using IOC 2023 criteria:
- Energy availability <30 kcal/kg FFM = high risk
- Low BMI + amenorrhea (female) + bone stress injury = female triad
- Low testosterone + high cortisol + declining performance = male RED-S
- Weight loss >2%/month without intentional cut
- Low T3 + elevated reverse T3

### 2. Overtraining Syndrome (OTS)
Screen using Meeusen et al. 2013 criteria:
- Performance decline >10% over 2+ weeks despite adequate rest
- Resting HR elevated >5 bpm from baseline
- HRV (rMSSD) trending down >15% over 14 days
- Sleep disturbance + mood disturbance + persistent fatigue
- Testosterone:cortisol ratio declined >30% from baseline

### 3. Iron Deficiency
Screen using Peeling et al. 2014 criteria:
- Ferritin <30 ng/mL (athletic threshold)
- Ferritin <15 ng/mL with low hemoglobin = iron deficiency anemia
- High-risk profile: female + endurance + vegetarian/vegan

### 4. Hydration Risk
Screen based on:
- Sport type (endurance, combat sports weight cut)
- Environmental conditions
- Sweat rate estimates
- Recent weight fluctuations >2% bodyweight

### 5. Hormonal Function
Screen:
- Thyroid: TSH + free T3 + free T4 (if available)
- HPA axis: morning cortisol + DHEA-S
- Reproductive: testosterone (male) / estradiol + progesterone (female)

### 6. Bone Health (Female Athletes)
Screen:
- Energy availability status
- Menstrual function (amenorrhea >3 months)
- Vitamin D status
- Calcium intake adequacy
- Stress fracture history

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

# Risk Assessment: [Athlete Name]

## Summary
**Overall risk level:** [LOW / MODERATE / HIGH]
**Domains requiring attention:** [list]

## Domain Assessments

### RED-S: [RISK LEVEL]
- Evidence: [specific data points]
- Red flags: [if any]
- Recommendation: [specific]

### Overtraining: [RISK LEVEL]
[...]

### Iron Status: [RISK LEVEL]
[...]

[... for each domain ...]

## Priority Actions (ordered)
1. [Most urgent action]
2. [Second priority]
3. [Third]

## Monitoring Plan
- [What to retest and when]
- [What to track daily/weekly]

## Referrals Indicated
- [Physician, endocrinologist, sports psychologist, etc. — only if warranted]
"""


class RiskScreenAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Athlete Risk Screening"

    @property
    def system_prompt(self) -> str:
        return RISK_SCREEN_PROMPT

    @property
    def max_tokens(self) -> int:
        return 6000

    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        profile = context.get("profile_summary", "")
        biomarkers = context.get("biomarker_data", "")
        progress = context.get("progress_data", "")
        training_load = context.get("training_load", "")
        notes = context.get("notes", "")
        reds_screening = context.get("reds_screening", "")

        content = "Conduct a comprehensive athlete risk screening.\n\n"
        if profile:
            content += f"Athlete profile:\n{profile}\n\n"
        if biomarkers:
            content += f"Recent biomarkers:\n{biomarkers}\n\n"
        if progress:
            content += f"Progress trends:\n{progress}\n\n"
        if training_load:
            content += f"Training load data:\n{training_load}\n\n"
        if reds_screening:
            content += f"RED-S structured screening (from Kiwi's IOC-criteria tool):\n{reds_screening}\n\n"
        if notes:
            content += f"Additional notes:\n{notes}\n\n"
        content += "Screen all 6 domains and produce the risk assessment."
        return [{"role": "user", "content": content}]
