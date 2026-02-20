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
from tools.interactions import lookup_interactions, lookup_single, format_interaction_report
from tools.food_database import FDCClient
from tools.periodization import (
    TrainingSession, TrainingLoadCalculator,
    prilepins_recommendation, get_block_plan, format_block_plan,
)
from tools.biomarkers import interpret_panel, BiomarkerInterpreter
from tools.sleep_optimizer import (
    classify_chronotype, optimal_wake_times, caffeine_clearance,
    sleep_debt_report, athlete_sleep_target, format_hormonal_windows, pre_sleep_protocol,
    CHRONOTYPE_PROFILES,
)
from tools.recovery import (
    HRVReading, compute_readiness, format_readiness_report,
    estimate_doms, supercompensation_window, assess_deload_need,
    recovery_modality_guide, mps_timing_guide,
    EXERCISE_DAMAGE_COEFFICIENTS,
)
from tools.hydration import (
    calculate_sweat_loss, estimate_sweat_loss_by_sport,
    design_rehydration_protocol, format_rehydration_report,
    urine_color_status, hyponatremia_risk, pre_exercise_hydration_plan,
    SPORT_SWEAT_RATES,
)
from agents.sports_agent import run_sports_assessment
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
        self.fdc = FDCClient()
        self.load_calc = TrainingLoadCalculator()
        self.bio_interp = BiomarkerInterpreter()
        self._pending_sessions: list[TrainingSession] = []  # For /load session entry
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
            "[bold dim cyan]Supplement Tools:[/bold dim cyan]\n"
            "  [cyan]/check <c1> [c2 ...][/cyan]   Check supplement interactions\n"
            "  [cyan]/interact <compound>[/cyan]    All known interactions for a compound\n\n"
            "[bold dim cyan]Food & Nutrition:[/bold dim cyan]\n"
            "  [cyan]/food <name> [grams][/cyan]    USDA food lookup (per 100g or custom)\n"
            "  [cyan]/food+ <name> [grams][/cyan]   Same + amino acid profile\n"
            "  [cyan]/compare <f1>, <f2>[/cyan]     Side-by-side food comparison\n\n"
            "[bold dim cyan]Training Load:[/bold dim cyan]\n"
            "  [cyan]/session <day> <min> <rpe>[/cyan]  Log session (day offset, minutes, RPE 1-10)\n"
            "  [cyan]/load[/cyan]                   Compute ATL/CTL/TSB from logged sessions\n"
            "  [cyan]/blocks [sport][/cyan]          Periodization plan (strength/endurance/hypertrophy)\n"
            "  [cyan]/prilepin <pct>[/cyan]          Prilepin's table for intensity %\n\n"
            "[bold dim cyan]Blood Panel:[/bold dim cyan]\n"
            "  [cyan]/labs <marker> <val> ...[/cyan]  Interpret biomarkers (e.g. /labs ferritin 25 vitamin_d 35)\n"
            "  [cyan]/biomarker <name> <val>[/cyan]  Single biomarker quick check\n\n"
            "[bold dim cyan]Sleep Optimization:[/bold dim cyan]\n"
            "  [cyan]/sleep <HH:MM>[/cyan]           Optimal wake times for a given bedtime\n"
            "  [cyan]/chronotype [meq_score][/cyan]  Classify chronotype (MEQ or ask questions)\n"
            "  [cyan]/caffeine <mg> <hours>[/cyan]   Caffeine clearance calculator\n"
            "  [cyan]/sleepdebt <h1> <h2>...[/cyan]  Sleep debt from recent nights (hours)\n"
            "  [cyan]/hormones[/cyan]                 Hormonal sleep window reference\n"
            "  [cyan]/bedtime [sport][/cyan]          Pre-sleep protocol for your chronotype\n\n"
            "[bold dim cyan]Recovery:[/bold dim cyan]\n"
            "  [cyan]/readiness <rmssd1> <rmssd2>...[/cyan]  HRV readiness score (rMSSD values)\n"
            "  [cyan]/doms <type> <rpe> <min>[/cyan]   DOMS severity estimate (session type, RPE, minutes)\n"
            "  [cyan]/supercomp <type> <h>[/cyan]     Supercompensation window (session type, hours ago)\n"
            "  [cyan]/deload [tsb] [days] [weeks][/cyan]  Deload trigger analysis\n"
            "  [cyan]/recover [goal] [session][/cyan]  Recovery modality guide\n"
            "  [cyan]/mps [weight_kg][/cyan]           MPS optimization timing guide\n\n"
            "[bold dim cyan]Hydration:[/bold dim cyan]\n"
            "  [cyan]/sweat <pre_kg> <post_kg> [fluid_L] [hrs][/cyan]  Sweat loss + electrolytes\n"
            "  [cyan]/sweatest <sport> <hrs>[/cyan]   Estimate sweat loss by sport\n"
            "  [cyan]/rehydrate <pre_kg> <post_kg>[/cyan]  Full rehydration protocol\n"
            "  [cyan]/urine <1-8>[/cyan]               Urine color hydration status\n"
            "  [cyan]/hyponatremia <hrs> <L_hr>[/cyan]  EAH risk assessment\n"
            "  [cyan]/prehydrate [sport] [hrs_to_start][/cyan]  Pre-exercise hydration plan\n\n"
            "[bold dim cyan]Sports Intelligence:[/bold dim cyan]\n"
            "  [cyan]/assess [notes][/cyan]            Full AI sports readiness assessment (uses profile + HRV data)\n\n"
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

                # ── Supplement Interaction Checker ──────────────────────────

                elif q_lower.startswith("/check "):
                    raw = query[7:].strip()
                    if raw:
                        compounds = [c.strip() for c in raw.split() if c.strip()]
                        with console.status(
                            f"[dim cyan]  Checking interactions for: {', '.join(compounds)}...[/dim cyan]",
                            spinner="dots2",
                        ):
                            interactions = lookup_interactions(compounds, min_severity="synergistic")
                        report = format_interaction_report(compounds, interactions)
                        console.print(Panel(
                            report,
                            title="[cyan]Supplement Interaction Report[/cyan]",
                            border_style="cyan",
                            box=box.ROUNDED,
                            padding=(0, 2),
                        ))
                    else:
                        console.print("[dim]  Usage: /check caffeine creatine melatonin[/dim]")

                elif q_lower.startswith("/interact "):
                    compound = query[10:].strip()
                    if compound:
                        interactions = lookup_single(compound)
                        if interactions:
                            report = format_interaction_report([compound], interactions)
                            console.print(Panel(
                                report,
                                title=f"[cyan]Interactions: {compound.title()}[/cyan]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        else:
                            console.print(f"[dim]  No known interactions for '{compound}' in database.[/dim]")
                            console.print("[dim]  Try researching it: just type your question.[/dim]")
                    else:
                        console.print("[dim]  Usage: /interact caffeine[/dim]")

                # ── Food & Nutrition Lookup ──────────────────────────────────

                elif q_lower.startswith("/food+ ") or q_lower.startswith("/food "):
                    include_aminos = q_lower.startswith("/food+ ")
                    prefix_len = 7 if include_aminos else 6
                    args = query[prefix_len:].strip().split()
                    food_name = " ".join(args[:-1]) if args and args[-1].lstrip("-").isdigit() else " ".join(args)
                    grams = float(args[-1]) if args and args[-1].lstrip("-").isdigit() else 100.0

                    if food_name:
                        with console.status(
                            f"[dim cyan]  Looking up '{food_name}' in USDA FoodData Central...[/dim cyan]",
                            spinner="earth",
                        ):
                            food = self.fdc.search_and_get(
                                food_name, serving_g=grams, include_aminos=include_aminos
                            )
                        if food:
                            console.print(Panel(
                                food.full_report(include_aminos=include_aminos),
                                title=f"[cyan]USDA FoodData Central[/cyan]  [dim]FDC#{food.fdc_id}[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        else:
                            console.print(f"[dim]  No results for '{food_name}'. Try a different name.[/dim]")
                    else:
                        console.print("[dim]  Usage: /food chicken breast [150][/dim]")

                elif q_lower.startswith("/compare "):
                    raw = query[9:].strip()
                    if raw:
                        foods = [f.strip() for f in raw.split(",") if f.strip()]
                        if len(foods) >= 2:
                            with console.status(
                                f"[dim cyan]  Comparing {len(foods)} foods...[/dim cyan]",
                                spinner="earth",
                            ):
                                table_str = self.fdc.compare_foods(foods)
                            console.print(Panel(
                                table_str,
                                title="[cyan]Food Comparison[/cyan]  [dim]USDA FoodData Central[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 1),
                            ))
                        else:
                            console.print("[dim]  Usage: /compare chicken breast, salmon, tofu[/dim]")
                    else:
                        console.print("[dim]  Usage: /compare chicken breast, salmon, tofu[/dim]")

                # ── Training Load Commands ──────────────────────────────────

                elif q_lower.startswith("/session "):
                    parts = query.split()
                    if len(parts) >= 4:
                        try:
                            day = int(parts[1])
                            duration = float(parts[2])
                            rpe = float(parts[3])
                            sport = " ".join(parts[4:]) if len(parts) > 4 else ""
                            s = TrainingSession(date_offset=day, duration_min=duration, rpe=rpe, sport=sport)
                            self._pending_sessions.append(s)
                            console.print(
                                f"[dim]  Session logged: Day {day} | {duration:.0f}min | "
                                f"RPE {rpe} | Load {s.session_load:.0f} AU[/dim]\n"
                                f"[dim]  Total sessions: {len(self._pending_sessions)}. "
                                f"Use /load to compute ATL/CTL/TSB.[/dim]"
                            )
                        except ValueError:
                            console.print("[dim]  Usage: /session <day_offset> <minutes> <rpe_1-10> [sport][/dim]")
                    else:
                        console.print("[dim]  Usage: /session 0 60 7 cycling[/dim]")

                elif q_lower == "/load":
                    if not self._pending_sessions:
                        console.print(
                            "[dim]  No sessions logged. Use /session <day> <min> <rpe> to add sessions.[/dim]\n"
                            "[dim]  Example: /session 0 60 7 running[/dim]"
                        )
                    else:
                        metrics = self.load_calc.compute(self._pending_sessions)
                        ramp = self.load_calc.ramp_rate(self._pending_sessions)
                        content = metrics.display() + "\n"
                        if "ramp_rates" in ramp:
                            content += "\n  Ramp Rate Analysis:\n"
                            for r in ramp["ramp_rates"]:
                                safe_icon = "✅" if r["safe"] else "⚠️"
                                content += (
                                    f"  Week {r['week']}: {r['load_au']:.0f} AU  "
                                    f"({r['ramp_pct']:+.1f}%)  {safe_icon}\n"
                                )
                        console.print(Panel(
                            content,
                            title=f"[cyan]Training Load Analysis[/cyan]  [dim]({len(self._pending_sessions)} sessions)[/dim]",
                            border_style="cyan",
                            box=box.ROUNDED,
                            padding=(0, 2),
                        ))

                elif q_lower.startswith("/blocks"):
                    parts = query.split()
                    sport = parts[1].lower() if len(parts) > 1 else "strength"
                    athlete_name = self.profile.data.get("name", "")
                    blocks = get_block_plan(sport)
                    report = format_block_plan(blocks, athlete_name=athlete_name)
                    console.print(Panel(
                        report,
                        title=f"[cyan]Periodization Plan[/cyan]  [dim]{sport.title()}[/dim]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                elif q_lower.startswith("/prilepin "):
                    try:
                        pct = float(query.split()[1])
                        result = prilepins_recommendation(pct)
                        console.print(Panel(
                            result["note"] + "\n\n"
                            f"  Optimal total reps: {result.get('optimal_total_reps', 'N/A')}\n"
                            f"  Rep range: {result.get('rep_range', 'N/A')}\n"
                            f"  Evidence: {result['evidence']}",
                            title=f"[cyan]Prilepin's Table[/cyan]  [dim]{pct:.0f}% intensity[/dim]",
                            border_style="cyan",
                            box=box.SIMPLE,
                        ))
                    except (ValueError, IndexError):
                        console.print("[dim]  Usage: /prilepin 80[/dim]")

                # ── Blood Panel Commands ─────────────────────────────────────

                elif q_lower.startswith("/labs "):
                    raw = query[6:].strip().split()
                    if len(raw) >= 2 and len(raw) % 2 == 0:
                        panel: dict[str, float] = {}
                        valid = True
                        for i in range(0, len(raw), 2):
                            name_part = raw[i]
                            try:
                                val = float(raw[i + 1])
                                panel[name_part] = val
                            except ValueError:
                                console.print(f"[dim red]  Invalid value for {name_part}: {raw[i+1]}[/dim red]")
                                valid = False
                                break
                        if valid and panel:
                            sex = self.profile.data.get("sex", "male")
                            athlete_name = self.profile.data.get("name", "")
                            report = interpret_panel(panel, sex=sex, athlete_name=athlete_name)
                            console.print(Panel(
                                report,
                                title="[cyan]Blood Panel Analysis[/cyan]  [dim]USDA / Clinical Reference[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                    else:
                        console.print("[dim]  Usage: /labs ferritin 25 vitamin_d 35 cortisol 12[/dim]")

                elif q_lower.startswith("/biomarker "):
                    parts = query.split(maxsplit=2)
                    if len(parts) == 3:
                        try:
                            name_part = parts[1]
                            val = float(parts[2])
                            sex = self.profile.data.get("sex", "male")
                            result = self.bio_interp.interpret(name_part, val, sex=sex)
                            if result:
                                console.print(Panel(
                                    result.display() +
                                    (f"\n\n  Evidence: {result.ref.evidence}" if result.ref.evidence else ""),
                                    title=f"[cyan]Biomarker[/cyan]  {result.name}",
                                    border_style="cyan",
                                    box=box.SIMPLE,
                                ))
                            else:
                                console.print(f"[dim]  '{name_part}' not in biomarker database. Try: ferritin, testosterone, vitamin_d, cortisol, crp...[/dim]")
                        except ValueError:
                            console.print("[dim]  Usage: /biomarker ferritin 45[/dim]")
                    else:
                        console.print("[dim]  Usage: /biomarker ferritin 45[/dim]")

                # ── Sleep Optimization Commands ──────────────────────────────

                elif q_lower.startswith("/sleep "):
                    bedtime = query.split()[1] if len(query.split()) > 1 else "23:00"
                    cycles = optimal_wake_times(bedtime)
                    console.print(Panel(
                        cycles.display(),
                        title=f"[cyan]Sleep Cycle Calculator[/cyan]  [dim]Bedtime: {bedtime}[/dim]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                elif q_lower.startswith("/chronotype"):
                    parts = query.split()
                    if len(parts) > 1:
                        try:
                            meq = int(parts[1])
                            result = classify_chronotype(meq_score=meq)
                        except ValueError:
                            # Treat as bedtime
                            result = classify_chronotype(bedtime_wfree=parts[1])
                    else:
                        # Default intermediate bear if no input
                        result = classify_chronotype(meq_score=55)

                    if "error" in result:
                        console.print(f"[dim]  {result['error']}[/dim]")
                    else:
                        sport = self.profile.data.get("sport", "general")
                        target = athlete_sleep_target(sport)
                        console.print(Panel(
                            f"[bold]{result['label']}[/bold]\n\n"
                            f"  {result['description']}\n\n"
                            f"  Sleep window: {result['sleep_window'][0]} – {result['sleep_window'][1]}\n"
                            f"  Peak alertness: {result['peak_alertness'][0]} – {result['peak_alertness'][1]}\n"
                            f"  Peak physical performance: {result['peak_physical'][0]} – {result['peak_physical'][1]}\n\n"
                            f"  Athlete note: {result['athlete_notes']}\n\n"
                            f"  Sleep target ({sport}): {target['optimal_hours']}h optimal / {target['min_hours']}h minimum\n"
                            f"  Evidence: {result['evidence']}",
                            title=f"[cyan]Chronotype Analysis[/cyan]",
                            border_style="cyan",
                            box=box.ROUNDED,
                            padding=(0, 2),
                        ))

                elif q_lower.startswith("/caffeine "):
                    parts = query.split()
                    if len(parts) >= 3:
                        try:
                            dose = float(parts[1])
                            hours = float(parts[2])
                            fast = len(parts) < 4 or parts[3].lower() != "slow"
                            status = caffeine_clearance(dose, hours, fast_metabolizer=fast)
                            console.print(Panel(
                                status.display(),
                                title="[cyan]Caffeine Clearance[/cyan]  [dim](CYP1A2 pharmacokinetics)[/dim]",
                                border_style="cyan",
                                box=box.SIMPLE,
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /caffeine 200 6 [slow][/dim]")
                    else:
                        console.print("[dim]  Usage: /caffeine <mg> <hours_since_dose> [slow][/dim]")

                elif q_lower.startswith("/sleepdebt "):
                    raw = query.split()[1:]
                    if raw:
                        try:
                            nights = [float(h) for h in raw]
                            sex = self.profile.data.get("sex", "male")
                            sport = self.profile.data.get("sport", "general")
                            target = athlete_sleep_target(sport)
                            debt = sleep_debt_report(nights, target_hours=target["optimal_hours"])
                            console.print(Panel(
                                debt.display(),
                                title=f"[cyan]Sleep Debt Tracker[/cyan]  [dim]Target: {target['optimal_hours']}h ({sport})[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /sleepdebt 7 6.5 8 7 6[/dim]")
                    else:
                        console.print("[dim]  Usage: /sleepdebt 7 6.5 8 7 6[/dim]")

                elif q_lower == "/hormones":
                    console.print(Panel(
                        format_hormonal_windows(),
                        title="[cyan]Hormonal Sleep Windows[/cyan]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                elif q_lower.startswith("/bedtime"):
                    parts = query.split()
                    sport = parts[1] if len(parts) > 1 else self.profile.data.get("sport", "general")
                    # Get chronotype from profile if set, else default bear
                    ct_data = self.profile.data.get("chronotype", "bear")
                    sleep_t = CHRONOTYPE_PROFILES.get(ct_data, CHRONOTYPE_PROFILES["bear"])["sleep_window"][0]
                    protocol = pre_sleep_protocol(chronotype=ct_data, sport=sport, sleep_time=sleep_t)
                    console.print(Panel(
                        protocol,
                        title=f"[cyan]Pre-Sleep Protocol[/cyan]  [dim]{ct_data.title()} chronotype · {sport}[/dim]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                # ── Recovery Commands ────────────────────────────────────────

                elif q_lower.startswith("/readiness"):
                    raw = query.split()[1:]
                    if raw:
                        try:
                            rmssd_vals = [float(v) for v in raw]
                            hrv_readings = [HRVReading(rmssd=v, resting_hr=60.0) for v in rmssd_vals]
                            tsb = self._last_tsb if hasattr(self, "_last_tsb") else None
                            sleep_debt = self.profile.data.get("sleep_debt_hours", 0.0)
                            r = compute_readiness(hrv_readings, tsb=tsb, sleep_debt_hours=sleep_debt)
                            console.print(Panel(
                                format_readiness_report(r),
                                title=f"[cyan]HRV Readiness[/cyan]  [dim]Score: {r.score:.0f}/100[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /readiness 55 58 52 61 64  (rMSSD values oldest→newest)[/dim]")
                    else:
                        console.print("[dim]  Usage: /readiness <rmssd1> <rmssd2> ...  (at least 2 values)[/dim]")

                elif q_lower.startswith("/doms "):
                    parts = query.split(maxsplit=3)
                    # /doms <type> <rpe> <min>
                    if len(parts) >= 4:
                        try:
                            session_type = parts[1]
                            rpe = float(parts[2])
                            minutes = int(parts[3].split()[0])
                            trained = self.profile.data.get("training_status", "trained")
                            d = estimate_doms(session_type, rpe, minutes, trained_status=trained)
                            lines = [
                                f"Session Type: {session_type.replace('_', ' ').title()}",
                                f"Severity: {d.severity.upper()}  (score {d.severity_score:.1f}/10)",
                                f"Peak DOMS: ~{d.peak_hours}h post-exercise",
                                f"Resolution: ~{d.resolution_hours}h",
                                f"Mechanism: {d.primary_mechanism}",
                                f"Evidence: {d.evidence}",
                            ]
                            if d.notes:
                                lines.append("\nNotes:")
                                for n in d.notes:
                                    lines.append(f"  • {n}")
                            console.print(Panel(
                                "\n".join(lines),
                                title=f"[cyan]DOMS Estimate[/cyan]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except (ValueError, IndexError):
                            console.print("[dim]  Usage: /doms strength_eccentric_heavy 8 60\n"
                                          "  Types: strength_eccentric_heavy, plyometrics, running_new, cycling, swimming...[/dim]")
                    else:
                        console.print("[dim]  Usage: /doms <session_type> <rpe> <duration_min>[/dim]\n"
                                      "[dim]  Types: " + ", ".join(list(EXERCISE_DAMAGE_COEFFICIENTS.keys())[:4]) + "...[/dim]")

                elif q_lower.startswith("/supercomp "):
                    parts = query.split()
                    if len(parts) >= 3:
                        try:
                            stype = parts[1]
                            hours_ago = float(parts[2])
                            result = supercompensation_window(stype, hours_ago)
                            lines = [
                                f"Session Type: {result['session_type']}",
                                f"Hours Elapsed: {result['hours_elapsed']:.0f}h",
                                f"Current Phase: {result['current_phase'].replace('_', ' ').title()}",
                            ]
                            if result["hours_to_supercomp_peak"] is None:
                                lines.append("Supercompensation Window: PASSED — schedule next session soon")
                            elif result["hours_to_supercomp_peak"] == 0:
                                lines.append("Supercompensation Window: NOW — optimal training time!")
                            else:
                                lines.append(f"Hours to Supercomp Peak: {result['hours_to_supercomp_peak']:.0f}h")
                            start, end = result["optimal_next_session_window_hours"]
                            lines.append(f"Optimal Next Session: {start:.0f}–{end:.0f}h post-session")
                            lines.append(f"\n{result['evidence']}")
                            console.print(Panel(
                                "\n".join(lines),
                                title=f"[cyan]Supercompensation Window[/cyan]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /supercomp strength 24  (type, hours since session)[/dim]")
                    else:
                        console.print("[dim]  Usage: /supercomp <strength|endurance|high_intensity_interval|team_sport> <hours_ago>[/dim]")

                elif q_lower.startswith("/deload"):
                    parts = query.split()
                    try:
                        tsb = float(parts[1]) if len(parts) > 1 else None
                        hard_days = int(parts[2]) if len(parts) > 2 else 0
                        weeks = int(parts[3]) if len(parts) > 3 else 0
                        sleep_debt = self.profile.data.get("sleep_debt_hours", 0.0)
                        subj = self.profile.data.get("subjective_fatigue")
                        d = assess_deload_need(
                            tsb=tsb,
                            consecutive_hard_days=hard_days,
                            weeks_since_deload=weeks,
                            sleep_debt_hours=sleep_debt,
                            subjective_fatigue=int(subj) if subj else None,
                        )
                        status_color = "red" if d.should_deload else "green"
                        lines = [
                            f"[{status_color}]{'⚠ DELOAD RECOMMENDED' if d.should_deload else '✓ No deload needed'}[/{status_color}]",
                            f"Urgency: {d.urgency.upper()}",
                        ]
                        if d.should_deload:
                            lines.append(f"Type: {d.deload_type}")
                            lines.append(f"\nTriggers:")
                            for t in d.triggered_by:
                                lines.append(f"  • {t}")
                            lines.append(f"\nGuidance:")
                            for g in d.deload_guidance:
                                lines.append(f"  • {g}")
                        lines.append(f"\nEvidence: {d.evidence}")
                        console.print(Panel(
                            "\n".join(lines),
                            title="[cyan]Deload Assessment[/cyan]",
                            border_style="cyan" if not d.should_deload else "yellow",
                            box=box.ROUNDED,
                            padding=(0, 2),
                        ))
                    except ValueError:
                        console.print("[dim]  Usage: /deload [tsb] [consecutive_hard_days] [weeks_since_deload][/dim]")

                elif q_lower.startswith("/recover"):
                    parts = query.split()
                    goal = parts[1] if len(parts) > 1 else "general"
                    session_type = parts[2] if len(parts) > 2 else "strength"
                    guide = recovery_modality_guide(goal=goal, post_session_type=session_type)
                    console.print(Panel(
                        guide,
                        title=f"[cyan]Recovery Modalities[/cyan]  [dim]Goal: {goal} | Post: {session_type}[/dim]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                elif q_lower.startswith("/mps"):
                    parts = query.split()
                    weight = float(parts[1]) if len(parts) > 1 else self.profile.data.get("weight_kg", 75.0)
                    guide = mps_timing_guide(body_weight_kg=float(weight))
                    console.print(Panel(
                        guide,
                        title=f"[cyan]MPS Timing Guide[/cyan]  [dim]{weight:.0f}kg[/dim]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                # ── Hydration Commands ───────────────────────────────────────

                elif q_lower.startswith("/sweat "):
                    parts = query.split()
                    if len(parts) >= 3:
                        try:
                            pre = float(parts[1])
                            post = float(parts[2])
                            fluid = float(parts[3]) if len(parts) > 3 else 0.0
                            hrs = float(parts[4]) if len(parts) > 4 else 1.0
                            sport = self.profile.data.get("sport", "general")
                            sl = calculate_sweat_loss(pre, post, fluid, hrs, sport=sport)
                            console.print(Panel(
                                sl.summary(),
                                title=f"[cyan]Sweat Loss Analysis[/cyan]  [dim]{sport}[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /sweat <pre_kg> <post_kg> [fluid_L] [duration_hrs][/dim]")
                    else:
                        console.print("[dim]  Usage: /sweat <pre_kg> <post_kg> [fluid_L] [duration_hrs][/dim]")

                elif q_lower.startswith("/sweatest "):
                    parts = query.split()
                    if len(parts) >= 3:
                        try:
                            sport = parts[1]
                            hrs = float(parts[2])
                            weight = self.profile.data.get("weight_kg", 75.0)
                            intensity = parts[3] if len(parts) > 3 else "moderate"
                            sl = estimate_sweat_loss_by_sport(sport, hrs, body_weight_kg=float(weight),
                                                              intensity=intensity)
                            console.print(Panel(
                                sl.summary(),
                                title=f"[cyan]Sweat Estimate[/cyan]  [dim]{sport} · {hrs:.1f}h · {intensity}[/dim]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /sweatest running 1.5 [easy|moderate|hard][/dim]")
                    else:
                        console.print("[dim]  Usage: /sweatest <sport> <hours> [intensity]  "
                                      "Sports: " + ", ".join(list(SPORT_SWEAT_RATES.keys())[:4]) + "...[/dim]")

                elif q_lower.startswith("/rehydrate "):
                    parts = query.split()
                    if len(parts) >= 3:
                        try:
                            pre = float(parts[1])
                            post = float(parts[2])
                            fluid = float(parts[3]) if len(parts) > 3 else 0.0
                            hrs = float(parts[4]) if len(parts) > 4 else 1.0
                            time_next = float(parts[5]) if len(parts) > 5 else 24.0
                            sport = self.profile.data.get("sport", "general")
                            sl = calculate_sweat_loss(pre, post, fluid, hrs, sport=sport)
                            protocol = design_rehydration_protocol(sl, time_next)
                            console.print(Panel(
                                format_rehydration_report(protocol, sl),
                                title="[cyan]Rehydration Protocol[/cyan]",
                                border_style="cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /rehydrate <pre_kg> <post_kg> [fluid_L] [duration_h] [hours_to_next_session][/dim]")
                    else:
                        console.print("[dim]  Usage: /rehydrate <pre_kg> <post_kg>[/dim]")

                elif q_lower.startswith("/urine "):
                    parts = query.split()
                    if len(parts) >= 2:
                        try:
                            color_num = int(parts[1])
                            result = urine_color_status(color_num)
                            urgent_flag = " ⚠" if result["urgent"] else ""
                            lines = [
                                f"Color #{result['color_number']}: {result['color_name']}",
                                f"Status: {result['status']}{urgent_flag}",
                                f"Action: {result['action']}",
                                f"Evidence: {result['evidence']}",
                            ]
                            console.print(Panel(
                                "\n".join(lines),
                                title="[cyan]Urine Color / Hydration Status[/cyan]",
                                border_style="red" if result["urgent"] else "cyan",
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /urine <1-8>  (1=pale, 8=dark brown)[/dim]")
                    else:
                        console.print("[dim]  Usage: /urine <1-8>  (Armstrong urine color scale)[/dim]")

                elif q_lower.startswith("/hyponatremia "):
                    parts = query.split()
                    if len(parts) >= 3:
                        try:
                            event_hrs = float(parts[1])
                            intake_L_hr = float(parts[2])
                            sport = parts[3] if len(parts) > 3 else self.profile.data.get("sport", "endurance")
                            weight = self.profile.data.get("weight_kg", 70.0)
                            result = hyponatremia_risk(event_hrs, intake_L_hr, sport, float(weight))
                            risk_color = {"HIGH": "red", "MODERATE": "yellow", "LOW": "green"}.get(result["risk_level"], "cyan")
                            lines = [
                                f"[{risk_color}]Risk Level: {result['risk_level']}[/{risk_color}]",
                                "",
                                "Risk Factors:",
                            ]
                            for d in result["drivers"]:
                                lines.append(f"  • {d}")
                            lines.append(f"\nRecommendation: {result['recommendation']}")
                            lines.append(f"\n⚠ {result['key_warning']}")
                            lines.append(f"\nEvidence: {result['evidence']}")
                            console.print(Panel(
                                "\n".join(lines),
                                title="[cyan]Hyponatremia (EAH) Risk Assessment[/cyan]",
                                border_style=risk_color,
                                box=box.ROUNDED,
                                padding=(0, 2),
                            ))
                        except ValueError:
                            console.print("[dim]  Usage: /hyponatremia <event_hours> <fluid_L_per_hr> [sport][/dim]")
                    else:
                        console.print("[dim]  Usage: /hyponatremia <event_hours> <L/hr intake>[/dim]")

                elif q_lower.startswith("/prehydrate"):
                    parts = query.split()
                    sport = parts[1] if len(parts) > 1 else self.profile.data.get("sport", "general")
                    hours_to_start = float(parts[2]) if len(parts) > 2 else 3.0
                    weight = self.profile.data.get("weight_kg", 75.0)
                    plan = pre_exercise_hydration_plan(
                        float(weight), event_duration_hours=1.5, sport=sport,
                        start_hours_from_now=hours_to_start,
                    )
                    lines = [
                        f"Pre-exercise fluid target: {plan['pre_exercise_target_mL']}mL",
                        f"Intra-exercise target: {plan['intra_exercise_L_hr']} L/h",
                        f"Expected sweat loss: ~{plan['total_expected_sweat_L']}L",
                        f"Urine target: {plan['urine_target']}",
                        "",
                        "Schedule:",
                    ]
                    for step in plan["schedule"]:
                        lines.append(f"  • {step}")
                    lines.append(f"\nSodium: {plan['sodium_recommendation']}")
                    lines.append(f"Evidence: {plan['evidence']}")
                    console.print(Panel(
                        "\n".join(lines),
                        title=f"[cyan]Pre-Exercise Hydration Plan[/cyan]  [dim]{sport} · T-{hours_to_start:.0f}h[/dim]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))

                # ── Sports Intelligence Assessment ──────────────────────────

                elif q_lower.startswith("/assess"):
                    notes = query[8:].strip() if len(query) > 8 else ""
                    console.print()
                    console.print(Panel(
                        "[dim]Running Sports Intelligence Assessment...[/dim]",
                        title="[bold cyan]Sports Intelligence Agent[/bold cyan]",
                        border_style="cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    ))
                    console.print()

                    # Build athlete data from profile + any recent state
                    athlete_data = {
                        "athlete_name": self.profile.data.get("name", "Athlete"),
                        "sport": self.profile.data.get("sport", "General"),
                        "training_phase": self.profile.data.get("training_phase", "General Preparation"),
                        "hrv_readings": [],  # User should provide via /readiness first; stored in profile
                        "tsb": getattr(self, "_last_tsb", None),
                        "atl": getattr(self, "_last_atl", None),
                        "ctl": getattr(self, "_last_ctl", None),
                        "sleep_debt_hours": self.profile.data.get("sleep_debt_hours", 0.0),
                        "consecutive_hard_days": self.profile.data.get("consecutive_hard_days", 0),
                        "weeks_since_deload": self.profile.data.get("weeks_since_deload", 0),
                        "subjective_fatigue": self.profile.data.get("subjective_fatigue"),
                        "biomarker_summary": self.profile.data.get("last_biomarker_summary", ""),
                        "planned_session": self.profile.data.get("planned_session", ""),
                        "notes": notes or self.profile.data.get("athlete_notes", ""),
                    }

                    def on_assess_text(text: str):
                        console.print(text, end="", markup=False)

                    console.print()
                    assessment = await run_sports_assessment(self.client, athlete_data, on_text=on_assess_text)
                    console.print()
                    console.print()
                    console.rule("[dim]Sports Intelligence Assessment Complete[/dim]")

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
