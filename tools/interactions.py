"""
Supplement Interaction Checker — evidence-based interaction database + Claude analysis.

Covers:
- Supplement–supplement interactions
- Supplement–drug interactions
- Nutrient depletion patterns
- Synergistic combinations

Data hierarchy:
  Level A: High-quality RCTs / systematic reviews (labeled 🟢)
  Level B: Clinical case series / pharmacokinetic data (labeled 🟡)
  Level C: Mechanistic / theoretical / in vitro (labeled 🟠)
  Level D: Anecdotal / preliminary (labeled 🔵)

If an interaction isn't in the local database, the analyzer falls back to
Claude Opus 4.6 with adaptive thinking for evidence synthesis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import anthropic

# ── Interaction severity ───────────────────────────────────────────────────────

Severity = Literal["synergistic", "safe", "monitor", "caution", "avoid"]

SEVERITY_EMOJI = {
    "synergistic": "🤝",
    "safe": "✅",
    "monitor": "👁️",
    "caution": "⚠️",
    "avoid": "🚫",
}

SEVERITY_ORDER = {"avoid": 0, "caution": 1, "monitor": 2, "safe": 3, "synergistic": 4}


@dataclass
class Interaction:
    compound_a: str
    compound_b: str
    severity: Severity
    mechanism: str
    evidence_tier: str   # 🟢 / 🟡 / 🟠 / 🔵
    recommendation: str
    sources: list[str] = field(default_factory=list)

    def display(self) -> str:
        emoji = SEVERITY_EMOJI[self.severity]
        return (
            f"{emoji} {self.compound_a.title()} + {self.compound_b.title()}\n"
            f"   Severity: {self.severity.upper()} {self.evidence_tier}\n"
            f"   Mechanism: {self.mechanism}\n"
            f"   Recommendation: {self.recommendation}\n"
            + (f"   Sources: {', '.join(self.sources)}\n" if self.sources else "")
        )


# ── Evidence-based interaction database ───────────────────────────────────────

INTERACTION_DB: list[Interaction] = [
    # ── Synergistic combinations ──────────────────────────────────────────────
    Interaction(
        compound_a="creatine", compound_b="beta-alanine",
        severity="synergistic",
        mechanism="Creatine replenishes PCr for explosive power; beta-alanine buffers H+ during high-intensity glycolysis. Complementary energy system support.",
        evidence_tier="🟡",
        recommendation="Safe to combine. Creatine 3–5g/day + beta-alanine 3.2–6.4g/day. Stack timing not critical.",
        sources=["Zoeller et al. 2007 IJSN", "ISSN 2010 Position Stand"],
    ),
    Interaction(
        compound_a="caffeine", compound_b="l-theanine",
        severity="synergistic",
        mechanism="L-theanine attenuates caffeine-induced jitteriness and anxiety via GABA modulation while preserving cognitive enhancement effects.",
        evidence_tier="🟢",
        recommendation="Optimal ratio 2:1 (theanine:caffeine). 200mg L-theanine + 100mg caffeine. Enhances focus without overstimulation.",
        sources=["Haskell et al. 2008 Biol Psych", "Dodd et al. 2015 Nutr Rev"],
    ),
    Interaction(
        compound_a="vitamin d3", compound_b="vitamin k2",
        severity="synergistic",
        mechanism="Vitamin D3 upregulates calcium-binding proteins; K2 (MK-7) activates matrix GLA protein to direct calcium to bone rather than arteries.",
        evidence_tier="🟡",
        recommendation="Combine for bone density. D3 2000–4000 IU + K2 (MK-7) 100–200mcg daily. Critical for athletes with high bone stress.",
        sources=["Maresz 2015 Integ Med", "Kidd 2010 Alt Med Rev"],
    ),
    Interaction(
        compound_a="zinc", compound_b="magnesium",
        severity="synergistic",
        mechanism="ZMA (zinc + magnesium + B6) combination supports testosterone production, sleep quality, and recovery. Both are commonly depleted in athletes.",
        evidence_tier="🟡",
        recommendation="ZMA protocol: 30mg zinc + 450mg magnesium + 10.5mg B6 before bed on empty stomach.",
        sources=["Brilla & Conte 2000 J Ex Phys", "Kilic et al. 2010 Neuro Endocrinol"],
    ),
    Interaction(
        compound_a="vitamin c", compound_b="iron",
        severity="synergistic",
        mechanism="Vitamin C (ascorbic acid) reduces Fe³⁺ to Fe²⁺, dramatically enhancing non-heme iron absorption (up to 3-fold increase).",
        evidence_tier="🟢",
        recommendation="Take 250–500mg vitamin C with iron-rich meals or iron supplements. Critical for plant-based athletes.",
        sources=["Hallberg et al. 1989 Am J Clin Nutr", "Lynch 2011 Int J Vitam Nutr Res"],
    ),
    Interaction(
        compound_a="protein", compound_b="creatine",
        severity="synergistic",
        mechanism="No direct pharmacological synergy, but combined intake post-exercise maximizes mTOR activation (leucine) and PCr resynthesis.",
        evidence_tier="🟢",
        recommendation="Post-workout: 20–40g protein + 3–5g creatine. Timing within 30-min post-exercise optimal.",
        sources=["Cribb & Hayes 2006 Med Sci Sports", "ISSN 2017 Creatine Stand"],
    ),

    # ── Monitor combinations ──────────────────────────────────────────────────
    Interaction(
        compound_a="caffeine", compound_b="creatine",
        severity="monitor",
        mechanism="Early studies suggested caffeine impaired creatine phosphorylation; more recent research shows no significant interaction at standard doses.",
        evidence_tier="🟡",
        recommendation="Current evidence: safe to combine. However, high caffeine (>600mg/day) may impair PCr recovery. Moderate caffeine fine.",
        sources=["Vandenberghe et al. 1996 J Appl Physiol", "Hespel et al. 2002 J Appl Physiol"],
    ),
    Interaction(
        compound_a="beta-alanine", compound_b="sodium bicarbonate",
        severity="synergistic",
        mechanism="Both buffer acidosis via different mechanisms: BA increases carnosine (intracellular); NaHCO3 buffers extracellular pH. Additive effect.",
        evidence_tier="🟡",
        recommendation="Combine for events 1–10 min. NaHCO3 0.3g/kg + BA 3.2g/day. NaHCO3 GI distress risk — test in training first.",
        sources=["Sale et al. 2011 Int J Sport Nutr", "Jones et al. 2016 EJAP"],
    ),
    Interaction(
        compound_a="st john's wort", compound_b="caffeine",
        severity="caution",
        mechanism="St John's Wort induces CYP1A2, the primary caffeine-metabolizing enzyme, potentially altering caffeine clearance rates.",
        evidence_tier="🟠",
        recommendation="If taking St John's Wort, caffeine sensitivity may change. Start with lower doses and monitor response.",
        sources=["Dresser et al. 2003 Clin Pharmacol Ther"],
    ),

    # ── Caution combinations ──────────────────────────────────────────────────
    Interaction(
        compound_a="iron", compound_b="calcium",
        severity="caution",
        mechanism="Calcium competitively inhibits iron absorption via shared DMT1 transporter. Dairy-based calcium most problematic.",
        evidence_tier="🟢",
        recommendation="Separate iron supplements/high-iron meals from dairy/calcium supplements by 2+ hours.",
        sources=["Hallberg 1998 Scand J Nutr", "Lönnerdal 2010 J Nutr"],
    ),
    Interaction(
        compound_a="zinc", compound_b="iron",
        severity="caution",
        mechanism="High-dose zinc (>40mg/day) competes with iron for absorption via DMT1. Relevant for athletes supplementing both.",
        evidence_tier="🟢",
        recommendation="Take zinc and iron supplements at different times. Whole food sources show less competition than supplements.",
        sources=["Solomons 1986 J Nutr", "Whittaker 1998 Am J Clin Nutr"],
    ),
    Interaction(
        compound_a="vitamin e", compound_b="fish oil",
        severity="caution",
        mechanism="High-dose fish oil increases oxidative stress from PUFA peroxidation; vitamin E may partially mitigate but high doses of both unneeded.",
        evidence_tier="🟠",
        recommendation="If taking >3g/day EPA+DHA, include adequate dietary vitamin E. High supplemental doses of both not recommended.",
        sources=["Higdon & Frei 2001 Biofactors"],
    ),

    # ── Avoid combinations ────────────────────────────────────────────────────
    Interaction(
        compound_a="melatonin", compound_b="caffeine",
        severity="avoid",
        mechanism="Caffeine is an adenosine antagonist that directly blocks melatonin's sleep-promoting mechanisms. CYP1A2 also metabolizes both — competitive inhibition.",
        evidence_tier="🟢",
        recommendation="Do not consume caffeine <6 hours before melatonin administration. Caffeine half-life 5–6 hours; consider genetic variation (CYP1A2 fast/slow metabolizers).",
        sources=["Viola et al. 2007 Physiol Behav", "Drake et al. 2013 J Clin Sleep Med"],
    ),
    Interaction(
        compound_a="warfarin", compound_b="vitamin k",
        severity="avoid",
        mechanism="Warfarin's anticoagulant mechanism antagonizes vitamin K. Even moderate vitamin K intake changes INR significantly.",
        evidence_tier="🟢",
        recommendation="CRITICAL: Athletes on anticoagulation therapy must not alter vitamin K intake without physician guidance. Consistent (not zero) intake is the goal.",
        sources=["Schurgers et al. 2004 Thromb Haemost", "FDA Warfarin prescribing info"],
    ),
    Interaction(
        compound_a="5-htp", compound_b="ssri",
        severity="avoid",
        mechanism="5-HTP increases serotonin precursor availability; SSRIs block serotonin reuptake. Combined risk of serotonin syndrome.",
        evidence_tier="🟡",
        recommendation="CONTRAINDICATED: Do not combine 5-HTP with any serotonergic medication without medical supervision.",
        sources=["Turner et al. 2006 Psychopharmacology"],
    ),

    # ── New interactions for expanded supplement DB ──────────────────────────

    Interaction(
        compound_a="citrulline", compound_b="nitrate",
        severity="synergistic",
        mechanism="Citrulline provides arginine substrate for eNOS; nitrates provide NO via nitrate→nitrite→NO pathway. Dual NO pathway activation.",
        evidence_tier="🟡",
        recommendation="Combine for enhanced nitric oxide production. 6g citrulline + 400mg nitrate (from beetroot). Take 60–90 min pre-exercise.",
        sources=["Bailey et al. 2015 Free Radic Biol Med"],
    ),
    Interaction(
        compound_a="citrulline", compound_b="pde5 inhibitors",
        severity="caution",
        mechanism="Both increase NO signaling — citrulline via arginine/eNOS, PDE5 inhibitors by preventing cGMP breakdown. Additive vasodilation and hypotension risk.",
        evidence_tier="🟡",
        recommendation="Use with caution. May cause excessive blood pressure drop. Consult physician before combining.",
        sources=["Schwedhelm et al. 2008 Br J Clin Pharmacol"],
    ),
    Interaction(
        compound_a="taurine", compound_b="beta-alanine",
        severity="monitor",
        mechanism="Share the same membrane transporter (TauT/SLC6A6). Chronic beta-alanine loading can reduce intracellular taurine by 15–20% via competitive inhibition.",
        evidence_tier="🟡",
        recommendation="If stacking long-term, supplement taurine 1–2g/d to offset depletion. Separate doses by 2+ hours.",
        sources=["Harris et al. 2006 Amino Acids", "Blancquaert et al. 2017 Med Sci Sports Exerc"],
    ),
    Interaction(
        compound_a="zinc", compound_b="copper",
        severity="caution",
        mechanism="Chronic zinc >40mg/d induces metallothionein in enterocytes which sequesters copper, causing secondary copper deficiency (sideroblastic anemia, neutropenia).",
        evidence_tier="🟢",
        recommendation="If supplementing zinc >30mg/d for >8 weeks, add 1–2mg copper daily. Monitor ceruloplasmin if symptomatic.",
        sources=["Prasad et al. 1978 JAMA", "IOM Dietary Reference Intakes for Zinc"],
    ),
    Interaction(
        compound_a="melatonin", compound_b="benzodiazepines",
        severity="caution",
        mechanism="Additive sedation via overlapping GABAergic and MT1/MT2 mechanisms. May cause excessive drowsiness, impaired coordination.",
        evidence_tier="🟡",
        recommendation="Do not combine without medical supervision. If used together, reduce melatonin to 0.3–0.5mg.",
        sources=["Garfinkel et al. 1999 Lancet"],
    ),
    Interaction(
        compound_a="tyrosine", compound_b="levodopa",
        severity="caution",
        mechanism="Compete for the same amino acid transporter (LAT1) across the blood-brain barrier. Tyrosine can reduce levodopa brain uptake.",
        evidence_tier="🟡",
        recommendation="Separate by 2+ hours. Patients on levodopa should not supplement tyrosine without neurologist guidance.",
        sources=["Growdon et al. 1982 Life Sci"],
    ),
    Interaction(
        compound_a="l-carnitine", compound_b="thyroid hormone",
        severity="caution",
        mechanism="L-carnitine inhibits thyroid hormone entry into the cell nucleus, potentially reducing T3/T4 action. Therapeutic in hyperthyroidism but problematic in hypothyroidism.",
        evidence_tier="🟡",
        recommendation="Hypothyroid patients on levothyroxine should monitor TSH if starting carnitine. May need dose adjustment.",
        sources=["Benvenga et al. 2004 Ann NY Acad Sci"],
    ),
    Interaction(
        compound_a="l-carnitine", compound_b="creatine",
        severity="synergistic",
        mechanism="Carnitine enhances fat oxidation (sparing glycogen); creatine enhances PCr resynthesis. Complementary energy system support at different intensities.",
        evidence_tier="🟠",
        recommendation="Safe to combine. Both require chronic loading. Take carnitine with carb meal, creatine any time.",
        sources=["Theoretical; no direct RCT on combination"],
    ),
    Interaction(
        compound_a="ashwagandha", compound_b="caffeine",
        severity="synergistic",
        mechanism="Ashwagandha reduces cortisol (via HPA axis modulation); caffeine acutely raises cortisol. Ashwagandha may buffer caffeine's cortisol spike while preserving alertness.",
        evidence_tier="🟠",
        recommendation="Safe to combine. Ashwagandha 300–600mg/d + caffeine as needed. May reduce jitteriness via GABAergic anxiolytic effect.",
        sources=["Chandrasekhar et al. 2012 Indian J Psychol Med", "Mechanistic rationale"],
    ),
    Interaction(
        compound_a="ashwagandha", compound_b="thyroid medication",
        severity="caution",
        mechanism="Ashwagandha may increase thyroid hormone levels (T3, T4) via stimulation of thyroid peroxidase activity. Can alter levothyroxine dosing requirements.",
        evidence_tier="🟡",
        recommendation="Monitor thyroid function if combining. May need levothyroxine dose adjustment. Contraindicated in hyperthyroidism.",
        sources=["Sharma et al. 2018 J Altern Complement Med"],
    ),
    Interaction(
        compound_a="omega-3", compound_b="anticoagulants",
        severity="caution",
        mechanism="Omega-3 fatty acids (EPA/DHA >3g/d) have mild antiplatelet and antithrombotic effects. Additive bleeding risk with warfarin, aspirin, or DOACs.",
        evidence_tier="🟡",
        recommendation="At standard doses (1–2g EPA+DHA) risk is low. Above 3g/d, monitor INR if on warfarin. Inform surgeon pre-operatively.",
        sources=["Gross et al. 2017 Thromb Res", "FDA safety communication 2014"],
    ),
    Interaction(
        compound_a="omega-3", compound_b="vitamin e",
        severity="synergistic",
        mechanism="Vitamin E protects polyunsaturated omega-3 fatty acids from lipid peroxidation. Many fish oil supplements include vitamin E as an antioxidant preservative.",
        evidence_tier="🟢",
        recommendation="Safe and beneficial to combine. 200–400 IU vitamin E with omega-3 supplements to prevent oxidation.",
        sources=["Ramos et al. 2008 Clin Nutr"],
    ),
    Interaction(
        compound_a="sodium bicarbonate", compound_b="caffeine",
        severity="synergistic",
        mechanism="Bicarb buffers H+ (peripheral), caffeine enhances CNS drive and adenosine blockade (central). Dual pathway performance enhancement.",
        evidence_tier="🟡",
        recommendation="Combine for high-intensity events (1–7 min). Take bicarb 0.3g/kg 60 min pre + caffeine 3mg/kg 30 min pre. GI distress risk increases with combination.",
        sources=["Higgins et al. 2016 JISSN", "Grgic & Mikulic 2021 J Sci Med Sport"],
    ),
    Interaction(
        compound_a="collagen", compound_b="vitamin c",
        severity="synergistic",
        mechanism="Vitamin C is a required cofactor for prolyl hydroxylase, the enzyme that cross-links collagen fibrils. Without vitamin C, collagen synthesis is impaired (scurvy mechanism).",
        evidence_tier="🟢",
        recommendation="ESSENTIAL combination: 15g collagen/gelatin + 50mg vitamin C, 30–60 min before exercise. Shaw et al. showed doubled collagen synthesis rate.",
        sources=["Shaw et al. 2017 Am J Clin Nutr", "DePhillipo et al. 2018 OJSM"],
    ),
    Interaction(
        compound_a="vitamin d", compound_b="magnesium",
        severity="synergistic",
        mechanism="Magnesium is required for vitamin D metabolism — it's a cofactor for 25-hydroxylase (liver) and 1α-hydroxylase (kidney) that convert D3 to active 1,25(OH)2D.",
        evidence_tier="🟡",
        recommendation="Co-supplement for optimal vitamin D activation. Mg deficiency can cause functional vitamin D deficiency even with adequate D3 intake.",
        sources=["Uwitonze & Razzaque 2018 J Am Osteopath Assoc", "Deng et al. 2013 BMC Med"],
    ),
    Interaction(
        compound_a="hmb", compound_b="creatine",
        severity="synergistic",
        mechanism="HMB reduces muscle protein breakdown (via ubiquitin-proteasome inhibition); creatine enhances MPS and PCr stores. Complementary anabolic/anti-catabolic pathways.",
        evidence_tier="🟡",
        recommendation="Safe to combine. 3g HMB-FA/d + 3–5g creatine/d. Most useful during caloric restriction or overreaching phases to preserve lean mass.",
        sources=["Jówko et al. 2001 Nutrition", "Wilson et al. 2013 JISSN"],
    ),
    Interaction(
        compound_a="glycerol", compound_b="creatine",
        severity="synergistic",
        mechanism="Both act as intracellular osmolytes. Creatine increases cell volume (ICF); glycerol expands total body water (ECF + ICF). Combined hyperhydration effect.",
        evidence_tier="🟠",
        recommendation="May enhance hyperhydration in heat. 1.2g/kg glycerol + standard creatine loading. Experimental — limited RCT data on combination.",
        sources=["Easton et al. 2007 IJSN"],
    ),
]

# Build lookup index for fast searching
_INDEX: dict[str, list[Interaction]] = {}
for _i in INTERACTION_DB:
    for _key in [_i.compound_a, _i.compound_b]:
        _INDEX.setdefault(_key.lower(), []).append(_i)


# ── Public API ─────────────────────────────────────────────────────────────────

def lookup_interactions(
    compounds: list[str],
    min_severity: Severity = "monitor",
) -> list[Interaction]:
    """
    Find all known interactions between a list of compounds.
    Returns interactions sorted by severity (most dangerous first).
    """
    compounds_lower = [c.lower().strip() for c in compounds]
    found: set[int] = set()
    results: list[Interaction] = []

    for comp in compounds_lower:
        for interaction in _INDEX.get(comp, []):
            obj_id = id(interaction)
            if obj_id in found:
                continue

            # Check if both parties are in the requested compound list
            a = interaction.compound_a.lower()
            b = interaction.compound_b.lower()
            if a in compounds_lower and b in compounds_lower:
                # Both specified — always include regardless of min_severity
                results.append(interaction)
                found.add(obj_id)
            elif a in compounds_lower or b in compounds_lower:
                # One specified — only include if at or above severity threshold
                if SEVERITY_ORDER.get(interaction.severity, 4) <= SEVERITY_ORDER.get(min_severity, 2):
                    results.append(interaction)
                    found.add(obj_id)

    return sorted(results, key=lambda x: SEVERITY_ORDER.get(x.severity, 4))


def lookup_single(compound: str) -> list[Interaction]:
    """Get all known interactions for a single compound."""
    comp = compound.lower().strip()
    return sorted(
        _INDEX.get(comp, []),
        key=lambda x: SEVERITY_ORDER.get(x.severity, 4),
    )


def format_interaction_report(
    compounds: list[str],
    interactions: list[Interaction],
) -> str:
    """Format a complete interaction report for display."""
    lines = [
        f"Supplement Interaction Report",
        f"Compounds checked: {', '.join(c.title() for c in compounds)}",
        f"Total interactions found: {len(interactions)}",
        "=" * 60,
    ]

    if not interactions:
        lines.append("\n✅ No significant interactions found in database.")
        lines.append("Note: Database covers common athletic supplements.")
        lines.append("For novel compounds, use Claude analysis (/check <compound>).")
        return "\n".join(lines)

    by_severity: dict[str, list[Interaction]] = {}
    for i in interactions:
        by_severity.setdefault(i.severity, []).append(i)

    for sev in ["avoid", "caution", "monitor", "synergistic", "safe"]:
        group = by_severity.get(sev, [])
        if not group:
            continue
        emoji = SEVERITY_EMOJI[sev]
        lines.append(f"\n{emoji} {sev.upper()} ({len(group)})")
        lines.append("-" * 40)
        for ix in group:
            lines.append(ix.display())

    return "\n".join(lines)


# ── Claude Fallback for Novel Compounds ──────────────────────────────────────

NOVEL_COMPOUND_SYSTEM = """\
You are a pharmacology and sports nutrition specialist. When given compounds \
that are not in the local interaction database, analyze potential interactions \
using your knowledge of:
- Pharmacokinetics (absorption, metabolism, CYP enzyme interactions)
- Pharmacodynamics (receptor competition, synergistic/antagonistic effects)
- Clinical evidence and case reports
- Theoretical mechanistic concerns

