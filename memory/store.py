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
from datetime import datetime
from pathlib import Path
from typing import Any

KIWI_DIR = Path.home() / ".kiwi"
MEMORY_JSON = KIWI_DIR / "memory.json"
MEMORY_MD = KIWI_DIR / "memory.md"


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
        self.data["episodic"] = self.data["episodic"][-50:]  # keep last 50
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

    # ── Human-Readable Log ───────────────────────────────────────────────────

    def _append_md(self, title: str, content: str):
        if not MEMORY_MD.exists():
            MEMORY_MD.write_text("# Kiwi Research Memory\n\n")
        with open(MEMORY_MD, "a") as f:
            f.write(f"\n## {title}\n\n{content.strip()}\n\n---\n")
