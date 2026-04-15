"""
Tests for the ResearchExporter — Markdown export functionality.
"""

import pytest
from pathlib import Path
from tools.exporter import ResearchExporter


@pytest.fixture
def exporter(tmp_path, monkeypatch):
    import tools.exporter as mod
    monkeypatch.setattr(mod, "EXPORT_DIR", tmp_path)
    return ResearchExporter()


def test_export_creates_file(exporter, tmp_path):
    path = exporter.export_markdown(
        query="creatine loading protocol",
        plan="1. Search PubMed\n2. Analyze",
        response="Creatine monohydrate is the most studied...",
        score=0.85,
        critique_data={
            "dimension_scores": {"evidence_grounding": 0.9, "mechanistic_accuracy": 0.8},
            "strengths": ["Strong evidence base"],
            "critical_issues": [],
        },
    )
    assert path.exists()
    assert path.suffix == ".md"
    content = path.read_text()
    assert "creatine loading protocol" in content
    assert "0.85" in content
    assert "Strong evidence base" in content


def test_export_with_thread(exporter, tmp_path):
    path = exporter.export_markdown(
        query="caffeine timing",
        plan="",
        response="Take 3–6mg/kg 30–60 min pre...",
        score=0.78,
        critique_data={"dimension_scores": {}, "strengths": [], "critical_issues": []},
        refined=True,
        thread_name="pre-workout-stack",
    )
    content = path.read_text()
    assert "pre-workout-stack" in content
    assert "(Refined)" in content


def test_export_special_characters_in_query(exporter, tmp_path):
    path = exporter.export_markdown(
        query="what's the deal with β-alanine & HMB?!",
        plan="",
        response="Beta-alanine buffers...",
        score=0.80,
        critique_data={"dimension_scores": {}, "strengths": [], "critical_issues": []},
    )
    assert path.exists()
    assert "?" not in path.name
    assert "&" not in path.name


def test_export_empty_response(exporter, tmp_path):
    path = exporter.export_markdown(
        query="test",
        plan="",
        response="",
        score=0.0,
        critique_data={},
    )
    assert path.exists()
    content = path.read_text()
    assert "0.00" in content


def test_export_list_exports(exporter, tmp_path):
    for q in ["query one", "query two", "query three"]:
        exporter.export_markdown(
            query=q, plan="", response="...", score=0.8,
            critique_data={"dimension_scores": {}, "strengths": [], "critical_issues": []},
        )
    exports = exporter.list_exports()
    assert len(exports) == 3


def test_export_filename_slug(exporter, tmp_path):
    path = exporter.export_markdown(
        query="This Is A Very Long Query That Should Be Truncated For The Filename",
        plan="", response="...", score=0.8,
        critique_data={"dimension_scores": {}, "strengths": [], "critical_issues": []},
    )
    assert len(path.stem) < 100
