"""
Unpaywall Client — Legal open access PDF discovery.

Given a DOI, Unpaywall returns legal OA versions of the paper from publisher
sites, institutional repositories, and preprint servers. ~50% of recent
research has an OA version somewhere.

API docs: https://unpaywall.org/products/api
Free, no API key (just pass email for polite identification).
"""

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
REQUEST_DELAY = 0.2
_last_request: float = 0.0


@dataclass
class OALocation:
    url: str
    url_for_pdf: str
    license: str       # e.g., "cc-by", "cc-by-nc-nd"
    version: str       # "publishedVersion", "acceptedVersion", "submittedVersion"
    host_type: str     # "publisher" or "repository"
    is_best: bool = False


@dataclass
class UnpaywallResult:
    doi: str
    title: str
    is_oa: bool
    oa_status: str           # "gold", "green", "hybrid", "bronze", "closed"
    best_oa_location: OALocation | None
    all_oa_locations: list[OALocation]

    def summary(self) -> str:
        if not self.is_oa:
            return f"No open access version found for {self.doi}"
        best = self.best_oa_location
        if not best:
            return f"OA available ({self.oa_status}) but no direct link"
        return (
            f"DOI: {self.doi}\n"
            f"Title: {self.title}\n"
            f"OA Status: {self.oa_status} ({best.version})\n"
            f"License: {best.license}\n"
            f"PDF: {best.url_for_pdf or best.url}\n"
            f"Other OA locations: {len(self.all_oa_locations) - 1}"
        )


class UnpaywallClient:
    """Unpaywall API client for discovering legal OA versions of papers."""

    def __init__(self, email: str = "kiwi@scythene.com"):
        self.email = email

    def _get(self, url: str, max_retries: int = 2) -> dict | None:
        global _last_request
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}email={self.email}"

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

    def lookup(self, doi: str) -> UnpaywallResult | None:
        """Look up OA availability for a DOI."""
        if not doi:
            return None
        doi_clean = doi.replace("https://doi.org/", "").strip().lower()
        url = f"{UNPAYWALL_BASE}/{urllib.parse.quote(doi_clean)}"
        data = self._get(url)
        if not data or "doi" not in data:
            return None

        best_raw = data.get("best_oa_location")
        best_location = None
        if best_raw:
            best_location = OALocation(
                url=best_raw.get("url", ""),
                url_for_pdf=best_raw.get("url_for_pdf", ""),
                license=best_raw.get("license", "") or "",
                version=best_raw.get("version", ""),
                host_type=best_raw.get("host_type", ""),
                is_best=True,
            )

        all_locations = []
        for loc in data.get("oa_locations", []) or []:
            all_locations.append(OALocation(
                url=loc.get("url", ""),
                url_for_pdf=loc.get("url_for_pdf", ""),
                license=loc.get("license", "") or "",
                version=loc.get("version", ""),
                host_type=loc.get("host_type", ""),
            ))

        return UnpaywallResult(
            doi=data.get("doi", doi_clean),
            title=data.get("title", ""),
            is_oa=data.get("is_oa", False),
            oa_status=data.get("oa_status", "closed") or "closed",
            best_oa_location=best_location,
            all_oa_locations=all_locations,
        )
