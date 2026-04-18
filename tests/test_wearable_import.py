"""Tests for generic wearable data importer."""

import json
import pytest
from pathlib import Path
from tools.wearable_import import (
    import_csv, import_json, import_file,
    format_import_result, _map_column, _parse_value,
    COLUMN_MAPPING,
)


def test_map_column_known():
    assert _map_column("resting_heart_rate") == "rhr"
    assert _map_column("total_sleep_duration") == "sleep_hours"
    assert _map_column("steps") == "steps"
    assert _map_column("hrv") == "hrv_rmssd"


def test_map_column_case_insensitive():
    assert _map_column("Resting_Heart_Rate") == "rhr"
    assert _map_column("STEPS") == "steps"


def test_map_column_unknown():
    assert _map_column("unknown_field_xyz") is None


def test_parse_value_normal():
    assert _parse_value("55.3", "rhr") == 55.3
    assert _parse_value("8500", "steps") == 8500.0


def test_parse_value_sleep_seconds_conversion():
    # 27000 seconds = 7.5 hours; should auto-convert
    assert abs(_parse_value("27000", "sleep_hours") - 7.5) < 0.01


def test_parse_value_empty():
    assert _parse_value("", "rhr") is None
    assert _parse_value("N/A", "rhr") is None
    assert _parse_value("—", "rhr") is None


def test_import_csv(tmp_path):
    csv_file = tmp_path / "oura_export.csv"
    csv_file.write_text(
        "date,resting_heart_rate,steps,total_sleep_duration\n"
        "2026-04-15,56,9000,27000\n"
        "2026-04-16,53,7500,29700\n"
    )
    records, result = import_csv(csv_file)
    assert result.rows_parsed == 2
    assert result.format_detected == "csv"
    assert len(result.errors) == 0
    assert len(records) > 0

    # Check specific records
    rhr_records = [r for r in records if r["metric"] == "rhr"]
    assert len(rhr_records) == 2
    assert rhr_records[0]["value"] == 56.0

    sleep_records = [r for r in records if r["metric"] == "sleep_hours"]
    assert len(sleep_records) == 2
    assert abs(sleep_records[0]["value"] - 7.5) < 0.01


def test_import_csv_no_date_column(tmp_path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("steps,rhr\n9000,56\n")
    records, result = import_csv(csv_file)
    assert len(result.errors) > 0
    assert "date" in result.errors[0].lower()


def test_import_json(tmp_path):
    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps([
        {"date": "2026-04-15", "resting_heart_rate": 56, "steps": 9000},
        {"date": "2026-04-16", "resting_heart_rate": 53, "steps": 7500},
    ]))
    records, result = import_json(json_file)
    assert result.rows_parsed == 2
    assert len(records) > 0


def test_import_json_nested(tmp_path):
    json_file = tmp_path / "oura.json"
    json_file.write_text(json.dumps({
        "data": [
            {"day": "2026-04-15", "hrv": 48.0, "resting_hr": 55},
        ]
    }))
    records, result = import_json(json_file)
    assert result.rows_parsed == 1
    hrv = [r for r in records if r["metric"] == "hrv_rmssd"]
    assert len(hrv) == 1


def test_import_file_auto_detect_csv(tmp_path):
    csv_file = tmp_path / "export.csv"
    csv_file.write_text("date,steps\n2026-04-15,9000\n")
    records, result = import_file(csv_file)
    assert result.format_detected == "csv"
    assert len(records) > 0


def test_import_file_auto_detect_json(tmp_path):
    json_file = tmp_path / "export.json"
    json_file.write_text(json.dumps([{"date": "2026-04-15", "steps": 9000}]))
    records, result = import_file(json_file)
    assert result.format_detected == "json"


def test_import_file_not_found():
    records, result = import_file("/nonexistent/file.csv")
    assert len(result.errors) > 0


def test_import_file_unsupported_format(tmp_path):
    f = tmp_path / "data.xml"
    f.write_text("<data/>")
    records, result = import_file(f)
    assert "Unsupported" in result.errors[0]


def test_format_result():
    from tools.wearable_import import ImportResult
    result = ImportResult("test.csv", "csv", 10, {"rhr": 10, "steps": 10}, [])
    output = format_import_result(result)
    assert "test.csv" in output
    assert "rhr: 10" in output
