"""
Base agent class for Kiwi's multi-agent architecture.
All specialist agents inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Any
import anthropic

AGENT_MODEL = "claude-opus-4-6"
REFINEMENT_THRESHOLD = 0.72


class BaseAgent(ABC):
    """Abstract base for all Kiwi specialist agents."""

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent display name."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Agent system prompt."""
        ...

    @property
    def max_tokens(self) -> int:
        """Max tokens for this agent's response. Override in subclasses."""
        return 4096

    async def run(self, context: dict[str, Any]) -> str:
        """Execute this agent with the given context. Returns text output."""
        messages = self._build_messages(context)
        response = await self.client.messages.create(
            model=AGENT_MODEL,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            system=self.system_prompt,
            messages=messages,
        )
        return next((b.text for b in response.content if hasattr(b, "text")), "")

    @abstractmethod
    def _build_messages(self, context: dict[str, Any]) -> list[dict]:
        """Build the message list from the given context dict."""
        ...
