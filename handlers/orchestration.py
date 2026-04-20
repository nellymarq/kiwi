"""Living-review orchestration handlers (Tier 60).

Sync. /watch, /unwatch, /watched/watchlist, /digest.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_watch(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /watch <topic> — add to watch list."""
    topic = query[7:].strip()
    if topic:
        if kiwi.watch_list.add(topic):
            kiwi.console.print(f"[dim]  Watching: [cyan]{topic}[/cyan]. Run /digest to get updates.[/dim]")
        else:
            kiwi.console.print(f"[dim]  Already watching '{topic}'.[/dim]")


def handle_unwatch(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /unwatch <topic>."""
    topic = query[9:].strip()
    if kiwi.watch_list.remove(topic):
        kiwi.console.print(f"[dim]  Removed watch on: {topic}[/dim]")
    else:
        kiwi.console.print(f"[dim]  Not in watch list: {topic}[/dim]")


def handle_watched(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /watched (alias /watchlist) — show watched topics."""
    topics = kiwi.watch_list.list_topics()
    if not topics:
        kiwi.console.print("[dim]  No watched topics. Add with /watch <topic>[/dim]")
    else:
        lines = []
        for t in topics:
            last = t.get("last_digest_ts", "never")[:10] if t.get("last_digest_ts") else "never digested"
            lines.append(f"  • [cyan]{t['topic']}[/cyan] — added {t.get('added_ts', '')[:10]}, last digest: {last}")
        kiwi.console.print(Panel(
            "\n".join(lines),
            title="[cyan]Watched Topics[/cyan]",
            border_style="cyan", box=box.SIMPLE,
        ))


def handle_digest(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /digest — new-papers-since-last-run for all watched topics."""
    topics = kiwi.watch_list.list_topics()
    if not topics:
        kiwi.console.print("[dim]  No watched topics. Add with /watch <topic>[/dim]")
    elif not (kiwi.pubmed or kiwi.openalex):
        kiwi.console.print("[dim]  Literature sources disabled. Run without --no-pubmed.[/dim]")
    else:
        kiwi.console.print(f"[dim]  Running digest for {len(topics)} watched topic(s)...[/dim]\n")
        for t in topics:
            topic_text = t["topic"]
            previous_seen = kiwi.watch_list.get_last_seen(topic_text)
            keywords = " ".join(topic_text.split()[:6])

            all_items = []
            all_dois = []

            if kiwi.pubmed:
                arts = kiwi.pubmed.search_and_fetch(keywords, max_results=5, years_back=2)
                for a in arts:
                    doi_l = (a.doi or "").lower()
                    is_new = doi_l and doi_l not in previous_seen
                    all_items.append((is_new, a.title, a.authors, a.year, a.doi, "PubMed"))
                    if doi_l:
                        all_dois.append(doi_l)

            if kiwi.openalex:
                works = kiwi.openalex.search_sports_nutrition(keywords, max_results=5, years_back=2)
                for w in works:
                    doi_l = (w.doi or "").lower()
                    is_new = doi_l and doi_l not in previous_seen
                    all_items.append((is_new, w.title, w.authors, str(w.year), w.doi, "OpenAlex"))
                    if doi_l:
                        all_dois.append(doi_l)

            new_items = [x for x in all_items if x[0]]
            kiwi.console.print(f"[bold]Topic: {topic_text}[/bold] — {len(new_items)} new, {len(all_items) - len(new_items)} already seen")
            for is_new, title, authors, year, doi, source in new_items[:8]:
                badge = "[green]NEW[/green]"
                author_str = ", ".join(authors[:2]) if authors else "?"
                kiwi.console.print(f"  {badge} {title[:100]}")
                kiwi.console.print(f"    [dim]{author_str} ({year}) · {source} · DOI: {doi}[/dim]")

            kiwi.watch_list.mark_digest_run(topic_text, all_dois)
            kiwi.console.print()

        kiwi.watch_list.update_global_digest_ts()
