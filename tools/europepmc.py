"""
Europe PMC Client — 40M+ articles with 6M+ full-text open access.

Europe PMC mirrors PubMed + PMC but adds full-text search across open access
content, preprints (bioRxiv, medRxiv), patents, and grants. No API key required.

API docs: https://europepmc.org/RestfulWebService
Rate limit: generous (polite throttling applied).
"""

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
REQUEST_DELAY = 0.2
_last_request: float = 0.0


@dataclass
class EuropePMCArticle:
    pmid: str
    pmcid: str
    title: str
    authors: list[str]
    journal: str
    year: str
    abstract: str
    doi: str
    is_open_access: bool = False
    has_fulltext: bool = False
    fulltext: str = ""

    def to_context_block(self) -> str:
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."
        oa_tag = " [Open Access]" if self.is_open_access else ""
        ft_tag = " [Full Text Available]" if self.has_fulltext else ""
        return (
            f"PMID: {self.pmid}  PMCID: {self.pmcid}\n"
            f"Title: {self.title}\n"
            f"Authors: {author_str} ({self.year})\n"
            f"Journal: {self.journal}{oa_tag}{ft_tag}\n"
            f"DOI: {self.doi}\n"
            f"Abstract: {self.abstract[:1200]}"
        )


class EuropePMCClient:
    """Europe PMC API client with full-text support."""

    def _get(self, url: str, max_retries: int = 2) -> dict | str | None:
        global _last_request
        for attempt in range(max_retries + 1):
            elapsed = time.time() - _last_request
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Kiwi/1.0"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    _last_request = time.time()
                    content = r.read().decode("utf-8", errors="ignore")
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return content
            except Exception:
                if attempt < max_retries:
                    time.sleep((attempt + 1) * 1.0)
                    continue
                return None

    def search(
        self,
        query: str,
        max_results: int = 8,
        years_back: int = 10,
        open_access_only: bool = False,
    ) -> list[EuropePMCArticle]:
        """Search Europe PMC for articles matching the query."""
        import datetime
        min_year = datetime.date.today().year - years_back

        search_query = f"{query} AND PUB_YEAR:[{min_year} TO *]"
        if open_access_only:
            search_query += " AND OPEN_ACCESS:Y"

        params = {
            "query": search_query,
            "format": "json",
            "pageSize": str(max_results),
            "resultType": "core",
        }
        url = f"{EPMC_BASE}/search?{urllib.parse.urlencode(params)}"
        data = self._get(url)
        if not isinstance(data, dict) or "resultList" not in data:
            return []

        articles = []
        for item in data["resultList"].get("result", [])[:max_results]:
            authors_raw = item.get("authorList", {}).get("author", []) or []
            authors = [a.get("fullName", "") for a in authors_raw if a.get("fullName")]

            articles.append(EuropePMCArticle(
                pmid=item.get("pmid", ""),
                pmcid=item.get("pmcid", ""),
                title=item.get("title", ""),
                authors=authors,
                journal=item.get("journalTitle", ""),
                year=str(item.get("pubYear", "")),
                abstract=item.get("abstractText", ""),
                doi=item.get("doi", ""),
                is_open_access=item.get("isOpenAccess", "N") == "Y",
                has_fulltext=item.get("hasTextMinedTerms", "N") == "Y" or bool(item.get("pmcid")),
            ))

        return articles

    def fetch_fulltext(self, pmcid: str) -> str:
        """Fetch full-text for a PMC article. Requires PMCID (e.g., 'PMC1234567')."""
        if not pmcid:
            return ""
        if not pmcid.startswith("PMC"):
            pmcid = f"PMC{pmcid}"

        url = f"{EPMC_BASE}/{pmcid}/fullTextXML"
        result = self._get(url)
        if not isinstance(result, str):
            return ""

        # Strip XML tags for a clean text representation
        import re
        text = re.sub(r"<[^>]+>", " ", result)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:20000]  # Cap at ~20K chars

    def build_context_block(self, articles: list[EuropePMCArticle]) -> str:
        """Format articles into a context block for Claude."""
        if not articles:
            return ""
        blocks = [f"=== Europe PMC Results ({len(articles)} articles) ===\n"]
        for i, art in enumerate(articles, 1):
            blocks.append(f"\n[{i}] {art.to_context_block()}")
            blocks.append("-" * 60)
        return "\n".join(blocks)
