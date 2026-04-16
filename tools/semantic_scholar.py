"""
Semantic Scholar Client — AI-generated TLDR summaries + citation graph.

Semantic Scholar indexes 200M+ papers and generates AI TLDR summaries
(one-sentence takeaways) for most. Critical for rapid paper triage.

API docs: https://api.semanticscholar.org/api-docs/
Free tier: 100 req/5min (no auth), higher limits with free API key.
"""

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

SS_BASE = "https://api.semanticscholar.org/graph/v1"
REQUEST_DELAY = 3.5  # 100 req / 5 min = ~3s; polite 3.5s
_last_request: float = 0.0


@dataclass
class SemanticScholarPaper:
    paper_id: str
    title: str
    authors: list[str]
    journal: str
    year: int
    abstract: str
    doi: str
    tldr: str = ""
    citation_count: int = 0
    influential_citation_count: int = 0
    is_open_access: bool = False
    fields_of_study: list[str] = None

    def __post_init__(self):
        if self.fields_of_study is None:
            self.fields_of_study = []

    def to_context_block(self) -> str:
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."
        oa_tag = " [OA]" if self.is_open_access else ""
        block = (
            f"Title: {self.title}\n"
            f"Authors: {author_str} ({self.year})\n"
            f"Journal: {self.journal}{oa_tag}\n"
            f"DOI: {self.doi}\n"
            f"Citations: {self.citation_count} (influential: {self.influential_citation_count})\n"
        )
        if self.tldr:
            block += f"TLDR: {self.tldr}\n"
        block += f"Abstract: {self.abstract[:1000]}"
        return block


class SemanticScholarClient:
    """Semantic Scholar API client with TLDR and citation graph support."""

    FIELDS = ",".join([
        "paperId", "title", "authors", "year", "abstract",
        "venue", "externalIds", "tldr",
        "citationCount", "influentialCitationCount",
        "isOpenAccess", "fieldsOfStudy",
    ])

    def _get(self, url: str, max_retries: int = 2) -> dict | None:
        global _last_request
        for attempt in range(max_retries + 1):
            elapsed = time.time() - _last_request
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Kiwi/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    _last_request = time.time()
                    return json.loads(r.read().decode("utf-8"))
            except Exception:
                if attempt < max_retries:
                    time.sleep((attempt + 1) * 2.0)
                    continue
                return None

    def search(self, query: str, max_results: int = 8, years_back: int = 10) -> list[SemanticScholarPaper]:
        """Search Semantic Scholar for papers with TLDR summaries."""
        import datetime
        min_year = datetime.date.today().year - years_back

        params = {
            "query": query,
            "limit": str(max_results),
            "year": f"{min_year}-",
            "fields": self.FIELDS,
        }
        url = f"{SS_BASE}/paper/search?{urllib.parse.urlencode(params)}"
        data = self._get(url)
        if not data or "data" not in data:
            return []

        return self._parse_papers(data["data"][:max_results])

    def _parse_papers(self, items: list[dict]) -> list[SemanticScholarPaper]:
        """Parse raw Semantic Scholar paper objects."""
        papers = []
        for item in items:
            authors = [a.get("name", "") for a in item.get("authors", [])[:5]]
            ext_ids = item.get("externalIds", {}) or {}
            tldr_obj = item.get("tldr") or {}
            tldr_text = tldr_obj.get("text", "") if isinstance(tldr_obj, dict) else ""

            papers.append(SemanticScholarPaper(
                paper_id=item.get("paperId", ""),
                title=item.get("title", "") or "",
                authors=[a for a in authors if a],
                journal=item.get("venue", "") or "",
                year=item.get("year", 0) or 0,
                abstract=item.get("abstract", "") or "",
                doi=ext_ids.get("DOI", ""),
                tldr=tldr_text,
                citation_count=item.get("citationCount", 0) or 0,
                influential_citation_count=item.get("influentialCitationCount", 0) or 0,
                is_open_access=item.get("isOpenAccess", False),
                fields_of_study=item.get("fieldsOfStudy", []) or [],
            ))
        return papers

    def build_context_block(self, papers: list[SemanticScholarPaper]) -> str:
        """Format papers into a context block."""
        if not papers:
            return ""
        blocks = [f"=== Semantic Scholar Results ({len(papers)} papers with TLDR) ===\n"]
        for i, p in enumerate(papers, 1):
            blocks.append(f"\n[{i}] {p.to_context_block()}")
            blocks.append("-" * 60)
        return "\n".join(blocks)
