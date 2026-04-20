"""Intel / daily-workflow command handlers (Tier 62).

Sync for most (/template, /frontiers, /freshness, /macros, /capabilities,
/timing, /retest_due, /gaps, /weekly_report). Async for /brief (invokes
daily_brief_agent) with Tier 34/38 autonomous enrichment.
"""
from __future__ import annotations

from datetime import datetime as _dt, timedelta as _td, timezone as _tz
from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.female_athlete import format_cycle_training, format_reds_report, match_training_to_phase, screen_reds
from tools.freshness import format_freshness_report
from tools.injury_prevention import calculate_acwr, format_acwr_report
from tools.knowledge_frontier import analyze_frontiers, format_frontiers
from tools.nutrient_gaps import analyze_gaps, format_gap_analysis
from tools.pdf_export import BrandConfig, generate_client_report
from tools.protocol_templates import get_template, list_templates
from tools.timing_schedule import check_separation_conflicts, format_timing_schedule, generate_timing_schedule

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_template(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /template — list or lookup a protocol template."""
    name = query[9:].strip() if len(query) > 9 else ""
    if not name:
        kiwi.console.print(Panel(
            list_templates(),
            title="[cyan]Protocol Templates[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))
    else:
        tmpl = get_template(name)
        if tmpl:
            kiwi.console.print(Panel(
                tmpl.content,
                title=f"[cyan]{tmpl.name}[/cyan]",
                subtitle=f"[dim]{tmpl.duration} · {tmpl.category}[/dim]",
                border_style="cyan", box=box.SIMPLE,
            ))
        else:
            kiwi.console.print(f"[dim red]  Template '{name}' not found. Use /template to list.[/dim red]")


def handle_frontiers(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /frontiers — research frontier gap analysis."""
    profile_data = kiwi.profile.to_dict()
    tracked = {}
    for m in kiwi.progress.get_all_metrics():
        history = kiwi.progress.get_history(m, limit=50)
        tracked[m] = [h["value"] for h in history]
    research_queries = [
        e.get("query", "").lower()
        for e in kiwi.memory.get_recent_episodic(50)
    ]
    gaps = analyze_frontiers(profile_data, tracked, research_queries)
    kiwi.console.print(Panel(
        format_frontiers(gaps),
        title="[cyan]Research Frontiers[/cyan]",
        border_style="cyan", box=box.SIMPLE,
    ))


def handle_freshness(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /freshness — evidence freshness report."""
    output = format_freshness_report()
    kiwi.console.print(Panel(
        output,
        title="[cyan]Evidence Freshness[/cyan]",
        border_style="cyan", box=box.SIMPLE,
    ))


async def handle_brief(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /brief — daily brief with Tier 34/38 autonomous enrichment."""
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

    if cycle_day is None:
        cycle_day = kiwi.profile.get_current_cycle_day()

    profile_summary = kiwi.profile.to_summary()

    progress_lines = []
    for m in kiwi.progress.get_all_metrics():
        history = kiwi.progress.get_history(m, limit=7)
        if history:
            latest = history[-1]
            vals = [h["value"] for h in history]
            direction = "↑" if len(vals) > 1 and vals[-1] > vals[0] else "↓" if len(vals) > 1 and vals[-1] < vals[0] else "→"
            progress_lines.append(
                f"  {m}: {latest['value']:.1f} {latest.get('unit', '')} {direction} "
                f"(last {len(vals)})")
    progress_text = "\n".join(progress_lines) if progress_lines else "No progress data"

    interventions_text = kiwi.interventions.format_active()

    profile_data = kiwi.profile.to_dict()
    tracked = {}
    for m in kiwi.progress.get_all_metrics():
        history = kiwi.progress.get_history(m, limit=10)
        tracked[m] = [h["value"] for h in history]
    research_queries = [e.get("query", "").lower() for e in kiwi.memory.get_recent_episodic(20)]
    frontier_gaps = analyze_frontiers(profile_data, tracked, research_queries)
    gaps_text = "\n".join(
        f"  [{g.priority}] {g.topic}" for g in frontier_gaps[:5]
    ) if frontier_gaps else "No critical gaps"

    retest_text = kiwi.interventions.format_retest_due()

    supplements = kiwi.profile.get("current_supplements") or []
    timing_text = ""
    if supplements:
        schedule = generate_timing_schedule(supplements)
        timing_text = format_timing_schedule(schedule)

    # Autonomous enrichment 1: ACWR when ≥7 distinct days of load in last 14
    training_load_text = ""
    raw_loads = kiwi.progress.get_history("training_load", limit=200)
    if raw_loads:
        raw_loads.sort(key=lambda e: e.get("ts", ""))
        by_day: dict = {}
        for e in raw_loads:
            day = str(e.get("ts", ""))[:10]
            if day:
                by_day[day] = by_day.get(day, 0.0) + float(e.get("value", 0.0))
        today = _dt.now(_tz.utc).date()
        recent_window_days = {(today - _td(days=i)).isoformat() for i in range(14)}
        recent_days_with_load = [d for d in by_day if d in recent_window_days]
        if len(recent_days_with_load) >= 7:
            sorted_days = sorted(by_day.keys())
            last_28 = sorted_days[-28:]
            daily_loads = [by_day[d] for d in last_28]
            acwr_result = calculate_acwr(daily_loads, acute_window=7, chronic_window=28)
            training_load_text = format_acwr_report(acwr_result)

    # Autonomous enrichment 2: RED-S from profile
    reds_screening_text = ""
    if kiwi.profile.data.get("sex") == "female":
        reds_responses: dict = {}
        profile_ms = kiwi.profile.data.get("menstrual_status")
        if profile_ms and profile_ms != "not_applicable":
            reds_responses["menstrual_status"] = profile_ms
        injury_history = kiwi.profile.data.get("injury_history") or []
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

    # Autonomous enrichment 3: cycle_phase
    cycle_phase_context_text = ""
    if cycle_day is not None and kiwi.profile.data.get("sex") == "female":
        try:
            sport_ctx = kiwi.profile.data.get("sport", "general")
            phase_info = match_training_to_phase(cycle_day, sport_ctx)
            phase_obj = phase_info["phase"]
            cycle_phase_context_text = (
                f"Menstrual cycle phase analysis (Kiwi tool, day {cycle_day}):\n"
                f"{format_cycle_training(phase_obj)}"
            )
        except (ValueError, KeyError):
            cycle_phase_context_text = ""

    kiwi.console.print("[dim]  Generating daily brief...[/dim]\n")
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
    kiwi._state["last_output"] = await kiwi.daily_brief_agent.run(brief_context)
    kiwi.console.print(kiwi._state["last_output"])

    if timing_text and supplements:
        kiwi.console.print(f"\n[dim]{timing_text}[/dim]")


def handle_macros(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /macros — training-day vs rest-day macro periodization table."""
    missing = [f for f in ("weight_kg", "height_cm", "age", "sex", "activity_level")
               if not kiwi.profile.get(f)]
    if missing:
        kiwi.console.print(f"[dim]  Missing: {', '.join(missing)}[/dim]")
        return
    try:
        m = kiwi.calc.compute_full_metrics(
            weight_kg=kiwi.profile.get("weight_kg"),
            height_cm=kiwi.profile.get("height_cm"),
            age=kiwi.profile.get("age"),
            sex=kiwi.profile.get("sex"),
            activity_level=kiwi.profile.get("activity_level"),
            body_fat_pct=kiwi.profile.get("body_fat_pct"),
        )
        goal = kiwi.profile.get("primary_goal") or "performance"
        macros = kiwi.calc.macro_periodization(
            weight_kg=kiwi.profile.get("weight_kg"),
            tdee=m.tdee,
            sex=kiwi.profile.get("sex"),
            goal=goal,
        )
        td = macros["training_day"]
        rd = macros["rest_day"]
        lines = [
            f"Macro Periodization — {kiwi.profile.get('weight_kg'):.0f}kg · {goal}",
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
        kiwi.console.print(Panel("\n".join(lines), title="[cyan]Macro Periodization[/cyan]",
                            border_style="cyan", box=box.SIMPLE))
    except Exception as e:
        kiwi.console.print(f"[dim red]  Error: {e}[/dim red]")


def handle_weekly_report(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /weekly_report — PDF export of client progress summary."""
    profile_summary = kiwi.profile.to_summary()

    progress_lines = []
    for m in kiwi.progress.get_all_metrics():
        history = kiwi.progress.get_history(m, limit=30)
        if history:
            trend = kiwi.progress.format_trend(m, limit=10)
            progress_lines.append(trend)
    progress_text = "\n\n".join(progress_lines) if progress_lines else "No progress data tracked"

    interventions_text = kiwi.interventions.format_active()
    retest_text = kiwi.interventions.format_retest_due()
    dashboard = kiwi.progress.format_dashboard()

    report_content = (
        f"Weekly Progress Report\n"
        f"Client: {kiwi.active_client_name}\n"
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
        practitioner = kiwi.profile.get("name") or ""
        brand = BrandConfig(practitioner=practitioner)
        pdf_path = generate_client_report(
            query=f"Weekly Report — {kiwi.active_client_name}",
            response=report_content,
            score=0.0,
            critique_data={},
            brand=brand,
            client_name=kiwi.active_client_name,
        )
        kiwi.console.print(f"[dim]  Weekly report exported: [cyan]{pdf_path}[/cyan][/dim]")
    except Exception as e:
        kiwi.console.print(f"[dim red]  Report failed: {e}[/dim red]")


def handle_capabilities(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /capabilities — categorized command reference."""
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
    kiwi.console.print(Panel(caps, title="[bold cyan]Kiwi Capabilities[/bold cyan]",
                        border_style="cyan", box=box.ROUNDED))


def handle_timing(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /timing — daily supplement timing + conflict check."""
    supplements = kiwi.profile.get("current_supplements") or []
    if not supplements:
        kiwi.console.print("[dim]  No supplements on file. Set with /profile set current_supplements creatine,caffeine,...[/dim]")
    else:
        schedule = generate_timing_schedule(supplements)
        conflicts = check_separation_conflicts(supplements)
        kiwi.console.print(Panel(
            format_timing_schedule(schedule, conflicts),
            title="[cyan]Daily Supplement Timing[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))


def handle_retest_due(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /retest_due — biomarker retest alerts."""
    output = kiwi.interventions.format_retest_due()
    kiwi.console.print(Panel(
        output,
        title="[cyan]Biomarker Retests Due[/cyan]",
        border_style="cyan", box=box.SIMPLE,
    ))


def handle_gaps(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /gaps — nutrient gap analysis from profile."""
    sex = kiwi.profile.get("sex") or "male"
    sport = kiwi.profile.get("sport") or ""
    restrictions = kiwi.profile.get("dietary_restrictions") or []
    supplements = kiwi.profile.get("current_supplements") or []
    conditions = kiwi.profile.get("health_conditions") or []

    gaps = analyze_gaps(
        sex=sex, sport=sport,
        dietary_restrictions=restrictions,
        current_supplements=supplements,
        health_conditions=conditions,
    )
    kiwi.console.print(Panel(
        format_gap_analysis(gaps),
        title="[cyan]Nutrient Gap Analysis[/cyan]",
        border_style="cyan", box=box.SIMPLE,
    ))
