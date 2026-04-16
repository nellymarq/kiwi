"""
Cost Tracker — Monitor API token usage per session.

Pricing based on Anthropic's published rates for Claude Opus 4.6 (as of 2026).
Tracks input tokens, output tokens, and cache hits separately.

Call sites emit usage via record(). Session totals available via summary().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Pricing per 1M tokens (USD) — Claude Opus 4.6 published rates
PRICING_PER_1M = {
    "claude-opus-4-6": {"input": 15.00, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25},
}

DEFAULT_MODEL_PRICING = PRICING_PER_1M["claude-opus-4-6"]


@dataclass
class CostEntry:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    purpose: str = ""

    def cost_usd(self) -> float:
        pricing = PRICING_PER_1M.get(self.model, DEFAULT_MODEL_PRICING)
        return (
            (self.input_tokens / 1_000_000) * pricing["input"]
            + (self.output_tokens / 1_000_000) * pricing["output"]
            + (self.cache_read_tokens / 1_000_000) * pricing["cache_read"]
            + (self.cache_write_tokens / 1_000_000) * pricing["cache_write"]
        )


@dataclass
class SessionCostTracker:
    entries: list[CostEntry] = field(default_factory=list)

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        purpose: str = "",
    ):
        self.entries.append(CostEntry(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            purpose=purpose,
        ))

    def record_from_response(self, model: str, response: Any, purpose: str = ""):
        """Extract usage from an Anthropic API response and record it."""
        usage = getattr(response, "usage", None)
        if not usage:
            return
        input_tok = getattr(usage, "input_tokens", 0) or 0
        output_tok = getattr(usage, "output_tokens", 0) or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        self.record(
            model=model,
            input_tokens=input_tok,
            output_tokens=output_tok,
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
            purpose=purpose,
        )

    def total_cost_usd(self) -> float:
        return sum(e.cost_usd() for e in self.entries)

    def total_input_tokens(self) -> int:
        return sum(e.input_tokens for e in self.entries)

    def total_output_tokens(self) -> int:
        return sum(e.output_tokens for e in self.entries)

    def call_count(self) -> int:
        return len(self.entries)

    def by_model(self) -> dict[str, dict]:
        summary: dict[str, dict] = {}
        for e in self.entries:
            s = summary.setdefault(e.model, {"calls": 0, "input": 0, "output": 0, "cost": 0.0})
            s["calls"] += 1
            s["input"] += e.input_tokens
            s["output"] += e.output_tokens
            s["cost"] += e.cost_usd()
        return summary

    def by_purpose(self) -> dict[str, dict]:
        summary: dict[str, dict] = {}
        for e in self.entries:
            key = e.purpose or "(unspecified)"
            s = summary.setdefault(key, {"calls": 0, "cost": 0.0})
            s["calls"] += 1
            s["cost"] += e.cost_usd()
        return summary

    def summary(self) -> str:
        if not self.entries:
            return "No API calls made this session."

        lines = [
            f"Session API usage:",
            f"  Total calls: {self.call_count()}",
            f"  Input tokens: {self.total_input_tokens():,}",
            f"  Output tokens: {self.total_output_tokens():,}",
            f"  Total cost: ${self.total_cost_usd():.4f}",
            "",
            "By model:",
        ]
        for model, s in sorted(self.by_model().items(), key=lambda x: -x[1]["cost"]):
            lines.append(
                f"  {model}: {s['calls']} calls · "
                f"{s['input']:,} in / {s['output']:,} out · ${s['cost']:.4f}"
            )

        by_purpose = self.by_purpose()
        if by_purpose and any(p != "(unspecified)" for p in by_purpose):
            lines.append("")
            lines.append("By purpose:")
            for purpose, s in sorted(by_purpose.items(), key=lambda x: -x[1]["cost"]):
                lines.append(f"  {purpose}: {s['calls']} calls · ${s['cost']:.4f}")

        return "\n".join(lines)

    def reset(self):
        self.entries.clear()
