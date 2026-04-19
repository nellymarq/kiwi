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
from tools.interactions import lookup_interactions, lookup_single, format_interaction_report, has_novel_compounds, analyze_novel_interactions
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
from tools.supplements import resolve_supplement, format_dosing_protocol, list_supplements_by_category
from tools.body_composition import (
    estimate_body_fat_jackson_pollock_3, analyze_body_composition,
    calculate_ffmi, calculate_energy_availability, safe_weight_change_rate,
    format_composition_report, SPORT_BF_TARGETS,
)
from tools.training_zones import (
    estimate_vo2max_cooper, estimate_vo2max_hr_based, predict_hr_max,
    calculate_hr_zones_karvonen, calculate_power_zones,
    calculate_pace_zones, recommend_intensity_distribution,
    format_hr_zones, format_power_zones, format_pace_zones,
    format_intensity_distribution,
)
from tools.injury_prevention import (
    calculate_acwr, check_ten_percent_rule, score_fms_movement,
    calculate_fms_composite, screen_overuse_risk, get_prevention_protocol,
    return_to_sport_decision, format_acwr_report, format_prevention_protocol,
    list_prevention_protocols, PROTOCOL_ALIASES, PROTOCOL_DB,
)
from tools.female_athlete import (
    calculate_energy_availability as calc_ea_female, get_cycle_phase,
    match_training_to_phase, screen_reds, postpartum_return_protocol,
    calculate_iron_needs, format_ea_report, format_reds_report,
    format_cycle_training, CYCLE_PHASES,
)
from tools.environmental import (
    altitude_training_protocol, heat_acclimatization_protocol,
    air_quality_adjustment, cold_exposure_protocol, jet_lag_protocol,
    format_altitude_protocol, format_heat_protocol, format_air_quality,
    format_cold_protocol, format_jet_lag,
)
from tools.mental_performance import (
    assess_competition_anxiety, assess_mental_fatigue, assess_burnout,
    get_visualization_protocol, generate_pre_competition_routine,
    list_visualization_protocols, format_anxiety_report, format_burnout_report,
    format_visualization, VISUALIZATION_DB,
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
from tools.supplements import resolve_supplement, SUPPLEMENT_DB, list_supplements_by_category
from tools.interactions import lookup_interactions
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

        elif q_lower.startswith("/fulltext "):
            doi = query[10:].strip()
            if doi and self.unpaywall:
                with console.status("[dim cyan]  Looking up open access version via Unpaywall...[/dim cyan]", spinner="earth"):
                    result = self.unpaywall.lookup(doi)
                if result and result.is_oa:
                    console.print(Panel(
                        result.summary(),
                        title="[cyan]Open Access Available[/cyan]",
                        border_style="green",
                        box=box.SIMPLE,
                    ))
                elif result:
                    console.print(f"[dim]  No OA version found for {doi}.[/dim]")
                else:
                    console.print(f"[dim]  DOI lookup failed.[/dim]")
            elif not self.unpaywall:
                console.print("[dim]  Unpaywall disabled (run without --no-pubmed).[/dim]")

        elif q_lower.startswith("/tldr "):
            search_query = query[6:].strip()
            if search_query and self.semantic:
                with console.status("[dim cyan]  Fetching Semantic Scholar TLDRs...[/dim cyan]", spinner="earth"):
                    papers = self.semantic.search(search_query, max_results=8)
                if papers:
                    for i, p in enumerate(papers, 1):
                        tldr = p.tldr or "(no TLDR available)"
                        console.print(
                            f"\n[cyan][{i}][/cyan] [bold]{p.title}[/bold]\n"
                            f"[dim]{', '.join(p.authors[:2])} ({p.year}) · {p.journal} · cited {p.citation_count}x[/dim]\n"
                            f"[green]TLDR:[/green] {tldr}\n"
                            f"DOI: {p.doi}"
                        )
                else:
                    console.print("[dim]  No papers found.[/dim]")
            elif not self.semantic:
                console.print("[dim]  Semantic Scholar disabled (run without --no-pubmed).[/dim]")

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
            topic = query[7:].strip()
            if topic:
                if self.watch_list.add(topic):
                    console.print(f"[dim]  Watching: [cyan]{topic}[/cyan]. Run /digest to get updates.[/dim]")
                else:
                    console.print(f"[dim]  Already watching '{topic}'.[/dim]")

        elif q_lower.startswith("/unwatch "):
            topic = query[9:].strip()
            if self.watch_list.remove(topic):
                console.print(f"[dim]  Removed watch on: {topic}[/dim]")
            else:
                console.print(f"[dim]  Not in watch list: {topic}[/dim]")

        elif q_lower == "/watched" or q_lower == "/watchlist":
            topics = self.watch_list.list_topics()
            if not topics:
                console.print("[dim]  No watched topics. Add with /watch <topic>[/dim]")
            else:
                lines = []
                for t in topics:
                    last = t.get("last_digest_ts", "never")[:10] if t.get("last_digest_ts") else "never digested"
                    lines.append(f"  • [cyan]{t['topic']}[/cyan] — added {t.get('added_ts', '')[:10]}, last digest: {last}")
                console.print(Panel(
                    "\n".join(lines),
                    title="[cyan]Watched Topics[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))

        elif q_lower == "/digest":
            topics = self.watch_list.list_topics()
            if not topics:
                console.print("[dim]  No watched topics. Add with /watch <topic>[/dim]")
            elif not (self.pubmed or self.openalex):
                console.print("[dim]  Literature sources disabled. Run without --no-pubmed.[/dim]")
            else:
                console.print(f"[dim]  Running digest for {len(topics)} watched topic(s)...[/dim]\n")
                for t in topics:
                    topic_text = t["topic"]
                    previous_seen = self.watch_list.get_last_seen(topic_text)
                    keywords = " ".join(topic_text.split()[:6])

                    all_items = []
                    all_dois = []

                    if self.pubmed:
                        arts = self.pubmed.search_and_fetch(keywords, max_results=5, years_back=2)
                        for a in arts:
                            doi_l = (a.doi or "").lower()
                            is_new = doi_l and doi_l not in previous_seen
                            all_items.append((is_new, a.title, a.authors, a.year, a.doi, "PubMed"))
                            if doi_l:
                                all_dois.append(doi_l)

                    if self.openalex:
                        works = self.openalex.search_sports_nutrition(keywords, max_results=5, years_back=2)
                        for w in works:
                            doi_l = (w.doi or "").lower()
                            is_new = doi_l and doi_l not in previous_seen
                            all_items.append((is_new, w.title, w.authors, str(w.year), w.doi, "OpenAlex"))
                            if doi_l:
                                all_dois.append(doi_l)

                    new_items = [x for x in all_items if x[0]]
                    console.print(f"[bold]Topic: {topic_text}[/bold] — {len(new_items)} new, {len(all_items) - len(new_items)} already seen")
                    for is_new, title, authors, year, doi, source in new_items[:8]:
                        badge = "[green]NEW[/green]"
                        author_str = ", ".join(authors[:2]) if authors else "?"
                        console.print(f"  {badge} {title[:100]}")
                        console.print(f"    [dim]{author_str} ({year}) · {source} · DOI: {doi}[/dim]")

                    self.watch_list.mark_digest_run(topic_text, all_dois)
                    console.print()

                self.watch_list.update_global_digest_ts()

        elif q_lower == "/cost":
            console.print(Panel(
                self.cost.summary(),
                title="[cyan]Session API Cost[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

        elif q_lower == "/team" or q_lower.startswith("/team "):
            summary = format_team_summary()
            console.print(Panel(
                summary,
                title="[cyan]Team Analytics[/cyan]",
                border_style="cyan", box=box.SIMPLE,
            ))

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
            payload = query.split(maxsplit=1)
            days = 3
            if len(payload) > 1:
                try:
                    days = int(payload[1].strip().split()[0])
                    days = max(1, min(14, days))
                except ValueError:
                    pass

            missing = [f for f in ("weight_kg", "height_cm", "age", "sex", "activity_level")
                       if not self.profile.get(f)]
            if missing:
                console.print(f"[dim red]  Missing profile fields: {', '.join(missing)}. Set with /profile set <field> <value>[/dim red]")
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
                    macros_text = m.summary()
                except Exception as e:
                    macros_text = f"(could not compute: {e})"

                restrictions = self.profile.get("dietary_restrictions") or []
                restrictions_text = ", ".join(restrictions) if restrictions else "none"
                goal = self.profile.get("primary_goal") or "maintenance"
                sport = self.profile.get("sport") or "general athletic"

                console.print(f"[dim]  Generating {days}-day meal plan for {sport}...[/dim]\n")
                result = await self.meal_plan_agent.run({
                    "profile_summary": self.profile.to_summary(),
                    "macro_targets": macros_text,
                    "days": days,
                    "training_schedule": f"Sport: {sport}",
                    "dietary_restrictions": restrictions_text,
                    "goal": goal,
                })
                self._state["last_output"] = result
                console.print(result)

        elif q_lower.startswith("/training_plan") or q_lower.startswith("/trainingplan"):
            parts = query.split(maxsplit=2)
            sport = self.profile.get("sport") or "strength"
            weeks = 8
            if len(parts) >= 2:
                try:
                    weeks = int(parts[1].strip())
                    weeks = max(2, min(24, weeks))
                except ValueError:
                    sport = parts[1].strip()
                    if len(parts) >= 3:
                        try:
                            weeks = int(parts[2].strip().split()[0])
                        except ValueError:
                            pass

            goal = self.profile.get("primary_goal") or "strength"
            training_status = self.profile.get("training_status") or "intermediate"

            console.print(f"[dim]  Generating {weeks}-week training block for {sport}...[/dim]\n")
            result = await self.training_plan_agent.run({
                "profile_summary": self.profile.to_summary(),
                "sport": sport,
                "weeks": weeks,
                "goal": goal,
                "current_maxes": "",
                "current_load": "",
                "frequency": 4,
            })
            self._state["last_output"] = result
            console.print(result)

        elif q_lower.startswith("/fight_prep") or q_lower.startswith("/race_prep"):
            notes = ""
            if " " in query:
                notes = query.split(maxsplit=1)[1].strip()
            sport = self.profile.get("sport") or "combat sports"
            current_weight = self.profile.get("weight_kg") or ""
            supplements_list = self.profile.get("current_supplements") or []
            supplements_text = ", ".join(supplements_list) if supplements_list else "none listed"

            console.print(f"[dim]  Generating competition preparation protocol for {sport}...[/dim]\n")
            result = await self.competition_prep_agent.run({
                "profile_summary": self.profile.to_summary(),
                "sport": sport,
                "event": "competition" if "fight" in q_lower else "race",
                "current_weight": str(current_weight) + " kg" if current_weight else "",
                "target_weight": "",
                "current_supplements": supplements_text,
                "notes": notes,
            })
            self._state["last_output"] = result
            console.print(result)

        elif q_lower.startswith("/oura "):
            subcmd = query[6:].strip().lower()
            if subcmd.startswith("sync"):
                # Get Oura token from config or env
                import os
                token = self.config.get("oura_token", "") or os.environ.get("OURA_TOKEN", "")
                if not token:
                    console.print(
                        "[dim red]  No Oura token. Set OURA_TOKEN env var or add oura_token to ~/.kiwi/config.json[/dim red]\n"
                        "[dim]  Get your token at: https://cloud.ouraring.com/personal-access-tokens[/dim]"
                    )
                else:
                    days = 7
                    parts = subcmd.split()
                    if len(parts) > 1:
                        try:
                            days = int(parts[1])
                        except ValueError:
                            pass
                    console.print(f"[dim]  Syncing last {days} days from Oura Ring...[/dim]")
                    oura = OuraClient(token)
                    summaries = oura.sync_days(days_back=days)
                    if summaries:
                        console.print(Panel(
                            oura.format_sync_report(summaries),
                            title="[cyan]Oura Ring Sync[/cyan]",
                            border_style="cyan", box=box.SIMPLE,
                        ))
                        # Auto-populate progress tracker
                        imported = 0
                        for s in summaries:
                            for metric, value in s.to_metrics().items():
                                self.progress.record(metric, value, note="oura sync")
                                imported += 1
                        console.print(f"[dim]  {imported} data points imported to progress tracker[/dim]")
                    else:
                        console.print("[dim red]  No data returned. Check your token and try again.[/dim red]")
            else:
                console.print("[dim]  Usage: /oura sync [days]  (default: 7 days)[/dim]")

        elif q_lower.startswith("/import_wearable "):
            filepath = query[17:].strip()
            if filepath:
                records, result = import_wearable_file(filepath)
                console.print(Panel(
                    format_import_result(result),
                    title="[cyan]Wearable Import[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))
                if records:
                    for r in records:
                        self.progress.record(r["metric"], r["value"], note=f"import {result.format_detected}")
                    console.print(f"[dim]  {len(records)} data points added to progress tracker[/dim]")
            else:
                console.print("[dim]  Usage: /import_wearable <path/to/file.csv or .json>[/dim]")

        elif q_lower.startswith("/import_labs "):
            parts = query[12:].strip().split()
            if len(parts) < 2 or len(parts) % 2 != 0:
                console.print("[dim]  Usage: /import_labs <marker1> <val1> <marker2> <val2> ...[/dim]")
            else:
                imported = 0
                all_actions = []
                sex = self.profile.get("sex") or "male"
                current_supps = self.profile.get("current_supplements") or []
                for i in range(0, len(parts), 2):
                    metric = parts[i].lower().replace(" ", "_")
                    try:
                        value = float(parts[i + 1])
                        self.progress.record(metric, value)
                        imported += 1
                        actions = check_biomarker(metric, value, sex=sex, current_supplements=current_supps)
                        all_actions.extend(actions)
                    except ValueError:
                        console.print(f"[dim red]  Skipped {metric}: '{parts[i+1]}' is not numeric[/dim red]")
                console.print(f"[dim]  Imported {imported} biomarkers[/dim]")
                if all_actions:
                    console.print()
                    console.print(format_proactive_actions(all_actions))

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
            parts = query[14:].strip().split(maxsplit=3)
            if not parts:
                console.print("[dim]  Usage: /intervention start|stop|check|list <name> [dose] [target_metric][/dim]")
            elif parts[0] == "start" and len(parts) >= 2:
                name = parts[1]
                dose = parts[2] if len(parts) > 2 else ""
                target = parts[3] if len(parts) > 3 else ""
                entry = self.interventions.start(name, dose, target)
                console.print(f"[dim]  Started intervention: [cyan]{name}[/cyan]"
                              + (f" ({dose})" if dose else "")
                              + (f" → tracking {target}" if target else "")
                              + f"[/dim]")
            elif parts[0] == "stop" and len(parts) >= 2:
                reason = parts[2] if len(parts) > 2 else ""
                if self.interventions.stop(parts[1], reason):
                    console.print(f"[dim]  Stopped intervention: {parts[1]}[/dim]")
                else:
                    console.print(f"[dim red]  No active intervention '{parts[1]}' found[/dim red]")
            elif parts[0] == "check" and len(parts) >= 2:
                result = self.interventions.check_outcome(parts[1])
                console.print(Panel(
                    self.interventions.format_outcome(result),
                    title="[cyan]Intervention Outcome[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))
            elif parts[0] == "list":
                console.print(Panel(
                    self.interventions.format_active(),
                    title="[cyan]Active Interventions[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))
            else:
                console.print("[dim]  /intervention start <name> [dose] [target_metric][/dim]")
                console.print("[dim]  /intervention stop <name> [reason][/dim]")
                console.print("[dim]  /intervention check <name>[/dim]")
                console.print("[dim]  /intervention list[/dim]")

        elif q_lower.startswith("/track "):
            parts = query[7:].strip().split(maxsplit=2)
            if len(parts) >= 2:
                metric = parts[0].lower().replace(" ", "_")
                try:
                    value = float(parts[1])
                    note = parts[2] if len(parts) > 2 else ""
                    self.progress.record(metric, value, note=note)
                    unit = KNOWN_METRICS.get(metric, "")
                    console.print(f"[dim]  Tracked: {metric} = {value} {unit}"
                                  + (f" ({note})" if note else "") + "[/dim]")
                    # Proactive: check if this biomarker triggers recommendations
                    sex = self.profile.get("sex") or "male"
                    current_supps = self.profile.get("current_supplements") or []
                    actions = check_biomarker(metric, value, sex=sex, current_supplements=current_supps)
                    if actions:
                        console.print()
                        console.print(format_proactive_actions(actions))
                except ValueError:
                    console.print(f"[dim red]  Value must be numeric: /track {metric} <number>[/dim red]")
            else:
                metrics_list = ", ".join(sorted(KNOWN_METRICS.keys())[:15]) + "..."
                console.print(f"[dim]  Usage: /track <metric> <value> [note][/dim]")
                console.print(f"[dim]  Known metrics: {metrics_list}[/dim]")

        elif q_lower.startswith("/trends "):
            metric = query[8:].strip().lower().replace(" ", "_")
            if metric:
                output = self.progress.format_trend(metric)
                console.print(Panel(output, title=f"[cyan]Trend: {metric}[/cyan]", border_style="cyan", box=box.SIMPLE))
            else:
                console.print("[dim]  Usage: /trends <metric>[/dim]")

        elif q_lower == "/trends" or q_lower == "/dashboard":
            output = self.progress.format_dashboard()
            console.print(Panel(output, title="[cyan]Progress Dashboard[/cyan]", border_style="cyan", box=box.SIMPLE))

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
                    if k in reds_keys:
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

            # Autonomous RED-S enrichment: gate on sex=female, ≥2 keys, ≥1 clinical key
            reds_screening_text = ""
            clinical_keys = {"menstrual_status", "bmi", "bone_stress_injuries", "disordered_eating"}
            if (
                self.profile.data.get("sex") == "female"
                and len(reds_responses) >= 2
                and any(k in reds_responses for k in clinical_keys)
            ):
                reds_result = screen_reds(reds_responses)
                reds_screening_text = format_reds_report(reds_result)

            console.print("[dim]  Running comprehensive risk screening...[/dim]\n")
            result = await self.risk_screen_agent.run({
                "profile_summary": profile_summary,
                "biomarker_data": biomarker_text,
                "progress_data": progress_text,
                "training_load": "",
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

        elif q_lower == "/brief":
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

            console.print("[dim]  Generating daily brief...[/dim]\n")
            brief_context = {
                "profile_summary": profile_summary,
                "progress_data": progress_text,
                "interventions": interventions_text,
                "risk_flags": retest_text if "OVERDUE" in retest_text or "DUE NOW" in retest_text else "",
                "research_gaps": gaps_text,
                "biomarker_due": retest_text if "No biomarkers" not in retest_text else "",
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
            ]
            for field_key, prompt_text in fields_order:
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

                # Autonomous injury-prevention enrichment: scan finding for protocol match
                # Rule: substring match, word-boundary on ≥1 side, alias len ≥4, first-match-wins
                prevention_text = ""
                finding_lower = finding.lower()
                candidates: list = []
                for key in PROTOCOL_DB.keys():
                    if len(key) >= 4:
                        candidates.append((key, key))
                for alias, target in PROTOCOL_ALIASES.items():
                    if len(alias) >= 4:
                        candidates.append((alias, target))
                # Longest-first for greedy match
                candidates.sort(key=lambda kv: -len(kv[0]))
                for alias, target_key in candidates:
                    idx = finding_lower.find(alias)
                    if idx == -1:
                        continue
                    left_ok = idx == 0 or not finding_lower[idx - 1].isalnum()
                    end = idx + len(alias)
                    right_ok = end == len(finding_lower) or not finding_lower[end].isalnum()
                    if left_ok or right_ok:
                        proto = get_prevention_protocol(target_key)
                        if proto:
                            sport = self.profile.data.get("sport", "general")
                            prevention_text = format_prevention_protocol(proto, sport)
                        break

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
            search_query = query[8:].strip()
            if search_query and self.trials:
                with console.status("[dim cyan]  Searching ClinicalTrials.gov...[/dim cyan]", spinner="earth"):
                    results = self.trials.search(search_query, max_results=8)
                if results:
                    for i, t in enumerate(results, 1):
                        console.print(
                            f"\n[cyan][{i}][/cyan] [bold]{t.title}[/bold]\n"
                            f"[dim]{t.status} · Phase {t.phase} · N={t.enrollment} · {t.sponsor}[/dim]\n"
                            f"NCT: {t.nct_id}\n"
                            f"Conditions: {', '.join(t.conditions[:3])}\n"
                            f"Interventions: {', '.join(t.interventions[:3])}\n"
                            f"{t.brief_summary[:300]}..."
                        )
                else:
                    console.print("[dim]  No trials found.[/dim]")
            elif not self.trials:
                console.print("[dim]  ClinicalTrials disabled (run without --no-pubmed).[/dim]")

        elif q_lower.startswith("/citedby "):
            doi = query[9:].strip()
            if doi and self.openalex:
                with console.status(f"[dim cyan]  Finding papers that cite {doi}...[/dim cyan]", spinner="earth"):
                    works = self.openalex.fetch_cited_by(doi, max_results=10)
                if works:
                    console.print(f"[dim]  Found {len(works)} papers citing {doi}[/dim]")
                    for i, w in enumerate(works, 1):
                        oa_tag = " [OA]" if w.open_access else ""
                        console.print(
                            f"\n[cyan][{i}][/cyan] [bold]{w.title}[/bold]\n"
                            f"[dim]{', '.join(w.authors[:2])} ({w.year}) · {w.journal}{oa_tag}[/dim]\n"
                            f"DOI: {w.doi}  Cited: {w.cited_by_count}"
                        )
                else:
                    console.print("[dim]  No citations found (or DOI invalid).[/dim]")
            elif not self.openalex:
                console.print("[dim]  OpenAlex disabled (run without --no-pubmed).[/dim]")

        elif q_lower.startswith("/openalex "):
            search_query = query[10:].strip()
            if search_query and self.openalex:
                with console.status("[dim cyan]  Searching OpenAlex (sports nutrition journals)...[/dim cyan]", spinner="earth"):
                    works = self.openalex.search_sports_nutrition(search_query, max_results=8)
                if works:
                    for i, w in enumerate(works, 1):
                        oa_tag = " [OA]" if w.open_access else ""
                        console.print(
                            f"\n[cyan][{i}][/cyan] [bold]{w.title}[/bold]\n"
                            f"[dim]{', '.join(w.authors[:2])} ({w.year}) · {w.journal}{oa_tag}[/dim]\n"
                            f"DOI: {w.doi}  Cited: {w.cited_by_count}\n"
                            f"{w.abstract[:400]}..."
                        )
                else:
                    console.print("[dim]  No results found.[/dim]")
            elif not self.openalex:
                console.print("[dim]  OpenAlex disabled (run without --no-pubmed).[/dim]")

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

                # Claude fallback for novel compounds not in local DB
                novel = has_novel_compounds(compounds)
                if novel:
                    console.print(f"\n[dim cyan]  Novel compounds detected: {', '.join(novel)}[/dim cyan]")
                    console.print("[dim cyan]  Running Claude analysis for comprehensive interaction check...[/dim cyan]\n")

                    def on_check_text(text: str):
                        console.print(text, end="", markup=False)

                    analysis = await analyze_novel_interactions(self.client, compounds, on_text=on_check_text)
                    console.print("\n")
                    console.rule("[dim]Claude Interaction Analysis Complete[/dim]")
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
                    console.print(f"[dim]  No known interactions for '{compound}' in local database.[/dim]")
                    console.print("[dim cyan]  Running Claude analysis...[/dim cyan]\n")

                    def on_interact_text(text: str):
                        console.print(text, end="", markup=False)

                    analysis = await analyze_novel_interactions(self.client, [compound], on_text=on_interact_text)
                    console.print("\n")
                    console.rule("[dim]Claude Interaction Analysis Complete[/dim]")
            else:
                console.print("[dim]  Usage: /interact caffeine[/dim]")

        # ── Food & Nutrition Lookup ──────────────────────────────────

        elif q_lower.startswith("/food+ ") or q_lower.startswith("/food "):
            include_aminos = q_lower.startswith("/food+ ")
            prefix_len = 7 if include_aminos else 6
            args = query[prefix_len:].strip().split()
            food_name = " ".join(args[:-1]) if args and args[-1].lstrip("-").replace(".", "", 1).isdigit() else " ".join(args)
            grams = float(args[-1]) if args and args[-1].lstrip("-").replace(".", "", 1).isdigit() else 100.0
            if grams <= 0:
                console.print("[dim red]  Serving size must be positive.[/dim red]")
                return False

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
                    if duration <= 0 or not (1 <= rpe <= 10):
                        console.print("[dim red]  Duration must be positive, RPE must be 1–10.[/dim red]")
                        return False
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
                if not (50 <= pct <= 110):
                    console.print("[dim red]  Intensity must be 50–110% of 1RM.[/dim red]")
                    return False
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
                    if dose <= 0 or hours < 0:
                        console.print("[dim red]  Dose must be positive, hours must be non-negative.[/dim red]")
                        return False
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

        # ── Supplements ────────────────────────────────────────────

        elif q_lower.startswith("/supplist"):
            cat = query[9:].strip() or None
            output = list_supplements_by_category(cat)
            console.print(Panel(output, title="[cyan]Supplement Database[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))

        elif q_lower.startswith("/supp "):
            name = query[6:].strip()
            proto = resolve_supplement(name)
            if proto:
                sport = self.profile.data.get("sport", "general")
                weight = self.profile.get("weight_kg")
                output = format_dosing_protocol(proto, sport, weight_kg=weight)
                console.print(Panel(output, title=f"[cyan]{proto.name}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print(f"[yellow]  Supplement '{name}' not found. Try /supplist to see all options.[/yellow]")

        # ── Body Composition ──────────────────────────────────────────

        elif q_lower.startswith("/skinfold "):
            parts = query[10:].strip().split()
            if len(parts) >= 5:
                sex, age_s = parts[0], parts[1]
                s1, s2, s3 = float(parts[2]), float(parts[3]), float(parts[4])
                age = int(age_s)
                if sex.lower() == "male":
                    bf = estimate_body_fat_jackson_pollock_3(sex, age, skinfold_chest_mm=s1, skinfold_abdomen_mm=s2, skinfold_thigh_mm=s3)
                else:
                    bf = estimate_body_fat_jackson_pollock_3(sex, age, skinfold_tricep_mm=s1, skinfold_suprailiac_mm=s2, skinfold_thigh_mm=s3)
                console.print(Panel(f"Estimated Body Fat: {bf:.1f}% (Jackson-Pollock 3-site)", title="[cyan]Skinfold Estimation[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /skinfold <sex> <age> <site1_mm> <site2_mm> <site3_mm>[/dim]")
                console.print("[dim]  Males: chest, abdomen, thigh | Females: tricep, suprailiac, thigh[/dim]")

        elif q_lower.startswith("/bodyfat "):
            parts = query[9:].strip().split()
            if len(parts) >= 2:
                wt, bf_pct = float(parts[0]), float(parts[1])
                sport = parts[2] if len(parts) > 2 else self.profile.data.get("sport", "general_fitness")
                sex = self.profile.data.get("sex", "male")
                ht = self.profile.data.get("height_cm", 175)
                result = analyze_body_composition(wt, bf_pct, sex, ht, sport)
                ffmi = calculate_ffmi(wt, bf_pct, ht)
                report = format_composition_report(result, ffmi=ffmi)
                console.print(Panel(report, title="[cyan]Body Composition Analysis[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /bodyfat <weight_kg> <body_fat_%> [sport][/dim]")

        elif q_lower.startswith("/ffmi "):
            parts = query[5:].strip().split()
            if len(parts) >= 3:
                wt, bf_pct, ht = float(parts[0]), float(parts[1]), float(parts[2])
                result = calculate_ffmi(wt, bf_pct, ht)
                lines = [
                    f"FFMI: {result.ffmi:.1f} kg/m²",
                    f"Adjusted FFMI: {result.adjusted_ffmi:.1f} kg/m² (normalized to 1.80m)",
                    f"Interpretation: {result.interpretation}",
                    f"{result.natural_limit_note}",
                    f"Evidence: {result.evidence}",
                ]
                console.print(Panel("\n".join(lines), title="[cyan]Fat-Free Mass Index[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /ffmi <weight_kg> <body_fat_%> <height_cm>[/dim]")

        elif q_lower.startswith("/ea "):
            parts = query[4:].strip().split()
            if len(parts) >= 3:
                intake, exercise, lm = float(parts[0]), float(parts[1]), float(parts[2])
                ea = calculate_energy_availability(intake, exercise, lm)
                lines = [
                    f"Energy Availability: {ea.ea_kcal_per_kg_ffm:.1f} kcal/kg FFM/day",
                    f"Status: {ea.status.upper()}",
                    f"Risk Level: {ea.risk_level.upper()}",
                ]
                if ea.consequences:
                    lines.append("\nConsequences:")
                    for c in ea.consequences:
                        lines.append(f"  • {c}")
                if ea.recommendations:
                    lines.append("\nRecommendations:")
                    for r in ea.recommendations:
                        lines.append(f"  • {r}")
                console.print(Panel("\n".join(lines), title="[cyan]Energy Availability (RED-S Screening)[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /ea <energy_intake_kcal> <exercise_expenditure_kcal> <lean_mass_kg>[/dim]")

        elif q_lower.startswith("/weightplan "):
            parts = query[12:].strip().split()
            if len(parts) >= 3:
                now_kg, goal_kg, bf = float(parts[0]), float(parts[1]), float(parts[2])
                goal = parts[3] if len(parts) > 3 else "fat_loss"
                sex = self.profile.data.get("sex", "male")
                wc = safe_weight_change_rate(now_kg, goal_kg, bf, sex, goal)
                lines = [
                    f"Direction: {wc.direction.title()}",
                    f"Rate: {wc.rate_kg_per_week:.2f} kg/week ({wc.rate_pct_bw_per_week}% BW/week)",
                    f"Safe: {'Yes' if wc.safe else 'AGGRESSIVE — consider slowing'}",
                    "",
                ]
                for note in wc.lean_mass_preservation_notes:
                    lines.append(f"  • {note}")
                lines.append(f"\nEvidence: {wc.evidence}")
                console.print(Panel("\n".join(lines), title="[cyan]Weight Change Plan[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /weightplan <current_kg> <target_kg> <body_fat_%> [goal: fat_loss/muscle_gain/contest_prep][/dim]")

        # ── Training Zones ────────────────────────────────────────────

        elif q_lower.startswith("/hrzones "):
            parts = query[9:].strip().split()
            if len(parts) >= 2:
                hr_rest, hr_max = int(parts[0]), int(parts[1])
                zones = calculate_hr_zones_karvonen(hr_rest, hr_max)
                output = format_hr_zones(zones)
                console.print(Panel(output, title=f"[cyan]HR Zones[/cyan]  [dim]HRrest={hr_rest} HRmax={hr_max}[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /hrzones <resting_hr> <max_hr>[/dim]")

        elif q_lower.startswith("/powerzones "):
            parts = query[12:].strip().split()
            if len(parts) >= 1:
                ftp = int(parts[0])
                zones = calculate_power_zones(ftp)
                output = format_power_zones(zones)
                console.print(Panel(output, title=f"[cyan]Power Zones[/cyan]  [dim]FTP={ftp}W[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /powerzones <ftp_watts>[/dim]")

        elif q_lower.startswith("/pacezones "):
            parts = query[11:].strip().split()
            if len(parts) >= 1:
                vdot = float(parts[0])
                zones = calculate_pace_zones(vdot)
                output = format_pace_zones(zones)
                console.print(Panel(output, title=f"[cyan]Pace Zones[/cyan]  [dim]VDOT={vdot}[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /pacezones <vdot>[/dim]")

        elif q_lower.startswith("/vo2max "):
            parts = query[8:].strip().split()
            if len(parts) >= 1:
                dist = float(parts[0])
                result = estimate_vo2max_cooper(dist)
                lines = [
                    f"VO2max: {result.vo2max:.1f} mL/kg/min",
                    f"Category: {result.fitness_category.title()}",
                    f"Method: {result.method}",
                    f"Evidence: {result.evidence}",
                ]
                console.print(Panel("\n".join(lines), title=f"[cyan]VO2max Estimate[/cyan]  [dim]{dist:.0f}m in 12 min[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /vo2max <distance_meters_in_12min>[/dim]")

        elif q_lower.startswith("/hrmax "):
            parts = query[7:].strip().split()
            if len(parts) >= 1:
                age = int(parts[0])
                method = parts[1] if len(parts) > 1 else "tanaka"
                hr = predict_hr_max(age, method)
                console.print(Panel(f"Predicted HRmax: {hr} bpm  (method: {method}, age: {age})", title="[cyan]HRmax Prediction[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                console.print("[dim]  Usage: /hrmax <age> [method: tanaka/fox/gulati][/dim]")

        elif q_lower.startswith("/distribution"):
            parts = query[13:].strip().split()
            sport = parts[0] if len(parts) > 0 else self.profile.data.get("sport", "endurance")
            level = parts[1] if len(parts) > 1 else "intermediate"
            phase = parts[2] if len(parts) > 2 else "base"
            dist = recommend_intensity_distribution(sport, level, phase)
            output = format_intensity_distribution(dist)
            console.print(Panel(output, title=f"[cyan]Intensity Distribution[/cyan]  [dim]{sport}/{level}/{phase}[/dim]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))

        # ── Injury Prevention ───────────────────────────────────────

        elif q_lower.startswith("/acwr"):
            parts = query[5:].strip().split()
            if len(parts) >= 2:
                try:
                    loads = [float(p) for p in parts]
                    result = calculate_acwr(loads)
                    output = format_acwr_report(result)
                    console.print(Panel(output, title="[cyan]Acute:Chronic Workload Ratio[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /acwr <load1> <load2> ... (daily training loads, ≥2 days)[/dim]")
            else:
                console.print("[dim]  Usage: /acwr <load1> <load2> ... (daily training loads, ≥2 days)[/dim]")

        elif q_lower.startswith("/fms"):
            parts = query[4:].strip().split()
            if len(parts) >= 2 and len(parts) % 2 == 0:
                try:
                    scores = {parts[i]: int(parts[i + 1]) for i in range(0, len(parts), 2)}
                    if len(scores) == 1:
                        movement, score = next(iter(scores.items()))
                        fms = score_fms_movement(movement, score)
                        lines = [
                            f"Movement: {fms.movement}",
                            f"Score: {fms.score}/3",
                        ]
                        if fms.compensations:
                            lines += ["", "Compensations:"] + [f"  • {c}" for c in fms.compensations]
                        if fms.corrective_exercises:
                            lines += ["", "Correctives:"] + [f"  • {c}" for c in fms.corrective_exercises]
                        output = "\n".join(lines)
                        console.print(Panel(output, title=f"[cyan]FMS — {movement}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    else:
                        composite = calculate_fms_composite(scores)
                        lines = [
                            f"Composite Score: {composite['composite_score']}/21",
                            f"Risk Level: {composite['risk_level'].upper()}",
                        ]
                        if composite["priority_movements"]:
                            lines.append(f"Priority: {', '.join(composite['priority_movements'])}")
                        if composite["asymmetries"]:
                            lines.append(f"Asymmetries: {', '.join(composite['asymmetries'])}")
                        output = "\n".join(lines)
                        console.print(Panel(output, title="[cyan]FMS Composite[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except (ValueError, KeyError):
                    console.print("[dim]  Usage: /fms <movement> <score> [<movement> <score> ...]  (scores 0-3)[/dim]")
            else:
                console.print("[dim]  Usage: /fms <movement> <score> [<movement> <score> ...]  (scores 0-3)[/dim]")
                console.print(f"[dim]  Movements: {', '.join(sorted(PROTOCOL_DB.keys())[:3])}..., etc. (see /prevent)[/dim]")

        elif q_lower.startswith("/overuse"):
            parts = query[8:].strip().split()
            if len(parts) >= 3:
                try:
                    sport = parts[0]
                    age = int(parts[1])
                    hours = float(parts[2])
                    spec_age = int(parts[3]) if len(parts) > 3 else None
                    result = screen_overuse_risk(sport, age, hours, specialization_age=spec_age)
                    lines = [
                        f"Sport: {result.sport}  Age: {result.age}",
                        f"Training: {result.training_history}",
                        f"Risk Level: {result.risk_level.upper()}",
                    ]
                    if result.risk_factors:
                        lines += ["", "Risk Factors:"] + [f"  ⚠ {f}" for f in result.risk_factors]
                    if result.recommendations:
                        lines += ["", "Recommendations:"] + [f"  • {r}" for r in result.recommendations]
                    lines += ["", f"Evidence: {result.evidence}"]
                    output = "\n".join(lines)
                    console.print(Panel(output, title="[cyan]Overuse Risk Screening[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /overuse <sport> <age> <weekly_hours> [specialization_age][/dim]")
            else:
                console.print("[dim]  Usage: /overuse <sport> <age> <weekly_hours> [specialization_age][/dim]")

        elif q_lower.startswith("/return"):
            parts = query[7:].strip().split()
            if len(parts) >= 4:
                try:
                    injury = parts[0]
                    weeks = int(parts[1])
                    pain = int(parts[2])
                    deficit = float(parts[3])
                    result = return_to_sport_decision(injury, weeks, pain, deficit)
                    lines = [
                        f"Injury: {injury}  Weeks since: {weeks}",
                        f"Phase: {result['phase']}",
                        f"Cleared: {'YES' if result['cleared'] else 'NO'}",
                        f"Timeline: {result['timeline_estimate']}",
                    ]
                    if result["criteria_met"]:
                        lines += ["", "Criteria Met:"] + [f"  ✓ {c}" for c in result["criteria_met"]]
                    if result["criteria_remaining"]:
                        lines += ["", "Remaining:"] + [f"  • {c}" for c in result["criteria_remaining"]]
                    output = "\n".join(lines)
                    console.print(Panel(output, title="[cyan]Return-to-Sport Decision[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /return <injury> <weeks_since> <pain_0_10> <strength_deficit_%>[/dim]")
            else:
                console.print("[dim]  Usage: /return <injury> <weeks_since> <pain_0_10> <strength_deficit_%>[/dim]")

        elif q_lower.startswith("/prevent"):
            arg = query[8:].strip()
            if not arg:
                output = list_prevention_protocols()
                console.print(Panel(output, title="[cyan]Prevention Protocols[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                proto = get_prevention_protocol(arg)
                if proto:
                    sport = self.profile.data.get("sport", "general")
                    output = format_prevention_protocol(proto, sport)
                    console.print(Panel(output, title=f"[cyan]{proto.name}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                else:
                    console.print(f"[yellow]  No protocol for '{arg}'. Try /prevent with no args to list available.[/yellow]")

        # ── Female Athlete Health ───────────────────────────────────

        elif q_lower.startswith("/cycle"):
            parts = query[6:].strip().split()
            if not parts:
                lines = ["═══ Menstrual Cycle Phases ═══", ""]
                for phase in CYCLE_PHASES:
                    lines.append(f"  {phase.phase_name}  (days {phase.day_range[0]}-{phase.day_range[1]})")
                output = "\n".join(lines)
                console.print(Panel(output, title="[cyan]Cycle Phases[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                try:
                    day = int(parts[0])
                    sport = parts[1] if len(parts) > 1 else self.profile.data.get("sport", "general")
                    match = match_training_to_phase(day, sport)
                    phase = match["phase"]
                    lines = [
                        f"Day {day} — Phase: {phase.phase_name.replace('_', ' ').title()}",
                        f"Days range: {phase.day_range[0]}-{phase.day_range[1]}",
                        "",
                        f"Focus: {match['recommended_focus']}",
                        f"Intensity modifier: {match['intensity_modifier']}x",
                        "",
                        f"Hormonal: {phase.hormonal_profile}",
                        "",
                        f"Training: {phase.training_recommendations}",
                        "",
                        f"Nutrition: {phase.nutrition_notes}",
                        "",
                        f"Key nutrients: {', '.join(match['key_nutrients'])}",
                        "",
                        f"Injury risk: {match['injury_risk_notes']}",
                    ]
                    output = "\n".join(lines)
                    console.print(Panel(output, title=f"[cyan]Cycle Training — Day {day}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /cycle [day_1-28] [sport][/dim]")

        elif q_lower.startswith("/reds"):
            arg = query[5:].strip()
            if not arg:
                console.print("[dim]  Usage: /reds key=value [key=value ...][/dim]")
                console.print("[dim]  Keys: bmi, menstrual_status, bone_stress_injuries, disordered_eating, weight_loss_pct, mood_disturbance, gi_issues, recurrent_illness, declining_performance, low_energy_availability[/dim]")
            else:
                responses: dict = {}
                for token in arg.split():
                    if "=" not in token:
                        continue
                    k, v = token.split("=", 1)
                    vl = v.lower()
                    if vl in ("true", "yes", "y", "1"):
                        responses[k] = True
                    elif vl in ("false", "no", "n", "0"):
                        responses[k] = False
                    else:
                        try:
                            responses[k] = float(v) if "." in v else int(v)
                        except ValueError:
                            responses[k] = v
                result = screen_reds(responses)
                output = format_reds_report(result)
                console.print(Panel(output, title="[cyan]RED-S Screening[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                self._state["last_output"] = output

        elif q_lower.startswith("/iron"):
            parts = query[5:].strip().split()
            if len(parts) >= 2:
                try:
                    menstrual_status = parts[0]
                    hours = float(parts[1])
                    diet = parts[2] if len(parts) > 2 else "omnivore"
                    result = calculate_iron_needs(menstrual_status, hours, diet)
                    lines = [
                        f"RDA: {result['rda_mg']} mg",
                        f"Recommended: {result['recommended_mg']} mg/day",
                        "",
                        f"Rationale: {result['rationale']}",
                        "",
                        f"Monitoring: {result['monitoring']}",
                    ]
                    output = "\n".join(lines)
                    console.print(Panel(output, title="[cyan]Iron Needs (Female Athlete)[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /iron <menstrual_status> <weekly_hours> [omnivore|vegetarian|vegan][/dim]")
                    console.print("[dim]  menstrual_status: normal, heavy, amenorrheic[/dim]")
            else:
                console.print("[dim]  Usage: /iron <menstrual_status> <weekly_hours> [omnivore|vegetarian|vegan][/dim]")

        elif q_lower.startswith("/postpartum"):
            parts = query[11:].strip().split()
            if len(parts) >= 1:
                try:
                    weeks = int(parts[0])
                    delivery = parts[1] if len(parts) > 1 else "vaginal"
                    complications = parts[2].split(",") if len(parts) > 2 else []
                    result = postpartum_return_protocol(weeks, delivery_type=delivery, complications=complications)
                    lines = [
                        f"Phase: {result.phase}",
                        f"Weeks postpartum: {result.weeks_postpartum}",
                        "",
                        "Exercise Guidelines:",
                    ]
                    lines += [f"  • {g}" for g in result.exercise_guidelines]
                    if result.contraindications:
                        lines += ["", "Contraindications:"] + [f"  ⚠ {c}" for c in result.contraindications]
                    if result.progression_criteria:
                        lines += ["", "Progression Criteria:"] + [f"  • {c}" for c in result.progression_criteria]
                    output = "\n".join(lines)
                    console.print(Panel(output, title="[cyan]Postpartum Return-to-Sport[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /postpartum <weeks> [vaginal|c-section] [comma,sep,complications][/dim]")
            else:
                console.print("[dim]  Usage: /postpartum <weeks> [vaginal|c-section] [comma,sep,complications][/dim]")

        # ── Environmental Factors ───────────────────────────────────

        elif q_lower.startswith("/altitude"):
            parts = query[9:].strip().split()
            if len(parts) >= 1:
                try:
                    target = int(parts[0])
                    current = int(parts[1]) if len(parts) > 1 else 0
                    weeks = int(parts[2]) if len(parts) > 2 else 3
                    sport = parts[3] if len(parts) > 3 else self.profile.data.get("sport", "endurance")
                    result = altitude_training_protocol(target, current, weeks, sport)
                    output = format_altitude_protocol(result)
                    console.print(Panel(output, title="[cyan]Altitude Training[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /altitude <target_m> [current_m] [weeks] [sport][/dim]")
            else:
                console.print("[dim]  Usage: /altitude <target_m> [current_m] [weeks] [sport][/dim]")

        elif q_lower.startswith("/heat"):
            parts = query[5:].strip().split()
            if len(parts) >= 1:
                try:
                    wbgt = float(parts[0])
                    acclim = parts[1].lower() in ("yes", "true", "y", "1") if len(parts) > 1 else False
                    result = heat_acclimatization_protocol(wbgt, acclimatized=acclim)
                    output = format_heat_protocol(result)
                    console.print(Panel(output, title="[cyan]Heat Acclimatization[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /heat <wbgt_celsius> [acclimatized:yes/no][/dim]")
            else:
                console.print("[dim]  Usage: /heat <wbgt_celsius> [acclimatized:yes/no][/dim]")

        elif q_lower.startswith("/cold"):
            parts = query[5:].strip().split()
            if len(parts) >= 1:
                try:
                    temp = float(parts[0])
                    wind = float(parts[1]) if len(parts) > 1 else 0.0
                    precip = parts[2].lower() in ("yes", "true", "y", "1") if len(parts) > 2 else False
                    result = cold_exposure_protocol(temp, wind_speed_kmh=wind, precipitation=precip)
                    output = format_cold_protocol(result)
                    console.print(Panel(output, title="[cyan]Cold Exposure[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /cold <temp_c> [wind_kmh] [precipitation:yes/no][/dim]")
            else:
                console.print("[dim]  Usage: /cold <temp_c> [wind_kmh] [precipitation:yes/no][/dim]")

        elif q_lower.startswith("/airquality"):
            parts = query[11:].strip().split()
            if len(parts) >= 1:
                try:
                    aqi = int(parts[0])
                    result = air_quality_adjustment(aqi)
                    output = format_air_quality(result)
                    console.print(Panel(output, title="[cyan]Air Quality[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /airquality <aqi_0_500>[/dim]")
            else:
                console.print("[dim]  Usage: /airquality <aqi_0_500>[/dim]")

        elif q_lower.startswith("/jetlag"):
            parts = query[7:].strip().split()
            if len(parts) >= 1:
                try:
                    zones = int(parts[0])
                    direction = parts[1] if len(parts) > 1 else "east"
                    result = jet_lag_protocol(zones, direction)
                    output = format_jet_lag(result)
                    console.print(Panel(output, title="[cyan]Jet Lag Protocol[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /jetlag <time_zones> [east|west][/dim]")
            else:
                console.print("[dim]  Usage: /jetlag <time_zones> [east|west][/dim]")

        # ── Mental Performance ──────────────────────────────────────

        elif q_lower.startswith("/anxiety"):
            parts = query[8:].strip().split()
            if len(parts) >= 3:
                try:
                    cog = float(parts[0])
                    som = float(parts[1])
                    conf = float(parts[2])
                    result = assess_competition_anxiety(cog, som, conf)
                    output = format_anxiety_report(result)
                    console.print(Panel(output, title="[cyan]Competition Anxiety[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /anxiety <cognitive_1_4> <somatic_1_4> <confidence_1_4>[/dim]")
            else:
                console.print("[dim]  Usage: /anxiety <cognitive_1_4> <somatic_1_4> <confidence_1_4>[/dim]")

        elif q_lower.startswith("/burnout"):
            arg = query[8:].strip()
            if not arg or " recovery " not in f" {arg} ":
                console.print("[dim]  Usage: /burnout stress k1=v1 k2=v2 ... recovery k3=v3 k4=v4 ...[/dim]")
                console.print("[dim]  Stress keys: general_stress, emotional_stress, social_stress, training_stress, injury_concern (0-6)[/dim]")
                console.print("[dim]  Recovery keys: sleep_quality, social_recovery, physical_recovery, general_wellbeing, self_efficacy (0-6)[/dim]")
            else:
                try:
                    stress_part, recovery_part = arg.split(" recovery ", 1)
                    stress_part = stress_part.replace("stress", "", 1).strip()
                    stress_scores: dict = {}
                    recovery_scores: dict = {}
                    for token in stress_part.split():
                        if "=" in token:
                            k, v = token.split("=", 1)
                            stress_scores[k] = float(v)
                    for token in recovery_part.split():
                        if "=" in token:
                            k, v = token.split("=", 1)
                            recovery_scores[k] = float(v)
                    result = assess_burnout(stress_scores, recovery_scores)
                    output = format_burnout_report(result)
                    console.print(Panel(output, title="[cyan]Burnout Risk[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                except ValueError:
                    console.print("[dim]  Usage: /burnout stress k1=v1 ... recovery k2=v2 ...[/dim]")

        elif q_lower.startswith("/visualize"):
            arg = query[10:].strip()
            if not arg:
                output = list_visualization_protocols()
                console.print(Panel(output, title="[cyan]Visualization Protocols[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            else:
                proto = get_visualization_protocol(arg)
                if proto:
                    output = format_visualization(proto)
                    console.print(Panel(output, title=f"[cyan]{proto.name}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
                    self._state["last_output"] = output
                else:
                    console.print(f"[yellow]  No visualization for '{arg}'. Try /visualize with no args to list available.[/yellow]")

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
