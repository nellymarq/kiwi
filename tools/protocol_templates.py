"""
Protocol Templates — Pre-built evidence-based templates for common scenarios.

Each template provides a structured starting point that the practitioner can
customize. Templates reference Kiwi tools and commands for deeper analysis.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProtocolTemplate:
    name: str
    category: str
    description: str
    duration: str
    content: str
    related_commands: list[str]


TEMPLATES: dict[str, ProtocolTemplate] = {
    "weight_cut": ProtocolTemplate(
        name="Rapid Weight Cut (Combat Sports)",
        category="competition",
        description="7-day acute weight cut protocol for combat sports athletes with weigh-in",
        duration="7 days",
        content="""\
## Weight Cut Protocol — 7-Day Template

### Prerequisites
- Target cut: ≤8% of body weight (acute methods)
- Chronic deficit for 4-6 weeks prior (0.5-1% BW/week)
- Physician awareness for cuts >5%

### Day -7 to -4: Water Loading Phase
- Water: 8L/day (gradually increase sodium excretion)
- Sodium: 3-4g/day (normal-high)
- Carbs: LOW (1-2g/kg) — begin glycogen depletion
- Protein: MAINTAIN (2.2g/kg) — preserve lean mass
- Fiber: START REDUCING (minimize gut content)
- Training: normal but reduce volume 20%

### Day -3: Water Taper Begins
- Water: reduce to 4L
- Sodium: reduce to 1g
- Carbs: <50g total (ketogenic range)
- Continue low-fiber, low-residue diet

### Day -2: Restriction Phase
- Water: 1-2L max
- Sodium: minimal
- Carbs: <30g
- Light activity only (walk, yoga)

### Day -1: Final Cut
- Water: sips only (≤500mL total)
- Hot bath/sauna: if needed, 30 min max per session
- Buddy system required
- STOP if: HR >100 resting, dizziness, confusion, dark urine
- Weigh frequently — stop dehydration when target reached

### Day 0: Weigh-In + Rehydration
- Oral rehydration: 1.5L per kg lost, over 4-6h
- Solution: water + 1g sodium/L + glucose
- First meal: white rice + chicken + banana (easily digestible)
- Carb reload: 8-10g/kg over 12-24h post-weigh-in
- Resume creatine immediately

### Supplement Adjustments
- STOP creatine 5-7 days out (holds water)
- CAFFEINE: taper from day -7, withdraw by day -3 (re-sensitize for competition)
- Electrolytes: match to water loading schedule
- Melatonin: 0.5-1mg for sleep during restriction phase

### Monitoring
- Body weight: twice daily (AM fasted, PM)
- Urine color: target 1-3 during loading, accept 5-6 during restriction
- Heart rate: if resting >100bpm → STOP cutting
- Mood/cognition: if impaired → STOP

### Related Commands
/fight_prep · /track weight · /intervention start creatine_cessation · /risk_screen
""",
        related_commands=["/fight_prep", "/track weight", "/risk_screen", "/hydration"],
    ),

    "muscle_gain": ProtocolTemplate(
        name="Lean Muscle Gain Protocol",
        category="body_composition",
        description="12-week hypertrophy-focused protocol with nutrition + supplementation",
        duration="12 weeks",
        content="""\
## Lean Muscle Gain Protocol — 12-Week Template

### Nutrition
- Surplus: +250-500 kcal above TDEE (lean gain, minimize fat)
- Protein: 1.8-2.2g/kg/day (split across 4-5 meals, 0.4g/kg per meal)
- Carbs: 4-6g/kg/day (higher on training days)
- Fat: 0.8-1.2g/kg/day
- Nutrient timing: protein + carbs within 2h post-training

### Supplement Stack
- Creatine monohydrate: 5g/day (no cycling needed)
- Whey protein: 20-40g post-workout (fast MPS)
- Casein: 30-40g before bed (sustained amino acid delivery)
- HMB-FA: 3g/day during caloric surplus (anti-catabolic, 🟡 evidence)
- Vitamin D: 2000-4000 IU/day (supports testosterone, bone)

