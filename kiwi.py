#!/usr/bin/env python3
"""
Kiwi — Performance Research Architect
======================================
Advanced multi-agent scientific research system for human performance,
sports nutrition, exercise physiology, vitamins & micronutrients,
metabolism, recovery, sleep, and human optimization.

Architecture:
  Planning Agent     — Query decomposition + PubMed retrieval strategy
  PubMed Tool        — Real-time literature retrieval (NCBI E-utilities)
  Research Synthesis — Streaming adaptive thinking (claude-opus-4-6)
  Ralph Wiggum Loop  — 5-dimension evidence critique (visible checkpoint)
  Refinement Agent   — Targeted rewrite when RWL score < 0.72
  Protocol Agent     — Evidence-based practical protocol generation
  Memory System      — Episodic + semantic + research threads (persistent)
  User Profile       — Personalized metrics and context injection
  Sports Calc        — Evidence-based physiological calculations

Usage:
  python3 kiwi.py                    — Interactive REPL
  python3 kiwi.py "your query"       — Single query mode
  python3 kiwi.py --no-pubmed "..."  — Skip PubMed retrieval
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich.table import Table
from rich import box

from agents.orchestrator import KiwiOrchestrator
from agents.base import REFINEMENT_THRESHOLD
from tools.pubmed import PubMedClient
from tools.calculations import SportsCalc
from tools.exporter import ResearchExporter
from memory.store import KiwiMemory
from memory.profile import UserProfile

# ── Console ───────────────────────────────────────────────────────────────────
console = Console()


# ── Ralph Wiggum Checkpoint Display ──────────────────────────────────────────

def display_rwl_checkpoint(critique_data: dict, score: float, refined: bool = False):
    """
    Display the full Ralph Wiggum Loop checkpoint — every dimension, every issue.
    Called after every research response so the user can see exactly what the
    critic found.
    """
    dims = critique_data.get("dimension_scores", {})
    critical = critique_data.get("critical_issues", [])
    minor = critique_data.get("minor_issues", [])
    strengths = critique_data.get("strengths", [])
    needs_refinement = critique_data.get("needs_refinement", False)
    priority = critique_data.get("refinement_priority", "")

    score_color = "green" if score >= 0.85 else "yellow" if score >= 0.72 else "red"
    status = "[red]REFINEMENT TRIGGERED[/red]" if needs_refinement else "[green]Quality threshold met[/green]"
    if refined:
        status = "[yellow]REFINED[/yellow] ✓"

    # Dimension table
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("Dimension", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("", width=20)

    dim_labels = {
        "evidence_grounding": "Evidence Grounding",
        "evidence_hierarchy": "Evidence Hierarchy",
        "mechanistic_accuracy": "Mechanistic Accuracy",
        "logical_consistency": "Logical Consistency",
        "uncertainty_handling": "Uncertainty Handling",
    }

    for key, label in dim_labels.items():
        val = float(dims.get(key, 0.0))
        bar_len = int(val * 15)
        bar = "█" * bar_len + "░" * (15 - bar_len)
        color = "green" if val >= 0.80 else "yellow" if val >= 0.60 else "red"
        table.add_row(
            label,
            f"[{color}]{val:.2f}[/{color}]",
            f"[{color}]{bar}[/{color}]",
        )

    # Build content block
    lines = []
    lines.append(f"[bold]Composite Score: [{score_color}]{score:.2f}[/{score_color}][/bold]   {status}")
    if priority and needs_refinement:
        lines.append(f"[dim]Priority fix: {priority}[/dim]")

    content = "\n".join(lines)

    console.print()
    console.print(Panel(
        content,
        title="[bold dim]Ralph Wiggum Loop — Evidence Quality Checkpoint[/bold dim]",
        border_style="dim",
        box=box.ROUNDED,
        padding=(0, 2),
    ))

    console.print(table)

    if critical:
        console.print("[bold red]  Critical Issues:[/bold red]")
        for issue in critical:
            console.print(f"  [red]•[/red] {issue}")

    if minor:
        console.print("[dim yellow]  Minor Issues:[/dim yellow]")
        for issue in minor:
            console.print(f"  [dim]•[/dim] {issue}")

    if strengths:
        console.print("[dim green]  Strengths:[/dim green]")
        for s in strengths:
            console.print(f"  [dim]•[/dim] {s}")

    console.print()


# ── PubMed Pre-fetch ──────────────────────────────────────────────────────────

def fetch_pubmed_context(query: str, pubmed: PubMedClient) -> str:
    """Run a quick PubMed search and return formatted context block."""
    with console.status("[dim cyan]  Searching PubMed for recent literature...[/dim cyan]", spinner="earth"):
        # Build search string from query keywords
        keywords = " ".join(query.split()[:6])  # Use first 6 words as search terms
        articles = pubmed.search_and_fetch(keywords, max_results=6, years_back=8)

    if articles:
        console.print(f"[dim]  PubMed: found {len(articles)} relevant articles[/dim]")
        return pubmed.build_context_block(articles)
    else:
        console.print("[dim]  PubMed: no recent articles found for this query[/dim]")
        return ""


# ── Main Kiwi Class ───────────────────────────────────────────────────────────

class Kiwi:
    """
    Kiwi orchestrator — coordinates the full multi-agent research pipeline
    and manages the interactive CLI.
    """

    def __init__(self, use_pubmed: bool = True):
        self.client = anthropic.AsyncAnthropic()
        self.orchestrator = KiwiOrchestrator(self.client)
        self.memory = KiwiMemory()
        self.profile = UserProfile()
        self.pubmed = PubMedClient() if use_pubmed else None
        self.exporter = ResearchExporter()
        self.calc = SportsCalc()
        self.messages: list[dict] = []      # Conversation context
        self.active_thread: str | None = None

    # ── Research Pipeline ────────────────────────────────────────────────────

    async def research(self, query: str, generate_protocol: bool = False) -> str:
        """Execute the full multi-agent research pipeline."""
        console.print()
        console.print(Panel(
            f"[bold white]{query}[/bold white]",
            title="[bold cyan]Kiwi[/bold cyan]  Performance Research Architect",
            subtitle=f"[dim]Multi-Agent Pipeline  ·  claude-opus-4-6 + Adaptive Thinking[/dim]"
                     + (f"  ·  Thread: {self.active_thread}" if self.active_thread else ""),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))

        # PubMed pre-fetch
        pubmed_context = ""
        if self.pubmed:
            pubmed_context = fetch_pubmed_context(query, self.pubmed)

        # Profile + memory context
        profile_summary = self.profile.to_summary()
        memory_summary = self.memory.get_history_summary()

        # Add calc metrics if profile is set
        if self.profile.is_complete():
            try:
                metrics = self.calc.compute_full_metrics(
                    weight_kg=self.profile.get("weight_kg"),
                    height_cm=self.profile.get("height_cm", 170),
                    age=self.profile.get("age", 25),
                    sex=self.profile.get("sex", "male"),
                    activity_level=self.profile.get("activity_level", "active"),
                    body_fat_pct=self.profile.get("body_fat_pct"),
                )
                profile_summary += f"\n\nComputed Metrics:\n{metrics.summary()}"
            except Exception:
                pass

        # Status callback
        def on_status(phase: str):
            labels = {
                "planning": "  Planning research strategy...",
                "synthesis": "  Synthesizing research...",
                "critique": "  Ralph Wiggum Loop: evaluating evidence quality...",
                "refinement": "  Refining response (RWL score below threshold)...",
            }
            label = labels.get(phase, f"  {phase}...")
            if phase == "planning":
                with console.status(f"[dim cyan]{label}[/dim cyan]", spinner="earth"):
                    pass

        # Text streaming callback
        current_section = {"name": ""}

        def on_text(text: str):
            console.print(text, end="", markup=False)

        # Phase 1+2: Planning + Synthesis header
        console.print()
        console.rule("[bold cyan]  Research Plan[/bold cyan]")

        # Execute pipeline
        with console.status("[dim cyan]  Planning research strategy...[/dim cyan]", spinner="earth"):
            plan = await self.orchestrator.planning_phase({
                "query": query,
                "history_summary": memory_summary,
                "profile_summary": profile_summary,
                "pubmed_hits": pubmed_context,
            })

        console.print(Panel(
            Markdown(plan),
            title="[dim]Research Plan (Planning Agent)[/dim]",
            border_style="dim white",
            box=box.SIMPLE,
            padding=(0, 1),
        ))

        # Phase 2: Synthesis (streaming)
        console.print()
        console.rule("[bold cyan]  Kiwi — Research Synthesis[/bold cyan]")
        console.print()

        response_text, _ = await self.orchestrator.synthesis_phase(
            query=query,
            plan=plan,
            messages=self.messages,
            pubmed_context=pubmed_context,
            profile_summary=profile_summary,
            on_text=on_text,
        )

        console.print("\n")

        # Phase 3: Ralph Wiggum Loop — ALWAYS display full checkpoint
        console.rule("[bold dim]  Ralph Wiggum Loop[/bold dim]")

        with console.status(
            "[dim]  Evaluating evidence quality across 5 dimensions...[/dim]",
            spinner="dots2",
        ):
            critique_data, score = await self.orchestrator.critique_phase(query, response_text)

        display_rwl_checkpoint(critique_data, score, refined=False)

        # Phase 4: Refinement (conditional)
        final_response = response_text
        refined = False

        if critique_data.get("needs_refinement") and score < REFINEMENT_THRESHOLD:
            n_critical = len(critique_data.get("critical_issues", []))
            console.print(
                f"[yellow]  RWL score {score:.2f} < threshold {REFINEMENT_THRESHOLD} "
                f"({n_critical} critical issue(s)) — initiating targeted refinement...[/yellow]\n"
            )
            console.rule("[bold yellow]  Refinement Pass[/bold yellow]")
            console.print()

            final_response, _ = await self.orchestrator.refinement_phase(
                critique_data=critique_data,
                messages=self.messages,
                on_text=on_text,
            )
            refined = True
            console.print("\n")

            # Re-score the refined response
            console.rule("[bold dim]  Ralph Wiggum Loop — Post-Refinement Check[/bold dim]")
            with console.status("[dim]  Re-evaluating refined response...[/dim]", spinner="dots2"):
                refined_critique, refined_score = await self.orchestrator.critique_phase(
                    query, final_response
                )
            display_rwl_checkpoint(refined_critique, refined_score, refined=True)
            score = refined_score

        # Phase 5: Optional protocol generation
        if generate_protocol:
            console.rule("[bold cyan]  Protocol Agent[/bold cyan]")
            console.print()
            with console.status("[dim cyan]  Generating evidence-based protocol...[/dim cyan]", spinner="earth"):
                protocol = await self.orchestrator.protocol_phase(
                    query=query,
                    synthesis=final_response,
                    profile_summary=profile_summary,
                    on_text=on_text,
                )
            console.print()
            final_response = final_response + "\n\n---\n\n" + protocol

        # Footer
        console.rule(
            f"[dim]  Complete  ·  Quality {score:.2f}  ·  "
            f"{'Refined' if refined else 'First pass'}  ·  "
            f"{len(self.messages) // 2} turn(s) in context[/dim]"
        )

        # Persist to memory
        self.memory.add_exchange(query, final_response, score, thread=self.active_thread)

        return final_response

    # ── Interactive CLI ──────────────────────────────────────────────────────

    def _show_welcome(self, session_num: int):
        console.print()
        console.print(Panel(
            "[bold cyan]Kiwi[/bold cyan] — Performance Research Architect\n"
            "[dim]Multi-agent · claude-opus-4-6 · Adaptive thinking · Ralph Wiggum Loop[/dim]\n\n"
            "[bold dim cyan]Research Commands:[/bold dim cyan]\n"
            "  Just type your research question\n"
            "  [cyan]/protocol <query>[/cyan]    Generate evidence-based protocol\n"
            "  [cyan]/plan <query>[/cyan]         Show only the research plan\n\n"
            "[bold dim cyan]Memory & Threads:[/bold dim cyan]\n"
            "  [cyan]/memory[/cyan]               View memory summary\n"
            "  [cyan]/thread new <name>[/cyan]    Create research thread\n"
            "  [cyan]/thread use <name>[/cyan]    Switch to a thread\n"
            "  [cyan]/thread list[/cyan]           List research threads\n"
            "  [cyan]/remember <note>[/cyan]       Save note to memory\n"
            "  [cyan]/export[/cyan]                Export last research to Markdown\n\n"
            "[bold dim cyan]Profile & Calculations:[/bold dim cyan]\n"
            "  [cyan]/profile[/cyan]               View current profile\n"
            "  [cyan]/profile set <field> <val>[/cyan]  Set profile field\n"
            "  [cyan]/calc[/cyan]                  Run sports science calculations\n"
            "  [cyan]/pubmed <query>[/cyan]         Search PubMed directly\n\n"
            "[bold dim cyan]Session:[/bold dim cyan]\n"
            "  [cyan]/clear[/cyan]                 Clear conversation context\n"
            "  [cyan]/new[/cyan]                   New research thread\n"
            "  [cyan]/quit[/cyan]                  Exit Kiwi",
            title=f"[bold]Session #{session_num}[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))

        if not self.profile.is_complete():
            console.print(
                "[dim yellow]  Tip: Set your profile for personalized responses: "
                "/profile set weight_kg 80[/dim yellow]"
            )

    async def interactive(self):
        """Main async REPL loop."""
        session_num = self.memory.start_session()
        self._show_welcome(session_num)

        last_query = ""
        last_response = ""
        last_critique: dict = {}
        last_score = 0.0

        while True:
            try:
                console.print()
                prompt = f"[bold cyan]Kiwi[/bold cyan]"
                if self.active_thread:
                    prompt += f"[dim] [{self.active_thread}][/dim]"
                prompt += "[bold cyan] >[/bold cyan] "
                query = console.input(prompt).strip()

                if not query:
                    continue

                q_lower = query.lower()

                # ── Session Commands ────────────────────────────────────────

                if q_lower in ("/quit", "/exit", "quit", "exit"):
                    console.print(
                        f"\n[dim]  Session #{session_num} complete. "
                        f"Memory saved to {Path.home() / '.kiwi'}[/dim]"
                    )
                    break

                elif q_lower == "/clear":
                    self.messages = []
                    console.print("[dim]  Conversation context cleared. Memory preserved.[/dim]")

                elif q_lower == "/new":
                    self.messages = []
                    self.active_thread = None
                    console.print("[dim]  New research thread. Context cleared.[/dim]")

                # ── Memory Commands ─────────────────────────────────────────

                elif q_lower == "/memory":
                    summary = self.memory.summary_dict()
                    console.print(Panel(
                        json.dumps(summary, indent=2, default=str),
                        title="[cyan]Kiwi Memory[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))

                elif q_lower.startswith("/remember "):
                    note = query[10:].strip()
                    if note:
                        self.memory.add_note(note)
                        console.print(f"[dim]  Saved to memory: {note}[/dim]")

                elif q_lower == "/export":
                    if last_response:
                        path = self.exporter.export_markdown(
                            query=last_query,
                            plan="",
                            response=last_response,
                            score=last_score,
                            critique_data=last_critique,
                            refined=last_score < REFINEMENT_THRESHOLD,
                            thread_name=self.active_thread,
                        )
                        console.print(f"[dim]  Exported to: {path}[/dim]")
                    else:
                        console.print("[dim]  No research to export yet.[/dim]")

                # ── Thread Commands ─────────────────────────────────────────

                elif q_lower.startswith("/thread "):
                    parts = query.split(maxsplit=2)
                    subcmd = parts[1].lower() if len(parts) > 1 else ""
                    arg = parts[2] if len(parts) > 2 else ""

                    if subcmd == "new" and arg:
                        ok = self.memory.create_thread(arg)
                        if ok:
                            self.active_thread = arg
                            self.messages = []
                            console.print(f"[dim]  Created and switched to thread: [cyan]{arg}[/cyan][/dim]")
                        else:
                            console.print(f"[dim]  Thread '{arg}' already exists.[/dim]")

                    elif subcmd == "use" and arg:
                        threads = {t["name"] for t in self.memory.list_threads()}
                        if arg in threads:
                            self.active_thread = arg
                            self.messages = []
                            ctx = self.memory.get_thread_context(arg)
                            console.print(f"[dim]  Switched to thread: [cyan]{arg}[/cyan][/dim]\n{ctx[:300]}")
                        else:
                            console.print(f"[dim]  Thread '{arg}' not found. Create with /thread new {arg}[/dim]")

                    elif subcmd == "list":
                        threads = self.memory.list_threads()
                        if threads:
                            for t in threads:
                                marker = " ●" if t["name"] == self.active_thread else ""
                                console.print(f"  [cyan]{t['name']}[/cyan]{marker} — {len(t.get('queries', []))} queries")
                        else:
                            console.print("[dim]  No research threads yet.[/dim]")

                # ── Profile Commands ────────────────────────────────────────

                elif q_lower == "/profile":
                    summary = self.profile.to_summary()
                    console.print(Panel(
                        summary,
                        title="[cyan]User Profile[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))
                    console.print(
                        f"[dim]  Available fields: {', '.join(self.profile.FIELDS.keys())}[/dim]"
                    )

                elif q_lower.startswith("/profile set "):
                    parts = query.split(maxsplit=3)
                    if len(parts) >= 4:
                        field, value = parts[2], parts[3]
                        ok = self.profile.set(field, value)
                        if ok:
                            console.print(f"[dim]  Profile updated: {field} = {value}[/dim]")
                        else:
                            console.print(f"[dim red]  Unknown field: {field}. "
                                          f"Valid: {', '.join(self.profile.FIELDS.keys())}[/dim red]")

                # ── Calculations ────────────────────────────────────────────

                elif q_lower == "/calc":
                    if not self.profile.is_complete():
                        console.print("[dim]  Set profile first: /profile set weight_kg 80, sex male, age 25, activity_level active[/dim]")
                    else:
                        try:
                            m = self.calc.compute_full_metrics(
                                weight_kg=self.profile.get("weight_kg"),
                                height_cm=self.profile.get("height_cm", 170),
                                age=self.profile.get("age", 25),
                                sex=self.profile.get("sex", "male"),
                                activity_level=self.profile.get("activity_level", "active"),
                                body_fat_pct=self.profile.get("body_fat_pct"),
                            )
                            console.print(Panel(
                                m.summary(),
                                title="[cyan]Sports Science Calculations[/cyan]",
                                border_style="cyan",
                                box=box.SIMPLE,
                            ))
                        except Exception as e:
                            console.print(f"[red]  Calculation error: {e}[/red]")

                # ── PubMed Direct Search ────────────────────────────────────

                elif q_lower.startswith("/pubmed "):
                    search_query = query[8:].strip()
                    if search_query and self.pubmed:
                        with console.status("[dim cyan]  Searching PubMed...[/dim cyan]", spinner="earth"):
                            articles = self.pubmed.search_and_fetch(search_query, max_results=8)
                        if articles:
                            for i, a in enumerate(articles, 1):
                                console.print(
                                    f"\n[cyan][{i}][/cyan] [bold]{a.title}[/bold]\n"
                                    f"[dim]{', '.join(a.authors[:2])} ({a.year}) · {a.journal}[/dim]\n"
                                    f"PMID: {a.pmid}  DOI: {a.doi}\n"
                                    f"{a.abstract[:400]}..."
                                )
                        else:
                            console.print("[dim]  No results found.[/dim]")
                    elif not self.pubmed:
                        console.print("[dim]  PubMed disabled (run without --no-pubmed).[/dim]")

                # ── Research Plan Only ──────────────────────────────────────

                elif q_lower.startswith("/plan "):
                    sub_query = query[6:].strip()
                    if sub_query:
                        with console.status("[dim cyan]  Planning...[/dim cyan]", spinner="earth"):
                            plan = await self.orchestrator.planning_phase({
                                "query": sub_query,
                                "history_summary": self.memory.get_history_summary(),
                                "profile_summary": self.profile.to_summary(),
                            })
                        console.print(Panel(
                            Markdown(plan),
                            title="[dim]Research Plan[/dim]",
                            border_style="dim white",
                        ))

                # ── Protocol Generation ─────────────────────────────────────

                elif q_lower.startswith("/protocol "):
                    sub_query = query[10:].strip()
                    if sub_query:
                        result = await self.research(sub_query, generate_protocol=True)
                        last_query = sub_query
                        last_response = result

                # ── Research ────────────────────────────────────────────────

                else:
                    result = await self.research(query)
                    last_query = query
                    last_response = result
                    # These are set during research — capture from orchestrator state
                    # (critique captured via display_rwl_checkpoint in research())

            except KeyboardInterrupt:
                console.print("\n[dim]  Use /quit to exit cleanly.[/dim]")

            except anthropic.AuthenticationError:
                console.print("[red]  Authentication failed. Check ANTHROPIC_API_KEY.[/red]")
                break

            except anthropic.RateLimitError:
                console.print("[yellow]  Rate limited. Please wait before retrying.[/yellow]")

            except anthropic.APIConnectionError:
                console.print("[red]  Connection error. Check your network.[/red]")

            except Exception as e:
                console.print(f"[red]  Error: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")


# ── Entry Point ───────────────────────────────────────────────────────────────

async def async_main():
    parser = argparse.ArgumentParser(
        description="Kiwi — Performance Research Architect"
    )
    parser.add_argument("query", nargs="*", help="Research query (single-query mode)")
    parser.add_argument("--no-pubmed", action="store_true", help="Disable PubMed retrieval")
    parser.add_argument("--protocol", action="store_true", help="Generate protocol (single-query mode)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("       export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    kiwi = Kiwi(use_pubmed=not args.no_pubmed)

    if args.query:
        # Single-query mode
        query_text = " ".join(args.query)
        await kiwi.research(query_text, generate_protocol=args.protocol)
    else:
        # Interactive REPL
        await kiwi.interactive()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
