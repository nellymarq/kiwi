"""
OpenAlex Client — Free scholarly metadata retrieval for sports nutrition research.

OpenAlex indexes 250M+ works across all publishers including Springer, Elsevier,
Frontiers, BMC, Wiley — covering journals that PubMed may not fully index.

API docs: https://docs.openalex.org/
Rate limit: 100K requests/day (polite pool with email), 10 req/s max.
No API key required.
"""

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

OPENALEX_BASE = "https://api.openalex.org"
REQUEST_DELAY = 0.12  # ~8 req/s (polite)
_last_request: float = 0.0

# Sports nutrition journal ISSNs for targeted filtering
SPORTS_NUTRITION_JOURNALS: dict[str, str] = {
    "JISSN": "1550-2783",
    "BJSM": "0306-3674",
    "IJSNEM": "1526-484X",
    "IJSPP": "1555-0265",
    "Sports Medicine": "0112-1642",
    "MSSE": "0195-9131",
    "EJAP": "1439-6319",
    "Nutrients": "2072-6643",
    "Frontiers in Nutrition": "2296-861X",
    "Frontiers in Physiology": "1664-042X",
    "JAMA": "0098-7484",
    "NEJM": "0028-4793",
    "Br J Nutr": "0007-1145",
    "Am J Clin Nutr": "0002-9165",
    "J Nutr": "0022-3166",
    "Int J Sport Nutr Exerc Metab": "1526-484X",
    "J Strength Cond Res": "1064-8011",
    "Scand J Med Sci Sports": "0905-7188",
    "J Sports Sci": "0264-0414",
    "Appl Physiol Nutr Metab": "1715-5312",
}

SPORTS_NUTRITION_ISSNS = list(SPORTS_NUTRITION_JOURNALS.values())


@dataclass
class OpenAlexWork:
    openalex_id: str
    title: str
    authors: list[str]
    journal: str
    year: int
    abstract: str
    doi: str
    cited_by_count: int = 0
    open_access: bool = False
    source: str = "OpenAlex"

    def to_context_block(self) -> str:
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."
        oa_tag = " [Open Access]" if self.open_access else ""
        return (
            f"Title: {self.title}\n"
            f"Authors: {author_str} ({self.year})\n"
            f"Journal: {self.journal}{oa_tag}\n"
            f"DOI: {self.doi}\n"
            f"Cited by: {self.cited_by_count}\n"
            f"Abstract: {self.abstract[:1200]}"
        )


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct abstract text from OpenAlex's inverted index format."""
    if not inverted_index:
        return ""
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in word_positions)


