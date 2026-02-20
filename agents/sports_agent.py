"""
Sports Intelligence Agent — Applied daily coaching decisions.

Unlike the KiwiOrchestrator (which answers research questions), the SportsAgent
synthesizes an athlete's real-time data (HRV, sleep, training load, biomarkers,
hydration) into an actionable daily training recommendation.

Use case: "Given everything I know about this athlete today, what should they do?"

Pipeline:
  Data Collection (HRV + load + sleep + biomarkers)
        ↓
  Local Metrics Computation (readiness, TSB, deload triggers)
        ↓
  Claude Synthesis (adaptive thinking, evidence-grounded coaching)
        ↓
  Actionable Daily Plan (training, nutrition, recovery priorities)
"""
from __future__ import annotations

from typing import Any, Optional
import anthropic

from .base import BaseAgent, AGENT_MODEL

# Tools imported with absolute paths (works when running from kiwi root)
try:
    from tools.recovery import (
        ReadinessScore, DeloadAssessment,
        compute_readiness, assess_deload_need, format_readiness_report,
    )
    from tools.sleep_optimizer import classify_chronotype, CHRONOTYPE_PROFILES
except ImportError:
    # Package-relative fallback
    from ..tools.recovery import (  # type: ignore
        ReadinessScore, DeloadAssessment,
        compute_readiness, assess_deload_need, format_readiness_report,
    )
    from ..tools.sleep_optimizer import classify_chronotype, CHRONOTYPE_PROFILES  # type: ignore


SPORTS_AGENT_SYSTEM = """\
You are Kiwi's Sports Intelligence Agent — a specialist in applied sports science \
and daily athletic performance optimization.

Your role is to synthesize an athlete's physiological data into clear, evidence-based \
daily coaching decisions. You do not provide generic advice — you interpret the SPECIFIC \
numbers provided and give precise, actionable recommendations.

═══════════════════════════════════════════════════════════════
CORE RESPONSIBILITIES
═══════════════════════════════════════════════════════════════

1. TRAINING READINESS ASSESSMENT
   • Interpret HRV (rMSSD trends), TSB/ATL/CTL, subjective fatigue
   • Determine optimal training intensity for today
   • Flag overreaching, underrecovery, or illness risk

2. DAILY TRAINING PRESCRIPTION
   • Session type: intensity zone, volume target, modalities
   • Modify today's planned session based on readiness data
   • When to push vs. when to back off (data-driven, not motivation-based)

3. NUTRITION PRIORITIES FOR TODAY
   • Carbohydrate targets based on session type/intensity
   • Protein timing windows for today's schedule
   • Micronutrient attention flags based on biomarkers

4. RECOVERY STRATEGY
   • Post-session recovery modality selection (with evidence)
   • Sleep priority signals
   • Acute intervention recommendations

5. RISK FLAGS
   • Overtraining syndrome indicators
   • Relative Energy Deficiency in Sport (RED-S) signals
   • Medical referral triggers

═══════════════════════════════════════════════════════════════
EVIDENCE AND COMMUNICATION STANDARDS
═══════════════════════════════════════════════════════════════

• Cite specific values from the data provided (never fabricate numbers)
• Use evidence tiers: 🟢 Strong | 🟡 Moderate | 🟠 Weak | 🔵 Emerging
• Be direct and specific — avoid hedging when data is clear
• Flag when data is insufficient for confident recommendations
• Never provide medical diagnoses — flag for medical evaluation when appropriate

═══════════════════════════════════════════════════════════════
OUTPUT STRUCTURE
═══════════════════════════════════════════════════════════════

## Today's Readiness Assessment
[Interpret readiness score + key drivers. Be specific about the numbers.]

## Training Prescription for Today
[Specific session recommendation: modality, intensity zone, volume, duration]

## Nutrition Focus
[Today's targets based on session type and biomarkers]

## Recovery Priority
[Top 1–2 recovery strategies with timing]

## Watch Flags
[Any concerning patterns or risk signals in the data]
"""


class SportsAgent(BaseAgent):
    """
    Applied sports intelligence agent for daily training recommendations.
    Synthesizes HRV, load, biomarkers, and sleep into actionable coaching.
    """

    @property
    def name(self) -> str:
        return "Sports Intelligence Agent"

    @property
    def system_prompt(self) -> str:
        return SPORTS_AGENT_SYSTEM

    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        """Build the analysis request from athlete data context."""
        athlete_name = context.get("athlete_name", "Athlete")
        sport = context.get("sport", "unspecified")
        phase = context.get("training_phase", "unspecified")

        # Pre-computed local metrics (from tools)
        readiness_report = context.get("readiness_report", "")
        deload_assessment = context.get("deload_assessment", "")
        planned_session = context.get("planned_session", "")

        # Raw data sections
        load_data = context.get("load_data", "")        # TSB/ATL/CTL
        biomarker_summary = context.get("biomarker_summary", "")
        sleep_data = context.get("sleep_data", "")
        hydration_data = context.get("hydration_data", "")
        notes = context.get("notes", "")

        content_parts = [
            f"Athlete: {athlete_name}",
            f"Sport: {sport}",
            f"Training Phase: {phase}",
            "",
        ]

        if readiness_report:
            content_parts += ["## HRV Readiness Report (Pre-Computed)", readiness_report, ""]

        if deload_assessment:
            content_parts += ["## Deload Assessment (Pre-Computed)", deload_assessment, ""]

        if load_data:
            content_parts += ["## Training Load Data", load_data, ""]

        if sleep_data:
            content_parts += ["## Sleep Data", sleep_data, ""]

        if biomarker_summary:
            content_parts += ["## Biomarker Summary", biomarker_summary, ""]

        if hydration_data:
            content_parts += ["## Hydration / Sweat Data", hydration_data, ""]

        if planned_session:
            content_parts += [f"## Planned Session Today", planned_session, ""]

        if notes:
            content_parts += ["## Athlete Notes / Subjective", notes, ""]

        content_parts.append(
            "Based on all available data above, provide your complete sports intelligence assessment."
        )

        return [{"role": "user", "content": "\n".join(content_parts)}]


