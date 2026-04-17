"""
Session Persistence — Save and resume research sessions across restarts.

Sessions stored at ~/.kiwi/clients/<name>/sessions/<session_id>.json
Each session captures: messages, thread, timestamp, summary.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import client_manager


def _sessions_dir(client: str | None = None) -> Path:
    d = client_manager.get_client_dir(client) / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session_path(session_id: str, client: str | None = None) -> Path:
    safe_id = re.sub(r"[^\w\-]", "_", session_id)[:60]
    return _sessions_dir(client) / f"{safe_id}.json"


def save_session(
    session_id: str,
    messages: list[dict],
    thread: str | None = None,
    summary: str = "",
    client: str | None = None,
) -> Path:
    """Save a session to disk. Returns the file path."""
    # Serialize messages — handle content blocks that aren't plain strings
    serializable_messages = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
            content = "\n".join(text_parts)
        serializable_messages.append({
            "role": msg.get("role", "user"),
            "content": content[:5000] if isinstance(content, str) else str(content)[:5000],
        })

    data = {
        "session_id": session_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "thread": thread,
        "summary": summary[:500],
        "message_count": len(serializable_messages),
        "messages": serializable_messages,
    }

    path = _session_path(session_id, client)
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


def load_session(session_id: str, client: str | None = None) -> dict[str, Any] | None:
    """Load a saved session. Returns None if not found."""
    path = _session_path(session_id, client)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_sessions(client: str | None = None) -> list[dict]:
    """List all saved sessions for a client, most recent first."""
    sessions_dir = _sessions_dir(client)
    results = []
    for f in sorted(sessions_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            results.append({
                "session_id": data.get("session_id", f.stem),
                "saved_at": data.get("saved_at", ""),
                "thread": data.get("thread"),
                "summary": data.get("summary", ""),
                "message_count": data.get("message_count", 0),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return results[:20]  # Cap at 20 most recent


def delete_session(session_id: str, client: str | None = None) -> bool:
    """Delete a saved session. Returns True if deleted."""
    path = _session_path(session_id, client)
    if path.exists():
        path.unlink()
        return True
    return False
