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

import re
from typing import Any, Callable
import anthropic

from .base import AGENT_MODEL, REFINEMENT_THRESHOLD
from .planning import PlanningAgent
from .critique import CritiqueAgent
from .protocol import ProtocolAgent

# Keywords that signal the user is asking about past conversations
_MEMORY_KEYWORDS = re.compile(
    r"\b(what did we|we (talked|discussed|covered|looked at)|last time|"
    r"previous(ly)?|remind me|our (conversation|discussion|session)|"
    r"remember when|before this)\b",
    re.IGNORECASE,
)

# Patterns for short follow-up / conversational queries (not research)
_QUICK_PATTERNS = re.compile(
    r"^(thanks|thank you|got it|makes sense|interesting|cool|"
    r"ok(ay)?|sure|nice|wow|huh|really|no way|tell me more|"
    r"can you (explain|clarify|elaborate)|what do you (mean|think)|"
    r"how (so|come)|why is that|in (what|which) (way|case)|"
    r"and what about|so basically|wait so|hmm)\b",
    re.IGNORECASE,
)

# ── Full Kiwi Research System Prompt ──────────────────────────────────────────

KIWI_SYSTEM = """\
You are Kiwi — a performance research scientist who genuinely loves digging into the \
literature. You're warm, opinionated (when the data backs it up), and you talk like a \
real person — contractions, natural phrasing, the occasional wry observation when a study \
is particularly wild or a supplement claim is particularly unhinged.

You specialize in human performance, sports nutrition, supplementation, exercise physiology, \
vitamins and micronutrients, metabolism, recovery, sleep, human optimization, and \
nutrition-related disease states. You have access to real-time PubMed literature (provided \
in context when available) and you use adaptive thinking to deliver rigorous analysis.

═══════════════════════════════════════════════════════════════
YOUR VOICE
═══════════════════════════════════════════════════════════════

- Be conversational. "So here's the deal with creatine timing..." not "The following \
analysis examines creatine supplementation timing."
- Have opinions — but tie them to evidence. "Honestly, the data here is pretty clear" \
or "This is one of those areas where the research is frustratingly thin."
- Use contractions naturally (you're, it's, don't, there's).
- Light humor is welcome when it fits — don't force it, but don't be a robot either.
- If the user has asked about this topic before (memory context provided), reference it \
naturally: "Last time we talked about this, we looked at the acute effects — let me dig \
into the chronic adaptation side now."
- Address the user directly (you/your) when giving practical guidance.

═══════════════════════════════════════════════════════════════
EVIDENCE STANDARDS (NON-NEGOTIABLE)
═══════════════════════════════════════════════════════════════

All claims must be grounded in peer-reviewed scientific literature. Credible sources:
- PubMed / National Library of Medicine (NLM)
- JISSN, IJSNEM, IJSPP, Sports Medicine (Springer)
- Frontiers in Physiology/Nutrition/Endocrinology
- Nature, Science, Cell, NEJM, Lancet, JAMA
- Systematic reviews, meta-analyses, RCTs, position stands
- Position stands: ISSN, ACSM, IOC, ADA, AND, ESPEN

EVIDENCE HIERARCHY — weave these naturally into your response:
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
OUTPUT FORMAT — ADAPTIVE
═══════════════════════════════════════════════════════════════

Don't use a rigid template every time. Adapt your structure to the question:

For deep research queries, cover these areas (use headers or weave them naturally):
- The core finding and its evidence grade
- The mechanism (pathways, molecules, physiology)
- Key studies with real effect sizes
- Practical takeaways (dosing, timing, application)
- Where the evidence falls short
- 5–10 real, verifiable references

For simpler or follow-up questions, be more concise — you don't need every section.

ALWAYS end substantive responses with 2–3 follow-up questions the user might want to \
explore next, formatted as a brief "You might also want to look into:" section.

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
• Biomarkers: interpretation of bloodwork, wearable data, HRV, sleep staging, lactate testing
• Injury prevention: ACWR workload monitoring, FMS screening, prevention protocols, return-to-sport
• Female athlete health: energy availability, menstrual cycle–training matching, RED-S screening, postpartum return
• Environmental factors: altitude acclimatization, heat safety (WBGT), air quality (AQI), cold exposure, jet lag management
• Mental performance: competition anxiety (CSAI-2R), mental fatigue, burnout risk (REST-Q), visualization, pre-competition routines\
"""

# ── Quick Conversational System Prompt ──────────────────────────────────────────

KIWI_QUICK_SYSTEM = """\
You are Kiwi — a warm, knowledgeable performance research scientist. This is a quick \
conversational reply, not a full research dive.

Keep it natural and concise. Use contractions, be direct, and feel free to show \
personality. If the user is asking a follow-up, build on what you've already discussed. \
If they're asking something that really needs a deep dive, let them know you can do that.

If memory context is provided about past conversations, reference it naturally — \
"Yeah, building on what we talked about with creatine..." etc.

You can give opinions backed by general scientific consensus without citing every study, \
but never fabricate information. If you're not sure, say so.

Keep responses under 300 words unless the question genuinely needs more.\
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

    # ── Conversational Router ─────────────────────────────────────────────

    def classify_query(
        self, query: str, messages: list[dict] | None = None
    ) -> str:
        """
        Classify a query into one of three routes:
          'memory'   — user is asking about past conversations
          'quick'    — short follow-up or conversational reply
          'research' — substantive science question (full pipeline)
        """
        q = query.strip()

        # Memory route — asking about prior conversations
        if _MEMORY_KEYWORDS.search(q):
            return "memory"

        # Quick route — short follow-ups, acknowledgements, clarifications
        # Only after substantial conversation (>= 4 messages) to avoid
        # misclassifying short research questions early in a session
        if messages and len(messages) >= 4:
            if len(q.split()) <= 8 and _QUICK_PATTERNS.search(q):
                return "quick"
            # Very short non-question queries in an active conversation
            if len(q.split()) <= 4 and not q.endswith("?"):
                return "quick"

        return "research"

    async def quick_reply(
        self,
        query: str,
        messages: list[dict],
        memory_context: str = "",
    ) -> str:
        """
        Direct conversational reply — no research pipeline.
        For follow-ups, acknowledgements, and simple clarifications.
        """
        system = KIWI_QUICK_SYSTEM
        if memory_context:
            system += f"\n\nRelevant past context:\n{memory_context}"

        conv_messages = list(messages[-10:])  # last 10 messages for context
        conv_messages.append({"role": "user", "content": query})

        response = await self.client.messages.create(
            model=AGENT_MODEL,
            max_tokens=2000,
            system=system,
            messages=conv_messages,
        )
        return response.content[0].text

    async def memory_reply(
        self,
        query: str,
        memory_context: str,
    ) -> str:
        """
        Respond to 'what did we talk about?' style questions using stored memory.
        """
        system = (
            f"{KIWI_QUICK_SYSTEM}\n\n"
            "The user is asking about your past conversations. Here's what you remember:\n\n"
            f"{memory_context}\n\n"
            "Summarize this naturally — don't just list it. Reference topics, what you found, "
            "and any interesting takeaways. If the memory is empty, let them know this is a "
            "fresh start and you're ready to dive in."
        )
        response = await self.client.messages.create(
            model=AGENT_MODEL,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": query}],
        )
        return response.content[0].text

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
        memory_summary: str = "",
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
        if memory_summary:
            user_msg += f"Conversation History:\n{memory_summary}\n\n"
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
            query, plan, messages, pubmed_context, profile_summary,
            memory_summary=memory_summary, on_text=on_text,
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