### Training Structure
- Phase 1 (Weeks 1-4): Accumulation — 4x/week, 65-75% 1RM, 3-4 sets × 8-12 reps
- Phase 2 (Weeks 5-8): Intensification — 4x/week, 75-85% 1RM, 4-5 sets × 5-8 reps
- Phase 3 (Weeks 9-12): Peak volume — 5x/week, mixed intensities, 20+ sets/muscle/week
- Deload: Week 13 (50% volume)

### Monitoring
- Body weight: daily AM fasted (7-day rolling average)
- Target: +0.25-0.5kg/week
- If gaining >0.5kg/week → reduce surplus
- If gaining <0.25kg/week → increase by 250 kcal
- Circumference: waist, chest, arms monthly
- 1RM testing: every 4 weeks

### Related Commands
/meal_plan 7 · /training_plan strength 12 · /track weight · /calc · /optimize_stack
""",
        related_commands=["/meal_plan", "/training_plan", "/track weight", "/optimize_stack"],
    ),

    "iron_repletion": ProtocolTemplate(
        name="Iron Repletion Protocol (Athletes)",
        category="clinical",
        description="Evidence-based iron supplementation for ferritin <30 ng/mL in athletes",
        duration="8-12 weeks",
        content="""\
## Iron Repletion Protocol — Template

### Diagnosis
- Ferritin <30 ng/mL = iron depletion (athletic threshold)
- Ferritin <15 ng/mL + low hemoglobin = iron deficiency anemia
- Always check: ferritin, hemoglobin, transferrin saturation, CRP

### Supplementation
- **Form:** Iron bisglycinate (Ferrochel) — best absorbed, fewest GI side effects
- **Dose:**
  - Mild depletion (ferritin 20-30): 25-36mg elemental iron/day
  - Moderate depletion (ferritin 10-20): 36-65mg/day
  - Severe (ferritin <10): 65-100mg/day + physician referral
- **Timing:** Empty stomach AM with 100mg vitamin C (enhances absorption 3-6x)
- **Frequency:** Alternate-day dosing if >60mg (improves fractional absorption)

### Avoid Within 2 Hours
- Calcium supplements (>300mg)
- Coffee, tea (tannins/polyphenols)
- Zinc supplements (>25mg)
- Dairy, eggs (calcium + phosphate)
- Whole grains, legumes (phytates)

### Monitoring
- Recheck ferritin + hemoglobin at 6 weeks
- If <50% improvement → check compliance, absorption, GI losses
- Target: ferritin >50 ng/mL for athletes
- Continue maintenance dose (25mg 3x/week) after repletion

### Red Flags
- No ferritin response after 8 weeks → GI evaluation (celiac, IBD)
- Hemoglobin dropping despite iron → urgent hematology referral
- GI bleeding symptoms → stop iron, refer immediately

### Related Commands
/import_labs ferritin <value> · /intervention start iron 36mg/d ferritin · /track ferritin · /intervention check iron
""",
        related_commands=["/import_labs", "/intervention start", "/track", "/intervention check"],
    ),

    "female_athlete_health": ProtocolTemplate(
        name="Female Athlete Health Screening Protocol",
        category="clinical",
        description="RED-S screening, menstrual cycle tracking, bone health, and iron status",
        duration="Ongoing",
        content="""\
## Female Athlete Health Protocol — Template

### Initial Screening
1. Energy availability assessment: (EI - EEE) / FFM
   - <30 kcal/kg FFM = HIGH risk for RED-S
   - 30-45 kcal/kg FFM = MODERATE risk
   - >45 kcal/kg FFM = LOW risk

