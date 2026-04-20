"""Supplement and interaction command handlers (Tier 51).

Mixed sync + async. /supp and /supplist are sync; /check and /interact
are async (they await analyze_novel_interactions when novel compounds
are detected). Dispatcher must `await` the async handlers.

This is the first domain with async handlers — pattern established here
for future async domains (Tier 55+ Sports, Literature, Planning, etc.).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.interactions import (
    analyze_novel_interactions,
    format_interaction_report,
    has_novel_compounds,
    lookup_interactions,
    lookup_single,
)
from tools.supplements import (
    format_dosing_protocol,
    list_supplements_by_category,
    resolve_supplement,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_supplist(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /supplist — list supplement DB by category."""
    cat = query[9:].strip() or None
    output = list_supplements_by_category(cat)
    kiwi.console.print(Panel(output, title="[cyan]Supplement Database[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))


def handle_supp(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /supp — dosing protocol for a specific supplement."""
    name = query[6:].strip()
    proto = resolve_supplement(name)
    if proto:
        sport = kiwi.profile.data.get("sport", "general")
        weight = kiwi.profile.get("weight_kg")
        output = format_dosing_protocol(proto, sport, weight_kg=weight)
        kiwi.console.print(Panel(output, title=f"[cyan]{proto.name}[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
    else:
        kiwi.console.print(f"[yellow]  Supplement '{name}' not found. Try /supplist to see all options.[/yellow]")


async def handle_check(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /check — multi-compound interaction check with Claude fallback."""
    raw = query[7:].strip()
    if raw:
        compounds = [c.strip() for c in raw.split() if c.strip()]
        with kiwi.console.status(
            f"[dim cyan]  Checking interactions for: {', '.join(compounds)}...[/dim cyan]",
            spinner="dots2",
        ):
            interactions = lookup_interactions(compounds, min_severity="synergistic")
        report = format_interaction_report(compounds, interactions)
        kiwi.console.print(Panel(
            report,
            title="[cyan]Supplement Interaction Report[/cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))

        novel = has_novel_compounds(compounds)
        if novel:
            kiwi.console.print(f"\n[dim cyan]  Novel compounds detected: {', '.join(novel)}[/dim cyan]")
            kiwi.console.print("[dim cyan]  Running Claude analysis for comprehensive interaction check...[/dim cyan]\n")

            def on_check_text(text: str):
                kiwi.console.print(text, end="", markup=False)

            await analyze_novel_interactions(kiwi.client, compounds, on_text=on_check_text)
            kiwi.console.print("\n")
            kiwi.console.rule("[dim]Claude Interaction Analysis Complete[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /check caffeine creatine melatonin[/dim]")


async def handle_interact(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /interact — single-compound interaction lookup with Claude fallback."""
    compound = query[10:].strip()
    if compound:
        interactions = lookup_single(compound)
        if interactions:
            report = format_interaction_report([compound], interactions)
            kiwi.console.print(Panel(
                report,
                title=f"[cyan]Interactions: {compound.title()}[/cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
        else:
            kiwi.console.print(f"[dim]  No known interactions for '{compound}' in local database.[/dim]")
            kiwi.console.print("[dim cyan]  Running Claude analysis...[/dim cyan]\n")

            def on_interact_text(text: str):
                kiwi.console.print(text, end="", markup=False)

            await analyze_novel_interactions(kiwi.client, [compound], on_text=on_interact_text)
            kiwi.console.print("\n")
            kiwi.console.rule("[dim]Claude Interaction Analysis Complete[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /interact caffeine[/dim]")
