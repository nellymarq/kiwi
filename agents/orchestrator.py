"""
Kiwi Orchestrator — Coordinates the full multi-agent research pipeline.

Pipeline:
  [parallel: PubMed search + profile load]
       ↓
  Planning Agent (query decomposition + retrieval strategy)
       ↓
  Research Synthesis (streaming, adaptive thinking, tool-augmented)
       ↓
  Ralph Wiggum Loop (critique: 5-dimension evidence scoring)
       ↓  (if score < 0.72)
  Refinement (targeted rewrite addressing critical issues)
       ↓  (on /protocol command)
  Protocol Agent (practical implementation guide)
       ↓
  Memory persistence + export
"""

import asyncio
from typing import Any, Callable
import anthropic

from .base import AGENT_MODEL, REFINEMENT_THRESHOLD
from .planning import PlanningAgent
from .critique import CritiqueAgent
from .protocol import ProtocolAgent

# ── Full Kiwi Research System Prompt ──────────────────────────────────────────

KIWI_SYSTEM = """\
You are Kiwi, a Performance Research Architect — an advanced multi-agent scientific \
research system specializing in human performance, sports nutrition, supplementation, \
exercise physiology, vitamins and micronutrients, metabolism, recovery, sleep, \
human optimization, and nutrition-related disease states.

You have access to real-time PubMed literature (provided in context when available) \
and operate with adaptive thinking to deliver the most rigorous scientific analysis possible.

═══════════════════════════════════════════════════════════════
EVIDENCE STANDARDS
═══════════════════════════════════════════════════════════════

All claims must be grounded in peer-reviewed scientific literature. Credible sources:
- PubMed / National Library of Medicine (NLM)
- JISSN, IJSNEM, IJSPP, Sports Medicine (Springer)
- Frontiers in Physiology/Nutrition/Endocrinology
- Nature, Science, Cell, NEJM, Lancet, JAMA
- Systematic reviews, meta-analyses, RCTs, position stands
- Position stands: ISSN, ACSM, IOC, ADA, AND, ESPEN

EVIDENCE HIERARCHY — label explicitly in every response:
🟢 Strong   — Multiple RCTs + systematic reviews with consistent findings
🟡 Moderate — Limited RCTs, heterogeneous findings, or well-designed observational studies
🟠 Weak     — Small studies, mechanistic/animal data only, or highly context-dependent
🔵 Emerging — Early-phase, preliminary, theoretical, or computational frameworks

CORE RULES:
- State explicitly when evidence is mixed, incomplete, or contradictory
- Separate established mechanism from theoretical pathway
- Never speculate beyond the evidence base
- Never fabricate studies, citations, authors, or effect sizes
- Note population-specific limitations (sex, training status, age, genetics, health)

═══════════════════════════════════════════════════════════════
OUTPUT STRUCTURE
═══════════════════════════════════════════════════════════════

For substantive queries, use:

### Research Summary
Core finding in 2–4 sentences. State the primary conclusion and its evidence grade.

### Mechanistic Framework
Biochemical pathways, physiological principles, molecular targets (receptors, enzymes,
signaling cascades), and downstream physiological effects. Be precise — name specific
molecules, genes, and pathways where evidence supports it.

### Evidence Review
Key studies: design (RCT/meta/observational), N, population, intervention, effect sizes,
what they specifically demonstrate. Distinguish high-quality from low-quality evidence.

### Evidence Hierarchy Assessment
Overall grade for this research area with rationale. Name specific weaknesses.

### Practical Implications
Evidence-based guidance (non-medical) for training, nutrition, supplementation, recovery,
sleep, or human optimization. Dose ranges, timing, and interactions where evidence supports.

### Knowledge Gaps & Contradictions
Where evidence is sparse, conflicting, or methodologically limited. Active scientific debates.

### Key References
5–10 representative real studies in APA-style format. Verifiable, real literature only.

═══════════════════════════════════════════════════════════════
PUBMED INTEGRATION
═══════════════════════════════════════════════════════════════

When PubMed search results are provided in context, integrate them directly:
- Reference specific PMIDs when discussing studies
- Note how recent the evidence is (publication year)
- Flag if pre-fetched articles directly support or contradict the query

═══════════════════════════════════════════════════════════════
SPECIALTY DOMAINS
═══════════════════════════════════════════════════════════════

Deep expertise across:
• Sports nutrition: macronutrient periodization, nutrient timing, ergogenic aids, body composition
• Supplementation: creatine, caffeine, beta-alanine, nitrates, HMB, adaptogens, peptides, nootropics
• Vitamins & micronutrients: deficiency states, RDAs vs. therapeutic dosing, bioavailability forms
• Metabolism: energy systems, substrate utilization, mitochondrial biogenesis, metabolic flexibility
• Recovery: MPS, inflammation resolution, glycogen resynthesis, sleep-recovery interaction
• Sleep: circadian biology, sleep architecture, melatonin, adenosine, hormonal regulation
• Human optimization: longevity, cognitive performance, hormonal health, gut microbiome, autophagy
• Exercise physiology: VO2max, lactate threshold, neuromuscular adaptation, periodization
• Nutrition-related disease: metabolic syndrome, sarcopenia, iron-deficiency anemia, RED-S
• Biomarkers: interpretation of bloodwork, wearable data, HRV, sleep staging, lactate testing\
"""


