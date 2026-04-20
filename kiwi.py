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
from handlers.optimization import (
    handle_optimize_stack,
    handle_risk_screen,
    handle_suggest_research,
)
from handlers.intel import (
    handle_brief,
    handle_capabilities,
    handle_freshness,
    handle_frontiers,
    handle_gaps,
    handle_macros,
    handle_retest_due,
    handle_template,
    handle_timing,
    handle_weekly_report,
)
from handlers.deep_research import (
    handle_autoquality,
    handle_effect,
    handle_grade,
    handle_n_of_1,
    handle_quality,
    handle_readpdf,
    handle_recommend,
    handle_review,
    handle_synthesize,
)
from handlers.delivery import (
    handle_accepted,
    handle_pdf,
    handle_pdf_last,
    handle_preferences,
    handle_rejected,
)
from handlers.sessions import (
    handle_log,
    handle_resume_session,
    handle_save_session,
    handle_sessions,
)

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
            await handle_synthesize(self, query, q_lower)

        elif q_lower.startswith("/review "):
            await handle_review(self, query, q_lower)

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
            await handle_n_of_1(self, query, q_lower)

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
            await handle_optimize_stack(self, query, q_lower)

        elif q_lower == "/risk_screen" or q_lower.startswith("/risk_screen "):
            await handle_risk_screen(self, query, q_lower)

        elif q_lower == "/suggest_research" or q_lower.startswith("/suggest_research "):
            await handle_suggest_research(self, query, q_lower)

        elif q_lower.startswith("/template"):
            handle_template(self, query, q_lower)

        elif q_lower == "/frontiers":
            handle_frontiers(self, query, q_lower)

        elif q_lower == "/freshness":
            handle_freshness(self, query, q_lower)

        elif q_lower == "/brief" or q_lower.startswith("/brief "):
            await handle_brief(self, query, q_lower)


        elif q_lower == "/macros":
            handle_macros(self, query, q_lower)

        elif q_lower == "/weekly_report":
            handle_weekly_report(self, query, q_lower)

        elif q_lower == "/capabilities":
            handle_capabilities(self, query, q_lower)

        elif q_lower == "/timing":
            handle_timing(self, query, q_lower)

        elif q_lower == "/retest_due":
            handle_retest_due(self, query, q_lower)

        elif q_lower == "/export_client":
            try:
                path = export_client(self.active_client_name)
                console.print(f"[dim]  Client exported to: [cyan]{path}[/cyan][/dim]")
            except Exception as e:
                console.print(f"[dim red]  Export failed: {e}[/dim red]")

        elif q_lower == "/gaps":
            handle_gaps(self, query, q_lower)

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
            handle_save_session(self, query, q_lower)

        elif q_lower.startswith("/resume_session") or q_lower.startswith("/resume "):
            handle_resume_session(self, query, q_lower)

        elif q_lower == "/sessions":
            handle_sessions(self, query, q_lower)

        elif q_lower == "/log" or q_lower == "/history":
            handle_log(self, query, q_lower)

        elif q_lower.startswith("/effect "):
            handle_effect(self, query, q_lower)

        elif q_lower.startswith("/readpdf "):
            handle_readpdf(self, query, q_lower)

        elif q_lower.startswith("/autoquality "):
            handle_autoquality(self, query, q_lower)

        elif q_lower == "/pdf_last":
            handle_pdf_last(self, query, q_lower)

        elif q_lower == "/pdf" or q_lower.startswith("/pdf "):
            handle_pdf(self, query, q_lower)

        elif q_lower.startswith("/recommend "):
            await handle_recommend(self, query, q_lower)

        elif q_lower.startswith("/accepted"):
            handle_accepted(self, query, q_lower)

        elif q_lower.startswith("/rejected"):
            handle_rejected(self, query, q_lower)

        elif q_lower == "/preferences":
            handle_preferences(self, query, q_lower)

        elif q_lower.startswith("/quality"):
            handle_quality(self, query, q_lower)

        elif q_lower.startswith("/grade "):
            handle_grade(self, query, q_lower)

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
