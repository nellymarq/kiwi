"""
Mental performance optimization tools for Kiwi.

Evidence-based tools for psychological performance factors:
- Competition anxiety assessment (CSAI-2R proxy)
- Mental fatigue detection and performance impact
- Burnout risk assessment (REST-Q style)
- Visualization / mental rehearsal protocols
- Pre-competition routine generator

References:
- Martens R et al. (1990) Competitive anxiety in sport — CSAI-2
- Cox RH et al. (2003) J Sport Behav — CSAI-2R validation
- Kellmann M & Kallus KW (2001) Recovery-Stress Questionnaire for Athletes (REST-Q)
- Vealey RS & Greenleaf CA (2010) — Imagery use in sport
- Weinberg RS & Gould D (2019) — Foundations of Sport and Exercise Psychology
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class AnxietyAssessment:
    cognitive_anxiety: float      # 1-4 scale
    somatic_anxiety: float        # 1-4 scale
    self_confidence: float        # 1-4 scale
    overall_profile: str          # "optimal", "facilitative", "debilitative", "mixed"
    interpretation: str
    strategies: list[str]
    evidence: str


@dataclass
class MentalFatigueAssessment:
    fatigue_score: float          # 0-10
    fatigue_level: str            # "low", "moderate", "high", "severe"
    performance_impact_pct: float # estimated % decrement
    contributing_factors: list[str]
    recovery_strategies: list[str]
    training_modifications: list[str]
    evidence: str


@dataclass
class BurnoutAssessment:
    stress_score: float           # 0-6 scale
    recovery_score: float         # 0-6 scale
    balance_ratio: float          # recovery/stress
    risk_level: str               # "low", "moderate", "high", "critical"
    risk_factors: list[str]
    intervention_strategies: list[str]
    evidence: str


@dataclass
class VisualizationProtocol:
    name: str
    purpose: str
    modalities: list[str]         # visual, kinesthetic, auditory, emotional
    script: list[str]             # step-by-step instructions
    duration_minutes: int
    frequency: str
    evidence: str
    key_references: list[str]


@dataclass
class PreCompetitionRoutine:
    time_to_event: str
    physical_actions: list[str]
    mental_actions: list[str]
    nutrition_timing: list[str]
    cue_words: list[str]
    contingency_plans: list[str]
    evidence: str


# ── Visualization Protocol Database ─────────────────────────────────────────

VISUALIZATION_DB: dict[str, VisualizationProtocol] = {
    "performance_rehearsal": VisualizationProtocol(
        name="Performance Rehearsal Imagery",
        purpose="Mentally rehearse successful execution of sport-specific skills and competition scenarios",
        modalities=["visual (first-person)", "kinesthetic (muscle sensation)", "auditory (crowd, coach cues)", "emotional (confidence, focus)"],
        script=[
            "Find a quiet space. Close your eyes. Take 5 slow, deep breaths.",
            "Visualize yourself at the competition venue — see the details (colors, lighting, equipment).",
            "Feel your body in your sport stance — weight balanced, muscles activated.",
            "Run through your warm-up sequence in real time — feel each movement.",
            "Now visualize your key performance moments — see yourself executing perfectly.",
            "Feel the confidence and flow as you perform at your best.",
            "If a mistake occurs in the imagery, re-run from before the mistake — always end successfully.",
            "Hear the sounds of competition — crowd, referee, teammates.",
            "Visualize the final moment — successful completion. Feel the satisfaction.",
            "Open your eyes. Take 3 deep breaths. Carry the confidence into your preparation.",
        ],
        duration_minutes=10,
        frequency="Daily for 2 weeks pre-competition; 1-2x/week during regular training",
        evidence="🟢 Strong — Cumming J & Williams SE (2012) Imagery in Sport; Vealey & Greenleaf (2010)",
        key_references=[
            "Cumming J & Williams SE (2012) — Imagery use in sport",
            "Vealey RS & Greenleaf CA (2010) — Imagery training for performance enhancement",
            "Holmes PS & Collins DJ (2001) J Appl Sport Psychol — PETTLEP model of motor imagery",
        ],
    ),
    "relaxation_imagery": VisualizationProtocol(
        name="Relaxation & Stress Reduction Imagery",
        purpose="Reduce pre-competition anxiety and promote optimal arousal state",
        modalities=["visual (calming scene)", "kinesthetic (muscle relaxation)", "auditory (peaceful sounds)", "emotional (calm, peace)"],
        script=[
            "Sit or lie comfortably. Close your eyes. Breathe slowly — 4 seconds in, 6 seconds out.",
            "Visualize your personal calm place — beach, forest, mountain, or anywhere you feel at peace.",
            "See the details — colors of sky, texture of ground, play of light.",
            "Hear the sounds — waves, wind, birds, silence.",
            "Feel the physical sensations — warmth, gentle breeze, solid ground beneath you.",
            "Scan your body from toes to head. With each exhale, release tension from each muscle group.",
            "Feel your shoulders drop, jaw unclench, hands open.",
            "Stay in this calm place for 3-5 minutes. Your breathing is slow and rhythmic.",
            "When ready, gradually bring awareness back. Maintain the feeling of calm as you open your eyes.",
        ],
        duration_minutes=8,
        frequency="Daily during high-stress periods; pre-competition (2-3h before event)",
        evidence="🟢 Strong — Kudlackova K et al. (2013) J Clin Sport Psychol; Williams SE & Cumming J (2011)",
        key_references=[
            "Kudlackova K et al. (2013) J Clin Sport Psychol — Relaxation imagery effectiveness",
            "Williams SE & Cumming J (2011) — Imagery and anxiety in sport",
        ],
    ),
    "confidence_building": VisualizationProtocol(
        name="Confidence Building Imagery",
        purpose="Build self-efficacy by mentally reliving peak performance moments",
        modalities=["visual (highlights reel)", "kinesthetic (peak performance feelings)", "emotional (pride, confidence)"],
        script=[
            "Close your eyes. Think of 3 moments in your career when you performed at your absolute best.",
            "Relive the FIRST moment — see it in vivid detail, first-person perspective.",
            "Feel the physical sensations — the power, speed, control, precision.",
            "Notice the emotions — confidence, flow, invincibility.",
            "Now relive the SECOND peak moment — same vivid detail, feelings, emotions.",
            "Now the THIRD moment — your personal highlight reel.",
            "Create a single 'confidence cue' — a word or gesture that captures these feelings.",
            "Say or do the cue now while holding the peak performance feeling.",
            "Open your eyes. Use this cue before competition to access your confident state.",
        ],
        duration_minutes=7,
        frequency="3x/week during regular training; daily in competition week",
        evidence="🟡 Moderate — Calmels C et al. (2003) J Sport Exerc Psychol; Short SE et al. (2002)",
        key_references=[
            "Calmels C et al. (2003) J Sport Exerc Psychol — Imagery and self-confidence",
            "Short SE et al. (2002) — Sport Imagery Questionnaire",
        ],
    ),
    "injury_recovery": VisualizationProtocol(
        name="Injury Recovery Imagery",
        purpose="Accelerate healing and maintain neural pathways during injury rehabilitation",
        modalities=["visual (healing process)", "kinesthetic (healthy movement)", "emotional (patience, determination)"],
        script=[
            "Find a comfortable position that doesn't aggravate your injury. Close your eyes.",
            "Visualize the injured area. See the healing process occurring — cells regenerating, inflammation resolving.",
            "Imagine healthy blood flow bringing nutrients to the injury site.",
            "Visualize the tissue becoming stronger — new fibers forming, alignment improving.",
            "Now mentally perform your sport movements — see and feel yourself moving with full capacity.",
            "Execute key skills in your mind — maintain the neural pathways while your body heals.",
            "Feel the gradual return of strength, range of motion, and confidence.",
            "End by visualizing yourself fully recovered, competing at your best.",
        ],
        duration_minutes=12,
        frequency="2x daily during rehabilitation; reduce to 1x daily as returning to training",
        evidence="🟡 Moderate — Driediger M et al. (2006) J Appl Sport Psychol; Cupal DD & Brewer BW (2001)",
        key_references=[
            "Driediger M et al. (2006) J Appl Sport Psychol — Imagery during injury rehabilitation",
            "Cupal DD & Brewer BW (2001) — Imagery and knee rehabilitation",
        ],
    ),
}


# ── Core Functions ───────────────────────────────────────────────────────────

def assess_competition_anxiety(
    cognitive_anxiety: float,
    somatic_anxiety: float,
    self_confidence: float,
) -> AnxietyAssessment:
    """
    Assess pre-competition anxiety using CSAI-2R proxy scoring.

    Scales: 1.0-4.0 (low to high)
    - Cognitive anxiety: worry, negative self-talk, concentration disruption
    - Somatic anxiety: butterflies, muscle tension, elevated HR, sweating
    - Self-confidence: belief in ability to perform

    Optimal profile: moderate somatic + low cognitive + high confidence
    (Inverted-U / IZOF model)
    """
    if not all(1.0 <= v <= 4.0 for v in [cognitive_anxiety, somatic_anxiety, self_confidence]):
        raise ValueError("All scores must be between 1.0 and 4.0")

    # Profile classification
    if cognitive_anxiety <= 2.0 and self_confidence >= 3.0:
        if 1.5 <= somatic_anxiety <= 3.0:
            profile = "optimal"
            interpretation = (
                "Optimal arousal profile. Low cognitive anxiety with high self-confidence "
                "and moderate somatic arousal suggests readiness for peak performance. "
                "Somatic arousal is being interpreted as facilitative (energizing)."
            )
        else:
            profile = "facilitative"
            interpretation = (
                "Facilitative profile. Good cognitive-confidence balance. "
                "May need arousal regulation to reach optimal zone."
            )
    elif cognitive_anxiety >= 3.0 and self_confidence <= 2.0:
        profile = "debilitative"
        interpretation = (
            "Debilitative anxiety profile. High worry combined with low self-confidence "
            "is likely to impair performance. Cognitive restructuring and confidence-building "
            "strategies are strongly recommended."
        )
    else:
        profile = "mixed"
        interpretation = (
            "Mixed profile. Some anxiety indicators present but compensated by other factors. "
            "Focus on managing the highest concern area while maintaining strengths."
        )

    # Strategies based on profile
    strategies = []
    if cognitive_anxiety >= 2.5:
        strategies += [
            "Cognitive restructuring: Replace negative self-talk with task-focused cues",
            "Thought-stopping technique: Use a cue word ('focus', 'breathe') to interrupt worry",
            "Pre-performance routine: Structured warm-up to occupy cognitive resources",
        ]
    if somatic_anxiety >= 3.0:
        strategies += [
            "Progressive muscle relaxation (10 min pre-event)",
            "Diaphragmatic breathing: 4-count inhale, 6-count exhale",
            "Centering technique: Focus attention on center of gravity",
        ]
    if somatic_anxiety <= 1.5:
        strategies += [
            "Psyching-up strategies: Energizing music, power poses",
            "Quick-burst physical activation (jumping, sprinting)",
        ]
    if self_confidence <= 2.0:
        strategies += [
            "Confidence building imagery: Relive 3 peak performance moments",
            "Self-affirmation: Write 3 evidence-based reasons you will perform well",
            "Process goals: Focus on controllable execution, not outcome",
        ]
    if not strategies:
        strategies = [
            "Maintain current mental preparation routine",
            "Use pre-performance routine to anchor optimal state",
            "Brief check-in: rate cognitive/somatic/confidence before competition",
        ]

    return AnxietyAssessment(
        cognitive_anxiety=cognitive_anxiety,
        somatic_anxiety=somatic_anxiety,
        self_confidence=self_confidence,
        overall_profile=profile,
        interpretation=interpretation,
        strategies=strategies,
        evidence="🟢 Strong — Martens R et al. (1990) CSAI-2; Cox RH et al. (2003) CSAI-2R validation; "
                "Hanton S et al. (2008) interpretation of anxiety symptoms",
    )


def assess_mental_fatigue(
    subjective_fatigue: float,
    sleep_hours: float,
    training_load_rpe: float,
    life_stress: float = 3.0,
    screen_time_hours: float = 4.0,
) -> MentalFatigueAssessment:
    """
    Assess mental fatigue and estimate performance impact.

    subjective_fatigue: 0-10 VAS scale
    sleep_hours: hours of sleep per night (avg last 3 nights)
    training_load_rpe: average session RPE (1-10) × duration
    life_stress: 1-5 scale (1=minimal, 5=severe)
    screen_time_hours: daily non-training screen time
    """
    # Composite fatigue score (weighted)
    sleep_penalty = max(0, (7.5 - sleep_hours) * 1.5)  # penalty for <7.5h
    stress_factor = (life_stress - 1) * 0.5  # 0-2 range
    screen_factor = max(0, (screen_time_hours - 3) * 0.3)  # penalty for >3h

    fatigue_score = min(10.0, subjective_fatigue + sleep_penalty + stress_factor + screen_factor)
    fatigue_score = round(fatigue_score, 1)

    # Classification
    if fatigue_score <= 3:
        level = "low"
        impact = 0.0
    elif fatigue_score <= 5:
        level = "moderate"
        impact = round((fatigue_score - 3) * 2.5, 1)  # 0-5% decrement
    elif fatigue_score <= 7:
        level = "high"
        impact = round(5 + (fatigue_score - 5) * 5, 1)  # 5-15% decrement
    else:
        level = "severe"
        impact = round(15 + (fatigue_score - 7) * 5, 1)  # 15-30% decrement

    # Contributing factors
    factors = []
    if subjective_fatigue >= 6:
        factors.append("High subjective mental fatigue")
    if sleep_hours < 7:
        factors.append(f"Insufficient sleep ({sleep_hours}h — target 7-9h)")
    if life_stress >= 4:
        factors.append("High life stress load")
    if screen_time_hours > 6:
        factors.append(f"Excessive screen time ({screen_time_hours}h/day)")
    if training_load_rpe > 7:
        factors.append("High training monotony / load")
    if not factors:
        factors.append("No significant contributing factors identified")

    # Recovery strategies
    recovery = [
        "Prioritize sleep: 8-9h per night for 3+ consecutive nights",
    ]
    if sleep_hours < 7:
        recovery.append("Sleep extension: aim for 9h for 1 week (sleep banking)")
    if subjective_fatigue >= 5:
        recovery.append("Mental recovery day: light physical activity + enjoyable non-sport activities")
    if life_stress >= 3:
        recovery.append("Stress management: journaling, mindfulness, or counseling")
    if screen_time_hours > 5:
        recovery.append("Digital detox: limit recreational screen time to <2h/day")
    recovery.append("Caffeine nap: 200mg caffeine + 20-min nap for acute cognitive boost")
    recovery.append("Nature exposure: 20 min outdoor walking (attention restoration theory)")

    # Training modifications
    training_mods = []
    if level == "low":
        training_mods = ["Normal training — monitor for accumulation"]
    elif level == "moderate":
        training_mods = [
            "Reduce cognitive demands in training (simplify drills)",
            "Avoid introducing new complex skills",
            "RPE-based intensity (may feel harder at same power/pace)",
        ]
    elif level == "high":
        training_mods = [
            "Reduce training volume by 20-30%",
            "No high-cognitive-load sessions (tactical, decision-making)",
            "Avoid monotonous long-duration sessions",
            "Add variety and enjoyment-focused activities",
        ]
    else:
        training_mods = [
            "Rest day or light active recovery only",
            "No competition or testing",
            "Reassess after 48-72h of recovery",
            "Consider short training break (3-5 days) if persistent",
        ]

    return MentalFatigueAssessment(
        fatigue_score=fatigue_score,
        fatigue_level=level,
        performance_impact_pct=impact,
        contributing_factors=factors,
        recovery_strategies=recovery,
        training_modifications=training_mods,
        evidence="🟡 Moderate — Van Cutsem J et al. (2017) Sports Med — Mental fatigue meta-analysis; "
                "Russell S et al. (2019) — Mental fatigue in team sports",
    )


def assess_burnout(
    stress_scores: dict[str, float],
    recovery_scores: dict[str, float],
) -> BurnoutAssessment:
    """
    Assess burnout risk using REST-Q style stress-recovery balance.

    stress_scores: dict with keys like "general_stress", "emotional_stress",
        "social_stress", "training_stress", "injury_concern" (each 0-6)
    recovery_scores: dict with keys like "sleep_quality", "social_recovery",
        "physical_recovery", "general_wellbeing", "self_efficacy" (each 0-6)
    """
    # Compute means
    stress_values = list(stress_scores.values())
    recovery_values = list(recovery_scores.values())

    avg_stress = sum(stress_values) / max(len(stress_values), 1)
    avg_recovery = sum(recovery_values) / max(len(recovery_values), 1)

    # Balance ratio (higher = better)
    balance = round(avg_recovery / max(avg_stress, 0.1), 2)

    # Risk level
    if balance >= 1.5 and avg_stress <= 2.5:
        risk_level = "low"
    elif balance >= 1.0 and avg_stress <= 3.5:
        risk_level = "moderate"
    elif balance >= 0.7 or avg_stress <= 4.5:
        risk_level = "high"
    else:
        risk_level = "critical"

    # Identify risk factors
    risk_factors = []
    for key, val in stress_scores.items():
        if val >= 4.0:
            risk_factors.append(f"High {key.replace('_', ' ')} ({val}/6)")
    for key, val in recovery_scores.items():
        if val <= 2.0:
            risk_factors.append(f"Low {key.replace('_', ' ')} ({val}/6)")
    if not risk_factors:
        risk_factors.append("No specific risk factors above threshold")

    # Interventions
    interventions = []
    if risk_level == "low":
        interventions = [
            "Maintain current approach — good stress-recovery balance",
            "Periodic check-in (monthly REST-Q monitoring)",
        ]
    elif risk_level == "moderate":
        interventions = [
            "Increase recovery activities: social, sleep, leisure",
            "Monitor weekly for trend changes",
            "Discuss training load with coach",
            "Ensure 1-2 complete rest days per week",
        ]
    elif risk_level == "high":
        interventions = [
            "Reduce training load by 20-30%",
            "Add structured recovery activities daily",
            "Sport psychology consultation recommended",
            "Address specific high-stress areas identified",
            "Sleep optimization protocol (8-9h target)",
            "Social support engagement",
        ]
    else:
        interventions = [
            "URGENT: Immediate training load reduction (50%+)",
            "Sport psychology referral — burnout management program",
            "Physician screening for overtraining syndrome (hormonal, immune markers)",
            "Structured break from competition (2-4 weeks minimum)",
            "Reconnect with intrinsic motivation for sport",
            "Address life stressors (academic, relationship, financial)",
        ]

    return BurnoutAssessment(
        stress_score=round(avg_stress, 2),
        recovery_score=round(avg_recovery, 2),
        balance_ratio=balance,
        risk_level=risk_level,
        risk_factors=risk_factors,
        intervention_strategies=interventions,
        evidence="🟢 Strong — Kellmann M & Kallus KW (2001) REST-Q; Raedeke TD (1997) — Burnout in sport",
    )


def get_visualization_protocol(protocol_type: str) -> VisualizationProtocol | None:
    """Look up a visualization protocol by type."""
    key = protocol_type.lower().strip().replace("-", "_").replace(" ", "_")
    return VISUALIZATION_DB.get(key)


def list_visualization_protocols() -> str:
    """List all available visualization protocols."""
    lines = ["═══ Kiwi Visualization Protocol Database ═══", ""]
    for key, proto in VISUALIZATION_DB.items():
        lines.append(f"  [{key}]")
        lines.append(f"    {proto.name}")
        lines.append(f"    Purpose: {proto.purpose}")
        lines.append(f"    Duration: {proto.duration_minutes} min | Frequency: {proto.frequency}")
        lines.append(f"    Evidence: {proto.evidence}")
        lines.append("")
    lines.append(f"  Total: {len(VISUALIZATION_DB)} protocols")
    return "\n".join(lines)


def generate_pre_competition_routine(
    hours_before: float = 3.0,
    sport: str = "general",
    anxiety_level: str = "moderate",
) -> PreCompetitionRoutine:
    """
    Generate a structured pre-competition routine.

    hours_before: time until competition start
    sport: sport type for context
    anxiety_level: "low", "moderate", "high"
    """
    time_to = f"{hours_before}h before event"

    # Physical actions (timeline)
    physical = []
    if hours_before >= 3:
        physical.append("T-3h: Light breakfast/snack (familiar foods only)")
    if hours_before >= 2:
        physical.append("T-2h: Begin physical warm-up (15-20 min light cardio)")
        physical.append("T-2h: Dynamic stretching routine")
    if hours_before >= 1:
        physical.append("T-1h: Sport-specific warm-up drills (progressive intensity)")
        physical.append("T-1h: Activation exercises (3-4 reps at competition intensity)")
    physical.append("T-15min: Final physical preparation (strides, practice shots, etc.)")
    physical.append("T-5min: Centering breath + body scan")

    # Mental actions
    mental = []
    if hours_before >= 2:
        mental.append("T-2h: Visualization session (5 min — see successful performance)")
    mental.append("T-1h: Review process goals (3 specific, controllable focus points)")
    mental.append("T-30min: Listening to pre-performance playlist (if part of routine)")

    if anxiety_level == "high":
        mental.append("T-20min: Progressive muscle relaxation (5 min)")
        mental.append("T-10min: Diaphragmatic breathing (4-6 pattern)")
        mental.append("T-5min: Power pose + affirmation statements")
    elif anxiety_level == "low":
        mental.append("T-15min: Energizing self-talk + activation imagery")
        mental.append("T-10min: Competitive mindset activation (recall key rivals)")
    else:
        mental.append("T-15min: Centering technique (focus on process)")
        mental.append("T-5min: Confidence cue word + deep breath")

    # Nutrition timing
    nutrition = [
        "T-3h: Pre-competition meal (1-2g/kg carbs, low fat, familiar)",
        "T-1h: Small snack if needed (banana, sports drink, energy bar)",
        "T-30min: Sip water/sports drink (200-300mL)",
    ]
    if hours_before >= 1:
        nutrition.append("T-45min: Caffeine if habitual (3-6mg/kg — already taken)")

    # Cue words
    cues = ["Focus", "Strong", "Trust", "Execute"]
    if anxiety_level == "high":
        cues = ["Breathe", "Calm", "Ready", "Trust the process"]
    elif anxiety_level == "low":
        cues = ["Attack", "Power", "Compete", "Go time"]

    # Contingency plans
    contingencies = [
        "If anxious: 3 deep breaths + refocus on process goals",
        "If distracted: cue word + return to routine",
        "If poor warm-up: remind yourself warm-up ≠ performance",
        "If opponent looks strong: focus on YOUR execution, not theirs",
        "If weather/conditions change: accept and adapt — 'same for everyone'",
    ]

    return PreCompetitionRoutine(
        time_to_event=time_to,
        physical_actions=physical,
        mental_actions=mental,
        nutrition_timing=nutrition,
        cue_words=cues,
        contingency_plans=contingencies,
        evidence="🟡 Moderate — Weinberg RS & Gould D (2019) — Foundations of Sport Psychology; "
                "Cotterill S (2010) — Pre-performance routines in sport",
    )


# ── Formatting Functions ─────────────────────────────────────────────────────

def format_anxiety_report(assessment: AnxietyAssessment) -> str:
    """Human-readable anxiety assessment."""
    lines = [
        "═══ Competition Anxiety Assessment ═══",
        "",
        f"  Cognitive Anxiety:  {assessment.cognitive_anxiety}/4.0",
        f"  Somatic Anxiety:    {assessment.somatic_anxiety}/4.0",
        f"  Self-Confidence:    {assessment.self_confidence}/4.0",
        f"  Profile:            {assessment.overall_profile.upper()}",
        "",
        "── Interpretation ──",
        f"  {assessment.interpretation}",
        "",
        "── Strategies ──",
    ]
    for s in assessment.strategies:
        lines.append(f"  • {s}")
    lines += ["", "── Evidence ──", f"  {assessment.evidence}"]
    return "\n".join(lines)


def format_burnout_report(assessment: BurnoutAssessment) -> str:
    """Human-readable burnout assessment."""
    lines = [
        "═══ Burnout Risk Assessment ═══",
        "",
        f"  Stress Score:    {assessment.stress_score}/6.0",
        f"  Recovery Score:  {assessment.recovery_score}/6.0",
        f"  Balance Ratio:   {assessment.balance_ratio}",
        f"  Risk Level:      {assessment.risk_level.upper()}",
        "",
        "── Risk Factors ──",
    ]
    for f in assessment.risk_factors:
        lines.append(f"  ⚠ {f}")
    lines += ["", "── Interventions ──"]
    for i in assessment.intervention_strategies:
        lines.append(f"  • {i}")
    lines += ["", "── Evidence ──", f"  {assessment.evidence}"]
    return "\n".join(lines)


def format_visualization(proto: VisualizationProtocol) -> str:
    """Human-readable visualization protocol."""
    lines = [
        f"═══ {proto.name} ═══",
        f"  Purpose: {proto.purpose}",
        f"  Duration: {proto.duration_minutes} min",
        f"  Frequency: {proto.frequency}",
        "",
        "── Modalities ──",
    ]
    for m in proto.modalities:
        lines.append(f"  • {m}")
    lines += ["", "── Script ──"]
    for i, step in enumerate(proto.script, 1):
        lines.append(f"  {i}. {step}")
    lines += ["", "── Evidence ──", f"  {proto.evidence}"]
    return "\n".join(lines)
