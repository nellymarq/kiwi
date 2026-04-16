"""
ClinicalTrials.gov Client — Free access to 500K+ registered clinical trials.

Provides evidence on ongoing and completed studies beyond what's published
in PubMed/OpenAlex. Useful for:
- Supplement efficacy trials (many not yet published)
- Sports nutrition intervention studies
- Multi-arm comparative trials
- Trials by phase (Phase 3 = registration-quality evidence)

API docs: https://clinicaltrials.gov/data-api/api
No API key required, no rate limit documented (reasonable throttling applied).
"""

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

CT_BASE = "https://clinicaltrials.gov/api/v2"
REQUEST_DELAY = 0.2  # polite 5 req/s max
_last_request: float = 0.0


@dataclass
class ClinicalTrial:
    nct_id: str
    title: str
    status: str          # RECRUITING, COMPLETED, TERMINATED, etc.
    phase: str           # PHASE1, PHASE2, PHASE3, PHASE4, NA
    study_type: str      # INTERVENTIONAL, OBSERVATIONAL
    conditions: list[str]
    interventions: list[str]
    primary_outcomes: list[str]
    enrollment: int = 0
    sponsor: str = ""
    start_date: str = ""
    completion_date: str = ""
    brief_summary: str = ""

    def to_context_block(self) -> str:
        interventions_str = "; ".join(self.interventions[:3])
        conditions_str = "; ".join(self.conditions[:3])
        outcomes_str = "; ".join(self.primary_outcomes[:2])
        return (
            f"NCT ID: {self.nct_id}\n"
            f"Title: {self.title}\n"
            f"Status: {self.status}  |  Phase: {self.phase}  |  N={self.enrollment}\n"
            f"Sponsor: {self.sponsor}\n"
            f"Conditions: {conditions_str}\n"
            f"Interventions: {interventions_str}\n"
            f"Primary Outcomes: {outcomes_str}\n"
            f"Summary: {self.brief_summary[:800]}"
        )


class ClinicalTrialsClient:
    """ClinicalTrials.gov API v2 client for trial search and retrieval."""

    def _get(self, url: str, max_retries: int = 2) -> dict | None:
        global _last_request
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
        status_filter: str | None = None,
        phase_filter: str | None = None,
    ) -> list[ClinicalTrial]:
        """
        Search ClinicalTrials.gov for trials matching the query.

        Args:
            query: search terms (condition, intervention, etc.)
            max_results: max trials to return
            status_filter: e.g., "RECRUITING" or "COMPLETED"
            phase_filter: e.g., "PHASE3"
        """
        params = {
            "query.term": query,
            "pageSize": str(max_results),
            "format": "json",
        }
        if status_filter:
            params["filter.overallStatus"] = status_filter
        if phase_filter:
            params["filter.advanced"] = f"AREA[Phase]{phase_filter}"

        url = f"{CT_BASE}/studies?{urllib.parse.urlencode(params)}"
        data = self._get(url)
        if not data or "studies" not in data:
            return []

        trials = []
        for study in data["studies"][:max_results]:
            p = study.get("protocolSection", {})
            ident = p.get("identificationModule", {}) or {}
            status = p.get("statusModule", {}) or {}
            design = p.get("designModule", {}) or {}
            desc = p.get("descriptionModule", {}) or {}
            conditions_mod = p.get("conditionsModule", {}) or {}
            interventions_mod = p.get("armsInterventionsModule", {}) or {}
            outcomes_mod = p.get("outcomesModule", {}) or {}
            sponsor_mod = p.get("sponsorCollaboratorsModule", {}) or {}

            phases = design.get("phases", []) or []
            interventions = [
                iv.get("name", "")
                for iv in interventions_mod.get("interventions", []) or []
            ]
            primary_outcomes = [
                po.get("measure", "")
                for po in outcomes_mod.get("primaryOutcomes", []) or []
            ]

            trials.append(ClinicalTrial(
                nct_id=ident.get("nctId", ""),
                title=ident.get("briefTitle", ""),
                status=status.get("overallStatus", ""),
                phase=(phases[0] if phases else "NA"),
                study_type=design.get("studyType", ""),
                conditions=conditions_mod.get("conditions", []) or [],
                interventions=[i for i in interventions if i],
                primary_outcomes=[o for o in primary_outcomes if o],
                enrollment=(design.get("enrollmentInfo", {}) or {}).get("count", 0),
                sponsor=(sponsor_mod.get("leadSponsor", {}) or {}).get("name", ""),
                start_date=(status.get("startDateStruct", {}) or {}).get("date", ""),
                completion_date=(status.get("completionDateStruct", {}) or {}).get("date", ""),
                brief_summary=desc.get("briefSummary", ""),
            ))

        return trials

    def build_context_block(self, trials: list[ClinicalTrial]) -> str:
        """Format trials into a context block for Claude."""
        if not trials:
            return ""
        blocks = [f"=== ClinicalTrials.gov Results ({len(trials)} trials) ===\n"]
        for i, trial in enumerate(trials, 1):
            blocks.append(f"\n[{i}] {trial.to_context_block()}")
            blocks.append("-" * 60)
        return "\n".join(blocks)
