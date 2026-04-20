"""Literature search command handlers (Tier 56).

Sync-only. All 6 handlers make blocking HTTP calls to literature APIs
(PubMed, Unpaywall, Semantic Scholar, ClinicalTrials, OpenAlex) wrapped
in rich console status spinners.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_pubmed(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /pubmed — NCBI PubMed search."""
    search_query = query[8:].strip()
    if search_query and kiwi.pubmed:
        with kiwi.console.status("[dim cyan]  Searching PubMed...[/dim cyan]", spinner="earth"):
            articles = kiwi.pubmed.search_and_fetch(search_query, max_results=8)
        if articles:
            for i, a in enumerate(articles, 1):
                kiwi.console.print(
                    f"\n[cyan][{i}][/cyan] [bold]{a.title}[/bold]\n"
                    f"[dim]{', '.join(a.authors[:2])} ({a.year}) · {a.journal}[/dim]\n"
                    f"PMID: {a.pmid}  DOI: {a.doi}\n"
                    f"{a.abstract[:400]}..."
                )
        else:
            kiwi.console.print("[dim]  No results found.[/dim]")
    elif not kiwi.pubmed:
        kiwi.console.print("[dim]  PubMed disabled (run without --no-pubmed).[/dim]")


def handle_fulltext(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /fulltext — Unpaywall OA lookup by DOI."""
    doi = query[10:].strip()
    if doi and kiwi.unpaywall:
        with kiwi.console.status("[dim cyan]  Looking up open access version via Unpaywall...[/dim cyan]", spinner="earth"):
            result = kiwi.unpaywall.lookup(doi)
        if result and result.is_oa:
            kiwi.console.print(Panel(
                result.summary(),
                title="[cyan]Open Access Available[/cyan]",
                border_style="green",
                box=box.SIMPLE,
            ))
        elif result:
            kiwi.console.print(f"[dim]  No OA version found for {doi}.[/dim]")
        else:
            kiwi.console.print("[dim]  DOI lookup failed.[/dim]")
    elif not kiwi.unpaywall:
        kiwi.console.print("[dim]  Unpaywall disabled (run without --no-pubmed).[/dim]")


def handle_tldr(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /tldr — Semantic Scholar TLDR summaries."""
    search_query = query[6:].strip()
    if search_query and kiwi.semantic:
        with kiwi.console.status("[dim cyan]  Fetching Semantic Scholar TLDRs...[/dim cyan]", spinner="earth"):
            papers = kiwi.semantic.search(search_query, max_results=8)
        if papers:
            for i, p in enumerate(papers, 1):
                tldr = p.tldr or "(no TLDR available)"
                kiwi.console.print(
                    f"\n[cyan][{i}][/cyan] [bold]{p.title}[/bold]\n"
                    f"[dim]{', '.join(p.authors[:2])} ({p.year}) · {p.journal} · cited {p.citation_count}x[/dim]\n"
                    f"[green]TLDR:[/green] {tldr}\n"
                    f"DOI: {p.doi}"
                )
        else:
            kiwi.console.print("[dim]  No papers found.[/dim]")
    elif not kiwi.semantic:
        kiwi.console.print("[dim]  Semantic Scholar disabled (run without --no-pubmed).[/dim]")


def handle_trials(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /trials — ClinicalTrials.gov search."""
    search_query = query[8:].strip()
    if search_query and kiwi.trials:
        with kiwi.console.status("[dim cyan]  Searching ClinicalTrials.gov...[/dim cyan]", spinner="earth"):
            results = kiwi.trials.search(search_query, max_results=8)
        if results:
            for i, t in enumerate(results, 1):
                kiwi.console.print(
                    f"\n[cyan][{i}][/cyan] [bold]{t.title}[/bold]\n"
                    f"[dim]{t.status} · Phase {t.phase} · N={t.enrollment} · {t.sponsor}[/dim]\n"
                    f"NCT: {t.nct_id}\n"
                    f"Conditions: {', '.join(t.conditions[:3])}\n"
                    f"Interventions: {', '.join(t.interventions[:3])}\n"
                    f"{t.brief_summary[:300]}..."
                )
        else:
            kiwi.console.print("[dim]  No trials found.[/dim]")
    elif not kiwi.trials:
        kiwi.console.print("[dim]  ClinicalTrials disabled (run without --no-pubmed).[/dim]")


def handle_citedby(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /citedby — OpenAlex forward-citation lookup by DOI."""
    doi = query[9:].strip()
    if doi and kiwi.openalex:
        with kiwi.console.status(f"[dim cyan]  Finding papers that cite {doi}...[/dim cyan]", spinner="earth"):
            works = kiwi.openalex.fetch_cited_by(doi, max_results=10)
        if works:
            kiwi.console.print(f"[dim]  Found {len(works)} papers citing {doi}[/dim]")
            for i, w in enumerate(works, 1):
                oa_tag = " [OA]" if w.open_access else ""
                kiwi.console.print(
                    f"\n[cyan][{i}][/cyan] [bold]{w.title}[/bold]\n"
                    f"[dim]{', '.join(w.authors[:2])} ({w.year}) · {w.journal}{oa_tag}[/dim]\n"
                    f"DOI: {w.doi}  Cited: {w.cited_by_count}"
                )
        else:
            kiwi.console.print("[dim]  No citations found (or DOI invalid).[/dim]")
    elif not kiwi.openalex:
        kiwi.console.print("[dim]  OpenAlex disabled (run without --no-pubmed).[/dim]")


def handle_openalex(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /openalex — sports-nutrition-filtered OpenAlex search."""
    search_query = query[10:].strip()
    if search_query and kiwi.openalex:
        with kiwi.console.status("[dim cyan]  Searching OpenAlex (sports nutrition journals)...[/dim cyan]", spinner="earth"):
            works = kiwi.openalex.search_sports_nutrition(search_query, max_results=8)
        if works:
            for i, w in enumerate(works, 1):
                oa_tag = " [OA]" if w.open_access else ""
                kiwi.console.print(
                    f"\n[cyan][{i}][/cyan] [bold]{w.title}[/bold]\n"
                    f"[dim]{', '.join(w.authors[:2])} ({w.year}) · {w.journal}{oa_tag}[/dim]\n"
                    f"DOI: {w.doi}  Cited: {w.cited_by_count}\n"
                    f"{w.abstract[:400]}..."
                )
        else:
            kiwi.console.print("[dim]  No results found.[/dim]")
    elif not kiwi.openalex:
        kiwi.console.print("[dim]  OpenAlex disabled (run without --no-pubmed).[/dim]")
