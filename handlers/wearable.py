"""Wearable import command handlers (Tier 59).

Sync. /oura syncs OuraClient, /import_wearable parses file, /import_labs
records markers into progress tracker (with proactive biomarker check).
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.oura import OuraClient
from tools.proactive import check_biomarker, format_proactive_actions
from tools.wearable_import import format_import_result, import_file as import_wearable_file

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_oura(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /oura sync — pull recent days from Oura Ring into progress tracker."""
    subcmd = query[6:].strip().lower()
    if subcmd.startswith("sync"):
        token = kiwi.config.get("oura_token", "") or os.environ.get("OURA_TOKEN", "")
        if not token:
            kiwi.console.print(
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
            kiwi.console.print(f"[dim]  Syncing last {days} days from Oura Ring...[/dim]")
            oura = OuraClient(token)
            summaries = oura.sync_days(days_back=days)
            if summaries:
                kiwi.console.print(Panel(
                    oura.format_sync_report(summaries),
                    title="[cyan]Oura Ring Sync[/cyan]",
                    border_style="cyan", box=box.SIMPLE,
                ))
                imported = 0
                for s in summaries:
                    for metric, value in s.to_metrics().items():
                        kiwi.progress.record(metric, value, note="oura sync")
                        imported += 1
                kiwi.console.print(f"[dim]  {imported} data points imported to progress tracker[/dim]")
            else:
                kiwi.console.print("[dim red]  No data returned. Check your token and try again.[/dim red]")
    else:
        kiwi.console.print("[dim]  Usage: /oura sync [days]  (default: 7 days)[/dim]")


def handle_import_wearable(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /import_wearable — parse CSV/JSON file into progress tracker."""
    filepath = query[17:].strip()
    if filepath:
        records, result = import_wearable_file(filepath)
        kiwi.console.print(Panel(
            format_import_result(result),
            title="[cyan]Wearable Import[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))
        if records:
            for r in records:
                kiwi.progress.record(r["metric"], r["value"], note=f"import {result.format_detected}")
            kiwi.console.print(f"[dim]  {len(records)} data points added to progress tracker[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /import_wearable <path/to/file.csv or .json>[/dim]")


def handle_import_labs(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /import_labs — bulk-record biomarker values with proactive biomarker checks."""
    parts = query[12:].strip().split()
    if len(parts) < 2 or len(parts) % 2 != 0:
        kiwi.console.print("[dim]  Usage: /import_labs <marker1> <val1> <marker2> <val2> ...[/dim]")
    else:
        imported = 0
        all_actions = []
        sex = kiwi.profile.get("sex") or "male"
        current_supps = kiwi.profile.get("current_supplements") or []
        for i in range(0, len(parts), 2):
            metric = parts[i].lower().replace(" ", "_")
            try:
                value = float(parts[i + 1])
                kiwi.progress.record(metric, value)
                imported += 1
                actions = check_biomarker(metric, value, sex=sex, current_supplements=current_supps)
                all_actions.extend(actions)
            except ValueError:
                kiwi.console.print(f"[dim red]  Skipped {metric}: '{parts[i+1]}' is not numeric[/dim red]")
        kiwi.console.print(f"[dim]  Imported {imported} biomarkers[/dim]")
        if all_actions:
            kiwi.console.print()
            kiwi.console.print(format_proactive_actions(all_actions))