2. Menstrual function:
   - Primary amenorrhea: no menarche by age 15
   - Secondary amenorrhea: absence ≥3 months
   - Oligomenorrhea: cycle >35 days
   - Functional hypothalamic amenorrhea (FHA): most common in athletes

3. Bone health:
   - DXA scan if amenorrhea >6 months or stress fracture history
   - Z-score <-1.0 = low BMD for age
   - Vitamin D status: target >40 ng/mL

4. Iron status:
   - Ferritin, hemoglobin, transferrin saturation
   - Higher risk: menstrual losses + foot-strike hemolysis + GI losses
   - 30-50% of female athletes are iron-deficient

### Lab Panel
- Ferritin, hemoglobin, transferrin saturation
- Estradiol, progesterone (day 21 for luteal assessment)
- LH, FSH (day 3 for baseline)
- TSH, free T3, free T4
- Vitamin D (25-OH)
- Fasting insulin
- TPO antibodies (if TSH abnormal)
- Calcium, magnesium

### Intervention Priorities
1. Increase energy availability if <30 kcal/kg FFM
2. Iron repletion if ferritin <30 ng/mL
3. Vitamin D optimization (target >40 ng/mL)
4. Calcium 1000-1500mg/day (food-first)
5. Consider cycle-phase training matching

### Related Commands
/reds · /import_labs · /risk_screen · /cycle · /ea · /intervention start · /track
""",
        related_commands=["/reds", "/risk_screen", "/import_labs", "/cycle", "/ea"],
    ),

    "endurance_build": ProtocolTemplate(
        name="Endurance Base Building Protocol",
        category="training",
        description="12-week aerobic base development with nutrition periodization",
        duration="12 weeks",
        content="""\
## Endurance Base Building — 12-Week Template

### Training Structure
- **Weeks 1-4:** Zone 2 focus (80% volume, 60-70% HRmax)
  - 4-5 sessions/week, gradually increase volume 10%/week
  - 1 session tempo/threshold per week

- **Weeks 5-8:** Add threshold work
  - 3 zone 2 sessions + 1 threshold + 1 interval
  - Volume plateau; intensity increases

- **Weeks 9-12:** Race-specific intensity
  - Maintain zone 2 base (60-70% of volume)
  - 2 high-intensity sessions per week
  - Begin taper in week 12 if racing

### Nutrition
- Carbs: 5-8g/kg/day (periodize: higher on long/hard days)
- Protein: 1.4-1.7g/kg/day
- Fat: 1.0-1.5g/kg/day
- Pre-workout: 1-4g/kg carbs, 1-4h before
- During (>60 min): 30-60g/h carbs
- Post: 1.0-1.2g/kg carbs + 0.3g/kg protein within 30 min

### Supplement Stack
- Caffeine: 3-6mg/kg, 30-60 min pre (for key sessions only)
- Nitrate (beetroot): 400mg NO3, 2-3h pre (for threshold sessions)
- Iron: only if ferritin <30 ng/mL
- Vitamin D: 2000 IU/day
- Omega-3: 2g EPA+DHA/day (anti-inflammatory)

### Monitoring
- Resting HR: daily (trending up = overreaching)
- HRV (rMSSD): daily (trending down = fatigue)
- Body weight: 3x/week (prevent unintended loss)
- Sleep: 8-9 hours target (recovery priority)

### Related Commands
/hrzones · /training_plan endurance 12 · /meal_plan · /track rhr · /track hrv_rmssd
""",
        related_commands=["/hrzones", "/training_plan", "/meal_plan", "/track"],
    ),
}


def get_template(name: str) -> ProtocolTemplate | None:
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    return TEMPLATES.get(key)


def list_templates() -> str:
    lines = ["Available protocol templates:", ""]
    for key, t in TEMPLATES.items():
        lines.append(f"  [cyan]{key}[/cyan] — {t.description}")
        lines.append(f"    Duration: {t.duration} · Commands: {', '.join(t.related_commands[:4])}")
    return "\n".join(lines)
