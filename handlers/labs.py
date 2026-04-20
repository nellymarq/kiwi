"""Blood panel / biomarker command handlers (Tier 50).

Sync-only. All return None implicitly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.biomarkers import interpret_panel

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_labs(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /labs — interpret multi-marker blood panel."""
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
                kiwi.console.print(f"[dim red]  Invalid value for {name_part}: {raw[i+1]}[/dim red]")
                valid = False
                break
        if valid and panel:
            sex = kiwi.profile.data.get("sex", "male")
            athlete_name = kiwi.profile.data.get("name", "")
            report = interpret_panel(panel, sex=sex, athlete_name=athlete_name)
            kiwi.console.print(Panel(
                report,
                title="[cyan]Blood Panel Analysis[/cyan]  [dim]USDA / Clinical Reference[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 2),
            ))
    else:
        kiwi.console.print("[dim]  Usage: /labs ferritin 25 vitamin_d 35 cortisol 12[/dim]")


def handle_biomarker(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /biomarker — single-marker interpretation via BiomarkerInterpreter."""
    parts = query.split(maxsplit=2)
    if len(parts) == 3:
        try:
            name_part = parts[1]
            val = float(parts[2])
            sex = kiwi.profile.data.get("sex", "male")
            result = kiwi.bio_interp.interpret(name_part, val, sex=sex)
            if result:
                kiwi.console.print(Panel(
                    result.display() +
                    (f"\n\n  Evidence: {result.ref.evidence}" if result.ref.evidence else ""),
                    title=f"[cyan]Biomarker[/cyan]  {result.name}",
                    border_style="cyan",
                    box=box.SIMPLE,
                ))
            else:
                kiwi.console.print(f"[dim]  '{name_part}' not in biomarker database. Try: ferritin, testosterone, vitamin_d, cortisol, crp...[/dim]")
        except ValueError:
            kiwi.console.print("[dim]  Usage: /biomarker ferritin 45[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /biomarker ferritin 45[/dim]")
