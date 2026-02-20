#!/usr/bin/env python3
"""
Kiwi — Performance Research Architect
Advanced multi-agent scientific research system

Multi-agent pipeline:
  1. Planning Agent       — Context interpretation + PubMed retrieval strategy
  2. Research Agent       — Full synthesis with adaptive thinking + streaming
  3. Ralph Wiggum Loop    — Internal self-critique for evidence/logic quality
  4. Refinement Agent     — Targeted improvement when critique score < threshold
  5. Memory Agent         — Persistent cross-session research memory
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich.text import Text
from rich.columns import Columns
from rich import box

# ─── Configuration ────────────────────────────────────────────────────────────

MODEL = "claude-opus-4-6"
MEMORY_PATH = Path.home() / ".kiwi" / "memory.json"
REFINEMENT_THRESHOLD = 0.72          # Trigger refinement if Ralph Wiggum score falls below this
MAX_HISTORY_TURNS = 30               # Max conversation turns kept in context

# ─── System Prompts ───────────────────────────────────────────────────────────

KIWI_SYSTEM = """\
You are Kiwi, a Performance Research Architect — a multi-agent scientific research assistant \
specializing in human performance, sports nutrition, supplementation, exercise physiology, \
vitamins and micronutrients, metabolism, recovery, sleep, human optimization, and \
nutrition-related disease states.

You operate like an internal research laboratory with modular specialist agents:
- **Context Agent**     — Interprets query scope, domain, user intent, and research framing
- **Retrieval Agent**   — Plans PubMed-style literature search strategies (MeSH terms, boolean logic)
- **Extraction Agent**  — Identifies key findings, effect sizes, study quality, populations
- **Mechanistic Agent** — Reasons through biochemical pathways and physiological principles
- **Synthesis Agent**   — Integrates findings into unified, mechanistically sound explanations
- **Critique Agent**    — (Ralph Wiggum Loop) Recursively evaluates reasoning and evidence integrity
- **Refinement Agent**  — Improves outputs based on internal critique findings
- **Memory Agent**      — Maintains conversational continuity for long-term projects and preferences

═══════════════════════════════════════════════════════════════
EVIDENCE STANDARDS
═══════════════════════════════════════════════════════════════

All claims must be grounded strictly in peer-reviewed scientific literature from credible sources:
- PubMed / National Library of Medicine (NLM)
- Journal of the International Society of Sports Nutrition (JISSN)
- International Journal of Sport Nutrition & Exercise Metabolism (IJSNEM)
- International Journal of Sports Physiology & Performance (IJSPP)
- Sports Medicine (Springer)
- Frontiers in Physiology / Frontiers in Nutrition / Frontiers in Endocrinology
- Nature, Science, Cell, NEJM, Lancet, JAMA
- Systematic reviews, meta-analyses, RCTs, position stands
- Position stands & consensus: ISSN, ACSM, IOC, ADA, AND, ESPEN

EVIDENCE HIERARCHY — always label explicitly in responses:
🟢 Strong   — Multiple RCTs + systematic reviews/meta-analyses with consistent findings
🟡 Moderate — Limited RCTs, heterogeneous findings, or well-designed observational studies
🟠 Weak     — Small studies, mechanistic/animal data only, or highly context-dependent
🔵 Emerging — Early-phase research, preliminary data, theoretical or computational frameworks

CORE RULES:
- Explicitly state when evidence is mixed, incomplete, or contradictory
- Clearly separate established mechanism from theoretical pathway
- Never speculate beyond the evidence base
- Never fabricate studies, citations, authors, or effect sizes
- Note population-specific limitations (sex, training status, age, genetics, health status)

═══════════════════════════════════════════════════════════════
OUTPUT STRUCTURE
═══════════════════════════════════════════════════════════════

For substantive research queries, use this structure:

### Research Summary
Concise synthesis of the core finding (2–4 sentences).

### Mechanistic Framework
Biochemical pathways, physiological principles, nutrient–receptor interactions, enzyme kinetics,
signaling cascades, and downstream physiological effects relevant to the query.

### Evidence Review
Key studies presented with: design (RCT/meta/observational), sample characteristics, intervention
details, effect sizes, and what they specifically demonstrate. Cite real studies only.

### Evidence Hierarchy Assessment
Overall classification of the evidence base with rationale.

### Practical Implications
Evidence-based protocol guidance (non-medical) for training, nutrition, supplementation,
recovery, sleep, or human optimization. Dose ranges, timing, and interaction considerations
where evidence supports them.

