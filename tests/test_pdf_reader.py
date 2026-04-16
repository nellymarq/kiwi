"""Tests for PDF reader (mocked — no real downloads)."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.pdf_reader import (
    PDFContent, _cache_path, clear_cache,
    HAS_PYPDF,
)


def test_pdf_content_preview():
    content = PDFContent(
        doi="10.1/test",
        source_url="https://example.com/paper.pdf",
        cached_path=Path("/tmp/fake.pdf"),
        num_pages=10,
        text="A" * 5000,
        extracted_chars=5000,
    )
    preview = content.preview(1000)
    assert len(preview) <= 1003  # 1000 chars + "..."
    assert preview.endswith("...")


def test_pdf_content_short_text_no_ellipsis():
    content = PDFContent(
        doi="10.1/test", source_url="url", cached_path=Path("/tmp/fake.pdf"),
        num_pages=1, text="short", extracted_chars=5,
    )
    preview = content.preview(2000)
    assert preview == "short"
    assert not preview.endswith("...")


def test_pdf_content_sections_extraction():
    text = (
        "This is the title\n"
        "Abstract\n"
        "Background information here.\n"
        "Introduction\n"
        "Study aims described.\n"
        "Methods\n"
        "Participants recruited from...\n"
        "Results\n"
        "We found significant differences.\n"
        "Discussion\n"
        "This suggests that...\n"
        "Conclusions\n"
        "Therefore...\n"
        "References\n"
        "[1] Smith et al..."
    )
    content = PDFContent(
        doi="10.1/test", source_url="url", cached_path=Path("/tmp/fake.pdf"),
        num_pages=1, text=text, extracted_chars=len(text),
    )
    sections = content.sections()
    assert "abstract" in sections
    assert "results" in sections
    assert "conclusions" in sections or "conclusion" in sections


def test_cache_path_deterministic():
    p1 = _cache_path("10.1/test")
    p2 = _cache_path("10.1/test")
    assert p1 == p2


def test_cache_path_different_dois():
    p1 = _cache_path("10.1/abc")
    p2 = _cache_path("10.1/xyz")
    assert p1 != p2


def test_pypdf_available():
    assert HAS_PYPDF, "pypdf should be installed for tests"


def test_clear_cache_empty(tmp_path, monkeypatch):
    import tools.pdf_reader as pdf_mod
    monkeypatch.setattr(pdf_mod, "PDF_CACHE_DIR", tmp_path / "pdf_cache")
    count = clear_cache()
    assert count == 0


def test_clear_cache_with_files(tmp_path, monkeypatch):
    import tools.pdf_reader as pdf_mod
    cache_dir = tmp_path / "pdf_cache"
    cache_dir.mkdir()
    monkeypatch.setattr(pdf_mod, "PDF_CACHE_DIR", cache_dir)

    # Create 3 dummy PDF files
    for i in range(3):
        (cache_dir / f"test{i}.pdf").write_text("dummy")

    count = clear_cache()
    assert count == 3
    assert list(cache_dir.glob("*.pdf")) == []


def test_read_pdf_empty_doi():
    from tools.pdf_reader import read_pdf
    result = read_pdf("")
    assert result is None
