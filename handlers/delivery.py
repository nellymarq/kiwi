"""Delivery / export command handlers (Tier 64).

Sync. /pdf, /pdf_last, /accepted, /rejected, /preferences.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.pdf_export import BrandConfig, generate_client_report

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_pdf_last(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /pdf_last — export the last command output to PDF."""
    if not kiwi._state["last_output"]:
        kiwi.console.print("[dim]  No command output to export. Run a command first.[/dim]")
    else:
        try:
            practitioner = kiwi.profile.get("name") or ""
            brand = BrandConfig(practitioner=practitioner)
            pdf_path = generate_client_report(
                query=kiwi._state["last_query"] or "Command Output",
                response=kiwi._state["last_output"],
                score=kiwi._state["last_score"],
                critique_data={},
                brand=brand,
                client_name=kiwi.active_client_name,
            )
            kiwi.console.print(f"[dim]  PDF exported: [cyan]{pdf_path}[/cyan][/dim]")
        except Exception as e:
            kiwi.console.print(f"[dim red]  PDF export failed: {e}[/dim red]")


def handle_pdf(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /pdf — export last research session with GRADE badge."""
    if not kiwi._state["last_response"]:
        kiwi.console.print("[dim]  No research session to export yet.[/dim]")
    else:
        practitioner = kiwi.profile.get("name") or ""
        brand = BrandConfig(practitioner=practitioner)
        grade_level = ""
        score_val = kiwi._state["last_score"] or 0.0
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
                query=kiwi._state["last_query"],
                response=kiwi._state["last_response"],
                score=score_val,
                critique_data=kiwi._state["last_critique"] or {},
                brand=brand,
                client_name=kiwi.active_client_name,
                grade_level=grade_level,
                thread_name=kiwi.active_thread,
            )
            kiwi.console.print(f"[dim]  PDF exported to: [cyan]{pdf_path}[/cyan][/dim]")
        except Exception as e:
            kiwi.console.print(f"[dim red]  PDF export failed: {e}[/dim red]")


def handle_accepted(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /accepted — mark last recommendation as accepted with optional note."""
    payload = query[9:].strip() if len(query) > 9 else ""
    rec_text = kiwi._state["last_response"][:500] if kiwi._state["last_response"] else ""
    if not rec_text:
        kiwi.console.print("[dim]  No recent recommendation to mark accepted.[/dim]")
    else:
        kiwi.preferences.record_accepted(rec_text, note=payload)
        kiwi.console.print(f"[dim]  Recorded as accepted. Total: {kiwi.preferences.stats()['total_accepted']}[/dim]")


def handle_rejected(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /rejected — mark last recommendation as rejected with optional reason."""
    payload = query[9:].strip() if len(query) > 9 else ""
    rec_text = kiwi._state["last_response"][:500] if kiwi._state["last_response"] else ""
    if not rec_text:
        kiwi.console.print("[dim]  No recent recommendation to mark rejected.[/dim]")
    else:
        kiwi.preferences.record_rejected(rec_text, reason=payload)
        kiwi.console.print(f"[dim]  Recorded as rejected. Total: {kiwi.preferences.stats()['total_rejected']}[/dim]")


def handle_preferences(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /preferences — show accept/reject stats + context block."""
    stats = kiwi.preferences.stats()
    block = kiwi.preferences.to_context_block()
    kiwi.console.print(Panel(
        f"Accepted: {stats['total_accepted']}  ·  Rejected: {stats['total_rejected']}\n\n"
        + (block or "[dim]No preferences recorded yet.[/dim]"),
        title="[cyan]Recommendation Preferences[/cyan]",
        border_style="cyan",
        box=box.SIMPLE,
    ))