### Knowledge Gaps & Contradictions
Where evidence is sparse, conflicting, or methodologically limited. Call out areas of active
scientific debate and why uncertainty exists.

### Key References
5–10 representative studies in APA-style format. Real, verifiable literature only.

═══════════════════════════════════════════════════════════════
SPECIALTY DOMAINS
═══════════════════════════════════════════════════════════════

You have deep expertise across:
• Sports nutrition: macronutrient periodization, nutrient timing, ergogenic aids
• Supplementation: creatine, caffeine, beta-alanine, nitrates, adaptogens, peptides
• Vitamins & micronutrients: deficiency states, RDAs, therapeutic dosing, bioavailability
• Metabolism: energy systems, substrate utilization, mitochondrial biogenesis, metabolic flexibility
• Recovery: muscle protein synthesis, inflammation resolution, glycogen resynthesis
• Sleep: circadian biology, sleep architecture, hormonal regulation, performance impact
• Human optimization: longevity, cognitive performance, hormonal health, gut microbiome
• Exercise physiology: VO2max, lactate threshold, neuromuscular adaptation, training load
• Nutrition-related disease: metabolic syndrome, sarcopenia, iron-deficiency, relative energy deficiency
• Performance psychology: arousal regulation, focus, resilience (when evidence-based)

═══════════════════════════════════════════════════════════════
ADVANCED WORKFLOWS (activate on request)
═══════════════════════════════════════════════════════════════

On user request, generate:
- Complete multi-agent folder structure and specialist prompt templates
- PubMed retrieval pipeline with full boolean strings and MeSH strategy
- Study design critique (RCT quality, confounders, blinding, statistical power)
- Hypothesis generation with mechanistic rationale and testable predictions
- Evidence-based protocol generators (training blocks, nutrition plans, supplementation stacks)
- Long-form literature reviews with full evidence tables and GRADE ratings
- SOAP-style clinical summary for practitioner/physician communication

You maintain long-term conversational memory across sessions, storing user preferences, \
ongoing research threads, conceptual frameworks, and long-term goals. \
You ignore irrelevant or sensitive details.

Tone: Articulate, precise, calm, deeply knowledgeable. \
Every output reflects rigorous scientific reasoning, coherent structure, and high-quality synthesis.\
"""

PLANNING_SYSTEM = """\
You are Kiwi's Context and Retrieval Planning Agent.
Your role: decompose research queries and plan the literature search strategy before main synthesis.
You cover: human performance, sports nutrition, supplementation, exercise physiology,
vitamins & micronutrients, metabolism, recovery, sleep, human optimization, and disease states.

Produce a structured plan covering:
1. **Query Decomposition** — Key sub-questions and distinct research angles
2. **Domain Classification** — Relevant sub-disciplines (e.g., exercise physiology, biochemistry,
   sleep science, micronutrient research) and intersecting fields
3. **PubMed Search Strategy** — Specific MeSH terms, keywords, boolean operators, publication filters
   Example: ("magnesium"[MeSH] OR "magnesium supplementation"[tiab]) AND "sleep quality"[tiab]
             AND ("randomized controlled trial"[pt] OR "systematic review"[pt])
4. **Evidence Target** — Study types to prioritize (RCTs, meta-analyses, mechanistic, longitudinal)
   and why for this specific query
5. **Known Evidence Landscape** — Areas of scientific consensus, active controversy, known gaps,
   and population-specific considerations

Be concise (300–500 words). This plan guides the synthesis agent for its full response.\
"""

CRITIQUE_SYSTEM = """\
You are Kiwi's internal critic — the Ralph Wiggum Loop.
Purpose: evaluate research output quality with rigorous, unbiased standards.
You have no stake in the content — only in its accuracy and integrity.

Evaluate on five dimensions:
1. Evidence Grounding (0–1)     — Are claims supported by actual peer-reviewed literature?
2. Evidence Hierarchy (0–1)     — Is quality clearly classified (strong/moderate/weak/emerging)?
3. Mechanistic Accuracy (0–1)   — Are biochemical pathways and physiology correctly described?
4. Logical Consistency (0–1)    — Any internal contradictions or unsupported inferential leaps?
5. Uncertainty Handling (0–1)   — Is uncertainty appropriately acknowledged where warranted?

Score = weighted mean (grounding×0.3, hierarchy×0.2, mechanistic×0.2, logic×0.2, uncertainty×0.1)

