"""
PubMed Client — Real-time literature retrieval via NCBI E-utilities API.

Free to use, no API key required for basic access (rate limit: 3 req/s unauthenticated).
With NCBI_API_KEY env var: 10 req/s.

E-utilities docs: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import os
import time
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass
from typing import Any

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
REQUEST_DELAY = 0.34 if not NCBI_API_KEY else 0.11   # seconds between requests
_last_request: float = 0.0


@dataclass
class Article:
    pmid: str
    title: str
    authors: list[str]
    journal: str
    year: str
    abstract: str
    doi: str

    def to_context_block(self) -> str:
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."
        return (
            f"PMID: {self.pmid}\n"
            f"Title: {self.title}\n"
            f"Authors: {author_str} ({self.year})\n"
            f"Journal: {self.journal}\n"
            f"DOI: {self.doi}\n"
            f"Abstract: {self.abstract[:1200]}"
        )


class PubMedClient:
    """
    NCBI E-utilities PubMed client for real-time literature retrieval.
    Implements search → fetch pipeline with rate limiting.
    """

    def __init__(self):
        self.api_key = NCBI_API_KEY

    def _get(self, url: str, max_retries: int = 2) -> dict | str:
        global _last_request

        if self.api_key:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}api_key={self.api_key}"

        for attempt in range(max_retries + 1):
            elapsed = time.time() - _last_request
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)

            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    _last_request = time.time()
                    content = r.read().decode("utf-8")
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return content
            except Exception as e:
                if attempt < max_retries:
                    backoff = (attempt + 1) * 1.0
                    time.sleep(backoff)
                    continue
                return {"error": str(e)}

    def search(self, query: str, max_results: int = 10, years_back: int = 10) -> list[str]:
        """
        Search PubMed and return a list of PMIDs.

        Args:
            query: PubMed search string (supports MeSH terms and boolean operators)
            max_results: maximum PMIDs to return
            years_back: filter results to last N years
        """
        import datetime
        min_date = (datetime.date.today().year - years_back)

        encoded = urllib.parse.quote(query)
        url = (
            f"{NCBI_BASE}/esearch.fcgi"
            f"?db=pubmed&term={encoded}"
            f"&retmax={max_results}"
            f"&retmode=json"
            f"&sort=relevance"
            f"&mindate={min_date}&datetype=pdat"
        )

        result = self._get(url)
        if isinstance(result, dict) and "esearchresult" in result:
            return result["esearchresult"].get("idlist", [])
        return []

    def fetch_summaries(self, pmids: list[str]) -> list[dict[str, Any]]:
        """Fetch document summaries (title, authors, journal, year) for PMIDs."""
        if not pmids:
            return []

        id_str = ",".join(pmids)
        url = f"{NCBI_BASE}/esummary.fcgi?db=pubmed&id={id_str}&retmode=json"
        result = self._get(url)

        articles = []
        if isinstance(result, dict) and "result" in result:
            for pmid in pmids:
                doc = result["result"].get(pmid, {})
                if not doc or "error" in doc:
                    continue

                authors = [
                    a.get("name", "")
                    for a in doc.get("authors", [])
                    if a.get("authtype") == "Author"
                ]

                articles.append({
                    "pmid": pmid,
                    "title": doc.get("title", ""),
                    "authors": authors,
                    "journal": doc.get("fulljournalname", doc.get("source", "")),
                    "year": doc.get("pubdate", "")[:4],
                    "doi": next(
                        (
                            a.get("value", "")
                            for a in doc.get("articleids", [])
                            if a.get("idtype") == "doi"
                        ),
                        "",
                    ),
                })

        return articles

    def fetch_abstract(self, pmid: str) -> str:
        """Fetch the full abstract text for a single PMID."""
        url = f"{NCBI_BASE}/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract&retmode=text"
        result = self._get(url)
        if isinstance(result, str):
            # Strip preamble lines (first 3 lines are usually bibliographic info)
            lines = result.strip().splitlines()
            abstract_lines = []
            in_abstract = False
            for line in lines:
                if line.startswith("Abstract") or in_abstract:
                    in_abstract = True
                    abstract_lines.append(line)
            if abstract_lines:
                return "\n".join(abstract_lines[1:]).strip()[:2000]
            return result[:2000]
        return ""

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 8,
        years_back: int = 10,
        fetch_abstracts: bool = True,
    ) -> list[Article]:
        """
        Full pipeline: search → summary → abstracts.
        Returns a list of Article objects ready for context injection.
        """
        pmids = self.search(query, max_results=max_results, years_back=years_back)
        if not pmids:
            return []

        summaries = self.fetch_summaries(pmids)

        articles = []
        for summ in summaries:
            abstract = ""
            if fetch_abstracts:
                abstract = self.fetch_abstract(summ["pmid"])

            articles.append(Article(
                pmid=summ["pmid"],
                title=summ["title"],
                authors=summ["authors"],
                journal=summ["journal"],
                year=summ["year"],
                abstract=abstract,
                doi=summ["doi"],
            ))

        return articles

    def build_context_block(self, articles: list[Article]) -> str:
        """Format articles into a context block for Claude."""
        if not articles:
            return ""

        blocks = [f"=== PubMed Results ({len(articles)} articles) ===\n"]
        for i, art in enumerate(articles, 1):
            blocks.append(f"\n[{i}] {art.to_context_block()}")
            blocks.append("-" * 60)

        return "\n".join(blocks)

    def build_search_string(self, topic: str, study_types: list[str] | None = None) -> str:
        """
        Build an optimized PubMed search string for a topic.
        study_types: e.g., ["randomized controlled trial", "systematic review", "meta-analysis"]
        """
        study_filter = ""
        if study_types:
            type_filters = " OR ".join(
                f'"{st}"[pt]' for st in study_types
            )
            study_filter = f" AND ({type_filters})"

        return f'"{topic}"[tiab] OR "{topic}"[MeSH]{study_filter}'
