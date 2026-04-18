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

    "injury_recovery": ProtocolTemplate(
        name="Return to Sport After Injury",
        category="clinical",
        description="Phased return-to-sport protocol with nutrition for tissue repair",
        duration="4-12 weeks depending on injury",
        content="""\
## Return to Sport Protocol — Template

### Phase 1: Acute (Days 0-7)
- **Nutrition:** Maintain caloric intake (DO NOT restrict — healing requires energy)
  - Protein: 2.0-2.5g/kg/day (support tissue repair + prevent muscle loss)
  - Collagen: 15g + 50mg vitamin C, 30-60 min before rehab exercises
  - Omega-3: 3-4g EPA+DHA/day (anti-inflammatory, 🟡 evidence for acute phase)
- **Supplements:** Vitamin D (2000-4000 IU), zinc (15-30mg), vitamin C (500mg)
- **Activity:** Only prescribed rehab exercises. No training.
- **Sleep:** 9+ hours — GH release peaks during deep sleep (tissue repair)

### Phase 2: Rehabilitation (Weeks 2-4)
- **Nutrition:** Slight surplus (+200-300 kcal) to support repair
- **Collagen:** Continue 15g + vitamin C pre-rehab
- **Progressive loading:** Follow physiotherapist protocol
- **Creatine:** Resume 5g/day (supports neuromotor recovery)
- **HRV monitoring:** Track readiness; don't push on low-readiness days

### Phase 3: Return to Training (Weeks 4-8)
- **Volume:** Start at 50% of pre-injury volume
- **Intensity:** 70-80% of pre-injury intensity
- **Progression:** Increase 10% per week (ten percent rule)
- **ACWR:** Monitor acute:chronic workload ratio — keep 0.8-1.3
- **Pain rule:** If pain >3/10 during activity → stop, reassess

### Phase 4: Full Return (Weeks 8-12)
- **Volume:** 100% of pre-injury
- **Sport-specific drills:** Gradual reintroduction
- **Competition clearance:** Only after 2 weeks pain-free at full load

### Red Flags (Seek Physician)
- Pain increasing despite rest
- Swelling that doesn't resolve with elevation/ice
- Loss of range of motion
- Numbness, tingling, instability

### Related Commands
/track weight · /readiness · /acwr · /return · /intervention start collagen 15g · /risk_screen
""",
        related_commands=["/acwr", "/return", "/readiness", "/intervention start"],
    ),

    "sleep_optimization": ProtocolTemplate(
        name="Sleep Optimization for Athletes",
        category="recovery",
        description="Evidence-based sleep hygiene and supplementation for recovery",
        duration="Ongoing",
        content="""\
## Sleep Optimization Protocol — Template

### Sleep Targets
- **Duration:** 8-9 hours for athletes (CDC minimum 7h insufficient for recovery)
- **Consistency:** Same bedtime/wake time ±30 min (including weekends)
- **Sleep efficiency:** >85% (time asleep / time in bed)

### Environment
- **Temperature:** 65-68°F (18-20°C)
- **Darkness:** Blackout curtains or eye mask (melatonin suppression from light)
- **Noise:** White noise machine or earplugs
- **Electronics:** No screens 60 min before bed (or blue-light glasses)

### Pre-Sleep Nutrition
- **Last meal:** 2-3h before bed (not too full, not hungry)
- **Casein protein:** 30-40g before bed (sustained amino acid release → overnight MPS)
- **Tart cherry juice:** 240mL 2x/day (natural melatonin source, 🟡)
- **Avoid:** Alcohol (disrupts REM), large fluid volumes (nocturia)

### Supplement Protocol
- **Magnesium glycinate:** 200-400mg, 30-60 min before bed (GABA modulation)
- **Melatonin:** 0.3-1mg if needed for onset (physiological dose, not pharmacological)
- **Glycine:** 3g before bed (reduces core temp, improves sleep quality, 🟡)
- **Ashwagandha:** 300mg KSM-66 at bedtime (reduces cortisol, improves sleep quality)

### Caffeine Management
- **Cutoff:** No caffeine after 2 PM (or 8h before bedtime)
- **Half-life awareness:** 5-6h average; slow metabolizers need 10h+ cutoff
- **Pre-competition:** Withdraw caffeine 5-7 days before, resume race day for re-sensitization

### Chronotype-Specific Adjustments
- **Lion (early):** Bedtime 9:30-10 PM, wake 5-6 AM
- **Bear (middle):** Bedtime 10:30-11 PM, wake 6:30-7 AM
- **Wolf (late):** Bedtime 11:30 PM-midnight, wake 7:30-8 AM

### Monitoring
- Daily: sleep duration, subjective quality 1-10
- Weekly: HRV trends (poor sleep → declining rMSSD)
- Monthly: review patterns, adjust protocol

### Related Commands
/sleep · /chronotype · /caffeine · /bedtime · /track sleep_hours · /supp melatonin · /supp magnesium
""",
        related_commands=["/sleep", "/chronotype", "/caffeine", "/track sleep_hours"],
    ),

    "gut_health": ProtocolTemplate(
        name="GI Optimization for Athletes",
        category="clinical",
        description="Gut health protocol addressing exercise-induced GI distress",
        duration="8-12 weeks",
        content="""\
## GI Optimization Protocol — Template

### Common Issues in Athletes
- Exercise-induced GI distress (30-70% of endurance athletes)
- Leaky gut (increased intestinal permeability from heat/ischemia)
- IBS-like symptoms during competition
- Bloating from high-carb loading protocols

### Phase 1: Elimination & Assessment (Weeks 1-2)
- **Food diary:** Log all foods + GI symptoms + training correlation
- **Remove common triggers:** FODMAPs trial if bloating/gas
- **Pre-exercise fasting window:** 2-3h (reduce gastric contents)
- **Reduce:** NSAIDs (increase gut permeability), excess caffeine

### Phase 2: Gut Repair (Weeks 3-8)
- **L-glutamine:** 5-10g/day (enterocyte fuel, gut barrier support, 🟡)
- **Zinc carnosine:** 75mg 2x/day (mucosal protection, 🟡)
- **Probiotics:** Multi-strain 10 billion CFU (L. rhamnosus GG, B. lactis)
  - Start at 5 billion, increase over 2 weeks
- **Collagen:** 10g/day (provides glycine for intestinal repair)
- **Omega-3:** 2g EPA+DHA (anti-inflammatory, gut barrier integrity)

### Phase 3: Gut Training (Weeks 6-12)
- **Train your gut:** Practice race nutrition during training
- **Start low:** 30g/h carbs during exercise, increase 10g/h per week
- **Target:** 60-90g/h for events >2.5h
- **Multiple transportable carbs:** Glucose:fructose 2:1 ratio
- **Nothing new on race day:** Only tested nutrition in competition

### Pre-Competition GI Protocol
- **Day -3 to -1:** Low-fiber, low-residue diet
- **Race morning:** Familiar foods only, 3h before start
- **During:** Practiced carb/fluid protocol
- **Avoid:** High-fat, high-fiber, dairy (if sensitive), artificial sweeteners

### Red Flags (Refer Out)
- Blood in stool
- Unintentional weight loss >5%
- Persistent symptoms despite protocol
- Iron deficiency from GI losses

### Related Commands
/supp probiotics · /supp bromelain · /food · /track weight · /intervention start glutamine 10g · /risk_screen
""",
        related_commands=["/supp probiotics", "/food", "/intervention start", "/risk_screen"],
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
