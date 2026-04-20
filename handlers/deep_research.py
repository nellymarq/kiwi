"""Deep-research command handlers (Tier 63).

Mixed sync + async. /synthesize /review /n_of_1 /recommend are async
(invoke agents). /effect /readpdf /autoquality /quality /grade are sync.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.auto_quality import auto_assess as auto_quality_assess
from tools.effect_size import (
    cohens_d,
    hedges_g,
    mean_difference,
    number_needed_to_treat,
    odds_ratio,
    relative_risk,
)
from tools.grade import assess_from_evidence_tier
from tools.injury_prevention import (
    format_prevention_protocol,
    get_prevention_protocol,
    match_prevention_protocol,
)
from tools.interactions import lookup_interactions
from tools.pdf_reader import read_pdf as read_oa_pdf
from tools.quality_assessment import format_checklist as quality_checklist
from tools.supplements import SUPPLEMENT_DB

if TYPE_CHECKING:
    from kiwi import Kiwi


async def handle_synthesize(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /synthesize — SynthesisAgent with multi-source literature context."""
    from kiwi import fetch_literature_context  # lazy import — kiwi.py defines this
    claim = query[12:].strip()
    if claim:
        kiwi.console.print(f"[dim]  Gathering evidence for synthesis: '{claim}'...[/dim]")
        papers_ctx = fetch_literature_context(
            claim, kiwi.pubmed, kiwi.openalex, kiwi.epmc, kiwi.semantic,
            max_pubmed=8, max_openalex=5, max_epmc=5, max_semantic=5,
        )
        if not papers_ctx:
            kiwi.console.print("[dim red]  No literature found for this claim.[/dim red]")
        else:
            kiwi.console.print("[dim]  Running structured synthesis with GRADE assessment...[/dim]\n")
            result = await kiwi.synthesis_agent.run({
                "claim": claim,
                "papers_context": papers_ctx,
                "profile_summary": kiwi.profile.to_summary() if kiwi.profile.is_complete() else "",
            })
            kiwi._state["last_output"] = result
            kiwi.console.print(result)