async def run_sports_assessment(
    client: anthropic.AsyncAnthropic,
    athlete_data: dict[str, Any],
    on_text=None,
) -> str:
    """
    Run the complete sports intelligence assessment pipeline.

    1. Compute local metrics (readiness score, deload assessment) from raw data
    2. Format data for Claude
    3. Run SportsAgent for synthesis

    Args:
        client: AsyncAnthropic client.
        athlete_data: Dict with keys:
            - athlete_name: str
            - sport: str
            - training_phase: str (e.g., 'base', 'build', 'peak', 'taper')
            - hrv_readings: list[HRVReading]
            - tsb: float | None
            - atl: float | None
            - ctl: float | None
            - sleep_debt_hours: float
            - consecutive_hard_days: int
            - weeks_since_deload: int
            - subjective_fatigue: int | None (1–10)
            - rpe_drift: float | None
            - biomarker_summary: str
            - hydration_data: str
            - planned_session: str
            - notes: str
        on_text: Optional streaming callback.

    Returns:
        Assessment text from the Sports Intelligence Agent.
    """
    # Step 1: Compute readiness score
    hrv_readings = athlete_data.get("hrv_readings", [])
    tsb = athlete_data.get("tsb")
    sleep_debt = athlete_data.get("sleep_debt_hours", 0.0)

    readiness = compute_readiness(hrv_readings, tsb=tsb, sleep_debt_hours=sleep_debt)
    readiness_report = format_readiness_report(readiness)

    # Step 2: Deload assessment
    deload = assess_deload_need(
        tsb=tsb,
        consecutive_hard_days=athlete_data.get("consecutive_hard_days", 0),
        weeks_since_deload=athlete_data.get("weeks_since_deload", 0),
        sleep_debt_hours=sleep_debt,
        subjective_fatigue=athlete_data.get("subjective_fatigue"),
        rpe_drift=athlete_data.get("rpe_drift"),
        performance_decline_pct=athlete_data.get("performance_decline_pct"),
    )

    deload_lines = [
        f"Deload Needed: {'YES' if deload.should_deload else 'No'}",
        f"Urgency: {deload.urgency}",
    ]
    if deload.should_deload:
        deload_lines.append(f"Type: {deload.deload_type}")
        deload_lines.append(f"Primary Trigger: {deload.primary_trigger}")
        deload_lines.append("Triggers:")
        for t in deload.triggered_by:
            deload_lines.append(f"  • {t}")

    deload_report = "\n".join(deload_lines)

    # Step 3: Load data summary
    load_parts = []
    if tsb is not None:
        load_parts.append(f"TSB: {tsb:.1f}")
    if athlete_data.get("atl") is not None:
        load_parts.append(f"ATL (Fatigue): {athlete_data['atl']:.1f}")
    if athlete_data.get("ctl") is not None:
        load_parts.append(f"CTL (Fitness): {athlete_data['ctl']:.1f}")
    load_data = "  ".join(load_parts) if load_parts else ""

    # Step 4: Build context for agent
    context = {
        "athlete_name":      athlete_data.get("athlete_name", "Athlete"),
        "sport":             athlete_data.get("sport", "General"),
        "training_phase":    athlete_data.get("training_phase", "Unspecified"),
        "readiness_report":  readiness_report,
        "deload_assessment": deload_report,
        "load_data":         load_data,
        "sleep_data":        (
            f"Sleep Debt: {sleep_debt:.1f}h"
            + (f"\nConsecutive Hard Days: {athlete_data['consecutive_hard_days']}"
               if athlete_data.get("consecutive_hard_days") else "")
        ),
        "biomarker_summary": athlete_data.get("biomarker_summary", ""),
        "hydration_data":    athlete_data.get("hydration_data", ""),
        "planned_session":   athlete_data.get("planned_session", ""),
        "notes":             athlete_data.get("notes", ""),
    }

    # Step 5: Run agent
    agent = SportsAgent(client)
    messages = agent._build_messages(context)

    if on_text:
        # Streaming mode
        accumulated = ""
        async with client.messages.stream(
            model=AGENT_MODEL,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=agent.system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                on_text(text)
                accumulated += text
        return accumulated
    else:
        return await agent.run(context)