class OpenAlexClient:
    """
    OpenAlex API client for scholarly literature retrieval.
    Complements PubMed with broader journal coverage.
    """

    def __init__(self, email: str = "kiwi@scythene.com"):
        self.email = email

    def _get(self, url: str, max_retries: int = 2) -> dict | None:
        global _last_request

        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}mailto={self.email}"

        for attempt in range(max_retries + 1):
            elapsed = time.time() - _last_request
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Kiwi/1.0"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    _last_request = time.time()
                    return json.loads(r.read().decode("utf-8"))
            except Exception:
                if attempt < max_retries:
                    time.sleep((attempt + 1) * 1.0)
                    continue
                return None

    def search(
        self,
        query: str,
        max_results: int = 8,
        years_back: int = 8,
        journal_issns: list[str] | None = None,
    ) -> list[OpenAlexWork]:
        """
        Search OpenAlex for works matching the query.

        Args:
            query: search string
            max_results: max works to return
            years_back: filter to recent N years
            journal_issns: optional ISSN filter for specific journals
        """
        import datetime
        min_year = datetime.date.today().year - years_back

        encoded = urllib.parse.quote(query)
        url = (
            f"{OPENALEX_BASE}/works"
            f"?search={encoded}"
            f"&filter=from_publication_date:{min_year}-01-01"
            f"&sort=relevance_score:desc"
            f"&per_page={max_results}"
        )

        if journal_issns:
            issn_filter = "|".join(journal_issns)
            url += f",primary_location.source.issn:{issn_filter}"

        data = self._get(url)
        if not data or "results" not in data:
            return []

        works = []
        for item in data["results"]:
            authors = []
            for authorship in item.get("authorships", [])[:5]:
                name = authorship.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)

            location = item.get("primary_location", {}) or {}
            source = location.get("source", {}) or {}
            journal_name = source.get("display_name", "")

            doi_raw = item.get("doi", "") or ""
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""

            abstract = reconstruct_abstract(item.get("abstract_inverted_index"))

            oa = item.get("open_access", {}) or {}

            works.append(OpenAlexWork(
                openalex_id=item.get("id", ""),
                title=item.get("title", ""),
                authors=authors,
                journal=journal_name,
                year=item.get("publication_year", 0),
                abstract=abstract,
                doi=doi,
                cited_by_count=item.get("cited_by_count", 0),
                open_access=oa.get("is_oa", False),
            ))

        return works

    def search_sports_nutrition(
        self,
        query: str,
        max_results: int = 6,
        years_back: int = 8,
    ) -> list[OpenAlexWork]:
        """Search specifically in sports nutrition journals."""
        return self.search(
            query,
            max_results=max_results,
            years_back=years_back,
            journal_issns=SPORTS_NUTRITION_ISSNS,
        )

    def fetch_cited_by(self, doi: str, max_results: int = 10) -> list[OpenAlexWork]:
        """Find papers that cite the given DOI (forward citations)."""
        if not doi:
            return []
        doi_clean = doi.replace("https://doi.org/", "").lower()
        url = (
            f"{OPENALEX_BASE}/works"
            f"?filter=cites:https://doi.org/{doi_clean}"
            f"&per_page={max_results}"
            f"&sort=cited_by_count:desc"
        )
        data = self._get(url)
        if not data or "results" not in data:
            return []
        return self._parse_works(data["results"])

    def fetch_references(self, doi: str, max_results: int = 10) -> list[OpenAlexWork]:
        """Find papers cited by the given DOI (backward citations / references)."""
        if not doi:
            return []
        doi_clean = doi.replace("https://doi.org/", "").lower()
        url = f"{OPENALEX_BASE}/works/doi:{doi_clean}"
        data = self._get(url)
        if not data:
            return []
        refs = data.get("referenced_works", [])[:max_results]
        if not refs:
            return []
        # Fetch each referenced work
        works = []
        for ref_id in refs:
            ref_data = self._get(ref_id.replace("openalex.org", "api.openalex.org"))
            if ref_data:
                parsed = self._parse_works([ref_data])
                if parsed:
                    works.append(parsed[0])
        return works

    def _parse_works(self, items: list[dict]) -> list[OpenAlexWork]:
        """Parse raw OpenAlex work objects into OpenAlexWork dataclass."""
        works = []
        for item in items:
            authors = []
            for authorship in item.get("authorships", [])[:5]:
                name = authorship.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)
            location = item.get("primary_location", {}) or {}
            source = location.get("source", {}) or {}
            journal_name = source.get("display_name", "")
            doi_raw = item.get("doi", "") or ""
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""
            abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
            oa = item.get("open_access", {}) or {}
            works.append(OpenAlexWork(
                openalex_id=item.get("id", ""),
                title=item.get("title", ""),
                authors=authors,
                journal=journal_name,
                year=item.get("publication_year", 0),
                abstract=abstract,
                doi=doi,
                cited_by_count=item.get("cited_by_count", 0),
                open_access=oa.get("is_oa", False),
            ))
        return works

    def build_context_block(self, works: list[OpenAlexWork]) -> str:
        """Format works into a context block for Claude."""
        if not works:
            return ""

        blocks = [f"=== OpenAlex Results ({len(works)} articles) ===\n"]
        for i, work in enumerate(works, 1):
            blocks.append(f"\n[{i}] {work.to_context_block()}")
            blocks.append("-" * 60)

        return "\n".join(blocks)
