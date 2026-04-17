"""
Contradiction Detector — Flag conflicts between new evidence and stored knowledge.

When a research response or synthesis contains claims that contradict what's in
semantic memory, this module identifies the conflict and presents both versions
for the practitioner to resolve.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class Contradiction:
    topic: str
    stored_claim: str
    new_claim: str
    confidence: float  # 0.0-1.0 — how confident the detector is this is a real contradiction

    def display(self) -> str:
        return (
            f"⚡ Potential contradiction: {self.topic}\n"
            f"   Stored: {self.stored_claim[:200]}\n"
            f"   New:    {self.new_claim[:200]}\n"
            f"   Confidence: {self.confidence:.0%}"
        )


# Keywords that signal contradicting positions
CONTRADICTION_SIGNALS = [
    (r"no (significant |meaningful )?effect", r"(significant|clear|robust) effect"),
    (r"not (recommended|supported|beneficial)", r"(recommended|supported|beneficial|effective)"),
    (r"does not (improve|enhance|increase)", r"(improves?|enhances?|increases?)"),
    (r"no benefit", r"(benefit|effective)"),
    (r"(harmful|detrimental|negative)", r"(beneficial|positive|protective)"),
    (r"(ineffective|useless)", r"(effective|useful)"),
    (r"contra-?indicated", r"(safe|recommended)"),
    (r"no interaction", r"(interaction|interfere)"),
    (r"does not attenuate", r"attenuates?"),
]


def _extract_key_claims(text: str) -> list[str]:
    """Extract sentences that look like claims (contain evidence keywords)."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    claim_keywords = {
        "evidence", "study", "found", "showed", "demonstrated",
        "suggests", "indicates", "associated", "correlated",
        "improved", "reduced", "increased", "decreased",
        "effective", "ineffective", "no effect", "significant",
        "meta-analysis", "rct", "trial", "review",
    }
    claims = []
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in claim_keywords):
            claims.append(s.strip())
    return claims[:20]


def detect_contradictions(
    new_text: str,
    semantic_memory: dict[str, Any],
) -> list[Contradiction]:
    """
    Compare new research text against stored semantic memory entries.
    Returns list of detected contradictions.
    """
    if not semantic_memory or not new_text:
        return []

    new_claims = _extract_key_claims(new_text)
    if not new_claims:
        return []

    contradictions = []

    for topic, entry in semantic_memory.items():
        stored_content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
        if not stored_content:
            continue
        stored_lower = stored_content.lower()

        for claim in new_claims:
            claim_lower = claim.lower()

            # Check if claim references same topic
            topic_words = topic.lower().split()
            if not any(tw in claim_lower for tw in topic_words if len(tw) > 3):
                continue

            # Check for contradiction signals
            for stored_pattern, new_pattern in CONTRADICTION_SIGNALS:
                stored_match = re.search(stored_pattern, stored_lower)
                new_match = re.search(new_pattern, claim_lower)
                if stored_match and new_match:
                    # Found a potential contradiction
                    # Extract the surrounding context from stored
                    start = max(0, stored_match.start() - 80)
                    end = min(len(stored_content), stored_match.end() + 80)
                    stored_excerpt = stored_content[start:end].strip()

                    contradictions.append(Contradiction(
                        topic=topic,
                        stored_claim=stored_excerpt,
                        new_claim=claim[:300],
                        confidence=0.6,
                    ))
                    break

                # Also check reverse (stored says positive, new says negative)
                stored_match_rev = re.search(new_pattern, stored_lower)
                new_match_rev = re.search(stored_pattern, claim_lower)
                if stored_match_rev and new_match_rev:
                    start = max(0, stored_match_rev.start() - 80)
                    end = min(len(stored_content), stored_match_rev.end() + 80)
                    stored_excerpt = stored_content[start:end].strip()

                    contradictions.append(Contradiction(
                        topic=topic,
                        stored_claim=stored_excerpt,
                        new_claim=claim[:300],
                        confidence=0.6,
                    ))
                    break

    # Deduplicate by topic (keep highest confidence per topic)
    seen_topics: set[str] = set()
    unique: list[Contradiction] = []
    for c in sorted(contradictions, key=lambda x: -x.confidence):
        if c.topic not in seen_topics:
            seen_topics.add(c.topic)
            unique.append(c)

    return unique[:5]


def format_contradictions(contradictions: list[Contradiction]) -> str:
    """Format contradictions for display."""
    if not contradictions:
        return ""
    lines = ["Potential contradictions with stored knowledge:", ""]
    for c in contradictions:
        lines.append(c.display())
        lines.append("")
    lines.append("Use /remember to update stored knowledge if the new evidence is stronger.")
    return "\n".join(lines)
