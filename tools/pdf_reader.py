"""
PDF Reader — Download and extract text from open-access research PDFs.

Flow:
  DOI → Unpaywall lookup → download OA PDF → extract text via pypdf → cache locally

Only retrieves legally available open-access PDFs via Unpaywall. Caches at
~/.kiwi/pdf_cache/ to avoid re-downloading.
"""
from __future__ import annotations

import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

from .unpaywall import UnpaywallClient


PDF_CACHE_DIR = Path.home() / ".kiwi" / "pdf_cache"
MAX_PDF_CHARS = 100_000  # Limit extracted text per paper


@dataclass
class PDFContent:
    doi: str
    source_url: str
    cached_path: Path
    num_pages: int
    text: str
    extracted_chars: int

    def preview(self, chars: int = 2000) -> str:
        return self.text[:chars] + ("..." if len(self.text) > chars else "")

    def sections(self) -> dict[str, str]:
        """Rough extraction of paper sections by common headers."""
        import re
        text = self.text
        section_markers = [
            r"(?i)\babstract\b",
            r"(?i)\b(introduction|background)\b",
            r"(?i)\bmethods?\b",
            r"(?i)\b(materials and methods|methodology)\b",
            r"(?i)\bresults?\b",
            r"(?i)\bdiscussion\b",
            r"(?i)\bconclusion[s]?\b",
            r"(?i)\breferences?\b",
        ]
        sections = {}
        positions = []
        for pattern in section_markers:
            for m in re.finditer(pattern, text):
                positions.append((m.start(), m.group().lower()))
        positions.sort()
        for i, (pos, name) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            key = name.lower().strip()
            if key not in sections:
                sections[key] = text[pos:end][:5000]
        return sections


def _cache_path(doi: str) -> Path:
    """Deterministic cache path for a DOI."""
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    hashed = hashlib.sha1(doi.encode()).hexdigest()[:16]
    return PDF_CACHE_DIR / f"{hashed}.pdf"


def _download_pdf(url: str, dest: Path, timeout: int = 30) -> bool:
    """Download PDF to destination path. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Kiwi/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read()
        # Basic PDF signature check (PDFs start with %PDF-)
        if not content.startswith(b"%PDF"):
            return False
        dest.write_bytes(content)
        return True
    except Exception:
        return False


def _extract_text(pdf_path: Path) -> tuple[str, int]:
    """Extract text from a PDF file. Returns (text, num_pages)."""
    if not HAS_PYPDF:
        return "", 0
    try:
        reader = PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        full_text = "\n".join(parts)
        return full_text[:MAX_PDF_CHARS], num_pages
    except Exception:
        return "", 0


def read_pdf(doi: str, unpaywall: Optional[UnpaywallClient] = None) -> Optional[PDFContent]:
    """
    Download (if needed) and extract text from an OA PDF.

    Returns None if:
    - DOI has no open access version
    - Download fails
    - pypdf is not installed
    """
    if not HAS_PYPDF:
        return None
    if not doi:
        return None

    cached = _cache_path(doi)
    source_url = ""

    # Use cached file if it exists and is valid
    if cached.exists() and cached.stat().st_size > 1000:
        text, pages = _extract_text(cached)
        if text:
            return PDFContent(
                doi=doi, source_url="cached",
                cached_path=cached, num_pages=pages,
                text=text, extracted_chars=len(text),
            )

    # Fetch OA location via Unpaywall
    if unpaywall is None:
        unpaywall = UnpaywallClient()
    result = unpaywall.lookup(doi)
    if not result or not result.is_oa or not result.best_oa_location:
        return None

    source_url = (
        result.best_oa_location.url_for_pdf
        or result.best_oa_location.url
    )
    if not source_url:
        return None

    if not _download_pdf(source_url, cached):
        return None

    text, pages = _extract_text(cached)
    if not text:
        return None

    return PDFContent(
        doi=doi, source_url=source_url,
        cached_path=cached, num_pages=pages,
        text=text, extracted_chars=len(text),
    )


def clear_cache() -> int:
    """Delete all cached PDFs. Returns number of files deleted."""
    if not PDF_CACHE_DIR.exists():
        return 0
    count = 0
    for f in PDF_CACHE_DIR.glob("*.pdf"):
        f.unlink()
        count += 1
    return count