For each interaction found, provide:
1. Severity: synergistic / safe / monitor / caution / avoid
2. Evidence tier: 🟢 Strong | 🟡 Moderate | 🟠 Weak | 🔵 Emerging
3. Mechanism of interaction
4. Practical recommendation

Be specific and evidence-grounded. If evidence is limited, say so explicitly. \
Never fabricate references — cite only well-known landmark studies or state \
"mechanistic basis only" when appropriate.\
"""


async def analyze_novel_interactions(
    client: anthropic.AsyncAnthropic,
    compounds: list[str],
    on_text=None,
) -> str:
    """
    Use Claude to analyze interactions for compounds not in the local DB.

    Falls back to Claude Opus 4.6 with adaptive thinking when the local
    interaction database has no data for one or more compounds.

    Args:
        client: AsyncAnthropic client.
        compounds: List of compound names to check.
        on_text: Optional streaming callback.

    Returns:
        Analysis text from Claude.
    """
    prompt = (
        f"Analyze potential interactions between these compounds:\n"
        f"{', '.join(c.title() for c in compounds)}\n\n"
        f"For each pair with a meaningful interaction, provide severity, "
        f"evidence tier, mechanism, and recommendation. If a compound is "
        f"obscure, note limited evidence availability."
    )

    messages = [{"role": "user", "content": prompt}]

    if on_text:
        accumulated = ""
        async with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=NOVEL_COMPOUND_SYSTEM,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                on_text(text)
                accumulated += text
        return accumulated
    else:
        response = await client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=NOVEL_COMPOUND_SYSTEM,
            messages=messages,
        )
        return next(b.text for b in response.content if b.type == "text")


def has_novel_compounds(compounds: list[str]) -> list[str]:
    """
    Check which compounds are NOT in the local interaction database.

    Returns list of compound names not found in the index.
    """
    novel = []
    for comp in compounds:
        if comp.lower().strip() not in _INDEX:
            novel.append(comp)
    return novel
