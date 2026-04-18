"""
Generic Wearable Data Importer — Parse CSV/JSON exports from any wearable.

Supports common export formats from Oura, Whoop, Garmin, Apple Health.
Auto-detects format and maps columns/fields to Kiwi progress metrics.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Column name → Kiwi metric mapping (case-insensitive)
COLUMN_MAPPING: dict[str, str] = {
    # Sleep
    "total_sleep_duration": "sleep_hours",
    "sleep_duration": "sleep_hours",
    "sleep_total": "sleep_hours",
    "total sleep": "sleep_hours",
    "sleep (hrs)": "sleep_hours",
    "sleep_hours": "sleep_hours",
    "sleep_efficiency": "sleep_efficiency",
    "efficiency": "sleep_efficiency",

    # Heart rate
    "resting_heart_rate": "rhr",
    "resting_hr": "rhr",
    "rhr": "rhr",
    "avg_resting_hr": "rhr",
    "resting heart rate": "rhr",

    # HRV
    "hrv": "hrv_rmssd",
    "hrv_rmssd": "hrv_rmssd",
    "rmssd": "hrv_rmssd",
    "hrv_average": "hrv_rmssd",
    "heart_rate_variability": "hrv_rmssd",

    # Readiness / Recovery
    "readiness_score": "readiness_score",
    "readiness": "readiness_score",
    "recovery_score": "readiness_score",
    "recovery": "readiness_score",

    # Body
    "weight": "weight",
    "weight_kg": "weight",
    "body_weight": "weight",
    "body_fat": "body_fat",
    "body_fat_pct": "body_fat",

    # Activity
    "steps": "steps",
    "step_count": "steps",
    "total_steps": "steps",
    "active_calories": "active_calories",
    "calories_burned": "active_calories",

    # Temperature
    "temperature_deviation": "temp_deviation",
    "temp_deviation": "temp_deviation",
    "skin_temperature": "temp_deviation",

    # Training
    "strain": "strain",
    "training_load": "training_load",
}

# Date column names to detect
DATE_COLUMNS = {"date", "day", "timestamp", "time", "recorded_at", "created_at", "start_date"}


@dataclass
class ImportResult:
    source_file: str
    format_detected: str  # "csv", "json", "oura_json", "whoop_csv"
    rows_parsed: int
    metrics_imported: dict[str, int]  # {metric: count}
    errors: list[str]


def _detect_date_column(headers: list[str]) -> str | None:
    """Find the date column from headers."""
    for h in headers:
        if h.lower().strip() in DATE_COLUMNS:
            return h
    return None


def _map_column(col_name: str) -> str | None:
    """Map a column name to a Kiwi metric."""
    return COLUMN_MAPPING.get(col_name.lower().strip())


def _parse_value(raw: str, metric: str) -> float | None:
    """Parse a raw string value into a float, with unit conversion."""
    if not raw or raw.strip() in ("", "—", "N/A", "null", "None"):
        return None
    try:
        val = float(raw.strip().replace(",", ""))
        # Convert seconds to hours for sleep if value > 100 (likely seconds)
        if metric == "sleep_hours" and val > 24:
            val = val / 3600
        return val
    except ValueError:
        return None


def import_csv(filepath: Path) -> tuple[list[dict], ImportResult]:
    """
    Import wearable data from a CSV file.
    Returns (records, result) where records = [{date, metric, value}].
    """
    records = []
    result = ImportResult(
        source_file=str(filepath),
        format_detected="csv",
        rows_parsed=0,
        metrics_imported={},
        errors=[],
    )

    try:
        with open(filepath, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            date_col = _detect_date_column(headers)
            if not date_col:
                result.errors.append("No date column found. Expected: date, day, timestamp, etc.")
                return records, result

            # Map columns to metrics
            col_map = {}
            for h in headers:
                metric = _map_column(h)
                if metric:
                    col_map[h] = metric

            if not col_map:
                result.errors.append(f"No recognized metric columns. Headers: {headers[:10]}")
                return records, result

            for row in reader:
                result.rows_parsed += 1
                date_val = row.get(date_col, "")[:10]  # Truncate to YYYY-MM-DD
                if not date_val:
                    continue

                for col, metric in col_map.items():
                    val = _parse_value(row.get(col, ""), metric)
                    if val is not None:
                        records.append({"date": date_val, "metric": metric, "value": val})
                        result.metrics_imported[metric] = result.metrics_imported.get(metric, 0) + 1

    except Exception as e:
        result.errors.append(str(e))

    return records, result


def import_json(filepath: Path) -> tuple[list[dict], ImportResult]:
    """
    Import wearable data from a JSON file.
    Handles both flat arrays and nested structures (Oura export format).
    """
    records = []
    result = ImportResult(
        source_file=str(filepath),
        format_detected="json",
        rows_parsed=0,
        metrics_imported={},
        errors=[],
    )

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))

        # Handle array of objects
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Look for a "data" key (common API export format)
            if "data" in data and isinstance(data["data"], list):
                items = data["data"]
            else:
                items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue
            result.rows_parsed += 1

            # Find date
            date_val = ""
            for key in DATE_COLUMNS:
                if key in item:
                    date_val = str(item[key])[:10]
                    break
            if not date_val and "day" in item:
                date_val = str(item["day"])[:10]

            # Map fields to metrics
            for key, value in item.items():
                metric = _map_column(key)
                if metric and value is not None:
                    try:
                        val = float(value)
                        if metric == "sleep_hours" and val > 24:
                            val = val / 3600
                        records.append({"date": date_val or "unknown", "metric": metric, "value": round(val, 2)})
                        result.metrics_imported[metric] = result.metrics_imported.get(metric, 0) + 1
                    except (ValueError, TypeError):
                        continue

    except Exception as e:
        result.errors.append(str(e))

    return records, result


def import_file(filepath: str | Path) -> tuple[list[dict], ImportResult]:
    """Auto-detect format and import wearable data."""
    path = Path(filepath)
    if not path.exists():
        return [], ImportResult(str(filepath), "unknown", 0, {}, [f"File not found: {filepath}"])

    if path.suffix.lower() == ".csv":
        return import_csv(path)
    elif path.suffix.lower() in (".json", ".jsonl"):
        return import_json(path)
    else:
        return [], ImportResult(str(filepath), "unknown", 0, {}, [f"Unsupported format: {path.suffix}"])


def format_import_result(result: ImportResult) -> str:
    """Format import results for display."""
    lines = [
        f"Import: {result.source_file}",
        f"Format: {result.format_detected}",
        f"Rows parsed: {result.rows_parsed}",
    ]
    if result.metrics_imported:
        lines.append("Metrics imported:")
        for metric, count in sorted(result.metrics_imported.items()):
            lines.append(f"  {metric}: {count} data points")
    if result.errors:
        lines.append("Errors:")
        for e in result.errors:
            lines.append(f"  ⚠️ {e}")
    return "\n".join(lines)
