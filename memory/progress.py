"""
Progress Tracker — Time-series data per client for body metrics and biomarkers.

Stores measurements as JSONL at ~/.kiwi/clients/<name>/progress.jsonl
Each line: {"ts": ISO, "metric": str, "value": float, "unit": str, "note": str}

Enables trending over time: weight cut tracking, ferritin repletion,
testosterone recovery, body fat progression.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import client_manager


KNOWN_METRICS: dict[str, str] = {
    "weight": "kg",
    "body_fat": "%",
    "lean_mass": "kg",
    "waist": "cm",
    "ferritin": "ng/mL",
    "hemoglobin": "g/dL",
    "testosterone": "ng/dL",
    "cortisol": "mcg/dL",
    "vitamin_d": "ng/mL",
    "crp": "mg/L",
    "fasting_insulin": "μIU/mL",
    "hba1c": "%",
    "ldl": "mg/dL",
    "hdl": "mg/dL",
    "triglycerides": "mg/dL",
    "homocysteine": "μmol/L",
    "tsh": "mIU/L",
    "free_t3": "pg/mL",
    "free_t4": "ng/dL",
    "dhea_s": "μg/dL",
    "estradiol": "pg/mL",
    "progesterone": "ng/mL",
    "rhr": "bpm",
    "hrv_rmssd": "ms",
    "vo2max": "mL/kg/min",
    "squat_1rm": "kg",
    "bench_1rm": "kg",
    "deadlift_1rm": "kg",
    "sleep_hours": "hrs",
}


def _progress_path(client: str | None = None) -> Path:
    d = client_manager.get_client_dir(client)
    d.mkdir(parents=True, exist_ok=True)
    return d / "progress.jsonl"


class ProgressTracker:
    """Per-client time-series metric tracking."""

    def __init__(self, client: str | None = None):
        self.client = client

    def record(self, metric: str, value: float, unit: str = "", note: str = ""):
        """Record a single measurement."""
        metric = metric.strip().lower().replace(" ", "_")
        if not unit and metric in KNOWN_METRICS:
            unit = KNOWN_METRICS[metric]
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "metric": metric,
            "value": round(value, 4),
            "unit": unit,
        }
        if note:
            entry["note"] = note[:200]
        path = _progress_path(self.client)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_history(self, metric: str, limit: int = 50) -> list[dict]:
        """Get time-series for a specific metric, most recent first."""
        metric = metric.strip().lower().replace(" ", "_")
        path = _progress_path(self.client)
        if not path.exists():
            return []
        entries = []
        try:
            for line in path.read_text().splitlines():
                if line.strip():
                    try:
                        e = json.loads(line)
                        if e.get("metric") == metric:
                            entries.append(e)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return []
        return entries[-limit:]

    def get_latest(self, metric: str) -> dict | None:
        """Get the most recent value for a metric."""
        history = self.get_history(metric, limit=1)
        return history[-1] if history else None

    def get_all_metrics(self) -> list[str]:
        """List all metrics that have been tracked for this client."""
        path = _progress_path(self.client)
        if not path.exists():
            return []
        metrics = set()
        try:
            for line in path.read_text().splitlines():
                if line.strip():
                    try:
                        e = json.loads(line)
                        metrics.add(e.get("metric", ""))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
        return sorted(m for m in metrics if m)

    def format_trend(self, metric: str, limit: int = 20) -> str:
        """Format a trend report for a metric."""
        history = self.get_history(metric, limit=limit)
        if not history:
            return f"No data for '{metric}'. Track with /track {metric} <value>"

        unit = history[0].get("unit", "")
        lines = [f"Trend: {metric} ({unit})", ""]

        for entry in history:
            date = entry.get("ts", "")[:10]
            val = entry["value"]
            note = entry.get("note", "")
            line = f"  {date}  {val:>8.1f} {unit}"
            if note:
                line += f"  ({note})"
            lines.append(line)

        if len(history) >= 2:
            first = history[0]["value"]
            last = history[-1]["value"]
            change = last - first
            pct = (change / first * 100) if first != 0 else 0
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            lines.append("")
            lines.append(f"  Change: {direction} {abs(change):.1f} {unit} ({pct:+.1f}%)")
            lines.append(f"  From {history[0].get('ts', '')[:10]} to {history[-1].get('ts', '')[:10]}")

        return "\n".join(lines)

    def format_dashboard(self) -> str:
        """One-line latest value for every tracked metric."""
        metrics = self.get_all_metrics()
        if not metrics:
            return "No metrics tracked yet. Use /track <metric> <value>"

        lines = ["Latest measurements:", ""]
        for m in metrics:
            latest = self.get_latest(m)
            if latest:
                date = latest.get("ts", "")[:10]
                val = latest["value"]
                unit = latest.get("unit", "")
                lines.append(f"  {m:<20} {val:>8.1f} {unit:<10} ({date})")
        return "\n".join(lines)
