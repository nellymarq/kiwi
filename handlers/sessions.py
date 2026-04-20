"""Session-persistence command handlers (Tier 65).

Sync. /save_session, /resume_session, /sessions, /log (alias /history).
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from memory.session_log import log_stats
from memory.sessions import list_sessions, load_session, save_session

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_save_session(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /save_session [label] — persist current conversation."""
    label = query[13:].strip() if len(query) > 13 else ""
    if not kiwi.messages:
        kiwi.console.print("[dim]  No conversation to save.[/dim]")
    else:
        session_id = label or datetime.now().strftime("%Y%m%d_%H%M%S")
        last_q = kiwi._state.get("last_query") or ""
        summary = last_q[:200] if last_q else ""
        save_session(
            session_id=session_id,
            messages=kiwi.messages,
            thread=kiwi.active_thread,
            summary=summary,
            client=kiwi.active_client_name,
        )
        kiwi.console.print(f"[dim]  Session saved: [cyan]{session_id}[/cyan] ({len(kiwi.messages)} messages)[/dim]")


def handle_resume_session(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /resume_session <id> — restore saved conversation."""
    offset = 16 if q_lower.startswith("/resume_session") else 8
    session_id = query[offset:].strip()
    if not session_id:
        kiwi.console.print("[dim]  Usage: /resume_session <session_id> (see /sessions for list)[/dim]")
    else:
        data = load_session(session_id, client=kiwi.active_client_name)
        if data:
            kiwi.messages = data.get("messages", [])
            if data.get("thread"):
                kiwi.active_thread = data["thread"]
            kiwi.console.print(
                f"[dim]  Resumed session: [cyan]{session_id}[/cyan] "
                f"({data.get('message_count', 0)} messages, "
                f"saved {data.get('saved_at', '')[:10]})[/dim]"
            )
            if data.get("summary"):
                kiwi.console.print(f"[dim]  Last topic: {data['summary']}[/dim]")
        else:
            kiwi.console.print(f"[dim red]  Session '{session_id}' not found.[/dim red]")


def handle_sessions(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /sessions — list all saved sessions for the active client."""
    sessions = list_sessions(client=kiwi.active_client_name)
    if not sessions:
        kiwi.console.print("[dim]  No saved sessions. Use /save_session [label] to save.[/dim]")
    else:
        lines = []
        for s in sessions:
            lines.append(
                f"  [cyan]{s['session_id']}[/cyan] — "
                f"{s.get('saved_at', '')[:16]} · "
                f"{s['message_count']} msgs"
                + (f" · {s['summary'][:60]}" if s.get("summary") else "")
            )
        kiwi.console.print(Panel(
            "\n".join(lines),
            title="[cyan]Saved Sessions[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))


def handle_log(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /log (alias /history) — research log stats."""
    stats = log_stats(client=kiwi.active_client_name)
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
    kiwi.console.print(Panel(
        "\n".join(lines),
        title="[cyan]Client Research Log[/cyan]",
        border_style="cyan", box=box.SIMPLE,
    ))