async def handle_review(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /review — PRISMA-compliant systematic review."""
    from kiwi import fetch_literature_context
    topic = query[8:].strip()
    if topic:
        kiwi.console.print(f"[dim]  Conducting systematic review on: '{topic}'...[/dim]")
        papers_ctx = fetch_literature_context(
            topic, kiwi.pubmed, kiwi.openalex, kiwi.epmc, kiwi.semantic,
            max_pubmed=10, max_openalex=8, max_epmc=8, max_semantic=8,
            years_back=10,
        )
        if not papers_ctx:
            kiwi.console.print("[dim red]  No literature retrieved. Cannot conduct review.[/dim red]")
        else:
            kiwi.console.print("[dim]  Running PRISMA-compliant systematic review...[/dim]\n")
            result = await kiwi.systematic_review_agent.run({
                "question": topic,
                "papers_context": papers_ctx,
                "profile_summary": kiwi.profile.to_summary() if kiwi.profile.is_complete() else "",
            })
            kiwi._state["last_output"] = result
            kiwi.console.print(result)


async def handle_n_of_1(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /n_of_1 — n-of-1 experimental design."""
    from kiwi import fetch_literature_context
    offset = 8 if q_lower.startswith("/n_of_1 ") else 6
    question = query[offset:].strip()
    if question:
        research_ctx = ""
        if kiwi.pubmed or kiwi.openalex:
            research_ctx = fetch_literature_context(
                question, kiwi.pubmed, kiwi.openalex, kiwi.epmc, kiwi.semantic,
            )
        kiwi.console.print("[dim]  Designing n-of-1 experimental protocol...[/dim]\n")
        result = await kiwi.n_of_1_agent.run({
            "question": question,
            "research_context": research_ctx,
            "profile_summary": kiwi.profile.to_summary() if kiwi.profile.is_complete() else "",
        })
        kiwi._state["last_output"] = result
        kiwi.console.print(result)


def handle_effect(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /effect — Cohen's d / Hedges' g / RR / OR / NNT."""
    parts = query[8:].strip().split()
    if len(parts) == 6:
        try:
            m1, sd1, n1, m2, sd2, n2 = (
                float(parts[0]), float(parts[1]), int(parts[2]),
                float(parts[3]), float(parts[4]), int(parts[5]),
            )
            d_result = cohens_d(m1, sd1, n1, m2, sd2, n2)
            g_result = hedges_g(m1, sd1, n1, m2, sd2, n2)
            md_result = mean_difference(m1, sd1, n1, m2, sd2, n2)
            kiwi.console.print(Panel(
                f"{d_result.display()}\n\n"
                f"{g_result.display()}\n\n"
                f"{md_result.display()}",
                title="[cyan]Effect Size Analysis[/cyan]",
                border_style="cyan",
                box=box.SIMPLE,
            ))
        except (ValueError, ZeroDivisionError) as e:
            kiwi.console.print(f"[dim red]  Error: {e}[/dim red]")
    elif len(parts) == 4:
        try:
            ea, ta, eb, tb = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            rr = relative_risk(ea, ta, eb, tb)
            or_val = odds_ratio(ea, ta, eb, tb)
            nnt = number_needed_to_treat(ea, ta, eb, tb)
            kiwi.console.print(Panel(
                f"{rr.display()}\n\n"
                f"{or_val.display()}\n\n"
                f"NNT: {nnt['interpretation']}",
                title="[cyan]Effect Size (Dichotomous)[/cyan]",
                border_style="cyan",
                box=box.SIMPLE,
            ))
        except ValueError as e:
            kiwi.console.print(f"[dim red]  Error: {e}[/dim red]")
    else:
        kiwi.console.print(
            "[dim]  Usage for continuous: /effect <mean1> <sd1> <n1> <mean2> <sd2> <n2>[/dim]\n"
            "[dim]  Usage for dichotomous: /effect <events_a> <total_a> <events_b> <total_b>[/dim]"
        )


def handle_readpdf(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /readpdf — download+extract OA PDF via Unpaywall."""
    doi = query[9:].strip()
    if doi and kiwi.unpaywall:
        kiwi.console.print(f"[dim]  Looking up OA version for {doi}...[/dim]")
        pdf = read_oa_pdf(doi, kiwi.unpaywall)
        if pdf:
            kiwi.console.print(f"[dim]  Extracted {pdf.extracted_chars:,} chars across {pdf.num_pages} pages[/dim]")
            kiwi.console.print(f"[dim]  Cached at: {pdf.cached_path}[/dim]\n")
            sections = pdf.sections()
            if sections:
                kiwi.console.print("[cyan]Detected sections:[/cyan]")
                for section_name in sections:
                    kiwi.console.print(f"  • {section_name}")
            kiwi.console.print("\n[cyan]Preview (first 2000 chars):[/cyan]\n")
            kiwi.console.print(pdf.preview(2000))
        else:
            kiwi.console.print("[dim red]  Could not retrieve PDF (no OA version or extraction failed).[/dim red]")
    elif not kiwi.unpaywall:
        kiwi.console.print("[dim]  Unpaywall disabled (run without --no-pubmed).[/dim]")


def handle_autoquality(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /autoquality — heuristic paper-quality triage from title."""
    payload = query[13:].strip()
    if payload:
        flag = auto_quality_assess(payload)
        kiwi.console.print(Panel(
            flag.display(),
            title="[cyan]Auto Quality Assessment[/cyan]",
            border_style="cyan",
            box=box.SIMPLE,
        ))
    else:
        kiwi.console.print("[dim]  Usage: /autoquality <paper title or title + abstract>[/dim]")


async def handle_recommend(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /recommend — cross-tool supplement recommendation w/ Tier 31 enrichment."""
    finding = query[11:].strip()
    if finding:
        kiwi.console.print(f"[dim]  Chaining tools for finding: '{finding}'...[/dim]")
        profile_summary = kiwi.profile.to_summary() if kiwi.profile.is_complete() else ""
        current_supps = kiwi.profile.get("current_supplements") or []

        supp_options_parts = []
        keywords = [w.lower() for w in finding.split() if len(w) > 3]
        for key, proto in SUPPLEMENT_DB.items():
            text_blob = (
                proto.name + " " + proto.mechanism + " "
                + " ".join(proto.sport_specific_notes.values())
            ).lower()
            if any(kw in text_blob for kw in keywords):
                supp_options_parts.append(
                    f"• {proto.name} — {proto.maintenance_dose} — "
                    f"Evidence: {proto.evidence}"
                )
        supp_options = "\n".join(supp_options_parts[:10]) or "(no direct matches in DB)"

        interaction_text = ""
        if current_supps:
            all_compounds = current_supps + [
                p.name for key, p in SUPPLEMENT_DB.items()
                if any(kw in p.name.lower() for kw in keywords)
            ][:5]
            if len(all_compounds) > 1:
                interactions = lookup_interactions(all_compounds, min_severity="safe")
                if interactions:
                    interaction_text = "\n".join(
                        f"• {i.compound_a} + {i.compound_b}: {i.severity} — {i.recommendation[:150]}"
                        for i in interactions[:10]
                    )
                else:
                    interaction_text = "No significant interactions detected with current stack."
            else:
                interaction_text = "Current stack has too few items to cross-check."
        else:
            interaction_text = "No current supplement stack on file."

        prevention_text = ""
        matched_key = match_prevention_protocol(finding)
        if matched_key:
            proto = get_prevention_protocol(matched_key)
            if proto:
                sport = kiwi.profile.data.get("sport", "general")
                prevention_text = format_prevention_protocol(proto, sport)

        kiwi.console.print("[dim]  Synthesizing integrated recommendation...[/dim]\n")
        result = await kiwi.recommender_agent.run({
            "finding": finding,
            "profile_summary": profile_summary,
            "biomarker_interpretation": "",
            "supplement_options": supp_options,
            "interaction_check": interaction_text,
            "prevention_protocol": prevention_text,
        })
        kiwi._state["last_output"] = result
        kiwi.console.print(result)


def handle_quality(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /quality — list quality-assessment checklist (RoB2, ROBINS-I, AMSTAR2)."""
    tool = query[8:].strip() if len(query) > 8 else ""
    if not tool:
        kiwi.console.print(
            "[dim]  Usage: /quality <tool>  where tool = RoB2 | ROBINS-I | AMSTAR2[/dim]\n"
            "[dim]  RoB2 — for randomized trials (Cochrane 2019)[/dim]\n"
            "[dim]  ROBINS-I — for non-randomized observational studies[/dim]\n"
            "[dim]  AMSTAR2 — for systematic reviews/meta-analyses[/dim]"
        )
    else:
        try:
            checklist = quality_checklist(tool)
            kiwi.console.print(Panel(
                checklist,
                title="[cyan]Quality Assessment Checklist[/cyan]",
                border_style="cyan",
                box=box.SIMPLE,
            ))
        except ValueError as e:
            kiwi.console.print(f"[dim red]  {e}[/dim red]")


def handle_grade(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /grade — convert Kiwi evidence tier emoji to GRADE certainty."""
    tier = query[7:].strip()
    if tier in ("🟢", "🟡", "🟠", "🔵"):
        assessment = assess_from_evidence_tier(tier)
        kiwi.console.print(Panel(
            assessment.display(),
            title="[cyan]GRADE Assessment[/cyan]",
            border_style="cyan",
            box=box.SIMPLE,
        ))
    else:
        kiwi.console.print("[dim]  Usage: /grade 🟢 (or 🟡/🟠/🔵) — converts tier to GRADE certainty level.[/dim]")
        kiwi.console.print("[dim]  For structured GRADE assessment of a claim, use /synthesize <claim>[/dim]")
