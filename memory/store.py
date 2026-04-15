"""
Kiwi Memory Store — Persistent cross-session research memory.

Dual-format storage (inspired by sports_agent memory_agent.py):
- Episodic memory: chronological research history
- Semantic memory: topic-keyed knowledge base
- Research threads: named, persistent research projects
- User notes: manually saved insights

Storage: ~/.kiwi/memory.json + ~/.kiwi/memory.md (human-readable log)
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

KIWI_DIR = Path.home() / ".kiwi"
MEMORY_JSON = KIWI_DIR / "memory.json"
MEMORY_MD = KIWI_DIR / "memory.md"
ARCHIVE_JSON = KIWI_DIR / "episodic_archive.json"
EPISODIC_LIMIT = 50
SEMANTIC_STALE_DAYS = 90


class KiwiMemory:
    """
    Persistent cross-session memory for Kiwi.

    Structure:
      episodic:         list of {ts, query, response_preview, score}
      semantic:         dict of topic -> research_summary
      threads:          dict of thread_name -> {created, queries, context}
      user_notes:       list of {ts, note}
      user_preferences: dict
      session_count:    int
      total_queries:    int
    """

    def __init__(self):
        KIWI_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if MEMORY_JSON.exists():
            try:
                return json.loads(MEMORY_JSON.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return self._default()

    def _default(self) -> dict[str, Any]:
        return {
            "episodic": [],
            "semantic": {},
            "threads": {},
            "user_notes": [],
            "user_preferences": {},
            "session_count": 0,
            "total_queries": 0,
            "created_at": datetime.now().isoformat(),
            "last_session": None,
        }

    def save(self):
        MEMORY_JSON.write_text(json.dumps(self.data, indent=2, default=str))

    # ── Episodic Memory ──────────────────────────────────────────────────────

    def add_exchange(self, query: str, response: str, score: float, thread: str | None = None):
        """Record a completed research exchange to episodic memory."""
        entry = {
            "ts": datetime.now().isoformat(),
            "query": query[:500],
            "response_preview": response[:1200],
            "quality_score": round(score, 3),
            "thread": thread,
        }
        self.data["episodic"].append(entry)
        if len(self.data["episodic"]) > EPISODIC_LIMIT:
            overflow = self.data["episodic"][:-EPISODIC_LIMIT]
            self.data["episodic"] = self.data["episodic"][-EPISODIC_LIMIT:]
            self._archive_episodic(overflow)
        self.data["total_queries"] = self.data.get("total_queries", 0) + 1
        self.data["last_session"] = datetime.now().isoformat()

        # Also append to human-readable log
        self._append_md(
            f"[{entry['ts'][:10]}] Q: {query[:200]}",
            f"Score: {score:.2f}\n\n{response[:800]}"
        )

        # Update thread if active
        if thread and thread in self.data["threads"]:
            self.data["threads"][thread]["queries"].append(query[:200])
            self.data["threads"][thread]["last_updated"] = datetime.now().isoformat()

        self.save()

    def get_recent_episodic(self, n: int = 5) -> list[dict]:
        return self.data.get("episodic", [])[-n:]

    # ── Semantic Memory ──────────────────────────────────────────────────────

    def add_semantic(self, topic: str, knowledge: str):
        """Store research knowledge keyed by topic (overwrites — use for updates)."""
        self.data.setdefault("semantic", {})[topic.lower().strip()] = {
            "content": knowledge[:3000],
            "updated": datetime.now().isoformat(),
        }
        self.save()

    def get_semantic(self, topic: str) -> str:
        """Retrieve semantic knowledge for a topic."""
        entry = self.data.get("semantic", {}).get(topic.lower().strip(), {})
        return entry.get("content", "") if entry else ""

    def search_semantic(self, keywords: list[str]) -> list[tuple[str, str]]:
        """Fuzzy search semantic memory for matching topics."""
        results = []
        for topic, entry in self.data.get("semantic", {}).items():
            if any(kw.lower() in topic for kw in keywords):
                results.append((topic, entry.get("content", "")[:500]))
        return results[:5]

    # ── Research Threads ─────────────────────────────────────────────────────

    def create_thread(self, name: str, description: str = "") -> bool:
        """Create a named research thread. Returns False if name already exists."""
        if name in self.data.get("threads", {}):
            return False
        self.data.setdefault("threads", {})[name] = {
            "created": datetime.now().isoformat(),
            "description": description,
            "queries": [],
            "context": "",
            "last_updated": datetime.now().isoformat(),
        }
        self.save()
        return True

    def list_threads(self) -> list[dict]:
        return [
            {"name": k, **v}
            for k, v in self.data.get("threads", {}).items()
        ]

    def get_thread_context(self, name: str) -> str:
        thread = self.data.get("threads", {}).get(name, {})
        queries = thread.get("queries", [])
        context = thread.get("context", "")
        recent = "\n".join(f"- {q}" for q in queries[-5:])
        return f"Thread: {name}\nRecent queries:\n{recent}\nContext:\n{context}"

    def update_thread_context(self, name: str, context: str):
        if name in self.data.get("threads", {}):
            self.data["threads"][name]["context"] = context[:2000]
            self.save()

    # ── User Notes ───────────────────────────────────────────────────────────

    def add_note(self, note: str):
        self.data.setdefault("user_notes", []).append({
            "ts": datetime.now().isoformat(),
            "note": note,
        })
        self._append_md("User Note", note)
        self.save()

    def list_notes(self) -> list[dict]:
        return self.data.get("user_notes", [])

    # ── User Preferences ─────────────────────────────────────────────────────

    def set_preference(self, key: str, value: Any):
        self.data.setdefault("user_preferences", {})[key] = value
        self.save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.data.get("user_preferences", {}).get(key, default)

    # ── Session Management ───────────────────────────────────────────────────

    def start_session(self) -> int:
        count = self.data.get("session_count", 0) + 1
        self.data["session_count"] = count
        self.save()
        return count

    # ── Context Builders ─────────────────────────────────────────────────────

    def get_history_summary(self) -> str:
        """Format recent episodic history for context injection."""
        history = self.get_recent_episodic(5)
        if not history:
            return "No prior research history."
        return "\n".join(
            f"[{e['ts'][:10]}] (score: {e.get('quality_score', '?')}) {e['query'][:200]}"
            for e in history
        )

    def summary_dict(self) -> dict:
        """Summary for /memory display."""
        return {
            "sessions": self.data.get("session_count", 0),
            "total_queries": self.data.get("total_queries", 0),
            "notes_saved": len(self.data.get("user_notes", [])),
            "semantic_topics": len(self.data.get("semantic", {})),
            "research_threads": len(self.data.get("threads", {})),
            "last_session": self.data.get("last_session", "—"),
            "recent_queries": [
                e["query"][:120]
                for e in self.get_recent_episodic(5)
            ],
            "threads": [
                {"name": k, "queries": len(v.get("queries", []))}
                for k, v in list(self.data.get("threads", {}).items())[:5]
            ],
        }

    # ── Conversational Context ──────────────────────────────────────────────

    def get_conversational_context(self, query: str) -> str:
        """
        Build a memory context block for injection into synthesis/conversation.
        Keyword-matches query against episodic history, semantic memory, and user notes.
        Returns formatted string capped at ~1000 tokens.
        """
        keywords = [
            w.lower() for w in query.split()
            if len(w) > 3 and w.lower() not in {
                "what", "when", "where", "which", "about", "could",
                "would", "should", "have", "been", "this", "that",
                "with", "from", "they", "their", "there", "than",
                "does", "were", "more", "also", "into", "some",
            }
        ]
        if not keywords:
            return ""

        sections: list[str] = []

        # Episodic matches (max 3)
        episodic_hits = []
        for ep in reversed(self.data.get("episodic", [])):
            q_text = ep.get("query", "").lower()
            preview = ep.get("response_preview", "").lower()
            if any(kw in q_text or kw in preview for kw in keywords):
                date = ep.get("ts", "")[:10]
                score = ep.get("quality_score", "?")
                episodic_hits.append(
                    f"[{date}] (score: {score}) Q: {ep['query'][:150]}\n"
                    f"  → {ep.get('response_preview', '')[:200]}"
                )
            if len(episodic_hits) >= 3:
                break
        if episodic_hits:
            sections.append("Past conversations:\n" + "\n".join(episodic_hits))

        # Semantic matches (max 3)
        semantic_hits = self.search_semantic(keywords)[:3]
        if semantic_hits:
            sem_lines = [f"• {topic}: {content[:200]}" for topic, content in semantic_hits]
            sections.append("Related knowledge:\n" + "\n".join(sem_lines))

        # User notes matches (max 2)
        note_hits = []
        for note_entry in reversed(self.data.get("user_notes", [])):
            note_text = note_entry.get("note", "")
            if any(kw in note_text.lower() for kw in keywords):
                date = note_entry.get("ts", "")[:10]
                note_hits.append(f"[{date}] {note_text[:150]}")
            if len(note_hits) >= 2:
                break
        if note_hits:
            sections.append("User notes:\n" + "\n".join(note_hits))

        return "\n\n".join(sections) if sections else ""

    # ── Episodic Archive ──────────────────────────────────────────────────────

    def _archive_episodic(self, entries: list[dict]):
        """Move overflow episodic entries to archive file."""
        archive = []
        if ARCHIVE_JSON.exists():
            try:
                archive = json.loads(ARCHIVE_JSON.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        archive.extend(entries)
        ARCHIVE_JSON.write_text(json.dumps(archive, indent=2, default=str))

    def search_archive(self, keywords: list[str], max_results: int = 10) -> list[dict]:
        """Search archived episodic memory by keywords."""
        if not ARCHIVE_JSON.exists():
            return []
        try:
            archive = json.loads(ARCHIVE_JSON.read_text())
        except (json.JSONDecodeError, OSError):
            return []
        results = []
        kws = [k.lower() for k in keywords if len(k) > 2]
        if not kws:
            return archive[-max_results:]
        for entry in reversed(archive):
            q = entry.get("query", "").lower()
            r = entry.get("response_preview", "").lower()
            if any(kw in q or kw in r for kw in kws):
                results.append(entry)
            if len(results) >= max_results:
                break
        return results

    def archive_stats(self) -> dict:
        """Return archive size info."""
        if not ARCHIVE_JSON.exists():
            return {"archived_entries": 0}
        try:
            archive = json.loads(ARCHIVE_JSON.read_text())
            return {"archived_entries": len(archive)}
        except (json.JSONDecodeError, OSError):
            return {"archived_entries": 0}

    # ── Semantic Staleness ─────────────────────────────────────────────────────

    def get_semantic_with_staleness(self) -> list[dict]:
        """Return all semantic entries annotated with staleness."""
        now = datetime.now(timezone.utc)
        results = []
        for topic, entry in self.data.get("semantic", {}).items():
            content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
            updated = entry.get("updated", "") if isinstance(entry, dict) else ""
            days_old = 0
            is_stale = False
            try:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                days_old = (now - dt).days
                is_stale = days_old > SEMANTIC_STALE_DAYS
            except (ValueError, TypeError):
                is_stale = True
                days_old = -1
            results.append({
                "topic": topic,
                "content": content,
                "updated": updated,
                "days_old": days_old,
                "is_stale": is_stale,
            })
        return results

    # ── Human-Readable Log ───────────────────────────────────────────────────

    def _append_md(self, title: str, content: str):
        if not MEMORY_MD.exists():
            MEMORY_MD.write_text("# Kiwi Research Memory\n\n")
        with open(MEMORY_MD, "a") as f:
            f.write(f"\n## {title}\n\n{content.strip()}\n\n---\n")
