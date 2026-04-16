"""Tests for PDF export."""

import pytest
from pathlib import Path

from tools.pdf_export import (
    BrandConfig, generate_client_report,
    _sanitize_filename, _clean_markdown, _grade_color,
)


def test_brand_config_defaults():
    brand = BrandConfig()
    assert brand.brand_name == "Kiwi Performance Research"
    assert "Evidence-Based" in brand.tagline


def test_brand_config_custom():
    brand = BrandConfig(
        brand_name="Acme Nutrition",
        practitioner="Dr. Example",
        org="Acme LLC",
    )
    assert brand.brand_name == "Acme Nutrition"
    assert brand.practitioner == "Dr. Example"
    assert brand.org == "Acme LLC"


def test_sanitize_filename():
    assert _sanitize_filename("Creatine Timing & Dose?") == "creatine_timing_dose"
    assert _sanitize_filename("") == "untitled"
    assert _sanitize_filename("   ") == "untitled"
    assert len(_sanitize_filename("a" * 200)) <= 52  # 50 char cap + slug cleanup


def test_clean_markdown_bold():
    assert _clean_markdown("**bold**") == "<b>bold</b>"
    assert _clean_markdown("**a** and **b**") == "<b>a</b> and <b>b</b>"


def test_clean_markdown_italic():
    assert _clean_markdown("*italic*") == "<i>italic</i>"


def test_clean_markdown_inline_code():
    assert "<font name='Courier'>code</font>" in _clean_markdown("`code`")


def test_grade_color_known():
    high = _grade_color("HIGH")
    moderate = _grade_color("MODERATE")
    assert high is not None
    assert moderate is not None
    assert high != moderate


def test_grade_color_unknown():
    color = _grade_color("UNKNOWN_LEVEL")
    assert color is not None  # Falls back to grey


def test_generate_report_creates_pdf(tmp_path):
    pdf_path = generate_client_report(
        query="Test research question",
        response="## Finding\n\nCreatine **5g/d** improves strength.",
        score=0.88,
        critique_data={
            "strengths": ["Strong evidence base"],
            "critical_issues": [],
        },
        grade_level="HIGH",
        output_dir=tmp_path,
    )
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 1000  # PDF should be at least 1KB


def test_generate_report_with_client_name(tmp_path):
    pdf_path = generate_client_report(
        query="Protocol for athlete",
        response="Details...",
        score=0.75,
        critique_data={},
        client_name="athlete_a",
        grade_level="MODERATE",
        output_dir=tmp_path,
    )
    assert pdf_path.exists()


def test_generate_report_empty_critique(tmp_path):
    pdf_path = generate_client_report(
        query="Q",
        response="A",
        score=0.0,
        critique_data={},
        output_dir=tmp_path,
    )
    assert pdf_path.exists()


def test_generate_report_branded(tmp_path):
    brand = BrandConfig(
        brand_name="MPS Performance",
        practitioner="Nelson Marques, RDN",
        org="MPS LLC",
    )
    pdf_path = generate_client_report(
        query="Q",
        response="A",
        score=0.85,
        critique_data={"strengths": ["S1"]},
        brand=brand,
        grade_level="HIGH",
        output_dir=tmp_path,
    )
    assert pdf_path.exists()
    # Check content includes brand name (rough check via file size)
    assert pdf_path.stat().st_size > 1500
