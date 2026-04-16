"""
Preferences Memory — Track accepted/rejected recommendations for learning.

Logs the practitioner's feedback on Kiwi's recommendations so future critique
and synthesis can be biased toward the practitioner's validated preferences
(e.g., "Nelson rejected high-dose vitamin C for endurance athletes — blunts
training adaptation").

Storage: per-client at ~/.kiwi/clients/<name>/preferences.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import client_manager


def _preferences_path(client: str | None = None) -> Path:
    return client_manager.get_client_dir(client) / "preferences.json"


class PreferencesStore:
    """Per-client preference tracking for Kiwi recommendations."""

    def __init__(self, client: str | None = None):
        self.client = client
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        path = _preferences_path(self.client)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"accepted": [], "rejected": [], "notes": []}

    def save(self):
        path = _preferences_path(self.client)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.data, indent=2, default=str))

    def record_accepted(self, recommendation: str, note: str = ""):
        self.data.setdefault("accepted", []).append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "recommendation": recommendation[:500],
            "note": note[:300],
        })
        self.save()

    def record_rejected(self, recommendation: str, reason: str = ""):
        self.data.setdefault("rejected", []).append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "recommendation": recommendation[:500],
            "reason": reason[:300],
        })
        self.save()

    def recent_accepted(self, n: int = 5) -> list[dict]:
        return self.data.get("accepted", [])[-n:]

    def recent_rejected(self, n: int = 5) -> list[dict]:
        return self.data.get("rejected", [])[-n:]

    def to_context_block(self) -> str:
        """Format preferences for injection into critique/synthesis prompts."""
        lines = []
        accepted = self.recent_accepted(5)
        rejected = self.recent_rejected(5)

        if accepted:
            lines.append("Recently accepted recommendations (practitioner validated):")
            for a in accepted:
                rec = a.get("recommendation", "")[:150]
                note = a.get("note", "")
                entry = f"  ✓ {rec}"
                if note:
                    entry += f" (note: {note[:100]})"
                lines.append(entry)

        if rejected:
            lines.append("Recently rejected recommendations (avoid repeating):")
            for r in rejected:
                rec = r.get("recommendation", "")[:150]
                reason = r.get("reason", "")
                entry = f"  ✗ {rec}"
                if reason:
                    entry += f" (reason: {reason[:100]})"
                lines.append(entry)

        return "\n".join(lines) if lines else ""

    def stats(self) -> dict:
        return {
            "total_accepted": len(self.data.get("accepted", [])),
            "total_rejected": len(self.data.get("rejected", [])),
        }
