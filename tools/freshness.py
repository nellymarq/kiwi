"""
Evidence Freshness Checker — Flag stale references in supplement/biomarker data.

Scans reference years in DosingProtocol and BiomarkerRef entries and flags
those older than a configurable threshold (default 5 years).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


FRESHNESS_THRESHOLD_YEARS = 5


@dataclass
class FreshnessFlag:
    source: str        # "supplement" or "biomarker"
    item_name: str
    reference: str
    year: int
    age_years: int
    severity: str      # "stale", "aging", "current"


def _extract_years(text: str) -> list[int]:
    """Extract 4-digit years from text."""
    return [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]


def _newest_year(references: list[str]) -> int | None:
    """Find the most recent year across a list of references."""
    all_years = []
    for ref in references:
        all_years.extend(_extract_years(ref))
    return max(all_years) if all_years else None


def check_supplement_freshness() -> list[FreshnessFlag]:
    """Check all supplement DB entries for evidence staleness."""
    from kiwi_core.tools.supplements import SUPPLEMENT_DB

    current_year = date.today().year
    flags = []

    for key, proto in SUPPLEMENT_DB.items():
        newest = _newest_year(proto.key_references)
        if newest is None:
            continue
        age = current_year - newest
        if age >= FRESHNESS_THRESHOLD_YEARS * 2:
            severity = "stale"
        elif age >= FRESHNESS_THRESHOLD_YEARS:
            severity = "aging"
        else:
            severity = "current"

        if severity != "current":
            # Find the specific old reference
            for ref in proto.key_references:
                years = _extract_years(ref)
                if years and max(years) == newest:
                    flags.append(FreshnessFlag(
                        source="supplement",
                        item_name=proto.name,
                        reference=ref,
                        year=newest,
                        age_years=age,
                        severity=severity,
                    ))
                    break

    flags.sort(key=lambda f: f.age_years, reverse=True)
    return flags


def check_biomarker_freshness() -> list[FreshnessFlag]:
    """Check all biomarker DB entries for evidence staleness."""
    from kiwi_core.tools.biomarkers import BIOMARKER_DB

    current_year = date.today().year
    flags = []

    for key, ref in BIOMARKER_DB.items():
        if not ref.evidence:
            continue
        years = _extract_years(ref.evidence)
        if not years:
            continue
        newest = max(years)
        age = current_year - newest
        if age >= FRESHNESS_THRESHOLD_YEARS * 2:
            severity = "stale"
        elif age >= FRESHNESS_THRESHOLD_YEARS:
            severity = "aging"
        else:
            severity = "current"

        if severity != "current":
            flags.append(FreshnessFlag(
                source="biomarker",
                item_name=ref.name,
                reference=ref.evidence,
                year=newest,
                age_years=age,
                severity=severity,
            ))

    flags.sort(key=lambda f: f.age_years, reverse=True)
    return flags


def format_freshness_report() -> str:
    """Full freshness report across supplements and biomarkers."""
    supp_flags = check_supplement_freshness()
    bio_flags = check_biomarker_freshness()

    all_flags = supp_flags + bio_flags
    if not all_flags:
        return "All evidence references are current (within last 5 years)."

    stale = [f for f in all_flags if f.severity == "stale"]
    aging = [f for f in all_flags if f.severity == "aging"]

    lines = ["Evidence Freshness Report", "=" * 40, ""]

    if stale:
        lines.append(f"🔴 Stale (>{FRESHNESS_THRESHOLD_YEARS * 2} years): {len(stale)}")
        for f in stale[:10]:
            lines.append(f"  {f.item_name} ({f.source}) — {f.year} ({f.age_years}y old)")
            lines.append(f"    {f.reference[:100]}")
        lines.append("")

    if aging:
        lines.append(f"🟡 Aging (>{FRESHNESS_THRESHOLD_YEARS} years): {len(aging)}")
        for f in aging[:10]:
            lines.append(f"  {f.item_name} ({f.source}) — {f.year} ({f.age_years}y old)")
        lines.append("")

    current_supps = len([1 for _ in __import__("kiwi_core.tools.supplements", fromlist=["SUPPLEMENT_DB"]).SUPPLEMENT_DB]) - len(supp_flags)
    lines.append(f"Summary: {current_supps} current, {len(aging)} aging, {len(stale)} stale")
    lines.append("Consider: /pubmed <topic> 2024-2026 to check for updates")

    return "\n".join(lines)
