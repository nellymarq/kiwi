"""Sleep-optimization command handlers (Tier 47).

Sync-only. All return None implicitly. Early-exit (return False) used
inside /caffeine for input validation — matches existing dispatcher
pattern (Tier 30 bug fix).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from kiwi_core.tools.sleep_optimizer import (
    CHRONOTYPE_PROFILES,
    athlete_sleep_target,
    caffeine_clearance,
    classify_chronotype,
    format_hormonal_windows,
    optimal_wake_times,
    pre_sleep_protocol,
    sleep_debt_report,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_sleep(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /sleep — sleep-cycle wake-time calculator from bedtime."""
    bedtime = query.split()[1] if len(query.split()) > 1 else "23:00"
    cycles = optimal_wake_times(bedtime)
    kiwi.console.print(Panel(
        cycles.display(),
        title=f"[cyan]Sleep Cycle Calculator[/cyan]  [dim]Bedtime: {bedtime}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def handle_chronotype(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /chronotype — MEQ score or bedtime → chronotype classification."""
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
        kiwi.console.print(f"[dim]  {result['error']}[/dim]")
    else:
        sport = kiwi.profile.data.get("sport", "general")
        target = athlete_sleep_target(sport)
        kiwi.console.print(Panel(
            f"[bold]{result['label']}[/bold]\n\n"
            f"  {result['description']}\n\n"
            f"  Sleep window: {result['sleep_window'][0]} – {result['sleep_window'][1]}\n"
            f"  Peak alertness: {result['peak_alertness'][0]} – {result['peak_alertness'][1]}\n"
            f"  Peak physical performance: {result['peak_physical'][0]} – {result['peak_physical'][1]}\n\n"
            f"  Athlete note: {result['athlete_notes']}\n\n"
            f"  Sleep target ({sport}): {target['optimal_hours']}h optimal / {target['min_hours']}h minimum\n"
            f"  Evidence: {result['evidence']}",
            title="[cyan]Chronotype Analysis[/cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))


def handle_caffeine(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /caffeine — clearance via CYP1A2 pharmacokinetics."""
    parts = query.split()
    if len(parts) >= 3:
        try:
            dose = float(parts[1])
            hours = float(parts[2])
            if dose <= 0 or hours < 0:
                kiwi.console.print("[dim red]  Dose must be positive, hours must be non-negative.[/dim red]")
                return
            fast = len(parts) < 4 or parts[3].lower() != "slow"
            status = caffeine_clearance(dose, hours, fast_metabolizer=fast)
            kiwi.console.print(Panel(
                status.display(),
                title="[cyan]Caffeine Clearance[/cyan]  [dim](CYP1A2 pharmacokinetics)[/dim]",
                border_style="cyan",
                box=box.SIMPLE,
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /caffeine 200 6 [slow][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /caffeine <mg> <hours_since_dose> [slow][/dim]")


def handle_sleepdebt(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /sleepdebt — accumulated sleep debt over N nights."""
    raw = query.split()[1:]
    if raw:
        try:
            nights = [float(h) for h in raw]
            sport = kiwi.profile.data.get("sport", "general")
            target = athlete_sleep_target(sport)
            debt = sleep_debt_report(nights, target_hours=target["optimal_hours"])
            kiwi.console.print(Panel(
                debt.display(),
                title=f"[cyan]Sleep Debt Tracker[/cyan]  [dim]Target: {target['optimal_hours']}h ({sport})[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        except ValueError:
            kiwi.console.print("[dim]  Usage: /sleepdebt 7 6.5 8 7 6[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /sleepdebt 7 6.5 8 7 6[/dim]")


def handle_hormones(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /hormones — hormonal sleep-window reference."""
    kiwi.console.print(Panel(
        format_hormonal_windows(),
        title="[cyan]Hormonal Sleep Windows[/cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def handle_bedtime(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /bedtime — pre-sleep protocol from chronotype + sport."""
    parts = query.split()
    sport = parts[1] if len(parts) > 1 else kiwi.profile.data.get("sport", "general")
    ct_data = kiwi.profile.data.get("chronotype", "bear")
    sleep_t = CHRONOTYPE_PROFILES.get(ct_data, CHRONOTYPE_PROFILES["bear"])["sleep_window"][0]
    protocol = pre_sleep_protocol(chronotype=ct_data, sport=sport, sleep_time=sleep_t)
    kiwi.console.print(Panel(
        protocol,
        title=f"[cyan]Pre-Sleep Protocol[/cyan]  [dim]{ct_data.title()} chronotype · {sport}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
