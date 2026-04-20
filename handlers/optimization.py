"""Optimization handlers (Tier 61).

Async. /optimize_stack, /risk_screen, /suggest_research — heavy
data-gathering from profile+progress before invoking agents.
/risk_screen preserves all Tier 31/33/34 autonomous enrichment.
"""
from __future__ import annotations

from datetime import datetime as _dt, timedelta as _td, timezone as _tz
from typing import TYPE_CHECKING

from tools.female_athlete import format_reds_report, screen_reds
from tools.injury_prevention import calculate_acwr, format_acwr_report
from tools.supplements import SUPPLEMENT_DB

if TYPE_CHECKING:
    from kiwi import Kiwi


async def handle_optimize_stack(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /optimize_stack — StackOptimizerAgent with profile + biomarkers + DB context."""
    notes = query[15:].strip() if len(query) > 15 else ""
    profile_summary = kiwi.profile.to_summary()
    current_supps = kiwi.profile.get("current_supplements") or []
    current_stack = ", ".join(current_supps) if current_supps else "none listed"
    goals = kiwi.profile.get("primary_goal") or notes or "general performance"

    db_lines = []
    for key, proto in SUPPLEMENT_DB.items():
        db_lines.append(
            f"• {proto.name} ({key}) — {proto.evidence} — "
            f"{proto.maintenance_dose} — {proto.mechanism[:100]}"
        )
    db_summary = "\n".join(db_lines)

    biomarker_lines = []
    for m in kiwi.progress.get_all_metrics():
        latest = kiwi.progress.get_latest(m)
        if latest:
            biomarker_lines.append(f"  {m}: {latest['value']} {latest.get('unit', '')} ({latest.get('ts', '')[:10]})")
    biomarker_text = "\n".join(biomarker_lines) if biomarker_lines else "No biomarker data tracked"

    kiwi.console.print("[dim]  Analyzing profile + biomarkers + supplement DB + interactions...[/dim]\n")
    result = await kiwi.stack_optimizer_agent.run({
        "profile_summary": profile_summary,
        "goals": goals,
        "biomarker_data": biomarker_text,
        "current_stack": current_stack,
        "supplement_db_summary": db_summary,
        "interaction_data": "",
    })
    kiwi._state["last_output"] = result
    kiwi.console.print(result)


async def handle_risk_screen(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /risk_screen — RiskScreenAgent with full Tier 31/33/34 autonomous enrichment."""
    notes_raw = query[12:].strip() if len(query) > 12 else ""
    profile_summary = kiwi.profile.to_summary()

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

    biomarker_lines = []
    for m in kiwi.progress.get_all_metrics():
        latest = kiwi.progress.get_latest(m)
        if latest:
            biomarker_lines.append(f"  {m}: {latest['value']} {latest.get('unit', '')} ({latest.get('ts', '')[:10]})")
    biomarker_text = "\n".join(biomarker_lines) if biomarker_lines else "No biomarker data tracked"

    progress_lines = []
    for m in ["weight", "rhr", "hrv_rmssd", "sleep_hours"]:
        history = kiwi.progress.get_history(m, limit=7)
        if history:
            vals = [h["value"] for h in history]
            progress_lines.append(f"  {m} (last {len(vals)} readings): {' → '.join(f'{v:.1f}' for v in vals)}")
    progress_text = "\n".join(progress_lines) if progress_lines else "No progress trends available"

    # Autonomous ACWR enrichment (Tier 34)
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

    # Autonomous RED-S enrichment (Tier 31 + Tier 33 profile-fill)
    reds_screening_text = ""
    clinical_keys = {"menstrual_status", "bmi", "bone_stress_injuries", "disordered_eating"}
    if kiwi.profile.data.get("sex") == "female":
        profile_ms = kiwi.profile.data.get("menstrual_status")
        if profile_ms and "menstrual_status" not in reds_responses:
            reds_responses["menstrual_status"] = profile_ms
        if "bone_stress_injuries" not in reds_responses:
            injury_history = kiwi.profile.data.get("injury_history") or []
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

    kiwi.console.print("[dim]  Running comprehensive risk screening...[/dim]\n")
    result = await kiwi.risk_screen_agent.run({
        "profile_summary": profile_summary,
        "biomarker_data": biomarker_text,
        "progress_data": progress_text,
        "training_load": training_load_text,
        "notes": notes,
        "reds_screening": reds_screening_text,
    })
    kiwi._state["last_output"] = result
    kiwi.console.print(result)


async def handle_suggest_research(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /suggest_research — QuestionGenAgent with profile + biomarkers + history."""
    profile_summary = kiwi.profile.to_summary()
    current_supps = kiwi.profile.get("current_supplements") or []

    biomarker_lines = []
    for m in kiwi.progress.get_all_metrics():
        latest = kiwi.progress.get_latest(m)
        if latest:
            biomarker_lines.append(f"  {m}: {latest['value']} {latest.get('unit', '')}")
    biomarker_text = "\n".join(biomarker_lines) if biomarker_lines else ""

    recent = kiwi.memory.get_recent_episodic(10)
    recent_text = "\n".join(
        f"  [{e.get('ts', '')[:10]}] {e.get('query', '')[:150]}"
        for e in recent
    ) if recent else "No prior research for this client"

    progress_lines = []
    for m in kiwi.progress.get_all_metrics():
        history = kiwi.progress.get_history(m, limit=5)
        if len(history) >= 2:
            first = history[0]["value"]
            last = history[-1]["value"]
            change = last - first
            progress_lines.append(f"  {m}: {first:.1f} → {last:.1f} ({change:+.1f})")
    progress_text = "\n".join(progress_lines) if progress_lines else ""

    kiwi.console.print("[dim]  Analyzing data to generate research suggestions...[/dim]\n")
    result = await kiwi.question_gen_agent.run({
        "profile_summary": profile_summary,
        "biomarker_data": biomarker_text,
        "current_stack": ", ".join(current_supps) if current_supps else "none",
        "recent_research": recent_text,
        "progress_data": progress_text,
    })
    kiwi._state["last_output"] = result
    kiwi.console.print(result)
