"""
Supplement dosing protocols for Kiwi.

Evidence-based dosing, timing, loading strategies, and bioavailability:
- 20+ ergogenic aids with sport-specific dosing
- Loading vs. maintenance phases
- Absorption enhancers and inhibitors
- Timing relative to training and sleep
- Toxicity thresholds (UL/NOAEL)

References:
- Kreider et al. (2017) JISSN — ISSN exercise and sports nutrition review
- Maughan et al. (2018) Br J Sports Med — IOC consensus on supplements
- Kerksick et al. (2018) JISSN — Nutrient timing position stand
- Close et al. (2022) BJSM — Supplement A-to-Z framework
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DosingProtocol:
    name: str
    category: str                    # ergogenic / health / recovery / cognitive
    loading_dose: Optional[str]       # e.g., "20g/d × 5d" or None
    maintenance_dose: str             # e.g., "3–5g/d"
    timing: str                       # relative to training
    duration: str                     # acute / chronic / cycling
    best_forms: list[str]             # bioavailability-ranked forms
    absorption_enhancers: list[str]
    absorption_inhibitors: list[str]
    food_interaction: str             # "take with food" / "empty stomach" / "either"
    onset_time: str                   # time to noticeable effect
    washout: str                      # clearance / cycling recommendation
    ul_or_noael: Optional[str]        # upper limit or no-observed-adverse-effect level
    contraindications: list[str]
    sport_specific_notes: dict[str, str]  # sport → note
    evidence: str                     # 🟢/🟡/🟠/🔵 tier
    mechanism: str                    # brief mechanism of action
    key_references: list[str]


# ── Supplement Database ───────────────────────────────────────────────────────

SUPPLEMENT_DB: dict[str, DosingProtocol] = {

    "creatine": DosingProtocol(
        name="Creatine Monohydrate",
        category="ergogenic",
        loading_dose="20g/d (4 × 5g) for 5–7 days",
        maintenance_dose="3–5g/d (0.03–0.05g/kg/d)",
        timing="Any time; post-workout with carbs may marginally enhance uptake",
        duration="Chronic — no need to cycle; safe for long-term use",
        best_forms=["Creatine monohydrate (gold standard)", "Creapure", "Micronized monohydrate"],
        absorption_enhancers=["Carbohydrate co-ingestion (50–100g)", "Protein co-ingestion"],
        absorption_inhibitors=["Excessive fiber"],
        food_interaction="Take with meal or carb-containing shake",
        onset_time="Loading: 5–7 days to full saturation; No-load: 28 days",
        washout="Stores deplete over 4–6 weeks after cessation",
        ul_or_noael="NOAEL: 30g/d (short-term); No established UL for long-term 3–5g/d",
        contraindications=["Pre-existing renal disease (consult physician)", "Renal-dose medications"],
        sport_specific_notes={
            "strength": "Most robust ergogenic aid; +5–10% strength, +1–2kg lean mass over 12 weeks",
            "endurance": "Limited direct benefit; may aid interval capacity and glycogen resynthesis",
            "team_sport": "Enhances repeated sprint ability (+5–15% across 6–10 sprints)",
            "combat_sports": "Useful for training; weight gain may be undesirable pre-weigh-in",
        },
        evidence="🟢 Strong — Most studied supplement in sports nutrition",
        mechanism="Increases phosphocreatine stores → faster ATP resynthesis during high-intensity efforts; "
                  "also acts as intracellular osmolyte (cell volumization) and may upregulate mTOR/IGF-1 signaling. "
                  "Note: Caffeine may attenuate ergogenic effect at the functional level (debated; Vandenberghe 1996 vs Hespel 2002)",
        key_references=[
            "Kreider et al. (2017) JISSN — ISSN position stand on creatine",
            "Buford et al. (2007) JISSN — Creatine supplementation and exercise",
            "Hall & Trojian (2013) Phys Sportsmed — Creatine renal safety review",
        ],
    ),

    "caffeine": DosingProtocol(
        name="Caffeine",
        category="ergogenic",
        loading_dose=None,
        maintenance_dose="3–6 mg/kg body weight",
        timing="30–60 min pre-exercise (peak plasma ~45–60 min)",
        duration="Acute — single dose pre-exercise; habitual users may need higher doses",
        best_forms=["Anhydrous caffeine (capsule/powder)", "Coffee (variable absorption)", "Caffeine gum (faster buccal absorption)"],
        absorption_enhancers=["Empty stomach accelerates absorption", "Caffeine gum bypasses first-pass metabolism"],
        absorption_inhibitors=["Food slows absorption by ~45 min", "Grapefruit (CYP1A2 inhibition, extends half-life)"],
        food_interaction="Preferably on empty stomach for fastest onset; low dose with food acceptable",
        onset_time="15–45 min depending on form (gum < capsule < coffee)",
        washout="Half-life: 4–6h (CYP1A2 fast) or 6–9h (CYP1A2 slow); abstain 7+ days to resensitize",
        ul_or_noael="Acute toxicity: >500mg single dose; NOAEL: ~400mg/d for adults (FDA); LD50: ~10g",
        contraindications=["Anxiety disorders", "Cardiac arrhythmias", "Pregnancy (limit <200mg/d)",
                          "Insomnia (avoid within 8h of sleep)", "GERD/peptic ulcer"],
        sport_specific_notes={
            "endurance": "Most robust benefit: +2–4% time trial performance; effective across all durations",
            "strength": "Moderate benefit: +2–7% maximal strength; may enhance training volume",
            "team_sport": "Improves reaction time, decision-making, and repeated sprint ability",
            "combat_sports": "Effective; ensure within weight class limits and WADA guidelines",
        },
        evidence="🟢 Strong — IOC consensus supplement; A-tier evidence",
        mechanism="Adenosine A1/A2A receptor antagonist → reduced perception of effort and fatigue; "
                  "central nervous system stimulation; increased catecholamine release; "
                  "enhanced calcium release from sarcoplasmic reticulum",
        key_references=[
            "Goldstein et al. (2010) JISSN — ISSN position stand on caffeine",
            "Southward et al. (2018) Br J Sports Med — Meta-analysis: caffeine and endurance",
            "Grgic et al. (2020) JISSN — Caffeine and resistance exercise meta-analysis",
        ],
    ),

    "beta_alanine": DosingProtocol(
        name="Beta-Alanine",
        category="ergogenic",
        loading_dose="3.2–6.4g/d in divided doses (0.8–1.6g per dose) for 4–6 weeks",
        maintenance_dose="1.6–3.2g/d after loading",
        timing="Divide throughout the day to minimize paresthesia; timing relative to exercise irrelevant",
        duration="Chronic — requires 4+ weeks to increase muscle carnosine; effects persist ~6 weeks post-cessation",
        best_forms=["CarnoSyn (patented sustained-release)", "Beta-alanine powder (generic)"],
        absorption_enhancers=["Sustained-release formulations reduce paresthesia", "Taking with meals"],
        absorption_inhibitors=["Taurine competes for transport (theoretical — clinical significance debated)"],
        food_interaction="Take with food to slow absorption and reduce paresthesia",
        onset_time="4–6 weeks to meaningfully increase carnosine (+40–60%)",
        washout="Carnosine levels decline ~2–4% per week after cessation; full washout ~15 weeks",
        ul_or_noael="NOAEL: 6.4g/d; main side effect is paresthesia (harmless tingling)",
        contraindications=["None significant; paresthesia may be uncomfortable for some"],
        sport_specific_notes={
            "endurance": "Benefits high-intensity efforts within endurance (e.g., surges, hill repeats, sprint finishes)",
            "strength": "May allow 1–2 extra reps at high intensity (60–240s time domain)",
            "team_sport": "Enhances repeated high-intensity efforts (basketball, football, hockey)",
            "rowing": "Strong evidence for 2000m rowing performance (+1–2s improvement)",
        },
        evidence="🟢 Strong — IOC consensus A-tier; effective for 60–240s duration efforts",
        mechanism="Increases intramuscular carnosine → enhanced intracellular pH buffering during "
                  "high-intensity exercise → delays acidosis-related fatigue",
        key_references=[
            "Trexler et al. (2015) JISSN — Beta-alanine position stand",
            "Saunders et al. (2017) Br J Sports Med — Meta-analysis of beta-alanine",
        ],
    ),

    "nitrate": DosingProtocol(
        name="Dietary Nitrate (Beetroot Juice)",
        category="ergogenic",
        loading_dose="2–3 days of 6–8 mmol nitrate (500ml beetroot juice/d) for acute events",
        maintenance_dose="6–8 mmol/d (~500ml beetroot juice or 400mg sodium nitrate)",
        timing="2–3h pre-exercise (peak plasma nitrite ~2.5h post-ingestion)",
        duration="Acute or chronic (5–7d loading slightly more effective)",
        best_forms=["Concentrated beetroot juice shots (e.g., Beet It)", "Beetroot powder", "Sodium nitrate (less palatable)"],
        absorption_enhancers=["Vitamin C co-ingestion may enhance nitrite conversion"],
        absorption_inhibitors=["Antibacterial mouthwash (kills oral nitrate-reducing bacteria!)",
                              "Proton pump inhibitors (reduce gastric nitrite conversion)"],
        food_interaction="Take with or without food; avoid mouthwash for 2h before/after",
        onset_time="Acute: 2–3h; chronic loading: 5–7d for maximal tissue saturation",
        washout="Nitrite cleared within 24h; tissue stores decline over 2–3d",
        ul_or_noael="No established UL for dietary nitrate; methemoglobinemia risk at extreme doses",
        contraindications=["Concurrent PDE5 inhibitors (sildenafil — hypotension risk)",
                          "Kidney stones (oxalate in beet juice)"],
        sport_specific_notes={
            "endurance": "Reduces O2 cost of exercise by 3–5%; improves time trial by 1–3% in recreational athletes",
            "strength": "Emerging evidence for enhanced muscle contractile efficiency",
            "team_sport": "May enhance repeated sprint performance (+3–4% in intermittent protocols)",
            "elite": "Benefits diminish in highly trained athletes (already optimized NO signaling)",
        },
        evidence="🟢 Strong for recreational athletes; 🟡 Moderate for elite athletes",
        mechanism="Dietary NO3⁻ → oral bacteria reduce to NO2⁻ → gastric/tissue conversion to nitric oxide (NO) → "
                  "vasodilation, improved mitochondrial efficiency (reduced O2 cost), enhanced muscle contractile function",
        key_references=[
            "Jones et al. (2018) Sports Med — Dietary nitrate and exercise review",
            "McMahon et al. (2017) Sports Med — Meta-analysis of nitrate supplementation",
        ],
    ),

    "vitamin_d": DosingProtocol(
        name="Vitamin D3 (Cholecalciferol)",
        category="health",
        loading_dose="10,000 IU/d for 8 weeks if deficient (<30 ng/mL) — under clinical supervision",
        maintenance_dose="1,000–4,000 IU/d (adjust based on serum 25(OH)D levels; target 40–60 ng/mL)",
        timing="With a fat-containing meal (fat-soluble vitamin)",
        duration="Chronic — year-round, especially in northern latitudes or indoor athletes",
        best_forms=["Vitamin D3 (cholecalciferol)", "D3 in oil-based softgels"],
        absorption_enhancers=["Fat-containing meals (+30–50% absorption)", "Medium-chain triglycerides"],
        absorption_inhibitors=["Fat malabsorption conditions", "Orlistat", "Cholestyramine"],
        food_interaction="Always take with fat-containing meal",
        onset_time="Serum levels rise within 1–2 weeks; plateau at 8–12 weeks",
        washout="Half-life: ~15 days; stores deplete over 2–3 months",
        ul_or_noael="UL: 4,000 IU/d (IOM); therapeutic doses up to 10,000 IU/d used clinically; "
                    "toxicity rare below 50,000 IU/d chronic",
        contraindications=["Hypercalcemia", "Sarcoidosis", "Granulomatous disease",
                          "Concurrent thiazide diuretics (monitor calcium)"],
        sport_specific_notes={
            "general": "Deficiency (<30 ng/mL) associated with increased injury risk, impaired immunity, reduced power",
            "indoor_sports": "Higher prevalence of deficiency; supplementation especially important",
            "endurance": "Optimal levels associated with improved VO2max and reduced respiratory infections",
            "strength": "May support testosterone production at optimal levels (40–60 ng/mL)",
        },
        evidence="🟢 Strong for deficiency correction; 🟡 Moderate for performance above sufficiency",
        mechanism="Steroid hormone precursor: 25(OH)D → 1,25(OH)₂D → VDR activation → "
                  "calcium homeostasis, immune modulation (cathelicidin), muscle protein synthesis (VDR on myocytes), "
                  "testosterone production support",
        key_references=[
            "Close et al. (2013) BJSM — Vitamin D and athletes",
            "Owens et al. (2018) Eur J Sport Sci — Vitamin D and muscle function",
        ],
    ),

    "omega_3": DosingProtocol(
        name="Omega-3 Fatty Acids (EPA/DHA)",
        category="health",
        loading_dose=None,
        maintenance_dose="1–3g combined EPA+DHA daily (higher EPA for inflammation; higher DHA for brain/recovery)",
        timing="With a fat-containing meal; split dose AM/PM for >2g",
        duration="Chronic — 4–8 weeks to achieve tissue saturation (Omega-3 Index target ≥8%)",
        best_forms=["Triglyceride form fish oil", "Algal oil (vegan)", "Re-esterified TG (rTG)"],
        absorption_enhancers=["Fat-containing meals (+3× absorption)", "Phospholipid-bound forms (krill oil)"],
        absorption_inhibitors=["Ethyl ester form on empty stomach (poor absorption)"],
        food_interaction="Always take with fat-containing meal; avoid ethyl ester form on empty stomach",
        onset_time="Blood levels: 1–2 weeks; tissue saturation: 4–8 weeks; anti-inflammatory: 6–12 weeks",
        washout="Tissue depletion: 8–12 weeks; Omega-3 Index decline: ~0.5%/month",
        ul_or_noael="FDA GRAS up to 3g/d combined EPA+DHA; anticoagulant concerns >3g/d (monitor with blood thinners)",
        contraindications=["Active anticoagulant therapy (consult physician >2g/d)", "Fish allergy (use algal source)",
                          "Scheduled surgery (discontinue 1 week prior — bleeding risk)"],
        sport_specific_notes={
            "endurance": "Anti-inflammatory: reduces exercise-induced bronchoconstriction; supports cardiac health",
            "strength": "May reduce DOMS severity and enhance recovery between sessions",
            "team_sport": "Neuroprotective: DHA may reduce concussion severity and improve recovery",
            "combat_sports": "Neuroprotective benefit for head impact exposure",
        },
        evidence="🟢 Strong for health; 🟡 Moderate for direct performance enhancement",
        mechanism="EPA: resolvin/protectin biosynthesis → inflammation resolution; COX-2 substrate competition. "
                  "DHA: neuronal membrane fluidity, BDNF expression. Both: membrane phospholipid incorporation, "
                  "gene expression modulation via PPARs",
        key_references=[
            "Philpott et al. (2019) JISSN — Omega-3 and exercise recovery",
            "Heileson & Funderburk (2020) Nutrients — Omega-3 for athletes",
        ],
    ),

    "magnesium": DosingProtocol(
        name="Magnesium",
        category="health",
        loading_dose=None,
        maintenance_dose="200–400mg elemental Mg daily (athletes may need 400–600mg due to sweat losses)",
        timing="Evening — supports sleep quality; or post-workout",
        duration="Chronic — daily supplementation recommended for athletes with high sweat rates",
        best_forms=["Magnesium glycinate (high bioavailability, sleep benefit)",
                   "Magnesium threonate (crosses BBB, cognitive)",
                   "Magnesium citrate (good absorption, mild laxative)"],
        absorption_enhancers=["Vitamin B6 co-supplementation", "Take apart from calcium supplements"],
        absorption_inhibitors=["Phytates (whole grains, legumes)", "High-dose calcium (>250mg at same time)",
                              "Zinc (high doses compete for absorption)"],
        food_interaction="Take with food to improve tolerance; avoid with high-phytate meals",
        onset_time="Serum levels improve within 1–2 weeks; tissue repletion: 4–12 weeks if deficient",
        washout="Stores deplete over 2–4 weeks depending on baseline status",
        ul_or_noael="UL: 350mg/d from supplements (IOM) — applies to supplemental, not dietary; "
                    "higher doses may cause GI distress (dose-dependent diarrhea)",
        contraindications=["Renal insufficiency (impaired Mg excretion)", "Myasthenia gravis",
                          "Concurrent aminoglycoside antibiotics"],
        sport_specific_notes={
            "endurance": "Sweat losses of 3–20mg Mg per liter; long events may deplete significantly",
            "strength": "Supports muscle contraction and neuromuscular function; deficiency impairs strength",
            "general": "RBC-Mg more reliable than serum Mg for assessing true status",
        },
        evidence="🟢 Strong for deficiency correction; 🟡 Moderate for performance above RDA",
        mechanism="Cofactor in 600+ enzymatic reactions; ATP-Mg²⁺ complex required for energy transfer; "
                  "NMDA receptor modulation (sleep/recovery); muscle relaxation via Ca²⁺ antagonism",
        key_references=[
            "Zhang et al. (2017) Nutrients — Magnesium and exercise meta-analysis",
            "Volpe (2015) Curr Sports Med Rep — Magnesium and the athlete",
        ],
    ),

    "hmb": DosingProtocol(
        name="HMB (Beta-Hydroxy Beta-Methylbutyrate)",
        category="recovery",
        loading_dose=None,
        maintenance_dose="3g/d in divided doses (1g × 3)",
        timing="30–60 min pre-exercise and/or with meals throughout the day",
        duration="Chronic — 2+ weeks for measurable anti-catabolic effects",
        best_forms=["HMB free acid (faster absorption, ~30 min to peak)",
                   "HMB calcium salt (HMB-Ca, standard form, ~60–120 min to peak)"],
        absorption_enhancers=["Free acid form pre-exercise for acute effect"],
        absorption_inhibitors=["None significant"],
        food_interaction="Either; free acid form better on empty stomach pre-exercise",
        onset_time="Anti-catabolic effects measurable within 1–2 weeks; lean mass gains over 4–12 weeks",
        washout="Clears within 24–48h; benefits fade within 2 weeks of cessation",
        ul_or_noael="NOAEL: 6g/d; well-tolerated with no significant side effects in RCTs",
        contraindications=["None established"],
        sport_specific_notes={
            "strength": "Most effective in untrained or during novel stimuli; trained athletes show smaller effects",
            "endurance": "May reduce muscle damage markers during intensified training blocks",
            "elderly": "Strong evidence for sarcopenia prevention in combination with resistance training",
        },
        evidence="🟡 Moderate — Effective for untrained/novel stimuli; smaller effects in well-trained athletes",
        mechanism="Leucine metabolite (~5% of leucine converted to HMB); inhibits ubiquitin-proteasome pathway → "
                  "reduced muscle protein breakdown; may stimulate mTOR-mediated MPS; "
                  "cholesterol synthesis precursor supporting cell membrane integrity",
        key_references=[
            "Wilson et al. (2013) JISSN — ISSN position stand on HMB",
            "Sanchez-Martinez et al. (2018) Nutrients — HMB meta-analysis",
        ],
    ),

    "ashwagandha": DosingProtocol(
        name="Ashwagandha (Withania somnifera)",
        category="recovery",
        loading_dose=None,
        maintenance_dose="300–600mg root extract daily (standardized to 5% withanolides)",
        timing="Evening preferred (cortisol modulation + sleep benefit); or split AM/PM",
        duration="Chronic — 8–12 weeks for full adaptogenic effects",
        best_forms=["KSM-66 (full-spectrum root extract)", "Sensoril (root + leaf extract)"],
        absorption_enhancers=["Piperine/black pepper extract (+30% bioavailability)"],
        absorption_inhibitors=["None significant"],
        food_interaction="Take with or without food; mild GI if taken on empty stomach",
        onset_time="Anxiolytic: 2–4 weeks; strength/body composition: 8–12 weeks; cortisol reduction: 4–8 weeks",
        washout="Effects diminish over 2–4 weeks after cessation",
        ul_or_noael="NOAEL: 600mg/d KSM-66 (human clinical trials); liver toxicity reports very rare, mainly with poor-quality extracts",
        contraindications=["Thyroid disorders (may increase T3/T4)", "Autoimmune conditions (immunostimulatory)",
                          "Pregnancy/lactation", "Nightshade allergy"],
        sport_specific_notes={
            "strength": "RCTs show +10–15% strength gains vs placebo over 8 weeks; enhanced recovery",
            "endurance": "Improved VO2max (+4–6%) in recreational athletes in 8-week RCTs",
            "general": "Significant cortisol reduction (−15–27%) supports recovery and sleep quality",
        },
        evidence="🟡 Moderate — Growing RCT base; most studies in untrained/recreational athletes",
        mechanism="Withanolides: GABAergic modulation (anxiolytic), HPA axis attenuation (cortisol reduction), "
                  "may enhance mitochondrial function, antioxidant (SOD/catalase upregulation), "
                  "potential testosterone support via DHEA pathway",
        key_references=[
            "Wankhede et al. (2015) JISSN — Ashwagandha and muscle strength",
            "Choudhary et al. (2015) JAIM — Ashwagandha and cardiorespiratory endurance",
            "Salve et al. (2019) Cureus — Ashwagandha and stress/anxiety",
        ],
    ),

    "iron": DosingProtocol(
        name="Iron",
        category="health",
        loading_dose="100–200mg elemental iron daily for 8–12 weeks if deficient (ferritin <30 ng/mL; under clinical supervision — exceeds IOM UL)",
        maintenance_dose="18–30mg elemental iron daily for at-risk athletes (female, endurance)",
        timing="Morning on empty stomach; alternate-day dosing may improve absorption (hepcidin cycling)",
        duration="Chronic for at-risk populations; repletion: 8–12 weeks; recheck ferritin at 3 months",
        best_forms=["Ferrous bisglycinate (best tolerated, good absorption)",
                   "Ferrous sulfate (cheap, effective, more GI side effects)",
                   "Iron polysaccharide complex"],
        absorption_enhancers=["Vitamin C (50–100mg with dose; +2–3× absorption)",
                             "Meat factor (MFP in animal protein)", "Citric acid"],
        absorption_inhibitors=["Calcium (>300mg)", "Phytates (grains, legumes)", "Tannins (tea, coffee)",
                              "Polyphenols", "Zinc (>25mg at same time)"],
        food_interaction="Best on empty stomach; if GI intolerance, take with small amount of food (avoid dairy/grains)",
        onset_time="Hemoglobin: 2–4 weeks; ferritin repletion: 8–12 weeks",
        washout="Stores maintained indefinitely unless ongoing losses (menstruation, GI, foot-strike hemolysis)",
        ul_or_noael="UL: 45mg/d elemental iron (IOM); acute toxicity at >20mg/kg body weight",
        contraindications=["Hemochromatosis", "Iron overload syndromes", "Concurrent IV iron therapy"],
        sport_specific_notes={
            "endurance": "Foot-strike hemolysis + sweat losses + GI bleeding → higher prevalence of deficiency",
            "female_athletes": "Menstrual losses + training demands; 30–50% of female athletes are iron-deficient",
            "strength": "Less prevalent but monitor if vegetarian/vegan or high training volume",
        },
        evidence="🟢 Strong for deficiency treatment; 🟡 Moderate for supplementation above sufficiency",
        mechanism="Fe²⁺ incorporated into hemoglobin (O2 transport), myoglobin (O2 storage in muscle), "
                  "cytochrome c oxidase (mitochondrial electron transport), iron-sulfur clusters (energy production). "
                  "Deficiency impairs VO2max, lactate threshold, and endurance capacity",
        key_references=[
            "Peeling et al. (2007) IJSNEM — Iron and the endurance athlete",
            "DellaValle (2011) Med Sci Sports Exerc — Iron depletion in female athletes",
        ],
    ),

    "citrulline": DosingProtocol(
        name="L-Citrulline",
        category="ergogenic",
        loading_dose=None,
        maintenance_dose="6–8g/d (or 8–10g citrulline malate 2:1)",
        timing="30–60 min pre-workout",
        duration="Acute benefits from single dose; enhanced with chronic use (7+ days)",
        best_forms=["L-citrulline (pure)", "Citrulline malate 2:1"],
        absorption_enhancers=["Empty stomach (faster absorption)"],
        absorption_inhibitors=[],
        food_interaction="Take on empty stomach or with light carb drink",
        onset_time="Acute: 30–60 min (peak plasma arginine)",
        washout="Clears within 24h; no accumulation concerns",
        ul_or_noael="NOAEL: 15g/d (short-term); no established UL",
        contraindications=["Citrullinemia (rare genetic disorder)", "PDE5 inhibitors (additive hypotension)"],
        sport_specific_notes={
            "strength": "May enhance rep performance (+2–3 reps at 60–80% 1RM) via improved blood flow",
            "endurance": "Improves time-to-exhaustion; reduces perceived exertion at submaximal intensities",
            "combat_sports": "Enhances repeated high-intensity bouts; reduces muscle soreness post-session",
        },
        evidence="🟡 Moderate — Consistent ergogenic signal in meta-analyses but effect sizes modest",
        mechanism="Citrulline → arginine (via ASS1/ASL in kidneys) → nitric oxide (via eNOS). "
                  "Bypasses hepatic first-pass metabolism (unlike oral arginine). Increases plasma arginine "
                  "~2x more effectively than equimolar arginine. Enhances blood flow, reduces O2 cost of exercise, "
                  "may buffer ammonia accumulation",
        key_references=[
            "Trexler et al. (2019) JISSN — Citrulline supplementation meta-analysis",
            "Gonzalez & Trexler (2020) Nutrients — Citrulline and exercise performance",
        ],
    ),

    "taurine": DosingProtocol(
        name="Taurine",
        category="ergogenic",
        loading_dose=None,
        maintenance_dose="1–3g/d",
        timing="60 min pre-exercise or with meals",
        duration="Chronic (14+ days) for maximal benefit; acute effects also documented",
        best_forms=["L-taurine (free-form powder or capsule)"],
        absorption_enhancers=["Can be taken with or without food"],
        absorption_inhibitors=["Beta-alanine (competitive transport; separate by 2+ hours)"],
        food_interaction="Either; no significant food interaction",
        onset_time="Acute effects within 1–2 hours; tissue saturation over 7–14 days",
        washout="Plasma half-life ~1h; muscle stores deplete over 1–2 weeks",
        ul_or_noael="NOAEL: 6g/d (EFSA); well-tolerated up to 10g/d in studies",
        contraindications=["Bipolar disorder (theoretical — may affect GABA)", "Kidney disease (impaired clearance)"],
        sport_specific_notes={
            "endurance": "May improve time-to-exhaustion (+1.7% in meta-analysis); reduces oxidative stress",
            "strength": "Limited direct strength benefit; may reduce DOMS and muscle damage markers",
            "combat_sports": "Cytoprotective against exercise-induced muscle damage; supports repeated-bout effect",
        },
        evidence="🟡 Moderate — Meta-analyses show small but consistent endurance benefit",
        mechanism="Cell volume regulator (osmolyte), antioxidant (scavenges HOCl, stabilizes membranes), "
                  "calcium handling modulator in muscle (enhances SR Ca²⁺ release/reuptake), "
                  "bile acid conjugation, GABA-A receptor modulation (anxiolytic at high doses)",
        key_references=[
            "Waldron et al. (2018) Sports Med — Taurine and exercise: systematic review",
            "Kurtz et al. (2021) JISSN — Taurine in sport and exercise",
        ],
    ),

    "tyrosine": DosingProtocol(
        name="L-Tyrosine",
        category="cognitive",
        loading_dose=None,
        maintenance_dose="500–2000mg (150mg/kg for acute stress protection)",
        timing="30–60 min before cognitive or physical demand; pre-competition",
        duration="Acute dosing — most effective under stress/sleep deprivation",
        best_forms=["L-tyrosine (free-form)", "N-acetyl-L-tyrosine (NALT — lower bioavailability)"],
        absorption_enhancers=["Empty stomach", "Vitamin B6 (cofactor for conversion)"],
        absorption_inhibitors=["Competing large neutral amino acids (high-protein meal)"],
        food_interaction="Best on empty stomach or with carb-only snack",
        onset_time="30–60 min (peak plasma levels)",
        washout="Plasma half-life ~2h; no accumulation",
        ul_or_noael="No established UL; 150mg/kg/d used safely in military studies",
        contraindications=["Hyperthyroidism (tyrosine → thyroid hormone precursor)", "MAO inhibitors",
                           "Melanoma (theoretical — tyrosine → melanin pathway)"],
        sport_specific_notes={
            "combat_sports": "Preserves cognitive function during weight cuts and sleep restriction",
            "endurance": "May maintain pacing strategy under heat stress or sleep deprivation",
            "tactical": "Military research shows preserved working memory under acute stress (cold, sleep loss)",
        },
        evidence="🟡 Moderate — Strong under stress/depletion; minimal benefit under normal conditions",
        mechanism="Precursor to catecholamines: tyrosine → L-DOPA (via TH) → dopamine → norepinephrine → epinephrine. "
                  "Under stress, catecholamine synthesis is rate-limited by tyrosine availability. "
                  "Supplementation replenishes the precursor pool, maintaining cognitive performance "
                  "during conditions that deplete catecholamines (cold, sleep loss, sustained ops)",
        key_references=[
            "Jongkees et al. (2015) J Clin Psychopharmacol — Tyrosine and cognitive performance meta-analysis",
            "Neri et al. (1995) Aviat Space Environ Med — Tyrosine and sustained military performance",
        ],
    ),

    "melatonin": DosingProtocol(
        name="Melatonin",
        category="health",
        loading_dose=None,
        maintenance_dose="0.3–1mg for sleep onset; 0.5–5mg for jet lag; 3–5mg for shift work",
        timing="30–60 min before desired sleep onset; for jet lag: at destination bedtime",
        duration="Short-term recommended; long-term safety data limited but generally favorable",
        best_forms=["Immediate-release (sleep onset)", "Extended-release (sleep maintenance)",
                    "Sublingual (fastest onset, bypasses first-pass)"],
        absorption_enhancers=["Darkness (endogenous production synergy)", "Cool ambient temperature"],
        absorption_inhibitors=["Blue light exposure (suppresses endogenous + reduces efficacy)",
                               "NSAIDs (some reduce endogenous melatonin)", "Beta-blockers (reduce endogenous)"],
        food_interaction="Take on empty stomach or with light snack; high-fat meals delay absorption",
        onset_time="20–40 min (sublingual: 10–15 min)",
        washout="Half-life: 20–50 min; clears fully by morning at physiological doses",
        ul_or_noael="No established UL; 0.3–1mg is physiological; >5mg is pharmacological",
        contraindications=["Autoimmune conditions (immunostimulatory)", "Seizure disorders",
                           "Concurrent sedative medications", "Pregnancy/breastfeeding"],
        sport_specific_notes={
            "endurance": "Useful for travel-heavy athletes crossing time zones; 0.5mg at destination bedtime",
            "combat_sports": "Supports recovery sleep after evening competitions; use lowest effective dose",
            "tactical": "Shift work protocol: 1–3mg before day sleep in blackout conditions",
        },
        evidence="🟢 Strong for jet lag; 🟡 Moderate for general sleep onset; 🟠 Weak for performance enhancement",
        mechanism="Binds MT1/MT2 receptors in suprachiasmatic nucleus → phase-shifts circadian clock. "
                  "MT1 activation promotes sleepiness; MT2 activation shifts circadian phase. "
                  "Also: potent antioxidant (hydroxyl radical scavenger), mild anti-inflammatory, "
                  "mild core body temperature reduction (facilitates sleep onset)",
        key_references=[
            "Costello et al. (2014) Eur J Appl Physiol — Melatonin and exercise recovery",
            "Herxheimer & Petrie (2002) Cochrane — Melatonin for jet lag",
        ],
    ),

    "zinc": DosingProtocol(
        name="Zinc",
        category="health",
        loading_dose=None,
        maintenance_dose="15–30mg/d elemental zinc (higher end if deficient)",
        timing="With meals to reduce GI side effects; separate from iron by 2+ hours",
        duration="Chronic for deficiency correction; 8–12 weeks then reassess",
        best_forms=["Zinc picolinate", "Zinc bisglycinate", "Zinc citrate", "Zinc acetate (for acute cold)"],
        absorption_enhancers=["Animal protein (releases zinc from phytate complexes)", "Citric acid"],
        absorption_inhibitors=["Phytates (grains, legumes)", "Calcium (>600mg)", "Iron (>25mg at same time)",
                               "Copper (competitive absorption)"],
        food_interaction="Take with food to minimize nausea; avoid high-phytate meals",
        onset_time="Serum levels: days; immune/testosterone effects: 4–8 weeks",
        washout="Body stores deplete over 2–4 weeks; no accumulation risk at recommended doses",
        ul_or_noael="UL: 40mg/d (IOM); chronic >50mg/d risks copper depletion",
        contraindications=["Concurrent quinolone/tetracycline antibiotics (chelation)", "Copper deficiency"],
        sport_specific_notes={
            "strength": "Supports testosterone maintenance in zinc-deficient athletes; no supra-physiological effect",
            "endurance": "Sweat losses 0.5–1mg/L; high-volume athletes at risk of depletion",
            "combat_sports": "Weight-cut diets often zinc-poor; supplement during caloric restriction",
        },
        evidence="🟢 Strong for deficiency correction; 🟠 Weak for supplementation above sufficiency",
        mechanism="Cofactor for 300+ enzymes including carbonic anhydrase (acid-base balance), "
                  "superoxide dismutase (antioxidant), alcohol dehydrogenase. Essential for testosterone synthesis "
                  "(5α-reductase cofactor), immune function (thymulin activation, T-cell maturation), "
                  "protein synthesis, and wound healing. Deficiency impairs growth hormone axis",
        key_references=[
            "Kilic et al. (2006) Neuro Endocrinol Lett — Zinc and testosterone in athletes",
            "Prasad (2008) Mol Med — Zinc in immune function",
        ],
    ),

    "l_carnitine": DosingProtocol(
        name="L-Carnitine",
        category="ergogenic",
        loading_dose="2g/d × 12–24 weeks (muscle loading requires chronic dosing with carbs)",
        maintenance_dose="2–3g/d with 30–80g carbohydrate (insulin-dependent uptake)",
        timing="With carbohydrate-containing meal (insulin drives muscle uptake)",
        duration="Chronic — 12–24 weeks minimum for intramuscular loading",
        best_forms=["L-carnitine L-tartrate (LCLT — best for exercise)", "Acetyl-L-carnitine (ALCAR — cognitive)",
                    "Glycine propionyl-L-carnitine (GPLC — blood flow)"],
        absorption_enhancers=["Carbohydrate co-ingestion (50–80g — insulin-mediated muscle uptake is essential)"],
        absorption_inhibitors=["Low insulin state (fasted) — carnitine stays in plasma, doesn't enter muscle"],
        food_interaction="MUST take with high-carb meal; fasted supplementation is ineffective for muscle loading",
        onset_time="Plasma: immediate; muscle loading: 12–24 weeks with carb co-ingestion",
        washout="Muscle stores maintained for weeks after cessation",
        ul_or_noael="No established UL; 2–3g/d used safely in long-term studies; >3g/d may cause GI distress",
        contraindications=["Hypothyroidism (may impair thyroid hormone action)", "Seizure history (ALCAR form)"],
        sport_specific_notes={
            "endurance": "Shifts substrate use toward fat oxidation at submaximal intensities when muscle stores loaded",
            "strength": "LCLT form reduces muscle damage markers and soreness post-resistance exercise",
            "combat_sports": "May support recovery during high-frequency training blocks",
        },
        evidence="🟡 Moderate — Effective only with chronic loading + carb co-ingestion (Wall et al. 2011)",
        mechanism="Carnitine shuttle: transports long-chain fatty acids across inner mitochondrial membrane "
                  "(CPT1/CPT2 system). When muscle carnitine is elevated, spares glycogen by increasing fat "
                  "oxidation at moderate intensities. Also buffers acetyl-CoA:CoA ratio (via carnitine "
                  "acetyltransferase), potentially reducing lactate accumulation during high-intensity work",
        key_references=[
            "Wall et al. (2011) J Physiol — Chronic carnitine + carb loading increases muscle carnitine",
            "Stephens et al. (2013) Med Sci Sports Exerc — Carnitine and exercise metabolism",
        ],
    ),

    "glycerol": DosingProtocol(
        name="Glycerol",
        category="ergogenic",
        loading_dose="1.2g/kg with 26mL/kg water, 60–120 min pre-exercise (hyperhydration protocol)",
        maintenance_dose="Not applicable — used acutely pre-exercise",
        timing="60–120 min before exercise in hot conditions",
        duration="Acute — single pre-exercise dose",
        best_forms=["Glycerol powder (65% concentration)", "GlycerSize (patented)"],
        absorption_enhancers=["Co-ingest with large fluid volume (500–1200mL)"],
        absorption_inhibitors=[],
        food_interaction="Take with water, not food — the water is the delivery mechanism",
        onset_time="60–120 min for hyperhydration effect (plasma volume expansion)",
        washout="Renal clearance within 4–6 hours",
        ul_or_noael="No established UL; GI distress common above 1.5g/kg",
        contraindications=["Kidney disease", "Congestive heart failure", "Hypervolemia"],
        sport_specific_notes={
            "endurance": "Delays dehydration by 600–1000mL effective fluid retention; most useful in >60min events in heat",
            "combat_sports": "Can mask weight post-weigh-in via rapid fluid retention (controversial in combat sports)",
            "tactical": "Useful for sustained operations in heat where fluid access is limited",
        },
        evidence="🟡 Moderate — Consistent hyperhydration effect; performance benefit context-dependent",
        mechanism="Osmolyte distributed across total body water. Increases plasma volume by reducing renal "
                  "free water clearance (aquaporin-mediated). Creates a fluid reservoir that delays the "
                  "onset of dehydration during prolonged exercise in the heat",
        key_references=[
            "van Rosendal et al. (2010) Sports Med — Glycerol hyperhydration review",
            "Goulet et al. (2007) BJSM — Glycerol-induced hyperhydration meta-analysis",
        ],
    ),

    "collagen": DosingProtocol(
        name="Collagen Peptides / Gelatin",
        category="recovery",
        loading_dose=None,
        maintenance_dose="15g collagen peptides or gelatin, with 50mg vitamin C",
        timing="30–60 min before exercise or rehab session (peak amino acid delivery to tendon)",
        duration="Chronic — 12+ weeks for tendon adaptation; 6 months for injury recovery",
        best_forms=["Hydrolyzed collagen peptides (Type I)", "Gelatin (with vitamin C)"],
        absorption_enhancers=["Vitamin C (50–100mg — required cofactor for collagen synthesis)",
                              "Timing before exercise (loading maximizes tendon collagen synthesis rate)"],
        absorption_inhibitors=[],
        food_interaction="Can mix into any liquid; vitamin C co-ingestion is essential",
        onset_time="Peak plasma glycine/proline: 60 min; tendon adaptation: 3–6 months",
        washout="No accumulation; amino acids cleared normally",
        ul_or_noael="No established UL; 15–30g/d used safely in studies",
        contraindications=["Histamine intolerance (some collagen products trigger histamine release)"],
        sport_specific_notes={
            "endurance": "Patellar and Achilles tendinopathy prevention in runners",
            "strength": "Joint health under heavy loading; may reduce joint pain in older athletes",
            "combat_sports": "Supports connective tissue resilience under repetitive impact",
        },
        evidence="🟡 Moderate — Shaw et al. (2017) demonstrated doubled collagen synthesis rate with gelatin + vitamin C pre-exercise",
        mechanism="Provides glycine, proline, and hydroxyproline — rate-limiting amino acids for collagen "
                  "synthesis. When taken before exercise, mechanical loading drives the amino acids into "
                  "tendons/ligaments via the exercise-induced increase in collagen synthesis (peaks 6h post). "
                  "Vitamin C is a required cofactor for prolyl hydroxylase (collagen cross-linking)",
        key_references=[
            "Shaw et al. (2017) Am J Clin Nutr — Vitamin C–enriched gelatin and collagen synthesis",
            "Baar (2017) J Physiol — Minimizing injury and maximizing return to play",
        ],
    ),

    "vitamin_c": DosingProtocol(
        name="Vitamin C (Ascorbic Acid)",
        category="health",
        loading_dose=None,
        maintenance_dose="90–500mg/d (higher for immune support during heavy training: 500–1000mg/d)",
        timing="With meals; split doses >500mg across the day for better absorption",
        duration="Chronic; acute high-dose (1–2g) for cold prophylaxis during travel/competition",
        best_forms=["Ascorbic acid (standard)", "Liposomal vitamin C (higher bioavailability)", "Buffered sodium/calcium ascorbate (gentler on GI)"],
        absorption_enhancers=["Bioflavonoids (rose hips, citrus extract)", "Take with food"],
        absorption_inhibitors=["Smoking (increases turnover 30–50%)"],
        food_interaction="Take with meals; essential cofactor for iron absorption from plant sources",
        onset_time="Plasma: 2–3h; tissue saturation: 1–2 weeks at 200mg/d",
        washout="Water-soluble; excess excreted in urine within 24h",
        ul_or_noael="UL: 2000mg/d (GI distress, oxalate stone risk above this)",
        contraindications=["Hemochromatosis (increases iron absorption)", "Active kidney stones (oxalate risk)", "G6PD deficiency at high doses"],
        sport_specific_notes={
            "endurance": "Caution: high-dose vitamin C (>1g/d chronic) may blunt mitochondrial adaptation. Time around competition, not training.",
            "strength": "Collagen synthesis cofactor — essential for tendon adaptation (pair with collagen pre-exercise)",
            "combat_sports": "Useful for weight-cut immune support; acute dosing during dehydration phase",
        },
        evidence="🟢 Strong for scurvy prevention; 🟡 Moderate for immune support; 🟠 Weak for performance enhancement",
        mechanism="Essential cofactor for prolyl hydroxylase (collagen synthesis), dopamine-β-hydroxylase (catecholamine synthesis), "
                  "and carnitine biosynthesis. Antioxidant: recycles vitamin E, glutathione. Enhances non-heme iron absorption "
                  "3-6x via reduction of Fe³⁺ → Fe²⁺. CAUTION: chronic supra-physiological doses may blunt exercise-induced "
                  "hormesis (training adaptation) via excessive ROS quenching.",
        key_references=[
            "Peternelj & Coombes (2011) Sports Med — Antioxidant supplementation and exercise adaptation",
            "Carr & Maggini (2017) Nutrients — Vitamin C and immune function",
        ],
    ),

    "vitamin_b12": DosingProtocol(
        name="Vitamin B12 (Cobalamin)",
        category="health",
        loading_dose="1000mcg/d × 4–8 weeks for deficiency correction",
        maintenance_dose="2.4mcg/d RDA; 500–1000mcg/d for vegans/vegetarians; 1000mcg/d for athletes on metformin",
        timing="Morning with breakfast (may be stimulating for some)",
        duration="Chronic for vegetarians/vegans; periodic for omnivores",
        best_forms=["Methylcobalamin (bioactive, preferred)", "Adenosylcobalamin (mitochondrial active)", "Cyanocobalamin (cheapest, needs conversion)", "Hydroxocobalamin (injection form, long-acting)"],
        absorption_enhancers=["Intrinsic factor (naturally produced in stomach)", "Sublingual/injection bypasses intrinsic factor requirement"],
        absorption_inhibitors=["Metformin (reduces absorption 10–30%)", "PPIs/H2 blockers (reduce acid needed for release from food)", "H. pylori infection", "Atrophic gastritis (common >50y)"],
        food_interaction="With food for natural B12; sublingual/liposomal forms don't require food",
        onset_time="Serum rise: 1–2 days; clinical improvement in deficiency: 2–6 weeks",
        washout="Body stores 3–5 years worth (liver); true deficiency is slow to develop but slow to correct",
        ul_or_noael="No established UL; doses up to 2000mcg/d used safely",
        contraindications=["Leber's hereditary optic neuropathy (theoretical)", "Sensitivity to cobalt"],
        sport_specific_notes={
            "endurance": "Essential for RBC production; deficiency mimics anemia and impairs VO2max",
            "vegan_athletes": "MUST supplement — no reliable plant sources. Check MMA/holoTC, not just serum B12.",
            "tactical": "Deficiency common in those taking metformin for glucose management",
        },
        evidence="🟢 Strong for deficiency correction; 🟠 Weak for performance enhancement in replete individuals",
        mechanism="Cofactor for methionine synthase (homocysteine → methionine, one-carbon metabolism) and methylmalonyl-CoA mutase "
                  "(odd-chain fatty acid metabolism). Essential for DNA synthesis, myelin maintenance, and RBC production. "
                  "Deficiency → megaloblastic anemia, neuropathy, elevated homocysteine (cardiovascular risk)",
        key_references=[
            "Stabler (2013) NEJM — Vitamin B12 deficiency review",
            "Pawlak et al. (2013) Nutr Rev — B12 status in vegetarians",
        ],
    ),

    "folate": DosingProtocol(
        name="Folate / Methylfolate",
        category="health",
        loading_dose=None,
        maintenance_dose="400mcg DFE/d RDA; 600mcg/d pregnancy; 800–1000mcg/d for MTHFR polymorphism",
        timing="With meals; consistent daily timing",
        duration="Chronic; critical for women of childbearing age (prevents neural tube defects)",
        best_forms=["L-5-methyltetrahydrofolate (5-MTHF, active form)", "Folinic acid (leucovorin)", "Folic acid (synthetic, requires MTHFR conversion)"],
        absorption_enhancers=["Vitamin B12 (work synergistically in methylation)", "Vitamin B6 (pyridoxine)"],
        absorption_inhibitors=["Alcohol (reduces folate status)", "Methotrexate (folate antagonist)", "Some antiepileptics"],
        food_interaction="Take with meals; often combined with B-complex",
        onset_time="Serum rise: days; RBC folate (true status): 2–3 months",
        washout="RBC folate reflects 120-day RBC lifespan; chronic changes slow",
        ul_or_noael="UL: 1000mcg/d synthetic folic acid (masks B12 deficiency); no UL for methylfolate from food",
        contraindications=["Untreated B12 deficiency (folate masks hematologic signs while neuropathy progresses)", "Methotrexate therapy"],
        sport_specific_notes={
            "female_athletes": "Critical if planning pregnancy; 800mcg/d reduces NTD risk 70%",
            "endurance": "Supports RBC production and methylation under oxidative stress",
            "strength": "Methylation supports testosterone metabolism and DNA repair post-training",
        },
        evidence="🟢 Strong for NTD prevention; 🟡 Moderate for homocysteine lowering; 🟠 Weak for direct performance",
        mechanism="One-carbon metabolism — transfers methyl groups for DNA synthesis (thymidylate), methionine regeneration, "
                  "and methylation of proteins/DNA/neurotransmitters. MTHFR C677T polymorphism (30% of population) reduces "
                  "conversion of folic acid to active 5-MTHF — these individuals benefit from methylfolate supplementation.",
        key_references=[
            "Bailey et al. (2015) J Nutr — Folate and B12 requirements",
            "Greenberg et al. (2011) Rev Obstet Gynecol — MTHFR and pregnancy",
        ],
    ),

    "probiotics": DosingProtocol(
        name="Probiotics",
        category="health",
        loading_dose=None,
        maintenance_dose="1–10 billion CFU/d (multi-strain); 10–20 billion during antibiotic use or travel",
        timing="With food or just before meal (improves gut survival); consistent daily",
        duration="Chronic for gut health; acute for travel/antibiotic protection (2 weeks before + during + 2 weeks after)",
        best_forms=["Lactobacillus + Bifidobacterium multi-strain", "Saccharomyces boulardii (yeast, antibiotic-resistant)", "Spore-based Bacillus (shelf-stable)"],
        absorption_enhancers=["Prebiotic fiber (FOS, inulin) — feeds probiotics", "Polyphenol-rich foods"],
        absorption_inhibitors=["Heat >40°C (kills live strains)", "Stomach acid without enteric coating"],
        food_interaction="With small meal containing fat; avoid hot beverages within 30 min",
        onset_time="Stool changes: 1–2 weeks; immune effects: 4–8 weeks",
        washout="Colonization is transient — benefits persist only while taking",
        ul_or_noael="No established UL; doses up to 100 billion CFU/d well-tolerated",
        contraindications=["Severe immunocompromise (sepsis risk)", "Central venous catheter (rare bacteremia)", "Acute pancreatitis"],
        sport_specific_notes={
            "endurance": "Reduces URI frequency (upper respiratory infections) in heavy training; L. casei and B. lactis strongest evidence",
            "combat_sports": "Protect GI during weight cuts; useful during travel competitions",
            "tactical": "Useful during deployments, high-stress environments, antibiotic use",
        },
        evidence="🟡 Moderate for GI symptom management and immune support in athletes; strain-specific",
        mechanism="Modulates gut microbiota — competes with pathogens, produces SCFAs (butyrate → colonocyte fuel), "
                  "supports tight junction integrity (reducing endotoxemia), and interacts with gut-associated lymphoid tissue (GALT) "
                  "to modulate systemic immunity. Specific strains have distinct effects — not interchangeable.",
        key_references=[
            "West et al. (2014) Br J Sports Med — Probiotics and exercise-related immune function",
            "Pyne et al. (2015) Curr Sports Med Rep — Probiotics for athletes",
        ],
    ),

    "curcumin": DosingProtocol(
        name="Curcumin (Turmeric)",
        category="recovery",
        loading_dose=None,
        maintenance_dose="500–1500mg/d curcuminoids (with piperine 5–20mg or liposomal form)",
        timing="With fat-containing meal (lipid-soluble); split BID for sustained levels",
        duration="Chronic for anti-inflammatory effect; acute pre-/post-workout for DOMS reduction",
        best_forms=["Meriva (phytosome, 29x bioavailability)", "Theracurmin (nanoparticle, 27x)", "Curcumin + piperine 95:5 (BioPerine, 20x)", "Liposomal curcumin"],
        absorption_enhancers=["Piperine (inhibits glucuronidation)", "Dietary fat (lipid-soluble)", "Liposomal/phytosome delivery systems"],
        absorption_inhibitors=["Low-fat intake", "Plain curcumin without bioenhancer (absorbed <1%)"],
        food_interaction="Requires fat for absorption; take with meal containing 10g+ fat",
        onset_time="Acute anti-inflammatory: 2–4h; chronic effects: 4–8 weeks",
        washout="Plasma half-life 2–6h depending on formulation",
        ul_or_noael="No established UL; up to 12g/d used in clinical trials without serious AE",
        contraindications=["Gallbladder disease (stimulates bile)", "Anticoagulants (mild platelet inhibition)", "Before surgery (stop 2 weeks prior)"],
        sport_specific_notes={
            "strength": "Reduces DOMS and CK post-eccentric exercise; 1500mg/d starting 7 days pre-training block",
            "endurance": "May preserve mitochondrial function; caution with chronic high-dose (antioxidant may blunt adaptation)",
            "combat_sports": "Useful for joint/tendon inflammation in repetitive-impact sports",
        },
        evidence="🟡 Moderate for DOMS reduction and joint inflammation; 🟢 Strong for molecular anti-inflammatory effects in vitro",
        mechanism="Pleiotropic anti-inflammatory: inhibits NF-κB signaling, reduces COX-2 and iNOS expression, modulates "
                  "JAK-STAT and MAPK pathways. Antioxidant via direct ROS scavenging and Nrf2 pathway activation. "
                  "Inhibits NLRP3 inflammasome. Poor oral bioavailability without bioenhancers (extensive glucuronidation + sulfation).",
        key_references=[
            "Fang & Bao (2022) Eur J Appl Physiol — Curcumin for exercise recovery meta-analysis",
            "Hewlings & Kalman (2017) Foods — Curcumin bioavailability and efficacy",
        ],
    ),

    "quercetin": DosingProtocol(
        name="Quercetin",
        category="ergogenic",
        loading_dose=None,
        maintenance_dose="500–1000mg/d (often 500mg BID)",
        timing="With meals (improves absorption); 1–2h pre-workout for acute ergogenic effect",
        duration="Chronic loading 1–2 weeks before endurance event; may be taken year-round for immune support",
        best_forms=["Quercetin dihydrate (standard)", "Quercetin phytosome (Lecithin complex, better bioavailability)", "EMIQ (enzymatically modified, ~40x absorbed)"],
        absorption_enhancers=["Bromelain/papain (proteolytic enzymes)", "Vitamin C (synergistic)", "Dietary fat"],
        absorption_inhibitors=["Plain quercetin glycosides (lower bioavailability than aglycone)"],
        food_interaction="With meal containing fat; quercetin from onions/apples has better bioavailability than pure supplement",
        onset_time="Plasma: 2–4h; performance effects: 7–14 days chronic loading",
        washout="Half-life ~16h; accumulates with repeated dosing",
        ul_or_noael="No established UL; 1000mg/d well-tolerated; >1500mg/d may cause headache, GI upset",
        contraindications=["Cyclosporine therapy (quercetin inhibits P-glycoprotein)", "Chronic kidney disease (high doses)", "Pregnancy (insufficient data)"],
        sport_specific_notes={
            "endurance": "Meta-analysis shows +2-3% VO2max and +11% endurance capacity with 1000mg/d × 2 weeks",
            "combat_sports": "Useful during weight cuts for immune support; blunts URI incidence under training stress",
            "tactical": "Military research shows improved cognitive performance under stress",
        },
        evidence="🟡 Moderate for endurance performance and immune modulation; synergistic with caffeine",
        mechanism="Flavonoid with multiple mechanisms: inhibits adenosine A1 receptors (adenosine antagonist, caffeine-like), "
                  "enhances mitochondrial biogenesis via PGC-1α upregulation, potent antioxidant, anti-inflammatory via NF-κB inhibition. "
                  "May improve endothelial function via nitric oxide preservation. Synergizes with caffeine — combined dose "
                  "enhances both acute and chronic adaptations.",
        key_references=[
            "Kressler et al. (2011) Med Sci Sports Exerc — Quercetin and endurance meta-analysis",
            "Nieman et al. (2007) Med Sci Sports Exerc — Quercetin immunomodulation in athletes",
        ],
    ),

    "sodium_bicarbonate": DosingProtocol(
        name="Sodium Bicarbonate",
        category="ergogenic",
        loading_dose="0.3g/kg, 60–90 min pre-exercise (serial loading: 0.1g/kg × 3 doses over 90 min to reduce GI issues)",
        maintenance_dose="0.3g/kg acute; or chronic loading 0.5g/kg/d split across meals for 3–5 days",
        timing="60–90 min pre-exercise (acute); or chronic loading 3–5 days before competition",
        duration="Acute (single dose) or short-term chronic (3–5 day loading)",
        best_forms=["Sodium bicarbonate capsules (reduces GI distress vs. solution)",
                    "Powder dissolved in water (faster absorption but more GI issues)"],
        absorption_enhancers=["Co-ingest with small carb-rich meal (delays absorption, reduces GI distress)"],
        absorption_inhibitors=[],
        food_interaction="Take with small meal to reduce nausea; avoid carbonated beverages",
        onset_time="Peak blood bicarbonate: 60–90 min post-ingestion",
        washout="Renal clearance within 4–6 hours",
        ul_or_noael="Acute dose >0.4g/kg significantly increases GI distress; no long-term UL established",
        contraindications=["Hypertension (sodium load)", "Kidney disease", "Metabolic alkalosis",
                           "Low-sodium diet prescriptions"],
        sport_specific_notes={
            "endurance": "Most effective for efforts lasting 1–7 min (high-intensity, glycolytic); e.g., 800m–1500m, rowing, 4km cycling TT",
            "strength": "May enhance muscular endurance (rep count) at moderate loads; less effective for 1RM",
            "combat_sports": "Enhances repeated high-intensity bout performance; useful for multi-round combat",
        },
        evidence="🟢 Strong — Well-established ergogenic effect in meta-analyses for high-intensity exercise",
        mechanism="Increases blood buffering capacity (raises bicarbonate concentration and blood pH). "
                  "Enhances efflux of H⁺ and lactate from working muscle via MCT1/MCT4 transporters "
                  "(increased extracellular pH gradient). Delays intramuscular acidosis during glycolytic "
                  "exercise, extending time to fatigue at intensities above lactate threshold",
        key_references=[
            "Carr et al. (2011) IJSN — Sodium bicarbonate and exercise performance meta-analysis",
            "McNaughton et al. (2016) Sports Med — Sodium bicarbonate position stand",
        ],
    ),
}

# ── Aliases ──────────────────────────────────────────────────────────────────

SUPPLEMENT_ALIASES: dict[str, str] = {
    "creatine monohydrate": "creatine",
    "cm": "creatine",
    "creapure": "creatine",
    "coffee": "caffeine",
    "beta alanine": "beta_alanine",
    "ba": "beta_alanine",
    "carnosyn": "beta_alanine",
    "beetroot": "nitrate",
    "beet juice": "nitrate",
    "beetroot juice": "nitrate",
    "no3": "nitrate",
    "sodium nitrate": "nitrate",
    "vit d": "vitamin_d",
    "d3": "vitamin_d",
    "cholecalciferol": "vitamin_d",
    "fish oil": "omega_3",
    "epa": "omega_3",
    "dha": "omega_3",
    "epa/dha": "omega_3",
    "krill oil": "omega_3",
    "mag": "magnesium",
    "mg": "magnesium",
    "mag glycinate": "magnesium",
    "threonate": "magnesium",
    "hmb-fa": "hmb",
    "hmb free acid": "hmb",
    "beta-hydroxy": "hmb",
    "ksm-66": "ashwagandha",
    "sensoril": "ashwagandha",
    "withania": "ashwagandha",
    "ferrous sulfate": "iron",
    "ferrous bisglycinate": "iron",
    "fe": "iron",
    "l-citrulline": "citrulline",
    "citrulline malate": "citrulline",
    "l-taurine": "taurine",
    "l-tyrosine": "tyrosine",
    "nalt": "tyrosine",
    "n-acetyl-l-tyrosine": "tyrosine",
    "sleep": "melatonin",
    "zn": "zinc",
    "zinc picolinate": "zinc",
    "zinc bisglycinate": "zinc",
    "carnitine": "l_carnitine",
    "l-carnitine": "l_carnitine",
    "lclt": "l_carnitine",
    "alcar": "l_carnitine",
    "acetyl-l-carnitine": "l_carnitine",
    "glycerine": "glycerol",
    "glycerine powder": "glycerol",
    "glycersize": "glycerol",
    "collagen peptides": "collagen",
    "gelatin": "collagen",
    "type 1 collagen": "collagen",
    "bicarb": "sodium_bicarbonate",
    "baking soda": "sodium_bicarbonate",
    "nahco3": "sodium_bicarbonate",
    "soda loading": "sodium_bicarbonate",
    "ascorbic acid": "vitamin_c",
    "vit c": "vitamin_c",
    "c": "vitamin_c",
    "cobalamin": "vitamin_b12",
    "methylcobalamin": "vitamin_b12",
    "b12": "vitamin_b12",
    "vit b12": "vitamin_b12",
    "methylfolate": "folate",
    "5-mthf": "folate",
    "folic acid": "folate",
    "l-methylfolate": "folate",
    "probiotic": "probiotics",
    "lactobacillus": "probiotics",
    "bifidobacterium": "probiotics",
    "turmeric": "curcumin",
    "meriva": "curcumin",
    "theracurmin": "curcumin",
    "flavonoid": "quercetin",
}


def resolve_supplement(name: str) -> Optional[DosingProtocol]:
    """Look up a supplement by name or alias."""
    key = name.lower().strip().replace("-", "_").replace(" ", "_")
    if key in SUPPLEMENT_DB:
        return SUPPLEMENT_DB[key]
    alias_key = SUPPLEMENT_ALIASES.get(name.lower().strip())
    if alias_key and alias_key in SUPPLEMENT_DB:
        return SUPPLEMENT_DB[alias_key]
    return None


def format_dosing_protocol(protocol: DosingProtocol, sport: str = "general") -> str:
    """Human-readable dosing protocol report."""
    lines = [
        f"═══ {protocol.name} ═══",
        f"Category: {protocol.category.title()}",
        f"Evidence: {protocol.evidence}",
        "",
        "── Dosing ──",
    ]
    if protocol.loading_dose:
        lines.append(f"  Loading  : {protocol.loading_dose}")
    lines.append(f"  Maintain : {protocol.maintenance_dose}")
    lines.append(f"  Timing   : {protocol.timing}")
    lines.append(f"  Duration : {protocol.duration}")
    lines.append(f"  Onset    : {protocol.onset_time}")

    lines += [
        "",
        "── Forms (bioavailability-ranked) ──",
    ]
    for i, form in enumerate(protocol.best_forms, 1):
        lines.append(f"  {i}. {form}")

    lines += [
        "",
        "── Absorption ──",
        f"  Enhancers  : {', '.join(protocol.absorption_enhancers) or 'None significant'}",
        f"  Inhibitors : {', '.join(protocol.absorption_inhibitors) or 'None significant'}",
        f"  Food       : {protocol.food_interaction}",
    ]

    if protocol.ul_or_noael:
        lines += ["", f"── Safety ──", f"  UL/NOAEL: {protocol.ul_or_noael}"]
    if protocol.contraindications:
        lines.append(f"  Avoid if : {'; '.join(protocol.contraindications)}")

    # Sport-specific notes
    sport_note = protocol.sport_specific_notes.get(
        sport.lower(), protocol.sport_specific_notes.get("general", "")
    )
    if sport_note:
        lines += ["", f"── Sport Note ({sport}) ──", f"  {sport_note}"]

    lines += [
        "",
        "── Mechanism ──",
        f"  {protocol.mechanism}",
        "",
        "── References ──",
    ]
    for ref in protocol.key_references:
        lines.append(f"  • {ref}")

    return "\n".join(lines)


def list_supplements_by_category(category: Optional[str] = None) -> str:
    """List all supplements grouped by category."""
    categories: dict[str, list[str]] = {}
    for key, proto in SUPPLEMENT_DB.items():
        cat = proto.category
        if category and cat != category:
            continue
        categories.setdefault(cat, []).append(f"{proto.name} ({key}) — {proto.evidence}")

    lines = ["═══ Kiwi Supplement Database ═══", ""]
    for cat, supplements in sorted(categories.items()):
        lines.append(f"  [{cat.upper()}]")
        for s in supplements:
            lines.append(f"    • {s}")
        lines.append("")

    lines.append(f"  Total: {sum(len(v) for v in categories.values())} supplements")
    return "\n".join(lines)
