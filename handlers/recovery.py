"""Recovery command handlers (Tier 48).

Sync-only. All return None implicitly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from kiwi_core.tools.recovery import (
    EXERCISE_DAMAGE_COEFFICIENTS,
    HRVReading,
    assess_deload_need,
    compute_readiness,
    estimate_doms,
    format_readiness_report,
    mps_timing_guide,
    recovery_modality_guide,
    supercompensation_window,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_readiness(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /readiness — HRV-based readiness score."""
    raw = query.split()[1:]
    if raw:
        try:
            rmssd_vals = [float(v) for v in raw]
            hrv_readings = [HRVReading(rmssd=v, resting_hr=60.0) for v in rmssd_vals]
            tsb = kiwi._last_tsb if hasattr(kiwi, "_last_tsb") else None
            sleep_debt = kiwi.profile.data.get("sleep_debt_hours", 0.0)
            r = compute_readiness(hrv_readings, tsb=tsb, sleep_debt_hours=sleep_debt)
            kiwi.console.print(Panel(
                format_readiness_report(r),
                title=f"[cyan]HRV Readiness[/cyan]  [dim]Score: {r.score:.0f}/100[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /readiness 55 58 52 61 64  (rMSSD values oldest→newest)[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /readiness <rmssd1> <rmssd2> ...  (at least 2 values)[/dim]")


def handle_doms(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /doms — DOMS severity by session type + RPE + duration."""
    parts = query.split(maxsplit=3)
    if len(parts) >= 4:
        try:
            session_type = parts[1]
            rpe = float(parts[2])
            minutes = int(parts[3].split()[0])
            trained = kiwi.profile.data.get("training_status", "trained")
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
            kiwi.console.print(Panel(
                "\n".join(lines),
                title="[cyan]DOMS Estimate[/cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except (ValueError, IndexError):
            kiwi.console.print("[dim]  Usage: /doms strength_eccentric_heavy 8 60\n"
                          "  Types: strength_eccentric_heavy, plyometrics, running_new, cycling, swimming...[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /doms <session_type> <rpe> <duration_min>[/dim]\n"
                      "[dim]  Types: " + ", ".join(list(EXERCISE_DAMAGE_COEFFICIENTS.keys())[:4]) + "...[/dim]")


def handle_supercomp(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /supercomp — supercompensation window by session type + hours elapsed."""
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
            kiwi.console.print(Panel(
                "\n".join(lines),
                title="[cyan]Supercompensation Window[/cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /supercomp strength 24  (type, hours since session)[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /supercomp <strength|endurance|high_intensity_interval|team_sport> <hours_ago>[/dim]")


def handle_deload(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /deload — deload-need assessment from TSB + fatigue signals."""
    parts = query.split()
    try:
        tsb = float(parts[1]) if len(parts) > 1 else None
        hard_days = int(parts[2]) if len(parts) > 2 else 0
        weeks = int(parts[3]) if len(parts) > 3 else 0
        sleep_debt = kiwi.profile.data.get("sleep_debt_hours", 0.0)
        subj = kiwi.profile.data.get("subjective_fatigue")
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
            lines.append("\nTriggers:")
            for t in d.triggered_by:
                lines.append(f"  • {t}")
            lines.append("\nGuidance:")
            for g in d.deload_guidance:
                lines.append(f"  • {g}")
        lines.append(f"\nEvidence: {d.evidence}")
        kiwi.console.print(Panel(
            "\n".join(lines),
            title="[cyan]Deload Assessment[/cyan]",
            border_style="cyan" if not d.should_deload else "yellow",
            box=box.ROUNDED,
            padding=(0, 2),
        ))
    except ValueError:
        kiwi.console.print("[dim]  Usage: /deload [tsb] [consecutive_hard_days] [weeks_since_deload][/dim]")


def handle_recover(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /recover — recovery modality guide by goal + session type."""
    parts = query.split()
    goal = parts[1] if len(parts) > 1 else "general"
    session_type = parts[2] if len(parts) > 2 else "strength"
    guide = recovery_modality_guide(goal=goal, post_session_type=session_type)
    kiwi.console.print(Panel(
        guide,
        title=f"[cyan]Recovery Modalities[/cyan]  [dim]Goal: {goal} | Post: {session_type}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def handle_mps(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /mps — muscle protein synthesis timing guide."""
    parts = query.split()
    weight = float(parts[1]) if len(parts) > 1 else kiwi.profile.data.get("weight_kg", 75.0)
    guide = mps_timing_guide(body_weight_kg=float(weight))
    kiwi.console.print(Panel(
        guide,
        title=f"[cyan]MPS Timing Guide[/cyan]  [dim]{weight:.0f}kg[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
