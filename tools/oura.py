"""
Oura Ring API Client — Pull sleep, HRV, readiness, and activity data.

Uses personal access tokens (no OAuth flow needed for personal use).
Generate at: https://cloud.ouraring.com/personal-access-tokens

API docs: https://cloud.ouraring.com/v2/docs
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


OURA_BASE = "https://api.ouraring.com/v2/usercollection"


@dataclass
class OuraDaySummary:
    date: str
    sleep_hours: float | None = None
    sleep_efficiency: float | None = None
    sleep_score: int | None = None
    resting_hr: float | None = None
    hrv_rmssd: float | None = None
    readiness_score: int | None = None
    temp_deviation: float | None = None
    activity_score: int | None = None
    steps: int | None = None
    active_calories: int | None = None

    def to_metrics(self) -> dict[str, float]:
        """Convert to {metric_name: value} for progress tracker."""
        metrics = {}
        if self.sleep_hours is not None:
            metrics["sleep_hours"] = round(self.sleep_hours, 2)
        if self.sleep_efficiency is not None:
            metrics["sleep_efficiency"] = round(self.sleep_efficiency, 1)
        if self.resting_hr is not None:
            metrics["rhr"] = round(self.resting_hr, 1)
        if self.hrv_rmssd is not None:
            metrics["hrv_rmssd"] = round(self.hrv_rmssd, 1)
        if self.readiness_score is not None:
            metrics["readiness_score"] = float(self.readiness_score)
        if self.temp_deviation is not None:
            metrics["temp_deviation"] = round(self.temp_deviation, 2)
        if self.steps is not None:
            metrics["steps"] = float(self.steps)
        return metrics


class OuraClient:
    """Oura Ring API v2 client using personal access tokens."""

    def __init__(self, token: str):
        self.token = token

    def _get(self, endpoint: str, params: dict | None = None) -> dict | None:
        """Make authenticated GET request to Oura API."""
        url = f"{OURA_BASE}/{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        try:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "Kiwi/1.0",
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def fetch_sleep(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch daily sleep data for a date range (YYYY-MM-DD)."""
        data = self._get("daily_sleep", {"start_date": start_date, "end_date": end_date})
        if not data or "error" in data:
            return []
        return data.get("data", [])

    def fetch_readiness(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch daily readiness scores."""
        data = self._get("daily_readiness", {"start_date": start_date, "end_date": end_date})
        if not data or "error" in data:
            return []
        return data.get("data", [])

    def fetch_activity(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch daily activity data."""
        data = self._get("daily_activity", {"start_date": start_date, "end_date": end_date})
        if not data or "error" in data:
            return []
        return data.get("data", [])

    def fetch_heart_rate(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch heart rate data (resting HR from sleep)."""
        data = self._get("heartrate", {"start_date": start_date, "end_date": end_date})
        if not data or "error" in data:
            return []
        return data.get("data", [])

    def sync_days(self, days_back: int = 7) -> list[OuraDaySummary]:
        """
        Fetch and merge all data types for the last N days.
        Returns list of OuraDaySummary objects.
        """
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=days_back)).isoformat()

        sleep_data = self.fetch_sleep(start, end)
        readiness_data = self.fetch_readiness(start, end)
        activity_data = self.fetch_activity(start, end)

        # Index by date
        by_date: dict[str, OuraDaySummary] = {}

        for s in sleep_data:
            d = s.get("day", "")
            if not d:
                continue
            summary = by_date.setdefault(d, OuraDaySummary(date=d))
            # Sleep total in seconds → hours
            total_sec = s.get("contributors", {}).get("total_sleep") or s.get("timestamp")
            if "total_sleep_duration" in s:
                summary.sleep_hours = s["total_sleep_duration"] / 3600
            elif total_sec:
                summary.sleep_hours = total_sec / 3600 if isinstance(total_sec, (int, float)) and total_sec > 100 else None
            summary.sleep_score = s.get("score")
            summary.sleep_efficiency = s.get("efficiency")

        for r in readiness_data:
            d = r.get("day", "")
            if not d:
                continue
            summary = by_date.setdefault(d, OuraDaySummary(date=d))
            summary.readiness_score = r.get("score")
            summary.temp_deviation = r.get("temperature_deviation")

        for a in activity_data:
            d = a.get("day", "")
            if not d:
                continue
            summary = by_date.setdefault(d, OuraDaySummary(date=d))
            summary.activity_score = a.get("score")
            summary.steps = a.get("steps")
            summary.active_calories = a.get("active_calories")

        return sorted(by_date.values(), key=lambda x: x.date)

    def format_sync_report(self, summaries: list[OuraDaySummary]) -> str:
        """Format synced data for display."""
        if not summaries:
            return "No data retrieved from Oura."

        lines = [
            "Oura Ring Data Sync",
            "=" * 50,
            "",
            f"{'Date':<12} {'Sleep':>6} {'RHR':>5} {'HRV':>5} {'Ready':>6} {'Steps':>7}",
            "-" * 50,
        ]
        for s in summaries:
            sleep = f"{s.sleep_hours:.1f}h" if s.sleep_hours else "—"
            rhr = f"{s.resting_hr:.0f}" if s.resting_hr else "—"
            hrv = f"{s.hrv_rmssd:.0f}" if s.hrv_rmssd else "—"
            ready = str(s.readiness_score) if s.readiness_score else "—"
            steps = str(s.steps) if s.steps else "—"
            lines.append(f"{s.date:<12} {sleep:>6} {rhr:>5} {hrv:>5} {ready:>6} {steps:>7}")

        return "\n".join(lines)
