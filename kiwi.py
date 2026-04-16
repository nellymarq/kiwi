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
    list_prevention_protocols, PROTOCOL_DB,
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
    format_jet_lag,
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
from tools.supplements import resolve_supplement, SUPPLEMENT_DB
from tools.interactions import lookup_interactions

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
                if self.active_client_name and self.active_client_name != "self":
                    prompt += f"[dim] ({self.active_client_name})[/dim]"
                if self.active_thread:
                    prompt += f"[dim] [{self.active_thread}][/dim]"
                prompt += "[bold cyan] >[/bold cyan] "
                query = console.input(prompt).strip()

                if not query:
                    continue

                q_lower = query.lower()

                # ── Help Command ────────────────────────────────────────────

                if q_lower in ("/help", "/commands"):
                    help_text = (
                        "[bold]Research:[/bold]  Just type a question · /protocol <query> · /plan <query>\n"
                        "[bold]Literature:[/bold] /pubmed · /openalex · /trials · /tldr · /fulltext <doi> · /citedby <doi>\n"
                        "[bold]Deep Research:[/bold] /synthesize <claim> · /n_of_1 <q> · /grade · /quality · /recommend <finding>\n"
                        "[bold]Delivery:[/bold]  /pdf · /accepted [note] · /rejected [reason] · /preferences\n"
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
                        "[bold]Session:[/bold]  /clear · /new · /quit"
                    )
                    console.print(Panel(
                        help_text,
                        title="[cyan]Kiwi Commands[/cyan]",
                        border_style="cyan",
                        box=box.SIMPLE,
                    ))

                # ── Session Commands ────────────────────────────────────────

                elif q_lower in ("/quit", "/exit", "quit", "exit"):
                    console.print(
                        f"\n[dim]  Session #{session_num} complete. "
                        f"Memory saved to {Path.home() / '.kiwi'}[/dim]"
                    )
                    break

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
                            console.print(result)

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
                        console.print(result)

                elif q_lower == "/pdf" or q_lower.startswith("/pdf "):
                    if not last_response:
                        console.print("[dim]  No research session to export yet.[/dim]")
                    else:
                        practitioner = self.profile.get("name") or ""
                        brand = BrandConfig(practitioner=practitioner)
                        grade_level = ""
                        score_val = last_score or 0.0
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
                                query=last_query,
                                response=last_response,
                                score=score_val,
                                critique_data=last_critique or {},
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

                        # Invoke recommender agent
                        console.print("[dim]  Synthesizing integrated recommendation...[/dim]\n")
                        result = await self.recommender_agent.run({
                            "finding": finding,
                            "profile_summary": profile_summary,
                            "biomarker_interpretation": "",
                            "supplement_options": supp_options,
                            "interaction_check": interaction_text,
                        })
                        console.print(result)

                elif q_lower.startswith("/accepted"):
                    payload = query[9:].strip() if len(query) > 9 else ""
                    rec_text = last_response[:500] if last_response else ""
                    if not rec_text:
                        console.print("[dim]  No recent recommendation to mark accepted.[/dim]")
                    else:
                        self.preferences.record_accepted(rec_text, note=payload)
                        console.print(f"[dim]  Recorded as accepted. Total: {self.preferences.stats()['total_accepted']}[/dim]")

                elif q_lower.startswith("/rejected"):
                    payload = query[9:].strip() if len(query) > 9 else ""
                    rec_text = last_response[:500] if last_response else ""
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
                        continue

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
                                continue
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
                            continue
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
                                continue
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
                        output = format_dosing_protocol(proto, sport)
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
