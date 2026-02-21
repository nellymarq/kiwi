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
