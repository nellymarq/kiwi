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
from tools.openalex import OpenAlexClient, SPORTS_NUTRITION_JOURNALS
from tools.clinical_trials import ClinicalTrialsClient
from tools.europepmc import EuropePMCClient
from tools.unpaywall import UnpaywallClient
from tools.semantic_scholar import SemanticScholarClient
from tools.grade import assess as grade_assess, GradeInputs, assess_from_evidence_tier
from tools.quality_assessment import format_checklist as quality_checklist
from agents.synthesis import SynthesisAgent
from agents.n_of_1 import NOf1Agent
from tools.calculations import SportsCalc
from tools.exporter import ResearchExporter
from tools.interactions import lookup_interactions
from tools.food_database import FDCClient
from tools.periodization import TrainingLoadCalculator
from tools.biomarkers import BiomarkerInterpreter
from tools.injury_prevention import (
    calculate_acwr, format_acwr_report,
    get_prevention_protocol, format_prevention_protocol,
    match_prevention_protocol,
)
from tools.female_athlete import (
    match_training_to_phase, screen_reds, format_reds_report,
    format_cycle_training,
)
from memory.store import KiwiMemory
from memory.profile import UserProfile
from memory import client_manager
from memory.preferences import PreferencesStore
from tools.pdf_export import generate_client_report, BrandConfig
from agents.recommender import RecommenderAgent
from agents.meal_plan import MealPlanAgent
from agents.training_plan import TrainingPlanAgent
from tools.auto_quality import auto_assess as auto_quality_assess
from tools.effect_size import cohens_d, hedges_g, mean_difference, relative_risk, odds_ratio, number_needed_to_treat
from tools.pdf_reader import read_pdf as read_oa_pdf
from tools.cost_tracker import SessionCostTracker
from tools.team_analytics import format_team_summary, compare_clients, format_client_snapshot
from memory.watch_list import WatchList
from memory.interventions import InterventionTracker
from agents.systematic_review import SystematicReviewAgent
from agents.competition_prep import CompetitionPrepAgent
from memory.sessions import save_session, load_session, list_sessions
from memory.session_log import log_exchange, log_stats
from tools.config import load_config, validate_config, first_run_check, create_default_config
from tools.supplements import SUPPLEMENT_DB
from memory.progress import ProgressTracker, KNOWN_METRICS
from agents.stack_optimizer import StackOptimizerAgent
from agents.risk_screen import RiskScreenAgent
from agents.question_gen import QuestionGenAgent
from tools.proactive import check_biomarker, format_proactive_actions
from tools.contradiction import detect_contradictions, format_contradictions
from tools.command_router import route_natural_language, format_route_suggestion
from tools.protocol_templates import get_template, list_templates
from tools.nutrient_gaps import analyze_gaps, format_gap_analysis
from tools.knowledge_frontier import analyze_frontiers, format_frontiers
from tools.freshness import format_freshness_report
from agents.daily_brief import DailyBriefAgent
from tools.timing_schedule import generate_timing_schedule, check_separation_conflicts, format_timing_schedule
from tools.client_export import export_client
from tools.oura import OuraClient
from tools.wearable_import import import_file as import_wearable_file, format_import_result

from handlers.injury import (
    handle_acwr,
    handle_fms,
    handle_overuse,
    handle_prevent,
    handle_return_to_sport,
)
from handlers.mental import (
    handle_anxiety,
    handle_burnout,
    handle_visualize,
)
from handlers.environmental import (
    handle_airquality,
    handle_altitude,
    handle_cold,
    handle_heat,
    handle_jetlag,
)
from handlers.female import (
    handle_cycle,
    handle_iron,
    handle_postpartum,
    handle_reds,
)
from handlers.training_zones import (
    handle_distribution,
    handle_hrmax,
    handle_hrzones,
    handle_pacezones,
    handle_powerzones,
    handle_vo2max,
)
from handlers.body_composition import (
    handle_bodyfat,
    handle_ea,
    handle_ffmi,
    handle_skinfold,
    handle_weightplan,
)
from handlers.sleep import (
    handle_bedtime,
    handle_caffeine,
    handle_chronotype,
    handle_hormones,
    handle_sleep,
    handle_sleepdebt,
)
from handlers.recovery import (
    handle_deload,
    handle_doms,
    handle_mps,
    handle_readiness,
    handle_recover,
    handle_supercomp,
)
from handlers.hydration import (
    handle_hyponatremia,
    handle_prehydrate,
    handle_rehydrate,
    handle_sweat,
    handle_sweatest,
    handle_urine,
)
from handlers.labs import handle_biomarker, handle_labs
from handlers.food import handle_compare, handle_food
from handlers.supplements import (
    handle_check,
    handle_interact,
    handle_supp,
    handle_supplist,
)
from handlers.training_load import (
    handle_blocks,
    handle_load,
    handle_prilepin,
    handle_session,
)
from handlers.progress import (
    handle_dashboard,
    handle_team,
    handle_track,
    handle_trends_with_metric,
)
from handlers.interventions import handle_intervention
from handlers.sports import handle_assess
from handlers.literature import (
    handle_citedby,
    handle_fulltext,
    handle_openalex,
    handle_pubmed,
    handle_tldr,
    handle_trials,
)
from handlers.planning import handle_meal_plan, handle_training_plan
from handlers.competition_prep import handle_competition_prep
from handlers.wearable import handle_import_labs, handle_import_wearable, handle_oura
from handlers.orchestration import handle_digest, handle_unwatch, handle_watch, handle_watched

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

DEFAULT_PUBMED_MAX_RESULTS = 6
DEFAULT_OPENALEX_MAX_RESULTS = 4
DEFAULT_EPMC_MAX_RESULTS = 3
DEFAULT_SS_MAX_RESULTS = 3
DEFAULT_YEARS_BACK = 8


def fetch_literature_context(
    query: str,
    pubmed: PubMedClient | None,
    openalex: OpenAlexClient | None,
    epmc: "EuropePMCClient | None" = None,
    semantic: "SemanticScholarClient | None" = None,
    max_pubmed: int = DEFAULT_PUBMED_MAX_RESULTS,
    max_openalex: int = DEFAULT_OPENALEX_MAX_RESULTS,
    max_epmc: int = DEFAULT_EPMC_MAX_RESULTS,
    max_semantic: int = DEFAULT_SS_MAX_RESULTS,
    years_back: int = DEFAULT_YEARS_BACK,
) -> str:
    """Search all configured literature sources, dedupe by DOI, return merged context."""
    keywords = " ".join(query.split()[:6])
    blocks = []
    seen_dois: set[str] = set()

    # PubMed search
    if pubmed:
        with console.status("[dim cyan]  Searching PubMed...[/dim cyan]", spinner="earth"):
            articles = pubmed.search_and_fetch(keywords, max_results=max_pubmed, years_back=years_back)
        if articles:
            for a in articles:
                if a.doi:
                    seen_dois.add(a.doi.lower())
            console.print(f"[dim]  PubMed: {len(articles)} articles[/dim]")
            blocks.append(pubmed.build_context_block(articles))

    # OpenAlex search (sports nutrition journals)
    if openalex:
        with console.status("[dim cyan]  Searching OpenAlex (sports nutrition journals)...[/dim cyan]", spinner="earth"):
            works = openalex.search_sports_nutrition(keywords, max_results=max_openalex + 2, years_back=years_back)
        unique_works = [w for w in works if not w.doi or w.doi.lower() not in seen_dois][:max_openalex]
        if unique_works:
            for w in unique_works:
                if w.doi:
                    seen_dois.add(w.doi.lower())
            console.print(f"[dim]  OpenAlex: {len(unique_works)} additional articles[/dim]")
            blocks.append(openalex.build_context_block(unique_works))

    # Europe PMC search (open access full-text focus)
    if epmc:
        with console.status("[dim cyan]  Searching Europe PMC (open access full-text)...[/dim cyan]", spinner="earth"):
            epmc_articles = epmc.search(keywords, max_results=max_epmc + 2, years_back=years_back, open_access_only=True)
        unique_epmc = [a for a in epmc_articles if not a.doi or a.doi.lower() not in seen_dois][:max_epmc]
        if unique_epmc:
            for a in unique_epmc:
                if a.doi:
                    seen_dois.add(a.doi.lower())
            console.print(f"[dim]  Europe PMC: {len(unique_epmc)} additional OA articles[/dim]")
            blocks.append(epmc.build_context_block(unique_epmc))

    # Semantic Scholar search (TLDR summaries for rapid triage)
    if semantic:
        with console.status("[dim cyan]  Searching Semantic Scholar (TLDR summaries)...[/dim cyan]", spinner="earth"):
            ss_papers = semantic.search(keywords, max_results=max_semantic + 2, years_back=years_back)
        unique_ss = [p for p in ss_papers if not p.doi or p.doi.lower() not in seen_dois][:max_semantic]
        if unique_ss:
            console.print(f"[dim]  Semantic Scholar: {len(unique_ss)} additional papers with TLDRs[/dim]")
            blocks.append(semantic.build_context_block(unique_ss))

    if not blocks:
        console.print("[dim]  No recent literature found for this query[/dim]")
        return ""

    return "\n\n".join(blocks)


# ── Main Kiwi Class ───────────────────────────────────────────────────────────