Return ONLY a valid JSON object — no preamble, no explanation:
{
  "score": <weighted float 0.0–1.0>,
  "dimension_scores": {
    "evidence_grounding": <0–1>,
    "evidence_hierarchy": <0–1>,
    "mechanistic_accuracy": <0–1>,
    "logical_consistency": <0–1>,
    "uncertainty_handling": <0–1>
  },
  "critical_issues": ["<specific issue>", ...],
  "minor_issues": ["<specific issue>", ...],
  "strengths": ["<specific strength>", ...],
  "needs_refinement": <true|false>
}\
"""

# ─── Memory ───────────────────────────────────────────────────────────────────

class KiwiMemory:
    """Persistent cross-session research memory stored at ~/.kiwi/memory.json"""

    def __init__(self):
        MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if MEMORY_PATH.exists():
            try:
                return json.loads(MEMORY_PATH.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "user_preferences": {},
            "research_threads": [],
            "conceptual_frameworks": [],
            "long_term_goals": [],
            "user_notes": [],
            "conversation_history": [],
            "session_count": 0,
            "total_queries": 0,
            "created_at": datetime.now().isoformat(),
            "last_session": None,
        }

    def save(self):
        MEMORY_PATH.write_text(json.dumps(self.data, indent=2, default=str))

    def add_exchange(self, query: str, response: str, score: float):
        self.data["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "query": query[:500],
            "response_preview": response[:1000],
            "quality_score": round(score, 3),
        })
        self.data["conversation_history"] = self.data["conversation_history"][-25:]
        self.data["total_queries"] = self.data.get("total_queries", 0) + 1
        self.data["last_session"] = datetime.now().isoformat()
        self.save()

    def add_note(self, note: str):
        self.data["user_notes"].append({
            "timestamp": datetime.now().isoformat(),
            "note": note,
        })
        self.save()

    def get_context_summary(self) -> str:
        history = self.data.get("conversation_history", [])
        if not history:
            return "No prior research history."
        recent = history[-5:]
        lines = [f"[{e['timestamp'][:10]}] {e['query'][:200]}" for e in recent]
        return "\n".join(lines)

    def summary_dict(self) -> dict:
        return {
            "sessions": self.data.get("session_count", 0),
            "total_queries": self.data.get("total_queries", 0),
            "notes_saved": len(self.data.get("user_notes", [])),
            "last_session": self.data.get("last_session", "—"),
            "recent_queries": [
                e["query"][:120]
                for e in self.data.get("conversation_history", [])[-5:]
            ],
        }

# ─── Core Research Engine ─────────────────────────────────────────────────────

class Kiwi:
    """Multi-agent research engine with Ralph Wiggum self-improvement loop."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.memory = KiwiMemory()
        self.console = Console()
        self.messages: list[dict] = []   # Conversation context for multi-turn

    # ── Agent 1: Planning ────────────────────────────────────────────────────

    def _planning_phase(self, query: str) -> str:
        """Context interpretation + PubMed retrieval strategy."""
        with self.console.status(
            "[dim cyan]  Planning research strategy...[/dim cyan]", spinner="earth"
        ):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1500,
                thinking={"type": "adaptive"},
                system=PLANNING_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Research Query: {query}\n\n"
                        f"Prior Session Context:\n{self.memory.get_context_summary()}\n\n"
                        "Produce the structured research plan."
                    ),
                }],
            )
        return next((b.text for b in response.content if b.type == "text"), "")

    # ── Agent 2: Research Synthesis (streaming) ──────────────────────────────

    def _research_phase(self, query: str, plan: str) -> tuple[str, list]:
        """Main evidence synthesis with adaptive thinking + streaming output."""
        user_msg = (
            f"Research Query: {query}\n\n"
            f"Research Plan (from planning agent):\n{plan}\n\n"
            "Now deliver your comprehensive research response per the "
            "Performance Research Architect protocol."
        )
        self.messages.append({"role": "user", "content": user_msg})

        self.console.print()
        self.console.rule("[bold cyan]  Kiwi — Research Synthesis[/bold cyan]")
        self.console.print()

        accumulated = ""
        final_content = []

        with self.client.messages.stream(
            model=MODEL,
            max_tokens=12000,
            thinking={"type": "adaptive"},
            system=KIWI_SYSTEM,
            messages=self.messages,
        ) as stream:
            for text in stream.text_stream:
                self.console.print(text, end="", markup=False)
                accumulated += text
            final_msg = stream.get_final_message()
            final_content = final_msg.content

        self.console.print("\n")

        # Append assistant turn — include full content (SDK handles thinking blocks)
        self.messages.append({"role": "assistant", "content": final_content})

        return accumulated, final_content

    # ── Agent 3: Ralph Wiggum Loop (critique) ────────────────────────────────

    def _ralph_wiggum_loop(self, query: str, response_text: str) -> tuple[dict, float]:
        """Internal self-critique for evidence integrity and logical quality."""
        with self.console.status(
            "[dim]  Ralph Wiggum Loop: Evaluating research quality...[/dim]",
            spinner="dots2",
        ):
            critique_response = self.client.messages.create(
                model=MODEL,
                max_tokens=1200,
                system=CRITIQUE_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": (
                        f"ORIGINAL QUERY:\n{query}\n\n"
                        f"RESEARCH RESPONSE (evaluate this):\n{response_text[:6000]}"
                    ),
                }],
            )

        critique_text = next(
            (b.text for b in critique_response.content if b.type == "text"), "{}"
        )

        # Parse JSON — be robust to markdown fences
        critique_data: dict = {
            "score": 1.0,
            "dimension_scores": {},
            "critical_issues": [],
            "minor_issues": [],
            "strengths": [],
            "needs_refinement": False,
        }
        try:
            json_match = re.search(r"\{.*\}", critique_text, re.DOTALL)
            if json_match:
                critique_data = json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        score = float(critique_data.get("score", 1.0))
        return critique_data, score

    # ── Agent 4: Refinement ──────────────────────────────────────────────────

    def _refinement_phase(self, critique_data: dict) -> str:
        """Targeted refinement pass addressing Ralph Wiggum's critical findings."""
        issues = critique_data.get("critical_issues", [])
        issues_block = "\n".join(f"  • {i}" for i in issues)

        refine_msg = (
            "Your internal Ralph Wiggum critic identified these critical issues "
            "in your research response:\n\n"
            f"{issues_block}\n\n"
            "Produce a refined, improved version that directly addresses each issue. "
            "Maintain all accurate content — only correct what the critique flagged. "
            "Do not truncate — deliver the full refined response."
        )

        # Build clean message thread for refinement
        # The SDK handles thinking blocks in prior messages automatically
        refine_messages = list(self.messages) + [{"role": "user", "content": refine_msg}]

        self.console.print()
        self.console.rule("[bold yellow]  Ralph Wiggum Refinement[/bold yellow]")
        self.console.print()

        refined_text = ""
        with self.client.messages.stream(
            model=MODEL,
            max_tokens=12000,
            thinking={"type": "adaptive"},
            system=KIWI_SYSTEM,
            messages=refine_messages,
        ) as stream:
            for text in stream.text_stream:
                self.console.print(text, end="", markup=False)
                refined_text += text
            final_msg = stream.get_final_message()

        # Extend main conversation with refinement exchange
        self.messages.append({"role": "user", "content": refine_msg})
        self.messages.append({"role": "assistant", "content": final_msg.content})

        self.console.print("\n")
        return refined_text

    # ── Full Pipeline ────────────────────────────────────────────────────────

    def research(self, query: str) -> str:
        """Execute the full multi-agent research pipeline for a query."""

        # Header
        self.console.print()
        self.console.print(Panel(
            f"[bold white]{query}[/bold white]",
            title="[bold cyan]Kiwi[/bold cyan]  Performance Research Architect",
            subtitle="[dim]Multi-Agent Research Pipeline[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))

        # ── Phase 1: Planning ───────────────────────────────
        plan = self._planning_phase(query)
        self.console.print(Panel(
            Markdown(plan),
            title="[dim]Research Plan[/dim]",
            border_style="dim white",
            box=box.SIMPLE,
            padding=(0, 2),
        ))

        # ── Phase 2: Research Synthesis ─────────────────────
        response_text, _ = self._research_phase(query, plan)

        # ── Phase 3: Ralph Wiggum Loop ──────────────────────
        critique_data, score = self._ralph_wiggum_loop(query, response_text)

        # Display critique score
        score_color = "green" if score >= 0.85 else "yellow" if score >= 0.70 else "red"
        n_critical = len(critique_data.get("critical_issues", []))
        n_minor = len(critique_data.get("minor_issues", []))

        dims = critique_data.get("dimension_scores", {})
        dim_text = "  ".join(
            f"{k.replace('_', ' ').title()}: {v:.2f}"
            for k, v in dims.items()
        ) if dims else ""

        self.console.print(
            f"\n[dim]  Ralph Wiggum Score:[/dim] [{score_color}]{score:.2f}[/{score_color}]  "
            + (f"[red]{n_critical} critical issue(s)[/red]  " if n_critical else "")
            + (f"[yellow]{n_minor} minor issue(s)[/yellow]  " if n_minor else "")
            + ("[green]Quality threshold met[/green]" if score >= REFINEMENT_THRESHOLD else "")
        )
        if dim_text:
            self.console.print(f"[dim]  {dim_text}[/dim]")

        # ── Phase 4: Refinement (conditional) ──────────────
        final_response = response_text
        if score < REFINEMENT_THRESHOLD and n_critical > 0:
            self.console.print(
                f"\n[yellow]  Score {score:.2f} below threshold {REFINEMENT_THRESHOLD} "
                f"— initiating self-refinement...[/yellow]"
            )
            final_response = self._refinement_phase(critique_data)
        else:
            strengths = critique_data.get("strengths", [])
            if strengths:
                self.console.print(
                    f"[dim]  Strengths: {'; '.join(strengths[:2])}[/dim]"
                )

        # Footer
        self.console.rule(
            f"[dim]  Complete  ·  Quality {score:.2f}  ·  "
            f"{len(self.messages)//2} turn(s) in context[/dim]"
        )

        # Persist to memory
        self.memory.add_exchange(query, final_response, score)

        return final_response

    # ── Interactive CLI ──────────────────────────────────────────────────────

    def interactive(self):
        """Main REPL loop."""
        session_num = self.memory.data.get("session_count", 0) + 1
        self.memory.data["session_count"] = session_num
        self.memory.save()

        self.console.print()
        self.console.print(Panel(
            "[bold cyan]Kiwi[/bold cyan] — Performance Research Architect\n"
            "[dim]Advanced multi-agent scientific research system\n"
            "Human performance · Sports nutrition · Exercise physiology · Recovery[/dim]\n\n"
            "[dim cyan]Commands:[/dim cyan]\n"
            "  [cyan]/memory[/cyan]          View persistent memory summary\n"
            "  [cyan]/clear[/cyan]           Clear conversation context (keep memory)\n"
            "  [cyan]/new[/cyan]             Start a fresh research thread\n"
            "  [cyan]/remember <note>[/cyan] Save a note to long-term memory\n"
            "  [cyan]/plan[/cyan]            Generate only the research plan\n"
            "  [cyan]/quit[/cyan]            Exit Kiwi",
            title=f"[bold]Session #{session_num}[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))

        while True:
            try:
                self.console.print()
                query = self.console.input("[bold cyan]Kiwi >[/bold cyan] ").strip()

                if not query:
                    continue

                # ── Commands ────────────────────────────────

                if query.lower() in ("/quit", "/exit", "quit", "exit"):
                    self.console.print(
                        "\n[dim]  Kiwi session complete. Research memory saved "
                        f"to {MEMORY_PATH}[/dim]"
                    )
                    break

                elif query.lower() == "/memory":
                    self.console.print(Panel(
                        json.dumps(self.memory.summary_dict(), indent=2),
                        title="[cyan]Kiwi Memory[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))

                elif query.lower() == "/clear":
                    self.messages = []
                    self.console.print("[dim]  Conversation context cleared.[/dim]")

                elif query.lower() == "/new":
                    self.messages = []
                    self.console.print("[dim]  New research thread started.[/dim]")

                elif query.lower().startswith("/remember "):
                    note = query[10:].strip()
                    if note:
                        self.memory.add_note(note)
                        self.console.print(f"[dim]  Saved to memory: {note}[/dim]")

                elif query.lower().startswith("/plan "):
                    sub_query = query[6:].strip()
                    if sub_query:
                        plan = self._planning_phase(sub_query)
                        self.console.print(Panel(
                            Markdown(plan),
                            title="[dim]Research Plan[/dim]",
                            border_style="dim white",
                        ))

                # ── Research ────────────────────────────────

                else:
                    self.research(query)

            except KeyboardInterrupt:
                self.console.print("\n[dim]  Use /quit to exit cleanly.[/dim]")

            except anthropic.AuthenticationError:
                self.console.print(
                    "[red]  Authentication failed. Check your ANTHROPIC_API_KEY.[/red]"
                )
                break

            except anthropic.RateLimitError:
                self.console.print(
                    "[yellow]  Rate limited. Please wait before retrying.[/yellow]"
                )

            except anthropic.APIConnectionError:
                self.console.print(
                    "[red]  Connection error. Check your network.[/red]"
                )

            except Exception as e:
                self.console.print(f"[red]  Error: {e}[/red]")


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("       export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    kiwi = Kiwi()

    if len(sys.argv) > 1:
        # Single-query mode: kiwi.py "your research question here"
        kiwi.research(" ".join(sys.argv[1:]))
    else:
        # Interactive REPL mode
        kiwi.interactive()


if __name__ == "__main__":
    main()