class KiwiOrchestrator:
    """
    Coordinates the full multi-agent Kiwi research pipeline.
    Designed for integration with the CLI (streaming-capable).
    """

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client
        self.planning_agent = PlanningAgent(client)
        self.critique_agent = CritiqueAgent(client)
        self.protocol_agent = ProtocolAgent(client)

    async def planning_phase(self, context: dict[str, Any]) -> str:
        """Phase 1: Query decomposition + PubMed strategy."""
        return await self.planning_agent.run(context)

    async def synthesis_phase(
        self,
        query: str,
        plan: str,
        messages: list[dict],
        pubmed_context: str,
        profile_summary: str,
        on_text: Callable[[str], None] | None = None,
    ) -> tuple[str, list]:
        """
        Phase 2: Main research synthesis with streaming.
        Returns (accumulated_text, final_content_list).
        on_text: callback for each streamed text chunk.
        """
        user_msg = (
            f"Research Query: {query}\n\n"
            f"Research Plan (from planning agent):\n{plan}\n\n"
        )
        if pubmed_context:
            user_msg += f"PubMed Literature (real-time retrieval):\n{pubmed_context}\n\n"
        if profile_summary:
            user_msg += f"User Profile: {profile_summary}\n\n"
        user_msg += (
            "Deliver your comprehensive research response per the "
            "Kiwi Performance Research Architect protocol."
        )

        messages.append({"role": "user", "content": user_msg})

        accumulated = ""
        final_content = []

        async with self.client.messages.stream(
            model=AGENT_MODEL,
            max_tokens=14000,
            thinking={"type": "adaptive"},
            system=KIWI_SYSTEM,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                if on_text:
                    on_text(text)
                accumulated += text
            final_msg = await stream.get_final_message()
            final_content = final_msg.content

        messages.append({"role": "assistant", "content": final_content})
        return accumulated, final_content

    async def critique_phase(
        self,
        query: str,
        response_text: str,
    ) -> tuple[dict, float]:
        """Phase 3: Ralph Wiggum Loop — evidence quality scoring."""
        return await self.critique_agent.critique(query, response_text)

    async def refinement_phase(
        self,
        critique_data: dict,
        messages: list[dict],
        on_text: Callable[[str], None] | None = None,
    ) -> tuple[str, list]:
        """Phase 4: Targeted refinement addressing Ralph Wiggum's critical issues."""
        issues = critique_data.get("critical_issues", [])
        priority = critique_data.get("refinement_priority", "evidence quality")
        score = critique_data.get("score", 0.0)

        issues_block = "\n".join(f"  • {i}" for i in issues)
        refine_msg = (
            f"Your internal Ralph Wiggum critic scored this response {score:.2f} "
            f"(threshold: {REFINEMENT_THRESHOLD}). Priority fix: {priority}.\n\n"
            "Critical issues identified:\n"
            f"{issues_block}\n\n"
            "Produce a fully refined response that addresses each critical issue precisely. "
            "Maintain all accurate content — only correct what the critique flagged. "
            "Do not truncate — deliver the complete, improved response."
        )

        refine_messages = list(messages) + [{"role": "user", "content": refine_msg}]
        accumulated = ""
        final_content = []

        async with self.client.messages.stream(
            model=AGENT_MODEL,
            max_tokens=14000,
            thinking={"type": "adaptive"},
            system=KIWI_SYSTEM,
            messages=refine_messages,
        ) as stream:
            async for text in stream.text_stream:
                if on_text:
                    on_text(text)
                accumulated += text
            final_msg = await stream.get_final_message()
            final_content = final_msg.content

        messages.append({"role": "user", "content": refine_msg})
        messages.append({"role": "assistant", "content": final_content})
        return accumulated, final_content

    async def protocol_phase(
        self,
        query: str,
        synthesis: str,
        profile_summary: str,
        on_text: Callable[[str], None] | None = None,
    ) -> str:
        """Optional Phase 5: Generate practical protocol from synthesis."""
        context = {
            "query": query,
            "synthesis": synthesis,
            "profile_summary": profile_summary,
        }

        # Stream the protocol response
        messages = self.protocol_agent._build_messages(context)
        accumulated = ""

        async with self.client.messages.stream(
            model=AGENT_MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=self.protocol_agent.system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                if on_text:
                    on_text(text)
                accumulated += text

        return accumulated

    async def run_full_pipeline(
        self,
        query: str,
        messages: list[dict],
        memory_summary: str,
        profile_summary: str,
        pubmed_context: str = "",
        on_status: Callable[[str], None] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute the complete Kiwi research pipeline.
        Returns dict with keys: plan, response, critique, score, refined, final_response
        """

        def status(msg: str):
            if on_status:
                on_status(msg)

        # Phase 1: Planning (async)
        status("planning")
        plan = await self.planning_phase({
            "query": query,
            "history_summary": memory_summary,
            "profile_summary": profile_summary,
            "pubmed_hits": pubmed_context,
        })

        # Phase 2: Synthesis (streaming)
        status("synthesis")
        response_text, _ = await self.synthesis_phase(
            query, plan, messages, pubmed_context, profile_summary, on_text=on_text
        )

        # Phase 3: Ralph Wiggum Loop (async, parallel with nothing currently)
        status("critique")
        critique_data, score = await self.critique_phase(query, response_text)

        # Phase 4: Refinement (conditional)
        final_response = response_text
        refined = False

        if critique_data.get("needs_refinement") and score < REFINEMENT_THRESHOLD:
            status("refinement")
            final_response, _ = await self.refinement_phase(
                critique_data, messages, on_text=on_text
            )
            refined = True

        return {
            "plan": plan,
            "response": response_text,
            "critique": critique_data,
            "score": score,
            "refined": refined,
            "final_response": final_response,
        }