class Kiwi:
    """
    Kiwi orchestrator — coordinates the full multi-agent research pipeline
    and manages the interactive CLI.
    """

    def __init__(self, use_pubmed: bool = True):
        self.console = console  # handlers/ modules access via kiwi.console
        self.client = anthropic.AsyncAnthropic()
        self.orchestrator = KiwiOrchestrator(self.client)
        client_manager.ensure_setup()
        self.active_client_name = client_manager.get_active_client()
        self.memory = KiwiMemory(client=self.active_client_name)
        self.profile = UserProfile(client=self.active_client_name)
        self.preferences = PreferencesStore(client=self.active_client_name)
        self.recommender_agent = RecommenderAgent(self.client)
        self.meal_plan_agent = MealPlanAgent(self.client)
        self.training_plan_agent = TrainingPlanAgent(self.client)
        self.systematic_review_agent = SystematicReviewAgent(self.client)
        self.competition_prep_agent = CompetitionPrepAgent(self.client)
        self.stack_optimizer_agent = StackOptimizerAgent(self.client)
        self.risk_screen_agent = RiskScreenAgent(self.client)
        self.question_gen_agent = QuestionGenAgent(self.client)
        self.daily_brief_agent = DailyBriefAgent(self.client)
        self.progress = ProgressTracker(client=self.active_client_name)
        self.interventions = InterventionTracker(client=self.active_client_name)
        self.watch_list = WatchList(client=self.active_client_name)
        self.cost = SessionCostTracker()
        self.config = load_config()
        self.pubmed = PubMedClient() if use_pubmed else None
        self.openalex = OpenAlexClient() if use_pubmed else None
        self.trials = ClinicalTrialsClient() if use_pubmed else None
        self.epmc = EuropePMCClient() if use_pubmed else None
        self.unpaywall = UnpaywallClient() if use_pubmed else None
        self.semantic = SemanticScholarClient() if use_pubmed else None
        self.synthesis_agent = SynthesisAgent(self.client)
        self.n_of_1_agent = NOf1Agent(self.client)
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

        # Literature pre-fetch (PubMed + OpenAlex)
        pubmed_context = ""
        if self.pubmed or self.openalex:
            pubmed_context = fetch_literature_context(
                query, self.pubmed, self.openalex, self.epmc, self.semantic,
            )

        # Profile + memory context
        profile_summary = self.profile.to_summary()
        memory_summary = self.memory.get_history_summary()

        # Add calc metrics only when all required fields are actually set
        if (self.profile.is_complete()
                and self.profile.get("height_cm")
                and self.profile.get("age")
                and self.profile.get("sex")):
            try:
                metrics = self.calc.compute_full_metrics(
                    weight_kg=self.profile.get("weight_kg"),
                    height_cm=self.profile.get("height_cm"),
                    age=self.profile.get("age"),
                    sex=self.profile.get("sex"),
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
            "[bold dim cyan]Supplements:[/bold dim cyan]\n"
            "  [cyan]/supp <name>[/cyan]              Dosing protocol for a supplement\n"
            "  [cyan]/supplist [category][/cyan]      List all supplements (or filter: ergogenic/health/recovery)\n\n"
            "[bold dim cyan]Body Composition:[/bold dim cyan]\n"
            "  [cyan]/bodyfat <kg> <bf%> [sport][/cyan]  Body composition analysis\n"
            "  [cyan]/ffmi <kg> <bf%> <height_cm>[/cyan] Fat-Free Mass Index\n"
            "  [cyan]/ea <kcal_in> <kcal_ex> <lm_kg>[/cyan] Energy Availability (RED-S screening)\n"
            "  [cyan]/weightplan <now_kg> <goal_kg> <bf%> [goal][/cyan] Safe weight change rate\n"
            "  [cyan]/skinfold <sex> <age> <s1> <s2> <s3>[/cyan] Body fat from skinfolds\n\n"
            "[bold dim cyan]Training Zones:[/bold dim cyan]\n"
            "  [cyan]/hrzones <hr_rest> <hr_max>[/cyan]  Heart rate zones (Karvonen)\n"
            "  [cyan]/powerzones <ftp_watts>[/cyan]     Power zones (Coggan/Allen FTP)\n"
            "  [cyan]/pacezones <vdot>[/cyan]           Running pace zones (Daniels' VDOT)\n"
            "  [cyan]/vo2max <distance_m>[/cyan]        VO2max from Cooper 12-min test\n"
            "  [cyan]/hrmax <age> [method][/cyan]       Predict max heart rate\n"
            "  [cyan]/distribution [sport] [level] [phase][/cyan] Training intensity distribution\n\n"
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
        """Main async REPL loop — dispatches to _handle_* methods."""
        session_num = self.memory.start_session()
        self._show_welcome(session_num)

        # Shared state dict passed to all handlers
        self._state = {
            "last_query": "",
            "last_response": "",
            "last_output": "",
            "last_critique": {},
            "last_score": 0.0,
            "session_num": session_num,
        }

        while True:
            try:
                console.print()
                prompt = f"[bold cyan]Kiwi[/bold cyan]"
                if self.active_client_name and self.active_client_name != "self":
                    prompt += f"[dim] ({self.active_client_name})[/dim]"
                if self.active_thread:
                    prompt += f"[dim] [{self.active_thread}][/dim]"
                prompt += "[bold cyan] >[/bold cyan] "
                query = console.input(prompt).strip()

                if not query:
                    continue

                should_break = await self._dispatch_command(query)
                if should_break:
                    break

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

    async def _dispatch_command(self, query: str) -> bool:
        """
        Dispatch a single command. Returns True if the REPL should exit.

        All 133 command handlers live here, organized by section headers.
        State is accessed via self._state dict.
        """
        q_lower = query.lower()

        # ── Help Command ────────────────────────────────────────────

        if q_lower in ("/help", "/commands"):
            help_text = (
                "[bold]Research:[/bold]  Just type a question · /protocol <query> · /plan <query>\n"
                "[bold]Literature:[/bold] /pubmed · /openalex · /trials · /tldr · /fulltext <doi> · /citedby <doi>\n"
                "[bold]Deep Research:[/bold] /synthesize <claim> · /n_of_1 <q> · /grade · /quality · /recommend <finding>\n"
                "[bold]Delivery:[/bold]  /pdf · /accepted [note] · /rejected [reason] · /preferences\n"
                "[bold]Planning:[/bold]  /meal_plan [days] · /training_plan [sport] [weeks] · /fight_prep · /race_prep\n"
                "[bold]Quality:[/bold]   /autoquality <title> · /quality <tool>\n"
                "[bold]Analytics:[/bold] /effect <m1 sd1 n1 m2 sd2 n2> · /readpdf <doi> · /cost · /team\n"
                "[bold]Progress:[/bold]  /track <metric> <value> · /trends <metric> · /dashboard\n"
                "[bold]Optimize:[/bold]  /optimize_stack · /risk_screen · /suggest_research · /gaps · /frontiers\n"
                "[bold]Intel:[/bold]     /brief · /freshness · /onboard · /summary\n"
                "[bold]Orchestration:[/bold] /review <topic> · /watch <topic> · /watched · /digest\n"
                "[bold]Clients:[/bold]    /clients · /new_client <name> · /switch_client <name> · /delete_client <name>\n"
                "[bold]Memory:[/bold]   /memory · /remember <note> · /export · /archive <keywords> · /stale\n"
                "[bold]Threads:[/bold]  /thread new|use|list <name>\n"
                "[bold]Profile:[/bold]  /profile · /profile set <field> <value>\n"
                "[bold]Calc:[/bold]     /calc\n"
                "[bold]Supps:[/bold]    /supp <name> · /supplist [cat] · /check <c1> [c2..] · /interact <c>\n"
                "[bold]Food:[/bold]     /food <name> [g] · /food+ <name> [g] · /compare <f1>, <f2>\n"
                "[bold]Training:[/bold] /session <day> <min> <rpe> · /load · /blocks [sport] · /prilepin <%>\n"
                "[bold]Zones:[/bold]    /hrzones <rest> <max> · /powerzones <ftp> · /pacezones <vdot> · /vo2max <m> · /hrmax <age> · /distribution\n"
                "[bold]Labs:[/bold]     /labs <marker val...> · /biomarker <name> <val>\n"
                "[bold]Sleep:[/bold]    /sleep <HH:MM> · /chronotype [meq] · /caffeine <mg> <hrs> · /sleepdebt <h1 h2..> · /hormones · /bedtime [sport]\n"
                "[bold]Recovery:[/bold] /readiness <r1 r2..> · /doms <type> <rpe> <min> · /supercomp <type> <h> · /deload · /recover · /mps <kg>\n"
                "[bold]Hydrate:[/bold]  /sweat <pre> <post> [L] [hrs] · /sweatest <sport> <hrs> · /rehydrate · /urine <1-8> · /hyponatremia · /prehydrate\n"
                "[bold]Body:[/bold]     /bodyfat <kg> <bf%> · /ffmi <kg> <bf%> <cm> · /ea <in> <ex> <lm> · /weightplan · /skinfold\n"
                "[bold]Injury:[/bold]   /acwr · /fms · /overuse · /return · /prevent [type]\n"
                "[bold]Female:[/bold]   /cycle [phase] · /reds · /iron · /postpartum\n"
                "[bold]Environ:[/bold]  /altitude · /heat · /cold · /airquality · /jetlag\n"
                "[bold]Mental:[/bold]   /anxiety · /burnout · /visualize [type]\n"
                "[bold]Sports:[/bold]   /assess [notes]\n"
                "[bold]Persist:[/bold]  /save_session [label] · /resume_session <id> · /sessions · /log\n"
                "[bold]Session:[/bold]  /clear · /new · /help · /quit"
            )
            console.print(Panel(
                help_text,
                title="[cyan]Kiwi Commands[/cyan]",
                border_style="cyan",
                box=box.SIMPLE,
            ))

        # ── Session Commands ────────────────────────────────────────

        elif q_lower in ("/quit", "/exit", "quit", "exit"):
            # Auto-save session on exit
            if self.messages:
                session_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                summary = self._state["last_query"][:200] if self._state["last_query"] else ""
                save_session(session_id, self.messages, self.active_thread, summary, self.active_client_name)
                console.print(f"[dim]  Session auto-saved: {session_id}[/dim]")
            # Log session cost
            if self.cost.call_count() > 0:
                console.print(f"[dim]  API cost: ${self.cost.total_cost_usd():.4f} ({self.cost.call_count()} calls)[/dim]")
            console.print(
                f"[dim]  Session #{self._state['session_num']} complete. "
                f"Memory saved to {Path.home() / '.kiwi'}[/dim]"
            )
            return True

        elif q_lower == "/clients" or q_lower.startswith("/clients "):
            clients = client_manager.list_clients()
            lines = []
            for c in clients:
                marker = " [bold green]●[/bold green] ACTIVE" if c["is_active"] else ""
                desc = f" — {c['description']}" if c["description"] else ""
                lines.append(f"  [cyan]{c['name']}[/cyan]{marker}{desc}")
            console.print(Panel(
                "\n".join(lines) if lines else "[dim]No clients[/dim]",
                title="[cyan]Clients[/cyan]",
                border_style="cyan",
                box=box.SIMPLE,
            ))
            console.print("[dim]  /new_client <name> [description]   /switch_client <name>   /delete_client <name>[/dim]")

        elif q_lower.startswith("/new_client "):
            parts = query[12:].strip().split(maxsplit=1)
            if parts:
                name = parts[0]
                desc = parts[1] if len(parts) > 1 else ""
                ok, msg = client_manager.create_client(name, desc)
                color = "dim" if ok else "dim red"
                console.print(f"[{color}]  {msg}[/{color}]")
                if ok:
                    console.print(f"[dim]  Switch with: /switch_client {client_manager._normalize_name(name)}[/dim]")

        elif q_lower.startswith("/switch_client "):
            name = query[15:].strip()
            if client_manager.set_active_client(name):
                self.active_client_name = client_manager.get_active_client()
                self.memory = KiwiMemory(client=self.active_client_name)
                self.profile = UserProfile(client=self.active_client_name)
                self.preferences = PreferencesStore(client=self.active_client_name)
                self.watch_list = WatchList(client=self.active_client_name)
                self.progress = ProgressTracker(client=self.active_client_name)
                self.interventions = InterventionTracker(client=self.active_client_name)
                self.messages = []
                console.print(f"[dim]  Switched to client: [cyan]{self.active_client_name}[/cyan][/dim]")
            else:
                console.print(f"[dim red]  Client '{name}' not found. Use /clients to list.[/dim red]")

        elif q_lower.startswith("/delete_client "):
            name = query[15:].strip()
            ok, msg = client_manager.delete_client(name)
            color = "dim" if ok else "dim red"
            console.print(f"[{color}]  {msg}[/{color}]")

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
            if self._state["last_response"]:
                path = self.exporter.export_markdown(
                    query=self._state["last_query"],
                    plan="",
                    response=self._state["last_response"],
                    score=self._state["last_score"],
                    critique_data=self._state["last_critique"],
                    refined=self._state["last_score"] < REFINEMENT_THRESHOLD,
                    thread_name=self.active_thread,
                )
                console.print(f"[dim]  Exported to: {path}[/dim]")
            else:
                console.print("[dim]  No research to export yet.[/dim]")

        elif q_lower.startswith("/archive"):
            keywords = query[8:].strip().split() if len(query) > 8 else []
            stats = self.memory.archive_stats()
            if stats["archived_entries"] == 0:
                console.print("[dim]  No archived research yet (archive fills after 50 active entries).[/dim]")
            elif keywords:
                results = self.memory.search_archive(keywords, max_results=10)
                if results:
                    console.print(f"[dim]  Found {len(results)} archived entries matching: {' '.join(keywords)}[/dim]")
                    for r in results:
                        score = r.get("quality_score", "?")
                        console.print(
                            f"\n  [{r.get('ts', '')[:10]}] (score: {score}) {r.get('query', '')[:150]}\n"
                            f"  [dim]{r.get('response_preview', '')[:200]}...[/dim]"
                        )
                else:
                    console.print(f"[dim]  No archived entries match: {' '.join(keywords)}[/dim]")
            else:
                console.print(
                    f"[dim]  Archive: {stats['archived_entries']} entries. "
                    f"Search with: /archive <keywords>[/dim]"
                )

        elif q_lower == "/stale":
            entries = self.memory.get_semantic_with_staleness()
            if not entries:
                console.print("[dim]  No semantic memory entries yet.[/dim]")
            else:
                stale = [e for e in entries if e["is_stale"]]
                fresh = [e for e in entries if not e["is_stale"]]
                console.print(f"[dim]  Semantic memory: {len(fresh)} current, {len(stale)} stale (>90 days)[/dim]")
                if stale:
                    console.print("[yellow]  Stale entries (consider refreshing):[/yellow]")
                    for e in stale:
                        age = f"{e['days_old']}d old" if e["days_old"] >= 0 else "unknown age"
                        console.print(f"    [yellow]•[/yellow] {e['topic']} ({age}): {e['content'][:100]}...")
                if fresh:
                    console.print("[dim]  Current entries:[/dim]")
                    for e in fresh[:10]:
                        console.print(f"    [green]•[/green] {e['topic']} ({e['days_old']}d): {e['content'][:100]}...")

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
                result = self.profile.set(field, value)
                if result is True:
                    console.print(f"[dim]  Profile updated: {field} = {value}[/dim]")
                elif result is False:
                    console.print(f"[dim red]  Unknown field: {field}. "
                                  f"Valid: {', '.join(self.profile.FIELDS.keys())}[/dim red]")
                else:
                    console.print(f"[dim red]  {result}[/dim red]")

        # ── Calculations ────────────────────────────────────────────

        elif q_lower == "/calc":
            missing = [f for f in ("weight_kg", "height_cm", "age", "sex", "activity_level")
                       if not self.profile.get(f)]
            if missing:
                console.print(f"[dim]  Missing profile fields: {', '.join(missing)}[/dim]")
                console.print("[dim]  Set with: /profile set <field> <value>[/dim]")
            else:
                try:
                    m = self.calc.compute_full_metrics(
                        weight_kg=self.profile.get("weight_kg"),
                        height_cm=self.profile.get("height_cm"),
                        age=self.profile.get("age"),
                        sex=self.profile.get("sex"),
                        activity_level=self.profile.get("activity_level"),
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
            handle_pubmed(self, query, q_lower)

        elif q_lower.startswith("/fulltext "):
            handle_fulltext(self, query, q_lower)

        elif q_lower.startswith("/tldr "):
            handle_tldr(self, query, q_lower)

        elif q_lower.startswith("/synthesize "):
            claim = query[12:].strip()
            if claim:
                console.print(f"[dim]  Gathering evidence for synthesis: '{claim}'...[/dim]")
                # Pull from all 5 sources with larger limits for deep synthesis
                papers_ctx = fetch_literature_context(
                    claim, self.pubmed, self.openalex, self.epmc, self.semantic,
                    max_pubmed=8, max_openalex=5, max_epmc=5, max_semantic=5,
                )

                if not papers_ctx:
                    console.print("[dim red]  No literature found for this claim.[/dim red]")
                else:
                    console.print("[dim]  Running structured synthesis with GRADE assessment...[/dim]\n")
                    result = await self.synthesis_agent.run({
                        "claim": claim,
                        "papers_context": papers_ctx,
                        "profile_summary": self.profile.to_summary() if self.profile.is_complete() else "",
                    })
                    self._state["last_output"] = result
                    console.print(result)

        elif q_lower.startswith("/review "):
            topic = query[8:].strip()
            if topic:
                console.print(f"[dim]  Conducting systematic review on: '{topic}'...[/dim]")
                papers_ctx = fetch_literature_context(
                    topic, self.pubmed, self.openalex, self.epmc, self.semantic,
                    max_pubmed=10, max_openalex=8, max_epmc=8, max_semantic=8,
                    years_back=10,
                )
                if not papers_ctx:
                    console.print("[dim red]  No literature retrieved. Cannot conduct review.[/dim red]")
                else:
                    console.print("[dim]  Running PRISMA-compliant systematic review...[/dim]\n")
                    result = await self.systematic_review_agent.run({
                        "question": topic,
                        "papers_context": papers_ctx,
                        "profile_summary": self.profile.to_summary() if self.profile.is_complete() else "",
                    })
                    self._state["last_output"] = result
                    console.print(result)

        elif q_lower.startswith("/watch "):
            handle_watch(self, query, q_lower)

        elif q_lower.startswith("/unwatch "):
            handle_unwatch(self, query, q_lower)

        elif q_lower == "/watched" or q_lower == "/watchlist":
            handle_watched(self, query, q_lower)

        elif q_lower == "/digest":
            handle_digest(self, query, q_lower)

        elif q_lower == "/cost":
            console.print(Panel(
                self.cost.summary(),
                title="[cyan]Session API Cost[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower == "/team" or q_lower.startswith("/team "):
            handle_team(self, query, q_lower)

        elif q_lower.startswith("/n_of_1 ") or q_lower.startswith("/nof1 "):
            offset = 8 if q_lower.startswith("/n_of_1 ") else 6
            question = query[offset:].strip()
            if question:
                research_ctx = ""
                if self.pubmed or self.openalex:
                    research_ctx = fetch_literature_context(
                        question, self.pubmed, self.openalex, self.epmc, self.semantic,
                    )
                console.print("[dim]  Designing n-of-1 experimental protocol...[/dim]\n")
                result = await self.n_of_1_agent.run({
                    "question": question,
                    "research_context": research_ctx,
                    "profile_summary": self.profile.to_summary() if self.profile.is_complete() else "",
                })
                self._state["last_output"] = result
                console.print(result)

        elif q_lower.startswith("/meal_plan") or q_lower.startswith("/mealplan"):
            await handle_meal_plan(self, query, q_lower)

        elif q_lower.startswith("/training_plan") or q_lower.startswith("/trainingplan"):
            await handle_training_plan(self, query, q_lower)

        elif q_lower.startswith("/fight_prep") or q_lower.startswith("/race_prep"):
            await handle_competition_prep(self, query, q_lower)

        elif q_lower.startswith("/oura "):
            handle_oura(self, query, q_lower)

        elif q_lower.startswith("/import_wearable "):
            handle_import_wearable(self, query, q_lower)

        elif q_lower.startswith("/import_labs "):
            handle_import_labs(self, query, q_lower)

        elif q_lower == "/snapshot":
            output = format_client_snapshot(self.active_client_name)
            console.print(Panel(output, title=f"[cyan]Snapshot: {self.active_client_name}[/cyan]",
                                border_style="cyan", box=box.SIMPLE))

        elif q_lower.startswith("/compare_clients "):
            parts = query[17:].strip().split()
            if len(parts) >= 2:
                output = compare_clients(parts[0], parts[1])
                console.print(Panel(output, title="[cyan]Client Comparison[/cyan]",
                                    border_style="cyan", box=box.SIMPLE))
            else:
                console.print("[dim]  Usage: /compare_clients <name_a> <name_b>[/dim]")

        elif q_lower.startswith("/intervention "):
            handle_intervention(self, query, q_lower)

        elif q_lower.startswith("/track "):
            handle_track(self, query, q_lower)

        elif q_lower.startswith("/trends "):
            handle_trends_with_metric(self, query, q_lower)

        elif q_lower == "/trends" or q_lower == "/dashboard":
            handle_dashboard(self, query, q_lower)

        elif q_lower == "/optimize_stack" or q_lower.startswith("/optimize_stack "):
            notes = query[15:].strip() if len(query) > 15 else ""
            profile_summary = self.profile.to_summary()
            current_supps = self.profile.get("current_supplements") or []
            current_stack = ", ".join(current_supps) if current_supps else "none listed"
            goals = self.profile.get("primary_goal") or notes or "general performance"

            # Build supplement DB summary (compact)
            db_lines = []
            for key, proto in SUPPLEMENT_DB.items():
                db_lines.append(
                    f"• {proto.name} ({key}) — {proto.evidence} — "
                    f"{proto.maintenance_dose} — {proto.mechanism[:100]}"
                )
            db_summary = "\n".join(db_lines)

            # Build biomarker context from progress data
            biomarker_lines = []
            for m in self.progress.get_all_metrics():
                latest = self.progress.get_latest(m)
                if latest:
                    biomarker_lines.append(f"  {m}: {latest['value']} {latest.get('unit', '')} ({latest.get('ts', '')[:10]})")
            biomarker_text = "\n".join(biomarker_lines) if biomarker_lines else "No biomarker data tracked"

            console.print("[dim]  Analyzing profile + biomarkers + supplement DB + interactions...[/dim]\n")
            result = await self.stack_optimizer_agent.run({
                "profile_summary": profile_summary,
                "goals": goals,
                "biomarker_data": biomarker_text,
                "current_stack": current_stack,
                "supplement_db_summary": db_summary,
                "interaction_data": "",
            })
            self._state["last_output"] = result
            console.print(result)

        elif q_lower == "/risk_screen" or q_lower.startswith("/risk_screen "):
            notes_raw = query[12:].strip() if len(query) > 12 else ""
            profile_summary = self.profile.to_summary()

            # Parse key=value tokens out of notes; keep non-kv tokens as free text
            reds_keys = {
                "menstrual_status", "bmi", "bone_stress_injuries", "disordered_eating",
                "weight_loss_pct", "mood_disturbance", "gi_issues", "recurrent_illness",
                "declining_performance", "low_energy_availability",
            }
            reds_responses: dict = {}
            notes_tokens: list = []
            for tok in notes_raw.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    if k in reds_keys and v.strip():
                        vl = v.lower()
                        if vl in ("true", "yes", "y", "1"):
                            reds_responses[k] = True
                        elif vl in ("false", "no", "n", "0"):
                            reds_responses[k] = False
                        else:
                            try:
                                reds_responses[k] = float(v) if "." in v else int(v)
                            except ValueError:
                                reds_responses[k] = v
                        continue
                notes_tokens.append(tok)
            notes = " ".join(notes_tokens)

            # Gather biomarker data from progress tracker
            biomarker_lines = []
            for m in self.progress.get_all_metrics():
                latest = self.progress.get_latest(m)
                if latest:
                    biomarker_lines.append(f"  {m}: {latest['value']} {latest.get('unit', '')} ({latest.get('ts', '')[:10]})")
            biomarker_text = "\n".join(biomarker_lines) if biomarker_lines else "No biomarker data tracked"

            # Gather progress trends for key metrics
            progress_lines = []
            for m in ["weight", "rhr", "hrv_rmssd", "sleep_hours"]:
                history = self.progress.get_history(m, limit=7)
                if history:
                    vals = [h["value"] for h in history]
                    progress_lines.append(f"  {m} (last {len(vals)} readings): {' → '.join(f'{v:.1f}' for v in vals)}")
            progress_text = "\n".join(progress_lines) if progress_lines else "No progress trends available"

            # Autonomous ACWR enrichment: require ≥7 distinct UTC calendar days
            # of training_load in the last 14 days. Aggregate multiple loads/day.
            training_load_text = ""
            raw_loads = self.progress.get_history("training_load", limit=200)
            if raw_loads:
                raw_loads.sort(key=lambda e: e.get("ts", ""))
                by_day: dict = {}
                for e in raw_loads:
                    day = str(e.get("ts", ""))[:10]
                    if day:
                        by_day[day] = by_day.get(day, 0.0) + float(e.get("value", 0.0))
                from datetime import datetime as _dt, timedelta as _td, timezone as _tz
                today = _dt.now(_tz.utc).date()
                recent_window_days = {
                    (today - _td(days=i)).isoformat() for i in range(14)
                }
                recent_days_with_load = [d for d in by_day if d in recent_window_days]
                if len(recent_days_with_load) >= 7:
                    sorted_days = sorted(by_day.keys())
                    last_28 = sorted_days[-28:]
                    daily_loads = [by_day[d] for d in last_28]
                    acwr_result = calculate_acwr(
                        daily_loads, acute_window=7, chronic_window=28,
                    )
                    training_load_text = format_acwr_report(acwr_result)

            # Autonomous RED-S enrichment: gate on sex=female, ≥2 keys, ≥1 clinical key
            reds_screening_text = ""
            clinical_keys = {"menstrual_status", "bmi", "bone_stress_injuries", "disordered_eating"}
            if self.profile.data.get("sex") == "female":
                # Fill from profile where notes didn't specify (notes override profile)
                profile_ms = self.profile.data.get("menstrual_status")
                if profile_ms and "menstrual_status" not in reds_responses:
                    reds_responses["menstrual_status"] = profile_ms
                # Derive bone_stress_injuries from injury_history via 3-phrase literal scan
                if "bone_stress_injuries" not in reds_responses:
                    injury_history = self.profile.data.get("injury_history") or []
                    bone_phrases = ("stress fracture", "bone stress", "stress reaction")
                    bone_count = sum(
                        1 for inj in injury_history
                        if any(phrase in str(inj).lower() for phrase in bone_phrases)
                    )
                    if bone_count > 0:
                        reds_responses["bone_stress_injuries"] = bone_count
                if (
                    len(reds_responses) >= 2
                    and any(k in reds_responses for k in clinical_keys)
                ):
                    reds_result = screen_reds(reds_responses)
                    reds_screening_text = format_reds_report(reds_result)

            console.print("[dim]  Running comprehensive risk screening...[/dim]\n")
            result = await self.risk_screen_agent.run({
                "profile_summary": profile_summary,
                "biomarker_data": biomarker_text,
                "progress_data": progress_text,
                "training_load": training_load_text,
                "notes": notes,
                "reds_screening": reds_screening_text,
            })
            self._state["last_output"] = result
            console.print(result)

        elif q_lower == "/suggest_research" or q_lower.startswith("/suggest_research "):
            notes = query[17:].strip() if len(query) > 17 else ""
            profile_summary = self.profile.to_summary()
            current_supps = self.profile.get("current_supplements") or []

            # Biomarkers from progress
            biomarker_lines = []
            for m in self.progress.get_all_metrics():
                latest = self.progress.get_latest(m)
                if latest:
                    biomarker_lines.append(f"  {m}: {latest['value']} {latest.get('unit', '')}")
            biomarker_text = "\n".join(biomarker_lines) if biomarker_lines else ""

            # Recent research history from memory
            recent = self.memory.get_recent_episodic(10)
            recent_text = "\n".join(
                f"  [{e.get('ts', '')[:10]}] {e.get('query', '')[:150]}"
                for e in recent
            ) if recent else "No prior research for this client"

            # Progress trends
            progress_lines = []
            for m in self.progress.get_all_metrics():
                history = self.progress.get_history(m, limit=5)
                if len(history) >= 2:
                    first = history[0]["value"]
                    last = history[-1]["value"]
                    change = last - first
                    progress_lines.append(f"  {m}: {first:.1f} → {last:.1f} ({change:+.1f})")
            progress_text = "\n".join(progress_lines) if progress_lines else ""

            console.print("[dim]  Analyzing data to generate research suggestions...[/dim]\n")
            result = await self.question_gen_agent.run({
                "profile_summary": profile_summary,
                "biomarker_data": biomarker_text,
                "current_stack": ", ".join(current_supps) if current_supps else "none",
                "recent_research": recent_text,
                "progress_data": progress_text,
            })
            self._state["last_output"] = result
            console.print(result)

        elif q_lower.startswith("/template"):
            name = query[9:].strip() if len(query) > 9 else ""
            if not name:
                console.print(Panel(
                    list_templates(),
                    title="[cyan]Protocol Templates[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))
            else:
                tmpl = get_template(name)
                if tmpl:
                    console.print(Panel(
                        tmpl.content,
                        title=f"[cyan]{tmpl.name}[/cyan]",
                        subtitle=f"[dim]{tmpl.duration} · {tmpl.category}[/dim]",
                        border_style="cyan", box=box.SIMPLE,
                    ))
                else:
                    console.print(f"[dim red]  Template '{name}' not found. Use /template to list.[/dim red]")

        elif q_lower == "/frontiers":
            profile_data = self.profile.to_dict()
            # Gather tracked metrics
            tracked = {}
            for m in self.progress.get_all_metrics():
                history = self.progress.get_history(m, limit=50)
                tracked[m] = [h["value"] for h in history]
            # Gather research history
            research_queries = [
                e.get("query", "").lower()
                for e in self.memory.get_recent_episodic(50)
            ]
            gaps = analyze_frontiers(profile_data, tracked, research_queries)
            console.print(Panel(
                format_frontiers(gaps),
                title="[cyan]Research Frontiers[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower == "/freshness":
            output = format_freshness_report()
            console.print(Panel(
                output,
                title="[cyan]Evidence Freshness[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower == "/brief" or q_lower.startswith("/brief "):
            # Parse cycle_day=N from args (first-match-wins, range 1-28)
            arg_text = query[6:].strip() if len(query) > 6 else ""
            cycle_day = None
            for tok in arg_text.split():
                if cycle_day is None and tok.startswith("cycle_day="):
                    try:
                        v = int(tok.split("=", 1)[1])
                        if 1 <= v <= 28:
                            cycle_day = v
                    except ValueError:
                        pass

            # Fall back to profile extrapolation when arg didn't specify
            if cycle_day is None:
                cycle_day = self.profile.get_current_cycle_day()

            profile_summary = self.profile.to_summary()

            # Progress trends
            progress_lines = []
            for m in self.progress.get_all_metrics():
                history = self.progress.get_history(m, limit=7)
                if history:
                    latest = history[-1]
                    vals = [h["value"] for h in history]
                    direction = "↑" if len(vals) > 1 and vals[-1] > vals[0] else "↓" if len(vals) > 1 and vals[-1] < vals[0] else "→"
                    progress_lines.append(
                        f"  {m}: {latest['value']:.1f} {latest.get('unit', '')} {direction} "
                        f"(last {len(vals)})")
            progress_text = "\n".join(progress_lines) if progress_lines else "No progress data"

            # Active interventions
            interventions_text = self.interventions.format_active()

            # Research gaps (lightweight)
            profile_data = self.profile.to_dict()
            tracked = {}
            for m in self.progress.get_all_metrics():
                history = self.progress.get_history(m, limit=10)
                tracked[m] = [h["value"] for h in history]
            research_queries = [e.get("query", "").lower() for e in self.memory.get_recent_episodic(20)]
            frontier_gaps = analyze_frontiers(profile_data, tracked, research_queries)
            gaps_text = "\n".join(
                f"  [{g.priority}] {g.topic}" for g in frontier_gaps[:5]
            ) if frontier_gaps else "No critical gaps"

            # Retest alerts
            retest_text = self.interventions.format_retest_due()

            # Timing schedule
            supplements = self.profile.get("current_supplements") or []
            timing_text = ""
            if supplements:
                schedule = generate_timing_schedule(supplements)
                timing_text = format_timing_schedule(schedule)

            # Autonomous enrichment 1: ACWR when ≥7 distinct days of load in last 14
            training_load_text = ""
            raw_loads = self.progress.get_history("training_load", limit=200)
            if raw_loads:
                raw_loads.sort(key=lambda e: e.get("ts", ""))
                by_day: dict = {}
                for e in raw_loads:
                    day = str(e.get("ts", ""))[:10]
                    if day:
                        by_day[day] = by_day.get(day, 0.0) + float(e.get("value", 0.0))
                from datetime import datetime as _dt, timedelta as _td, timezone as _tz
                today = _dt.now(_tz.utc).date()
                recent_window_days = {
                    (today - _td(days=i)).isoformat() for i in range(14)
                }
                recent_days_with_load = [d for d in by_day if d in recent_window_days]
                if len(recent_days_with_load) >= 7:
                    sorted_days = sorted(by_day.keys())
                    last_28 = sorted_days[-28:]
                    daily_loads = [by_day[d] for d in last_28]
                    acwr_result = calculate_acwr(
                        daily_loads, acute_window=7, chronic_window=28,
                    )
                    training_load_text = format_acwr_report(acwr_result)

            # Autonomous enrichment 2: RED-S from profile (sex=female + ≥2 clinical keys)
            reds_screening_text = ""
            if self.profile.data.get("sex") == "female":
                reds_responses: dict = {}
                profile_ms = self.profile.data.get("menstrual_status")
                if profile_ms and profile_ms != "not_applicable":
                    reds_responses["menstrual_status"] = profile_ms
                injury_history = self.profile.data.get("injury_history") or []
                bone_phrases = ("stress fracture", "bone stress", "stress reaction")
                bone_count = sum(
                    1 for inj in injury_history
                    if any(phrase in str(inj).lower() for phrase in bone_phrases)
                )
                if bone_count > 0:
                    reds_responses["bone_stress_injuries"] = bone_count
                clinical_keys = {"menstrual_status", "bmi", "bone_stress_injuries", "disordered_eating"}
                if (
                    len(reds_responses) >= 2
                    and any(k in reds_responses for k in clinical_keys)
                ):
                    reds_result = screen_reds(reds_responses)
                    reds_screening_text = format_reds_report(reds_result)

            # Autonomous enrichment 3: cycle_phase when cycle_day arg provided + sex=female
            cycle_phase_context_text = ""
            if cycle_day is not None and self.profile.data.get("sex") == "female":
                try:
                    sport_ctx = self.profile.data.get("sport", "general")
                    phase_info = match_training_to_phase(cycle_day, sport_ctx)
                    phase_obj = phase_info["phase"]
                    cycle_phase_context_text = (
                        f"Menstrual cycle phase analysis (Kiwi tool, day {cycle_day}):\n"
                        f"{format_cycle_training(phase_obj)}"
                    )
                except (ValueError, KeyError):
                    cycle_phase_context_text = ""

            console.print("[dim]  Generating daily brief...[/dim]\n")
            brief_context = {
                "profile_summary": profile_summary,
                "progress_data": progress_text,
                "interventions": interventions_text,
                "risk_flags": retest_text if "OVERDUE" in retest_text or "DUE NOW" in retest_text else "",
                "research_gaps": gaps_text,
                "biomarker_due": retest_text if "No biomarkers" not in retest_text else "",
                "training_load": training_load_text,
                "reds_screening": reds_screening_text,
                "cycle_phase_context": cycle_phase_context_text,
            }
            self._state["last_output"] = await self.daily_brief_agent.run(brief_context)
            console.print(self._state["last_output"])

            # Append timing schedule if available
            if timing_text and supplements:
                console.print(f"\n[dim]{timing_text}[/dim]")

        elif q_lower == "/macros":
            missing = [f for f in ("weight_kg", "height_cm", "age", "sex", "activity_level")
                       if not self.profile.get(f)]
            if missing:
                console.print(f"[dim]  Missing: {', '.join(missing)}[/dim]")
            else:
                try:
                    m = self.calc.compute_full_metrics(
                        weight_kg=self.profile.get("weight_kg"),
                        height_cm=self.profile.get("height_cm"),
                        age=self.profile.get("age"),
                        sex=self.profile.get("sex"),
                        activity_level=self.profile.get("activity_level"),
                        body_fat_pct=self.profile.get("body_fat_pct"),
                    )
                    goal = self.profile.get("primary_goal") or "performance"
                    macros = self.calc.macro_periodization(
                        weight_kg=self.profile.get("weight_kg"),
                        tdee=m.tdee,
                        sex=self.profile.get("sex"),
                        goal=goal,
                    )
                    td = macros["training_day"]
                    rd = macros["rest_day"]
                    lines = [
                        f"Macro Periodization — {self.profile.get('weight_kg'):.0f}kg · {goal}",
                        "",
                        f"{'':>16} {'Training Day':>16} {'Rest Day':>16}",
                        "─" * 50,
                        f"{'Calories':>16} {td['kcal']:>13} kcal {rd['kcal']:>13} kcal",
                        f"{'Protein':>16} {td['protein_g']:>10}g ({td['protein_g_per_kg']:.1f}/kg) {rd['protein_g']:>10}g ({rd['protein_g_per_kg']:.1f}/kg)",
                        f"{'Carbs':>16} {td['carb_g']:>10}g ({td['carb_g_per_kg']:.1f}/kg) {rd['carb_g']:>10}g ({rd['carb_g_per_kg']:.1f}/kg)",
                        f"{'Fat':>16} {td['fat_g']:>13}g {rd['fat_g']:>13}g",
                        "",
                        "Evidence: ISSN (Kerksick et al. 2018)",
                    ]
                    console.print(Panel("\n".join(lines), title="[cyan]Macro Periodization[/cyan]",
                                        border_style="cyan", box=box.SIMPLE))
                except Exception as e:
                    console.print(f"[dim red]  Error: {e}[/dim red]")

        elif q_lower == "/weekly_report":
            profile_summary = self.profile.to_summary()

            # Gather all client data for the report
            progress_lines = []
            for m in self.progress.get_all_metrics():
                history = self.progress.get_history(m, limit=30)
                if history:
                    vals = [h["value"] for h in history]
                    latest = history[-1]
                    trend = self.progress.format_trend(m, limit=10)
                    progress_lines.append(trend)
            progress_text = "\n\n".join(progress_lines) if progress_lines else "No progress data tracked"

            interventions_text = self.interventions.format_active()
            retest_text = self.interventions.format_retest_due()
            dashboard = self.progress.format_dashboard()

            # Build report content
            report_content = (
                f"Weekly Progress Report\n"
                f"Client: {self.active_client_name}\n"
                f"{'=' * 40}\n\n"
                f"Profile:\n{profile_summary}\n\n"
                f"{'─' * 40}\n"
                f"Current Metrics:\n{dashboard}\n\n"
                f"{'─' * 40}\n"
                f"Trends:\n{progress_text}\n\n"
                f"{'─' * 40}\n"
                f"Interventions:\n{interventions_text}\n\n"
                f"{'─' * 40}\n"
                f"Retests Due:\n{retest_text}\n"
            )

            try:
                practitioner = self.profile.get("name") or ""
                brand = BrandConfig(practitioner=practitioner)
                pdf_path = generate_client_report(
                    query=f"Weekly Report — {self.active_client_name}",
                    response=report_content,
                    score=0.0,
                    critique_data={},
                    brand=brand,
                    client_name=self.active_client_name,
                )
                console.print(f"[dim]  Weekly report exported: [cyan]{pdf_path}[/cyan][/dim]")
            except Exception as e:
                console.print(f"[dim red]  Report failed: {e}[/dim red]")

        elif q_lower == "/capabilities":
            caps = (
                "[bold cyan]RESEARCH[/bold cyan]\n"
                "  Ask any question · /synthesize · /review (PRISMA) · /n_of_1\n"
                "  /pubmed · /openalex · /trials · /tldr · /readpdf · /citedby\n"
                "  /grade · /quality · /autoquality · /effect · /freshness\n\n"
                "[bold cyan]ATHLETE MANAGEMENT[/bold cyan]\n"
                "  /clients · /new_client · /switch_client · /onboard · /snapshot\n"
                "  /compare_clients · /team · /export_client\n\n"
                "[bold cyan]DAILY WORKFLOW[/bold cyan]\n"
                "  /brief · /timing · /retest_due · /frontiers · /gaps · /suggest_research\n\n"
                "[bold cyan]BIOMARKERS & TRACKING[/bold cyan]\n"
                "  /import_labs · /track · /trends · /dashboard · /labs · /biomarker\n"
                "  /intervention start|stop|check|list · /risk_screen\n\n"
                "[bold cyan]NUTRITION[/bold cyan]\n"
                "  /macros · /meal_plan · /calc · /food · /food+ · /compare\n"
                "  /supp · /supplist · /check · /interact · /optimize_stack\n\n"
                "[bold cyan]TRAINING[/bold cyan]\n"
                "  /training_plan · /fight_prep · /race_prep · /template\n"
                "  /session · /load · /blocks · /prilepin · /hrzones · /powerzones\n\n"
                "[bold cyan]DELIVERY[/bold cyan]\n"
                "  /pdf · /pdf_last · /export · /save_session · /resume_session\n"
                "  /accepted · /rejected · /watch · /digest · /cost"
            )
            console.print(Panel(caps, title="[bold cyan]Kiwi Capabilities[/bold cyan]",
                                border_style="cyan", box=box.ROUNDED))

        elif q_lower == "/timing":
            supplements = self.profile.get("current_supplements") or []
            if not supplements:
                console.print("[dim]  No supplements on file. Set with /profile set current_supplements creatine,caffeine,...[/dim]")
            else:
                schedule = generate_timing_schedule(supplements)
                conflicts = check_separation_conflicts(supplements)
                console.print(Panel(
                    format_timing_schedule(schedule, conflicts),
                    title="[cyan]Daily Supplement Timing[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))

        elif q_lower == "/retest_due":
            output = self.interventions.format_retest_due()
            console.print(Panel(
                output,
                title="[cyan]Biomarker Retests Due[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower == "/export_client":
            try:
                path = export_client(self.active_client_name)
                console.print(f"[dim]  Client exported to: [cyan]{path}[/cyan][/dim]")
            except Exception as e:
                console.print(f"[dim red]  Export failed: {e}[/dim red]")

        elif q_lower == "/gaps":
            sex = self.profile.get("sex") or "male"
            sport = self.profile.get("sport") or ""
            restrictions = self.profile.get("dietary_restrictions") or []
            supplements = self.profile.get("current_supplements") or []
            conditions = self.profile.get("health_conditions") or []

            gaps = analyze_gaps(
                sex=sex, sport=sport,
                dietary_restrictions=restrictions,
                current_supplements=supplements,
                health_conditions=conditions,
            )
            console.print(Panel(
                format_gap_analysis(gaps),
                title="[cyan]Nutrient Gap Analysis[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower == "/onboard":
            console.print("[cyan]  Client Onboarding Wizard[/cyan]\n")
            fields_order = [
                ("name", "Full name"),
                ("age", "Age"),
                ("sex", "Sex (male/female)"),
                ("weight_kg", "Weight in kg"),
                ("height_cm", "Height in cm"),
                ("body_fat_pct", "Body fat % (leave blank if unknown)"),
                ("sport", "Primary sport"),
                ("training_status", "Training status (novice/intermediate/advanced/elite)"),
                ("activity_level", "Activity level (sedentary/light/moderate/active/very_active)"),
                ("primary_goal", "Primary goal (performance/body_composition/health/longevity)"),
                ("dietary_restrictions", "Dietary restrictions (comma-separated, or blank)"),
                ("current_supplements", "Current supplements (comma-separated, or blank)"),
                ("health_conditions", "Health conditions (comma-separated, or blank)"),
                ("injury_history", "Injury history (comma-separated past/current, or blank)"),
                ("menstrual_status", "Menstrual status (normal / irregular / amenorrheic / heavy / postmenopausal / not_applicable)"),
                ("cycle_day", "Current cycle day 1-28 (blank to skip; auto-extrapolates going forward)"),
            ]
            for field_key, prompt_text in fields_order:
                # Skip menstrual_status and cycle_day if sex is not female
                if field_key in ("menstrual_status", "cycle_day") and self.profile.get("sex") != "female":
                    continue
                current = self.profile.get(field_key)
                current_str = f" [dim](current: {current})[/dim]" if current else ""
                try:
                    val = console.input(f"  {prompt_text}{current_str}: ").strip()
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[dim]  Onboarding cancelled.[/dim]")
                    break
                if val:
                    result = self.profile.set(field_key, val)
                    if result is True:
                        console.print(f"    [dim]✓ {field_key} = {val}[/dim]")
                    elif isinstance(result, str):
                        console.print(f"    [dim red]✗ {result}[/dim red]")
            console.print("\n[dim]  Onboarding complete. Review with /profile[/dim]")

        elif q_lower == "/summary":
            if not self.messages:
                console.print("[dim]  No conversation to summarize.[/dim]")
            else:
                user_msgs = [m for m in self.messages if m.get("role") == "user"]
                lines = [f"Session Summary — {len(user_msgs)} exchanges\n"]
                for i, msg in enumerate(user_msgs, 1):
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        lines.append(f"  {i}. {content[:150]}")
                if self._state["last_query"] and self._state["last_score"]:
                    lines.append(f"\n  Last RWL score: {self._state['last_score']:.2f}")
                lines.append(f"  Active client: {self.active_client_name}")
                if self.active_thread:
                    lines.append(f"  Thread: {self.active_thread}")
                console.print(Panel(
                    "\n".join(lines),
                    title="[cyan]Session Summary[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))

        elif q_lower.startswith("/save_session"):
            label = query[13:].strip() if len(query) > 13 else ""
            if not self.messages:
                console.print("[dim]  No conversation to save.[/dim]")
            else:
                session_id = label or datetime.now().strftime("%Y%m%d_%H%M%S")
                summary = self._state["last_query"][:200] if last_query else ""
                path = save_session(
                    session_id=session_id,
                    messages=self.messages,
                    thread=self.active_thread,
                    summary=summary,
                    client=self.active_client_name,
                )
                console.print(f"[dim]  Session saved: [cyan]{session_id}[/cyan] ({len(self.messages)} messages)[/dim]")

        elif q_lower.startswith("/resume_session") or q_lower.startswith("/resume "):
            offset = 16 if q_lower.startswith("/resume_session") else 8
            session_id = query[offset:].strip()
            if not session_id:
                console.print("[dim]  Usage: /resume_session <session_id> (see /sessions for list)[/dim]")
            else:
                data = load_session(session_id, client=self.active_client_name)
                if data:
                    self.messages = data.get("messages", [])
                    if data.get("thread"):
                        self.active_thread = data["thread"]
                    console.print(
                        f"[dim]  Resumed session: [cyan]{session_id}[/cyan] "
                        f"({data.get('message_count', 0)} messages, "
                        f"saved {data.get('saved_at', '')[:10]})[/dim]"
                    )
                    if data.get("summary"):
                        console.print(f"[dim]  Last topic: {data['summary']}[/dim]")
                else:
                    console.print(f"[dim red]  Session '{session_id}' not found.[/dim red]")

        elif q_lower == "/sessions":
            sessions = list_sessions(client=self.active_client_name)
            if not sessions:
                console.print("[dim]  No saved sessions. Use /save_session [label] to save.[/dim]")
            else:
                lines = []
                for s in sessions:
                    lines.append(
                        f"  [cyan]{s['session_id']}[/cyan] — "
                        f"{s.get('saved_at', '')[:16]} · "
                        f"{s['message_count']} msgs"
                        + (f" · {s['summary'][:60]}" if s.get("summary") else "")
                    )
                console.print(Panel(
                    "\n".join(lines),
                    title="[cyan]Saved Sessions[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))

        elif q_lower == "/log" or q_lower == "/history":
            stats = log_stats(client=self.active_client_name)
            lines = [
                f"Total queries: {stats['total_queries']}",
            ]
            if stats.get("by_route"):
                lines.append("By route:")
                for route, count in stats["by_route"].items():
                    lines.append(f"  {route}: {count}")
            if stats.get("avg_score") is not None:
                lines.append(f"Average RWL score: {stats['avg_score']:.2f}")
            if stats.get("total_cost_usd"):
                lines.append(f"Total cost: ${stats['total_cost_usd']:.4f}")
            if stats.get("first_query"):
                lines.append(f"First query: {stats['first_query']} · Last: {stats['last_query']}")
            console.print(Panel(
                "\n".join(lines),
                title="[cyan]Client Research Log[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower.startswith("/effect "):
            parts = query[8:].strip().split()
            if len(parts) == 6:
                try:
                    m1, sd1, n1, m2, sd2, n2 = (
                        float(parts[0]), float(parts[1]), int(parts[2]),
                        float(parts[3]), float(parts[4]), int(parts[5]),
                    )
                    d_result = cohens_d(m1, sd1, n1, m2, sd2, n2)
                    g_result = hedges_g(m1, sd1, n1, m2, sd2, n2)
                    md_result = mean_difference(m1, sd1, n1, m2, sd2, n2)
                    console.print(Panel(
                        f"{d_result.display()}\n\n"
                        f"{g_result.display()}\n\n"
                        f"{md_result.display()}",
                        title="[cyan]Effect Size Analysis[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))
                except (ValueError, ZeroDivisionError) as e:
                    console.print(f"[dim red]  Error: {e}[/dim red]")
            elif len(parts) == 4:
                try:
                    ea, ta, eb, tb = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                    rr = relative_risk(ea, ta, eb, tb)
                    or_val = odds_ratio(ea, ta, eb, tb)
                    nnt = number_needed_to_treat(ea, ta, eb, tb)
                    console.print(Panel(
                        f"{rr.display()}\n\n"
                        f"{or_val.display()}\n\n"
                        f"NNT: {nnt['interpretation']}",
                        title="[cyan]Effect Size (Dichotomous)[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))
                except ValueError as e:
                    console.print(f"[dim red]  Error: {e}[/dim red]")
            else:
                console.print(
                    "[dim]  Usage for continuous: /effect <mean1> <sd1> <n1> <mean2> <sd2> <n2>[/dim]\n"
                    "[dim]  Usage for dichotomous: /effect <events_a> <total_a> <events_b> <total_b>[/dim]"
                )

        elif q_lower.startswith("/readpdf "):
            doi = query[9:].strip()
            if doi and self.unpaywall:
                console.print(f"[dim]  Looking up OA version for {doi}...[/dim]")
                pdf = read_oa_pdf(doi, self.unpaywall)
                if pdf:
                    console.print(f"[dim]  Extracted {pdf.extracted_chars:,} chars across {pdf.num_pages} pages[/dim]")
                    console.print(f"[dim]  Cached at: {pdf.cached_path}[/dim]\n")
                    sections = pdf.sections()
                    if sections:
                        console.print("[cyan]Detected sections:[/cyan]")
                        for section_name in sections:
                            console.print(f"  • {section_name}")
                    console.print(f"\n[cyan]Preview (first 2000 chars):[/cyan]\n")
                    console.print(pdf.preview(2000))
                else:
                    console.print(f"[dim red]  Could not retrieve PDF (no OA version or extraction failed).[/dim red]")
            elif not self.unpaywall:
                console.print("[dim]  Unpaywall disabled (run without --no-pubmed).[/dim]")

        elif q_lower.startswith("/autoquality "):
            payload = query[13:].strip()
            if payload:
                # Simple: run auto-quality on a title (useful for rapid triage)
                flag = auto_quality_assess(payload)
                console.print(Panel(
                    flag.display(),
                    title="[cyan]Auto Quality Assessment[/cyan]",
                    border_style="cyan",
                    box=box.SIMPLE,
                ))
            else:
                console.print("[dim]  Usage: /autoquality <paper title or title + abstract>[/dim]")

        elif q_lower == "/pdf_last":
            if not self._state["last_output"]:
                console.print("[dim]  No command output to export. Run a command first.[/dim]")
            else:
                try:
                    practitioner = self.profile.get("name") or ""
                    brand = BrandConfig(practitioner=practitioner)
                    pdf_path = generate_client_report(
                        query=self._state["last_query"] or "Command Output",
                        response=self._state["last_output"],
                        score=self._state["last_score"],
                        critique_data={},
                        brand=brand,
                        client_name=self.active_client_name,
                    )
                    console.print(f"[dim]  PDF exported: [cyan]{pdf_path}[/cyan][/dim]")
                except Exception as e:
                    console.print(f"[dim red]  PDF export failed: {e}[/dim red]")

        elif q_lower == "/pdf" or q_lower.startswith("/pdf "):
            if not self._state["last_response"]:
                console.print("[dim]  No research session to export yet.[/dim]")
            else:
                practitioner = self.profile.get("name") or ""
                brand = BrandConfig(practitioner=practitioner)
                grade_level = ""
                score_val = self._state["last_score"] or 0.0
                if score_val >= 0.85:
                    grade_level = "HIGH"
                elif score_val >= 0.72:
                    grade_level = "MODERATE"
                elif score_val >= 0.50:
                    grade_level = "LOW"
                else:
                    grade_level = "VERY LOW"
                try:
                    pdf_path = generate_client_report(
                        query=self._state["last_query"],
                        response=self._state["last_response"],
                        score=score_val,
                        critique_data=self._state["last_critique"] or {},
                        brand=brand,
                        client_name=self.active_client_name,
                        grade_level=grade_level,
                        thread_name=self.active_thread,
                    )
                    console.print(f"[dim]  PDF exported to: [cyan]{pdf_path}[/cyan][/dim]")
                except Exception as e:
                    console.print(f"[dim red]  PDF export failed: {e}[/dim red]")

        elif q_lower.startswith("/recommend "):
            finding = query[11:].strip()
            if finding:
                console.print(f"[dim]  Chaining tools for finding: '{finding}'...[/dim]")
                profile_summary = self.profile.to_summary() if self.profile.is_complete() else ""
                current_supps = self.profile.get("current_supplements") or []

                # Quick string-match scan of supplement DB
                supp_options_parts = []
                keywords = [w.lower() for w in finding.split() if len(w) > 3]
                for key, proto in SUPPLEMENT_DB.items():
                    text_blob = (
                        proto.name + " " + proto.mechanism + " "
                        + " ".join(proto.sport_specific_notes.values())
                    ).lower()
                    if any(kw in text_blob for kw in keywords):
                        supp_options_parts.append(
                            f"• {proto.name} — {proto.maintenance_dose} — "
                            f"Evidence: {proto.evidence}"
                        )
                supp_options = "\n".join(supp_options_parts[:10]) or "(no direct matches in DB)"

                # Interaction check if current stack is known
                interaction_text = ""
                if current_supps:
                    all_compounds = current_supps + [
                        p.name for key, p in SUPPLEMENT_DB.items()
                        if any(kw in p.name.lower() for kw in keywords)
                    ][:5]
                    if len(all_compounds) > 1:
                        interactions = lookup_interactions(all_compounds, min_severity="safe")
                        if interactions:
                            interaction_text = "\n".join(
                                f"• {i.compound_a} + {i.compound_b}: {i.severity} — {i.recommendation[:150]}"
                                for i in interactions[:10]
                            )
                        else:
                            interaction_text = "No significant interactions detected with current stack."
                    else:
                        interaction_text = "Current stack has too few items to cross-check."
                else:
                    interaction_text = "No current supplement stack on file."

                # Autonomous injury-prevention enrichment via shared helper
                prevention_text = ""
                matched_key = match_prevention_protocol(finding)
                if matched_key:
                    proto = get_prevention_protocol(matched_key)
                    if proto:
                        sport = self.profile.data.get("sport", "general")
                        prevention_text = format_prevention_protocol(proto, sport)

                # Invoke recommender agent
                console.print("[dim]  Synthesizing integrated recommendation...[/dim]\n")
                result = await self.recommender_agent.run({
                    "finding": finding,
                    "profile_summary": profile_summary,
                    "biomarker_interpretation": "",
                    "supplement_options": supp_options,
                    "interaction_check": interaction_text,
                    "prevention_protocol": prevention_text,
                })
                self._state["last_output"] = result
                console.print(result)

        elif q_lower.startswith("/accepted"):
            payload = query[9:].strip() if len(query) > 9 else ""
            rec_text = self._state["last_response"][:500] if self._state["last_response"] else ""
            if not rec_text:
                console.print("[dim]  No recent recommendation to mark accepted.[/dim]")
            else:
                self.preferences.record_accepted(rec_text, note=payload)
                console.print(f"[dim]  Recorded as accepted. Total: {self.preferences.stats()['total_accepted']}[/dim]")

        elif q_lower.startswith("/rejected"):
            payload = query[9:].strip() if len(query) > 9 else ""
            rec_text = self._state["last_response"][:500] if self._state["last_response"] else ""
            if not rec_text:
                console.print("[dim]  No recent recommendation to mark rejected.[/dim]")
            else:
                self.preferences.record_rejected(rec_text, reason=payload)
                console.print(f"[dim]  Recorded as rejected. Total: {self.preferences.stats()['total_rejected']}[/dim]")

        elif q_lower == "/preferences":
            stats = self.preferences.stats()
            block = self.preferences.to_context_block()
            console.print(Panel(
                f"Accepted: {stats['total_accepted']}  ·  Rejected: {stats['total_rejected']}\n\n"
                + (block or "[dim]No preferences recorded yet.[/dim]"),
                title="[cyan]Recommendation Preferences[/cyan]",
                border_style="cyan",
                box=box.SIMPLE,
            ))

        elif q_lower.startswith("/quality"):
            tool = query[8:].strip() if len(query) > 8 else ""
            if not tool:
                console.print(
                    "[dim]  Usage: /quality <tool>  where tool = RoB2 | ROBINS-I | AMSTAR2[/dim]\n"
                    "[dim]  RoB2 — for randomized trials (Cochrane 2019)[/dim]\n"
                    "[dim]  ROBINS-I — for non-randomized observational studies[/dim]\n"
                    "[dim]  AMSTAR2 — for systematic reviews/meta-analyses[/dim]"
                )
            else:
                try:
                    checklist = quality_checklist(tool)
                    console.print(Panel(
                        checklist,
                        title=f"[cyan]Quality Assessment Checklist[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))
                except ValueError as e:
                    console.print(f"[dim red]  {e}[/dim red]")

        elif q_lower.startswith("/grade "):
            tier = query[7:].strip()
            if tier in ("🟢", "🟡", "🟠", "🔵"):
                assessment = assess_from_evidence_tier(tier)
                console.print(Panel(
                    assessment.display(),
                    title="[cyan]GRADE Assessment[/cyan]",
                    border_style="cyan",
                    box=box.SIMPLE,
                ))
            else:
                console.print("[dim]  Usage: /grade 🟢 (or 🟡/🟠/🔵) — converts tier to GRADE certainty level.[/dim]")
                console.print("[dim]  For structured GRADE assessment of a claim, use /synthesize <claim>[/dim]")

        elif q_lower.startswith("/trials "):
            handle_trials(self, query, q_lower)

        elif q_lower.startswith("/citedby "):
            handle_citedby(self, query, q_lower)

        elif q_lower.startswith("/openalex "):
            handle_openalex(self, query, q_lower)

        # ── Supplement Interaction Checker ──────────────────────────

        elif q_lower.startswith("/check "):
            await handle_check(self, query, q_lower)

        elif q_lower.startswith("/interact "):
            await handle_interact(self, query, q_lower)

        # ── Food & Nutrition Lookup ──────────────────────────────────

        elif q_lower.startswith("/food+ ") or q_lower.startswith("/food "):
            handle_food(self, query, q_lower)

        elif q_lower.startswith("/compare "):
            handle_compare(self, query, q_lower)

        # ── Training Load Commands ──────────────────────────────────

        elif q_lower.startswith("/session "):
            handle_session(self, query, q_lower)

        elif q_lower == "/load":
            handle_load(self, query, q_lower)

        elif q_lower.startswith("/blocks"):
            handle_blocks(self, query, q_lower)

        elif q_lower.startswith("/prilepin "):
            handle_prilepin(self, query, q_lower)

        # ── Blood Panel Commands ─────────────────────────────────────

        elif q_lower.startswith("/labs "):
            handle_labs(self, query, q_lower)

        elif q_lower.startswith("/biomarker "):
            handle_biomarker(self, query, q_lower)

        # ── Sleep Optimization Commands ──────────────────────────────

        elif q_lower.startswith("/sleep "):
            handle_sleep(self, query, q_lower)

        elif q_lower.startswith("/chronotype"):
            handle_chronotype(self, query, q_lower)

        elif q_lower.startswith("/caffeine "):
            handle_caffeine(self, query, q_lower)

        elif q_lower.startswith("/sleepdebt "):
            handle_sleepdebt(self, query, q_lower)

        elif q_lower == "/hormones":
            handle_hormones(self, query, q_lower)

        elif q_lower.startswith("/bedtime"):
            handle_bedtime(self, query, q_lower)

        # ── Recovery Commands ────────────────────────────────────────

        elif q_lower.startswith("/readiness"):
            handle_readiness(self, query, q_lower)

        elif q_lower.startswith("/doms "):
            handle_doms(self, query, q_lower)

        elif q_lower.startswith("/supercomp "):
            handle_supercomp(self, query, q_lower)

        elif q_lower.startswith("/deload"):
            handle_deload(self, query, q_lower)

        elif q_lower.startswith("/recover"):
            handle_recover(self, query, q_lower)

        elif q_lower.startswith("/mps"):
            handle_mps(self, query, q_lower)

        # ── Hydration Commands ───────────────────────────────────────

        elif q_lower.startswith("/sweat "):
            handle_sweat(self, query, q_lower)

        elif q_lower.startswith("/sweatest "):
            handle_sweatest(self, query, q_lower)

        elif q_lower.startswith("/rehydrate "):
            handle_rehydrate(self, query, q_lower)

        elif q_lower.startswith("/urine "):
            handle_urine(self, query, q_lower)

        elif q_lower.startswith("/hyponatremia "):
            handle_hyponatremia(self, query, q_lower)

        elif q_lower.startswith("/prehydrate"):
            handle_prehydrate(self, query, q_lower)

        # ── Supplements ────────────────────────────────────────────

        elif q_lower.startswith("/supplist"):
            handle_supplist(self, query, q_lower)

        elif q_lower.startswith("/supp "):
            handle_supp(self, query, q_lower)

        # ── Body Composition ──────────────────────────────────────────

        elif q_lower.startswith("/skinfold "):
            handle_skinfold(self, query, q_lower)

        elif q_lower.startswith("/bodyfat "):
            handle_bodyfat(self, query, q_lower)

        elif q_lower.startswith("/ffmi "):
            handle_ffmi(self, query, q_lower)

        elif q_lower.startswith("/ea "):
            handle_ea(self, query, q_lower)

        elif q_lower.startswith("/weightplan "):
            handle_weightplan(self, query, q_lower)

        # ── Training Zones ────────────────────────────────────────────

        elif q_lower.startswith("/hrzones "):
            handle_hrzones(self, query, q_lower)

        elif q_lower.startswith("/powerzones "):
            handle_powerzones(self, query, q_lower)

        elif q_lower.startswith("/pacezones "):
            handle_pacezones(self, query, q_lower)

        elif q_lower.startswith("/vo2max "):
            handle_vo2max(self, query, q_lower)

        elif q_lower.startswith("/hrmax "):
            handle_hrmax(self, query, q_lower)

        elif q_lower.startswith("/distribution"):
            handle_distribution(self, query, q_lower)

        # ── Injury Prevention ───────────────────────────────────────

        elif q_lower.startswith("/acwr"):
            handle_acwr(self, query, q_lower)

        elif q_lower.startswith("/fms"):
            handle_fms(self, query, q_lower)

        elif q_lower.startswith("/overuse"):
            handle_overuse(self, query, q_lower)

        elif q_lower.startswith("/return"):
            handle_return_to_sport(self, query, q_lower)

        elif q_lower.startswith("/prevent"):
            handle_prevent(self, query, q_lower)

        # ── Female Athlete Health ───────────────────────────────────

        elif q_lower.startswith("/cycle"):
            handle_cycle(self, query, q_lower)

        elif q_lower.startswith("/reds"):
            handle_reds(self, query, q_lower)

        elif q_lower.startswith("/iron"):
            handle_iron(self, query, q_lower)

        elif q_lower.startswith("/postpartum"):
            handle_postpartum(self, query, q_lower)

        # ── Environmental Factors ───────────────────────────────────

        elif q_lower.startswith("/altitude"):
            handle_altitude(self, query, q_lower)

        elif q_lower.startswith("/heat"):
            handle_heat(self, query, q_lower)

        elif q_lower.startswith("/cold"):
            handle_cold(self, query, q_lower)

        elif q_lower.startswith("/airquality"):
            handle_airquality(self, query, q_lower)

        elif q_lower.startswith("/jetlag"):
            handle_jetlag(self, query, q_lower)

        # ── Mental Performance ──────────────────────────────────────

        elif q_lower.startswith("/anxiety"):
            handle_anxiety(self, query, q_lower)

        elif q_lower.startswith("/burnout"):
            handle_burnout(self, query, q_lower)

        elif q_lower.startswith("/visualize"):
            handle_visualize(self, query, q_lower)

        # ── Sports Intelligence Assessment ──────────────────────────

        elif q_lower.startswith("/assess"):
            await handle_assess(self, query, q_lower)

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
                self._state["last_query"] = sub_query
                self._state["last_response"] = result

        # ── Research (with natural language routing) ──────────────────

        else:
            # Check if the query maps to a tool command
            route = route_natural_language(query)
            if route and route.confidence >= 0.8:
                console.print(format_route_suggestion(route))
                console.print(f"[dim]  (Type the command above, or just ask your question as-is)[/dim]")

            result = await self.research(query)
            self._state["last_query"] = query
            self._state["last_response"] = result
            self._state["last_output"] = result
            log_exchange(query, "research", score=self._state["last_score"], thread=self.active_thread,
                        client=self.active_client_name)

        return False


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
