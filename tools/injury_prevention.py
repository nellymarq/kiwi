"""
Injury prevention and return-to-sport tools for Kiwi.

Evidence-based injury risk assessment, workload monitoring, and prevention protocols:
- Acute:Chronic Workload Ratio (ACWR) calculation (Gabbett 2016)
- Ten Percent Rule for load progression
- Functional Movement Screen (FMS) scoring and composite analysis
- Overuse risk screening (youth and adult athletes)
- Prevention protocol database (8+ evidence-based programs)
- Return-to-sport decision framework

References:
- Gabbett TJ (2016) Br J Sports Med — ACWR and injury risk
- Cook G et al. (2006) NAJSPT — Functional Movement Screen
- Myer GD et al. (2011) Sports Health — Youth athlete overuse prevention
- van der Horst N et al. (2015) Br J Sports Med — Nordic hamstring protocol
- Thorborg K et al. (2017) Br J Sports Med — Copenhagen adductor protocol
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InjuryRiskAssessment:
    sport: str
    age: int
    training_history: str
    risk_level: str
    risk_factors: list[str]
    recommendations: list[str]
    evidence: str


@dataclass
class ACWRResult:
    acute_load: float
    chronic_load: float
    ratio: float
    risk_zone: str
    recommendation: str
    evidence: str


@dataclass
class FMSScore:
    movement: str
    score: int
    compensations: list[str]
    corrective_exercises: list[str]


@dataclass
class PreventionProtocol:
    name: str
    target_injury: str
    exercises: list[str]
    frequency: str
    duration: str
    evidence: str
    sport_specific_notes: dict[str, str]
    key_references: list[str]


# ── FMS Corrective Exercise Database ─────────────────────────────────────────

FMS_CORRECTIVES: dict[str, dict] = {
    "deep_squat": {
        "compensations": [
            "Heel rise", "Forward trunk lean", "Knee valgus",
            "Arms fall forward", "Loss of lumbar lordosis",
        ],
        "correctives": [
            "Goblet squat to box", "Ankle mobility drills (wall stretch)",
            "Thoracic spine foam rolling", "Hip flexor stretch",
            "Bodyweight squat with heel elevation",
        ],
    },
    "hurdle_step": {
        "compensations": [
            "Trunk lean", "Hip hike", "Loss of balance",
            "Toe-out on stance leg", "Knee valgus on stance leg",
        ],
        "correctives": [
            "Single-leg stance holds", "Hip flexor marching",
            "Mini-band lateral walks", "Standing hip flexion with band",
            "Single-leg RDL progressions",
        ],
    },
    "inline_lunge": {
        "compensations": [
            "Loss of balance", "Trunk rotation", "Knee valgus",
            "Rear foot lifts", "Forward trunk lean",
        ],
        "correctives": [
            "Split squat with dowel", "Half-kneeling chops and lifts",
            "Lateral band walks", "Rear-foot elevated split squat",
            "Inline lunge with TRX assist",
        ],
    },
    "shoulder_mobility": {
        "compensations": [
            "Inability to touch fists", "Excessive lumbar extension",
            "Shoulder pain", "Scapular winging",
        ],
        "correctives": [
            "Sleeper stretch", "Doorway pec stretch",
            "Thoracic spine rotation on foam roller",
            "Band pull-aparts", "Wall slides",
        ],
    },
    "active_straight_leg_raise": {
        "compensations": [
            "Contralateral leg lifts", "Pelvis rotates",
            "Low back arches", "Knee bends on moving leg",
        ],
        "correctives": [
            "Active hamstring stretch with strap",
            "Supine leg lowering with core engagement",
            "Hip flexor stretch (half-kneeling)",
            "Dead bug progressions", "Single-leg hip bridge",
        ],
    },
    "trunk_stability_pushup": {
        "compensations": [
            "Low back sags", "Hips rise first", "Inability to perform",
            "Asymmetric push pattern",
        ],
        "correctives": [
            "Plank progressions (front, side)",
            "Dead bug variations", "Bird-dog holds",
            "Push-up from knees with neutral spine",
            "Tall-kneeling Pallof press",
        ],
    },
    "rotary_stability": {
        "compensations": [
            "Loss of balance", "Trunk rotation during movement",
            "Inability to perform diagonal pattern",
            "Excessive lateral shift",
        ],
        "correctives": [
            "Quadruped rocking", "Bird-dog progressions",
            "Half-kneeling cable chops", "Pallof press variations",
            "Bear crawl holds and movement",
        ],
    },
}

FMS_VALID_MOVEMENTS = list(FMS_CORRECTIVES.keys())


# ── Prevention Protocol Database ─────────────────────────────────────────────

PROTOCOL_DB: dict[str, PreventionProtocol] = {

    "acl": PreventionProtocol(
        name="FIFA 11+ Neuromuscular Warm-Up",
        target_injury="Anterior Cruciate Ligament (ACL) Tear",
        exercises=[
            "Running straight ahead with hip-out and hip-in",
            "Running with partner contact (shoulder)",
            "Nordic hamstring curls (3 × 10)",
            "Single-leg balance on unstable surface (3 × 30s each leg)",
            "Lateral bounding (3 × 8 each direction)",
            "Box jumps with soft landing emphasis (3 × 8)",
            "Single-leg squat with valgus control (3 × 10 each leg)",
            "Plank variations — front and side (3 × 30s each)",
            "Plyometric jump-cut drills with deceleration focus",
        ],
        frequency="2–3 sessions per week as warm-up (20 min)",
        duration="Ongoing throughout season; minimum 10 weeks pre-season",
        evidence="🟢 Strong — 50–70% reduction in ACL injuries (Thorborg meta-analysis 2017)",
        sport_specific_notes={
            "soccer": "Developed specifically for soccer; strongest evidence base in this sport",
            "basketball": "Emphasize landing mechanics from jumps and cutting drills",
            "skiing": "Add ski-specific balance drills on wobble board",
            "handball": "Include overhead reaching and pivot-specific patterns",
            "general": "Effective across all field and court sports with cutting/pivoting demands",
        },
        key_references=[
            "Soligard T et al. (2008) BMJ — FIFA 11+ effectiveness",
            "Thorborg K et al. (2017) Br J Sports Med — Neuromuscular training meta-analysis",
            "Myer GD et al. (2013) Am J Sports Med — ACL prevention in female athletes",
        ],
    ),

    "ankle_sprain": PreventionProtocol(
        name="Balance and Proprioception Training Program",
        target_injury="Lateral Ankle Sprain",
        exercises=[
            "Single-leg stance eyes open → eyes closed (3 × 30s each leg)",
            "BOSU ball balance drills (3 × 45s each leg)",
            "Star excursion balance test drills (3 × 6 directions each leg)",
            "Wobble board multi-directional balance (3 × 60s)",
            "Single-leg hop and stabilize — forward, lateral, diagonal (3 × 5 each)",
            "Resistance band ankle eversion/inversion (3 × 15 each direction)",
            "Calf raises — bilateral and single-leg (3 × 15)",
            "Sport-specific agility ladder drills with balance focus",
        ],
        frequency="3–5 sessions per week (10–15 min per session)",
        duration="Minimum 6 weeks; ongoing for athletes with prior sprains",
        evidence="🟢 Strong — 35–50% reduction in ankle sprain recurrence (Verhagen 2004)",
        sport_specific_notes={
            "basketball": "Focus on landing mechanics from layups and rebounds; consider ankle bracing",
            "soccer": "Emphasize single-leg stability on uneven surfaces",
            "volleyball": "Landing drills from block and attack positions",
            "trail_running": "Progressively uneven surface training; trail-specific balance",
            "general": "Prior ankle sprain is strongest risk factor; proprioception deficits persist >1 year",
        },
        key_references=[
            "Verhagen E et al. (2004) Br J Sports Med — Proprioceptive balance board training",
            "Doherty C et al. (2017) Sports Med — Recurrent ankle sprain prevention meta-analysis",
            "Hupperets MD et al. (2009) BMJ — Proprioceptive training after ankle sprain",
        ],
    ),

    "hamstring": PreventionProtocol(
        name="Nordic Hamstring Curl Protocol",
        target_injury="Hamstring Strain Injury",
        exercises=[
            "Nordic hamstring curl — eccentric focus (3–4 × 5–12, progressive over 10 weeks)",
            "Romanian deadlift — single and bilateral (3 × 8–12)",
            "Hip bridge with hamstring walkout (3 × 8)",
            "Single-leg hip bridge with hold (3 × 10 each, 3s hold)",
            "Supine slider leg curl (3 × 10)",
            "Standing single-leg hamstring curl with band (3 × 12 each)",
            "High-speed running exposure (progressive sprinting program)",
        ],
        frequency="2–3 sessions per week (Nordic curls: start 1×/wk, progress to 3×/wk)",
        duration="Minimum 10 weeks pre-season; maintain 1×/week in-season",
        evidence="🟢 Strong — 51% reduction in hamstring injuries (van der Horst 2015)",
        sport_specific_notes={
            "soccer": "Highest hamstring injury rate of all sports; Nordics reduce first-time and recurrent injuries",
            "sprinting": "Add progressive high-speed running exposure; eccentric strength critical at long muscle lengths",
            "australian_football": "Strong evidence in AFL; compliance is key factor for effectiveness",
            "rugby": "Include in pre-season; combine with high-speed running progressions",
            "general": "Previous hamstring injury is strongest risk factor; eccentric weakness is modifiable",
        },
        key_references=[
            "van der Horst N et al. (2015) Br J Sports Med — Nordic hamstring RCT",
            "Al Attar WS et al. (2017) Br J Sports Med — Hamstring injury prevention meta-analysis",
            "Bourne MN et al. (2018) Br J Sports Med — Eccentric knee flexor strength and hamstring injury",
        ],
    ),

    "shoulder": PreventionProtocol(
        name="Rotator Cuff Prehabilitation Program",
        target_injury="Shoulder Impingement / Rotator Cuff Injury",
        exercises=[
            "External rotation with band at 0° abduction (3 × 15)",
            "External rotation with band at 90° abduction (3 × 12)",
            "Side-lying external rotation with dumbbell (3 × 12)",
            "Prone Y-T-W raises (3 × 10 each position)",
            "Serratus anterior wall slides (3 × 12)",
            "Lower trapezius activation — prone horizontal abduction (3 × 12)",
            "Scapular push-ups (3 × 15)",
            "Cross-body posterior shoulder stretch (3 × 30s each side)",
        ],
        frequency="3–4 sessions per week (10–15 min per session)",
        duration="Ongoing throughout season; intensify pre-season for overhead athletes",
        evidence="🟡 Moderate — 28–40% reduction in shoulder injuries in overhead athletes (Andersson 2017)",
        sport_specific_notes={
            "swimming": "Focus on scapular stability; internal rotation stretching; high volume shoulders are at risk",
            "baseball": "Emphasize external rotation strength; maintain total arc of motion; pitch count compliance",
            "volleyball": "Scapular dyskinesis screening; focus on deceleration strength",
            "tennis": "Eccentric rotator cuff work; thoracic mobility emphasis",
            "crossfit": "Overhead stability and endurance; strict form before kipping",
            "general": "Scapular stability is foundation; address thoracic mobility before rotator cuff isolation",
        },
        key_references=[
            "Andersson SH et al. (2017) Br J Sports Med — Shoulder injury prevention in handball",
            "Cools AM et al. (2015) Br J Sports Med — Shoulder rehabilitation framework",
            "Wilk KE et al. (2011) J Am Acad Orthop Surg — Shoulder rehab in overhead athletes",
        ],
    ),

    "shin_splints": PreventionProtocol(
        name="Gradual Loading and Calf Strengthening Program",
        target_injury="Medial Tibial Stress Syndrome (Shin Splints)",
        exercises=[
            "Calf raises — bilateral (3 × 20, progress to single-leg)",
            "Single-leg calf raises — straight knee and bent knee (3 × 15 each)",
            "Toe walks and heel walks (3 × 20m each)",
            "Tibialis anterior raises (dorsiflexion against band) (3 × 20)",
            "Single-leg hop progressions (3 × 10 each leg)",
            "Foam rolling — posterior and lateral compartments (2 min each leg)",
            "Eccentric heel drops off step (3 × 15, slow 3-count descent)",
        ],
        frequency="Daily calf work during build-up phases; 3×/week maintenance",
        duration="Minimum 6 weeks before increasing running volume; ongoing during training",
        evidence="🟡 Moderate — Load management strongest evidence; calf strengthening supportive (Winters 2019)",
        sport_specific_notes={
            "running": "10% rule for weekly mileage increase; transition to minimalist shoes gradually (>8 weeks)",
            "military": "Gradual marching load progression; avoid sudden increases in ruck weight",
            "basketball": "Court surface and shoe cushioning matter; monitor jump-landing volumes",
            "dancing": "Address turnout mechanics; progressive pointe work loading",
            "general": "Most common overuse injury in runners; load management is primary prevention strategy",
        },
        key_references=[
            "Winters M et al. (2019) Br J Sports Med — MTSS prevention and treatment",
            "Moen MH et al. (2012) Sports Med — MTSS risk factors and prevention",
            "Nielsen RO et al. (2014) Br J Sports Med — Running load and injury risk",
        ],
    ),

    "stress_fracture": PreventionProtocol(
        name="Load Management and Bone Health Program",
        target_injury="Stress Fracture",
        exercises=[
            "Progressive impact loading — walk → jog → run (graduated over 4–6 weeks)",
            "Plyometric progressions — bilateral → unilateral (2–3 × 8–12)",
            "Single-leg hop for distance and height (3 × 5 each leg)",
            "Resistance training for lower extremity — squats, deadlifts, lunges (3 × 8–12)",
            "Calf raises — bilateral and single-leg (3 × 15–20)",
            "Balance and proprioception drills (3 × 30s each leg)",
        ],
        frequency="Resistance training 2–3×/week; impact loading progressive daily",
        duration="Ongoing load management; bone adaptation requires 12+ weeks",
        evidence="🟡 Moderate — Load management is primary prevention; calcium/vitamin D supportive (Warden 2014)",
        sport_specific_notes={
            "running": "Avoid >30% weekly volume increases; bone stress injury most common 4–6 weeks into new program",
            "military": "Structured running programs reduce stress fracture rates by 50% vs ad hoc training",
            "ballet": "Monitor RED-S indicators; low energy availability is primary risk factor",
            "triathlon": "Multi-sport loading is additive; monitor cumulative impact not just running volume",
            "general": "Calcium 1500mg/d + vitamin D 2000–4000 IU/d for at-risk athletes; address energy availability",
        },
        key_references=[
            "Warden SJ et al. (2014) Br J Sports Med — Stress fracture management framework",
            "Mountjoy M et al. (2018) Br J Sports Med — IOC RED-S consensus statement",
            "Tenforde AS et al. (2016) Sports Med — Bone stress injuries in runners",
        ],
    ),

    "groin": PreventionProtocol(
        name="Copenhagen Adductor Strengthening Protocol",
        target_injury="Groin / Adductor Strain",
        exercises=[
            "Copenhagen adductor exercise — partner-assisted (3 × 6–15, progressive over 8 weeks)",
            "Side-lying hip adduction with band (3 × 15 each side)",
            "Sumo squat / wide-stance squat (3 × 12)",
            "Lateral lunges (3 × 10 each side)",
            "Single-leg squat with adductor focus (3 × 8 each side)",
            "Adductor squeeze — supine with ball (3 × 10, 5s holds)",
            "Skating / slide board drills (3 × 30s intervals)",
        ],
        frequency="2–3 sessions per week; start 1×/week and progress",
        duration="Minimum 8 weeks pre-season; maintain 1–2×/week in-season",
        evidence="🟢 Strong — 41% reduction in groin injuries (Harøy 2019)",
        sport_specific_notes={
            "soccer": "Groin injuries account for 10–18% of all injuries; Copenhagen protocol highly effective",
            "ice_hockey": "High adductor demands from skating stride; pre-season adductor:abductor ratio screening",
            "australian_football": "Kicking and change-of-direction demands; monitor hip adductor squeeze strength",
            "rugby": "Combine with hip flexor and core stability work",
            "general": "Adductor weakness relative to abductors is primary modifiable risk factor",
        },
        key_references=[
            "Harøy J et al. (2019) Br J Sports Med — Copenhagen adductor exercise RCT",
            "Thorborg K et al. (2017) Br J Sports Med — Adductor strengthening for groin injury prevention",
            "Hölmich P et al. (2010) Lancet — Groin pain in athletes",
        ],
    ),

    "tennis_elbow": PreventionProtocol(
        name="Eccentric Wrist Extension Protocol",
        target_injury="Lateral Epicondylitis (Tennis Elbow)",
        exercises=[
            "Eccentric wrist extension with dumbbell (3 × 15, slow 3-count lowering)",
            "Wrist flexion curls with light dumbbell (3 × 15)",
            "Forearm pronation/supination with hammer (3 × 15 each direction)",
            "Grip strengthening — squeezing rubber ball or grip trainer (3 × 15)",
            "Tyler Twist with FlexBar (3 × 15, progressive resistance)",
            "Wrist extensor stretch (3 × 30s holds)",
            "Eccentric radial deviation with band (3 × 12)",
        ],
        frequency="Daily eccentric exercises; 3×/week resistance exercises",
        duration="Minimum 6–12 weeks for tendon adaptation; ongoing for at-risk athletes",
        evidence="🟡 Moderate — Eccentric loading superior to wait-and-see (Pienimäki 1996; Tyler 2006)",
        sport_specific_notes={
            "tennis": "Backhand technique correction; grip size optimization; racquet vibration dampening",
            "golf": "Address grip pressure and swing mechanics; medial epicondylitis also common (golfer's elbow)",
            "climbing": "Progressive crimp and open-hand loading; monitor finger and wrist tendon stress",
            "weightlifting": "Neutral wrist position during pressing; avoid excessive wrist extension under load",
            "general": "Tendon adaptation slower than muscle; expect 6–12 weeks for structural changes",
        },
        key_references=[
            "Pienimäki TT et al. (1996) Lancet — Eccentric exercise for lateral epicondylitis",
            "Tyler TF et al. (2006) J Hand Ther — FlexBar eccentric exercise for lateral epicondylitis",
            "Coombes BK et al. (2010) BMJ — Corticosteroid vs eccentric exercise for tennis elbow",
        ],
    ),
}


# ── Aliases ──────────────────────────────────────────────────────────────────

PROTOCOL_ALIASES: dict[str, str] = {
    "anterior cruciate ligament": "acl",
    "acl tear": "acl",
    "acl injury": "acl",
    "knee ligament": "acl",
    "fifa 11+": "acl",
    "fifa 11": "acl",
    "neuromuscular warm-up": "acl",
    "ankle": "ankle_sprain",
    "lateral ankle sprain": "ankle_sprain",
    "ankle instability": "ankle_sprain",
    "sprained ankle": "ankle_sprain",
    "proprioception": "ankle_sprain",
    "hamstring strain": "hamstring",
    "hamstring injury": "hamstring",
    "hamstring pull": "hamstring",
    "nordic curl": "hamstring",
    "nordic hamstring": "hamstring",
    "rotator cuff": "shoulder",
    "shoulder impingement": "shoulder",
    "shoulder injury": "shoulder",
    "shoulder prehab": "shoulder",
    "swimmers shoulder": "shoulder",
    "medial tibial stress syndrome": "shin_splints",
    "mtss": "shin_splints",
    "shin pain": "shin_splints",
    "tibial stress": "shin_splints",
    "bone stress injury": "stress_fracture",
    "bsi": "stress_fracture",
    "stress reaction": "stress_fracture",
    "bone stress": "stress_fracture",
    "adductor strain": "groin",
    "groin strain": "groin",
    "groin injury": "groin",
    "copenhagen": "groin",
    "adductor": "groin",
    "hip adductor": "groin",
    "lateral epicondylitis": "tennis_elbow",
    "elbow tendinitis": "tennis_elbow",
    "lateral epicondylalgia": "tennis_elbow",
    "flexbar": "tennis_elbow",
    "wrist pain": "tennis_elbow",
}


# ── Sport-Specific Overuse Patterns ──────────────────────────────────────────

SPORT_OVERUSE_PATTERNS: dict[str, list[str]] = {
    "running": ["Shin splints (MTSS)", "Stress fractures", "Patellofemoral pain", "IT band syndrome", "Achilles tendinopathy"],
    "swimming": ["Shoulder impingement", "Rotator cuff tendinopathy", "Low back pain", "Knee pain (breaststroke)"],
    "baseball": ["UCL sprain (Tommy John)", "Rotator cuff injury", "Labral tear", "Little League elbow (youth)"],
    "basketball": ["Ankle sprains", "ACL tears", "Patellar tendinopathy", "Stress fractures"],
    "soccer": ["ACL tears", "Hamstring strains", "Groin injuries", "Ankle sprains", "Concussions"],
    "tennis": ["Tennis elbow (lateral epicondylitis)", "Shoulder impingement", "Wrist tendinitis", "Ankle sprains"],
    "gymnastics": ["Wrist pain / stress fractures", "Low back pain (spondylolysis)", "Ankle sprains", "Achilles tendinopathy"],
    "volleyball": ["Shoulder impingement", "Patellar tendinopathy (jumper's knee)", "Ankle sprains", "Finger injuries"],
    "cycling": ["Knee pain (patellofemoral)", "Low back pain", "Neck pain", "Ulnar neuropathy (handlebar palsy)"],
    "crossfit": ["Shoulder injuries", "Low back injuries", "Rhabdomyolysis risk", "Wrist strain"],
}


# ── Core Functions ───────────────────────────────────────────────────────────

def calculate_acwr(
    daily_loads: list[float],
    acute_window: int = 7,
    chronic_window: int = 28,
) -> ACWRResult:
    """
    Acute:Chronic Workload Ratio using EWMA for chronic load.

    Based on Gabbett TJ (2016) Br J Sports Med.
    Acute = rolling average of last `acute_window` days.
    Chronic = EWMA over `chronic_window` days (decay = 2 / (chronic_window + 1)).

    Risk zones:
      <0.8  — undertraining (detraining risk, spike vulnerability)
      0.8–1.3 — sweet spot (optimal adaptation)
      1.3–1.5 — caution (elevated injury risk)
      >1.5  — danger (high injury risk)
    """
    if not daily_loads:
        return ACWRResult(
            acute_load=0.0,
            chronic_load=0.0,
            ratio=0.0,
            risk_zone="insufficient data",
            recommendation="No load data provided. Begin tracking daily training loads.",
            evidence="🟢 Strong — Gabbett TJ (2016) Br J Sports Med",
        )

    if len(daily_loads) < acute_window:
        acute_load = sum(daily_loads) / len(daily_loads)
    else:
        acute_load = sum(daily_loads[-acute_window:]) / acute_window

    # EWMA for chronic load
    decay = 2.0 / (chronic_window + 1)
    ewma = daily_loads[0]
    for load in daily_loads[1:]:
        ewma = load * decay + ewma * (1 - decay)
    chronic_load = ewma

    if chronic_load == 0:
        ratio = 0.0
        risk_zone = "insufficient data"
        recommendation = "Chronic load is zero. Establish a training baseline before interpreting ACWR."
    else:
        ratio = round(acute_load / chronic_load, 2)

        if ratio < 0.8:
            risk_zone = "undertraining"
            recommendation = (
                "Workload is below optimal. Risk of detraining and vulnerability to load spikes. "
                "Gradually increase training load toward the 0.8–1.3 sweet spot."
            )
        elif ratio <= 1.3:
            risk_zone = "sweet spot"
            recommendation = (
                "Workload ratio is in the optimal zone. Continue current loading pattern. "
                "This range is associated with the lowest injury risk and best adaptation."
            )
        elif ratio <= 1.5:
            risk_zone = "caution"
            recommendation = (
                "Workload ratio is elevated. Injury risk is increasing. "
                "Consider reducing acute load or allowing more recovery. Monitor for fatigue symptoms."
            )
        else:
            risk_zone = "danger"
            recommendation = (
                "Workload ratio is dangerously high. Significantly elevated injury risk. "
                "Reduce training load immediately. Implement active recovery and monitor closely."
            )

    return ACWRResult(
        acute_load=round(acute_load, 2),
        chronic_load=round(chronic_load, 2),
        ratio=ratio,
        risk_zone=risk_zone,
        recommendation=recommendation,
        evidence="🟢 Strong — Gabbett TJ (2016) Br J Sports Med",
    )


def check_ten_percent_rule(current_load: float, previous_load: float) -> dict:
    """
    Check if load increase follows the 10% rule.

    Returns dict with increase_pct, safe (bool), and recommendation.
    If previous_load is zero, any increase is flagged as unsafe (no baseline).
    """
    if previous_load == 0:
        if current_load == 0:
            return {
                "increase_pct": 0.0,
                "safe": True,
                "recommendation": "No load recorded. Establish a baseline training load.",
            }
        return {
            "increase_pct": float("inf"),
            "safe": False,
            "recommendation": (
                "No previous load baseline. Any increase from zero is a spike. "
                "Start with conservative loading and build gradually."
            ),
        }

    increase_pct = round(((current_load - previous_load) / previous_load) * 100, 1)

    if increase_pct <= 10.0:
        return {
            "increase_pct": increase_pct,
            "safe": True,
            "recommendation": (
                f"Load increase of {increase_pct}% is within the 10% guideline. "
                "Safe to proceed with current progression."
            ),
        }
    else:
        return {
            "increase_pct": increase_pct,
            "safe": False,
            "recommendation": (
                f"Load increase of {increase_pct}% exceeds the 10% guideline. "
                "Consider reducing the increase to minimize injury risk. "
                "Rapid load spikes are associated with overuse injuries."
            ),
        }


def score_fms_movement(movement: str, score: int, notes: str = "") -> FMSScore:
    """
    Score a single FMS movement pattern.

    Movements: deep_squat, hurdle_step, inline_lunge, shoulder_mobility,
               active_straight_leg_raise, trunk_stability_pushup, rotary_stability

    Scores: 0 = pain during movement
            1 = unable to perform the movement pattern
            2 = performs with compensations
            3 = performs movement correctly (no compensations)
    """
    movement = movement.lower().strip().replace("-", "_").replace(" ", "_")

    if movement not in FMS_CORRECTIVES:
        raise ValueError(
            f"Unknown FMS movement: '{movement}'. "
            f"Valid movements: {', '.join(FMS_VALID_MOVEMENTS)}"
        )

    if not (0 <= score <= 3):
        raise ValueError(f"FMS score must be 0–3, got {score}")

    data = FMS_CORRECTIVES[movement]

    if score == 3:
        compensations = []
        corrective_exercises = []
    elif score == 2:
        compensations = data["compensations"][:3]
        corrective_exercises = data["correctives"][:3]
    elif score == 1:
        compensations = data["compensations"]
        corrective_exercises = data["correctives"]
    else:  # score == 0 (pain)
        compensations = ["Pain reported — refer for clinical evaluation"]
        corrective_exercises = ["Discontinue movement; refer to medical professional for assessment"]

    return FMSScore(
        movement=movement,
        score=score,
        compensations=compensations,
        corrective_exercises=corrective_exercises,
    )


def calculate_fms_composite(scores: dict[str, int]) -> dict:
    """
    Calculate FMS composite score and identify risk factors.

    Returns:
        composite_score: sum of all 7 movement scores (max 21)
        risk_level: "high injury risk" (<14), "moderate" (14–17), "low" (>17)
        asymmetries: list of movements with bilateral asymmetry (if applicable)
        priority_movements: movements scoring <=1 that need immediate attention
    """
    if not scores:
        raise ValueError("No FMS scores provided")

    valid_movements = set(FMS_VALID_MOVEMENTS)
    for movement in scores:
        normalized = movement.lower().strip().replace("-", "_").replace(" ", "_")
        if normalized not in valid_movements:
            raise ValueError(
                f"Unknown FMS movement: '{movement}'. "
                f"Valid movements: {', '.join(FMS_VALID_MOVEMENTS)}"
            )

    for score_val in scores.values():
        if not (0 <= score_val <= 3):
            raise ValueError(f"FMS score must be 0–3, got {score_val}")

    composite_score = sum(scores.values())

    if composite_score < 14:
        risk_level = "high injury risk"
    elif composite_score <= 17:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # Identify movements scored 0 or 1
    priority_movements = [
        movement for movement, score_val in scores.items() if score_val <= 1
    ]

    # Bilateral movements where asymmetry can be detected
    bilateral_movements = ["hurdle_step", "inline_lunge", "shoulder_mobility",
                           "active_straight_leg_raise", "rotary_stability"]
    asymmetries = [
        movement for movement in scores
        if movement in bilateral_movements and scores[movement] <= 1
    ]

    return {
        "composite_score": composite_score,
        "risk_level": risk_level,
        "asymmetries": asymmetries,
        "priority_movements": priority_movements,
    }


def screen_overuse_risk(
    sport: str,
    age: int,
    weekly_hours: float,
    specialization_age: int | None = None,
    injury_history: list[str] | None = None,
) -> InjuryRiskAssessment:
    """
    Screen for overuse injury risk in athletes.

    Rules:
    - Youth: weekly training hours should not exceed age (Jayanthi 2013)
    - Early sport specialization (<12 years) increases overuse risk
    - Sport-specific overuse patterns are flagged
    - Prior injury history compounds risk
    """
    risk_factors: list[str] = []
    recommendations: list[str] = []
    injury_history = injury_history or []

    # Youth hours rule
    is_youth = age < 18
    if is_youth and weekly_hours > age:
        risk_factors.append(
            f"Training hours ({weekly_hours}h/week) exceed age ({age}y) — "
            "Jayanthi guideline violation"
        )
        recommendations.append(
            f"Reduce weekly hours to ≤{age}h/week or ensure adequate rest days"
        )

    # Early specialization
    if specialization_age is not None and specialization_age < 12:
        risk_factors.append(
            f"Early sport specialization at age {specialization_age} (<12 years)"
        )
        recommendations.append(
            "Encourage multi-sport participation to reduce overuse risk and burnout"
        )

    # High volume flag (adults and youth)
    if weekly_hours > 20:
        risk_factors.append(f"Very high training volume ({weekly_hours}h/week)")
        recommendations.append("Monitor for signs of overtraining syndrome; ensure periodization")

    # Injury history
    if injury_history:
        risk_factors.append(f"Previous injuries: {', '.join(injury_history)}")
        recommendations.append("Address prior injury rehabilitation deficits; targeted prehab for injury sites")

    # Sport-specific patterns
    sport_lower = sport.lower().strip()
    overuse_patterns = SPORT_OVERUSE_PATTERNS.get(sport_lower, [])
    if overuse_patterns:
        risk_factors.append(f"Sport-specific risks ({sport}): {', '.join(overuse_patterns)}")
        recommendations.append(f"Screen for common {sport} overuse patterns; implement sport-specific prehab")

    # Determine risk level
    risk_score = len(risk_factors)
    if risk_score == 0:
        risk_level = "low"
        recommendations.append("Current risk profile is favorable. Maintain training load monitoring.")
    elif risk_score <= 2:
        risk_level = "moderate"
    else:
        risk_level = "high"

    training_history = f"{weekly_hours}h/week in {sport}"
    if specialization_age is not None:
        training_history += f", specialized at age {specialization_age}"

    return InjuryRiskAssessment(
        sport=sport,
        age=age,
        training_history=training_history,
        risk_level=risk_level,
        risk_factors=risk_factors,
        recommendations=recommendations,
        evidence="🟡 Moderate — Jayanthi N et al. (2013) Sports Health; Myer GD et al. (2011) Sports Health",
    )


def get_prevention_protocol(injury_type: str) -> PreventionProtocol | None:
    """Look up a prevention protocol by injury type or alias."""
    key = injury_type.lower().strip().replace("-", "_").replace(" ", "_")
    if key in PROTOCOL_DB:
        return PROTOCOL_DB[key]
    alias_key = PROTOCOL_ALIASES.get(injury_type.lower().strip())
    if alias_key and alias_key in PROTOCOL_DB:
        return PROTOCOL_DB[alias_key]
    return None


def return_to_sport_decision(
    injury: str,
    weeks_since: int,
    pain_level: int,
    strength_deficit_pct: float,
) -> dict:
    """
    Return-to-sport decision framework.

    Phases: acute → rehabilitation → return_to_training → return_to_competition
    Criteria: pain_free, strength_symmetry (>90%), sport_specific_function, psychological_readiness

    Args:
        injury: type of injury
        weeks_since: weeks since injury occurred
        pain_level: 0–10 VAS pain scale
        strength_deficit_pct: percentage deficit compared to uninjured side (0–100)
    """
    criteria_met: list[str] = []
    criteria_remaining: list[str] = []

    # Pain assessment
    if pain_level == 0:
        criteria_met.append("pain_free")
    elif pain_level <= 2:
        criteria_met.append("minimal_pain")
        criteria_remaining.append("pain_free (current: VAS {}/10)".format(pain_level))
    else:
        criteria_remaining.append("pain_free (current: VAS {}/10)".format(pain_level))

    # Strength symmetry (deficit < 10% means >90% symmetry)
    if strength_deficit_pct <= 10:
        criteria_met.append("strength_symmetry (>90%)")
    else:
        criteria_remaining.append(
            f"strength_symmetry (current deficit: {strength_deficit_pct}%, target: <10%)"
        )

    # Sport-specific function (inferred from pain and strength)
    if pain_level <= 1 and strength_deficit_pct <= 15:
        criteria_met.append("sport_specific_function")
    else:
        criteria_remaining.append("sport_specific_function")

    # Psychological readiness (inferred from timeline and pain)
    if pain_level == 0 and strength_deficit_pct <= 10 and weeks_since >= 4:
        criteria_met.append("psychological_readiness")
    else:
        criteria_remaining.append("psychological_readiness")

    # Determine phase
    if pain_level >= 5 or weeks_since < 1:
        phase = "acute"
        timeline_estimate = "4–8 weeks until return to training (injury-dependent)"
    elif pain_level >= 2 or strength_deficit_pct > 25:
        phase = "rehabilitation"
        timeline_estimate = "2–6 weeks until return to training"
    elif strength_deficit_pct > 10 or pain_level >= 1:
        phase = "return_to_training"
        timeline_estimate = "1–3 weeks until return to competition"
    else:
        phase = "return_to_competition"
        timeline_estimate = "Ready for graduated return to full competition"

    cleared = (
        phase == "return_to_competition"
        and pain_level == 0
        and strength_deficit_pct <= 10
    )

    return {
        "cleared": cleared,
        "phase": phase,
        "criteria_met": criteria_met,
        "criteria_remaining": criteria_remaining,
        "timeline_estimate": timeline_estimate,
    }


# ── Formatting Functions ─────────────────────────────────────────────────────

def format_acwr_report(result: ACWRResult) -> str:
    """Human-readable ACWR report."""
    zone_indicators = {
        "undertraining": "⬇️  UNDERTRAINING",
        "sweet spot": "✅  SWEET SPOT",
        "caution": "⚠️  CAUTION",
        "danger": "🚨  DANGER",
        "insufficient data": "❓  INSUFFICIENT DATA",
    }

    indicator = zone_indicators.get(result.risk_zone, result.risk_zone.upper())

    lines = [
        "═══ Acute:Chronic Workload Ratio Report ═══",
        "",
        f"  Acute Load (avg)  : {result.acute_load}",
        f"  Chronic Load (EWMA): {result.chronic_load}",
        f"  ACWR Ratio        : {result.ratio}",
        f"  Risk Zone         : {indicator}",
        "",
        "── Recommendation ──",
        f"  {result.recommendation}",
        "",
        "── Risk Zone Reference ──",
        "  < 0.8   — Undertraining (detraining risk)",
        "  0.8–1.3 — Sweet Spot (optimal adaptation)",
        "  1.3–1.5 — Caution (elevated risk)",
        "  > 1.5   — Danger (high injury risk)",
        "",
        "── Evidence ──",
        f"  {result.evidence}",
    ]
    return "\n".join(lines)


def format_prevention_protocol(protocol: PreventionProtocol, sport: str = "general") -> str:
    """Human-readable prevention protocol report."""
    lines = [
        f"═══ {protocol.name} ═══",
        f"Target: {protocol.target_injury}",
        f"Evidence: {protocol.evidence}",
        "",
        "── Exercises ──",
    ]
    for i, exercise in enumerate(protocol.exercises, 1):
        lines.append(f"  {i}. {exercise}")

    lines += [
        "",
        "── Programming ──",
        f"  Frequency: {protocol.frequency}",
        f"  Duration : {protocol.duration}",
    ]

    sport_note = protocol.sport_specific_notes.get(
        sport.lower(), protocol.sport_specific_notes.get("general", "")
    )
    if sport_note:
        lines += ["", f"── Sport Note ({sport}) ──", f"  {sport_note}"]

    lines += ["", "── References ──"]
    for ref in protocol.key_references:
        lines.append(f"  • {ref}")

    return "\n".join(lines)


def list_prevention_protocols() -> str:
    """List all available prevention protocols."""
    lines = ["═══ Kiwi Injury Prevention Protocol Database ═══", ""]
    for key, proto in sorted(PROTOCOL_DB.items()):
        lines.append(f"  • {proto.name} ({key})")
        lines.append(f"    Target: {proto.target_injury}")
        lines.append(f"    Evidence: {proto.evidence}")
        lines.append("")

    lines.append(f"  Total: {len(PROTOCOL_DB)} protocols")
    return "\n".join(lines)
