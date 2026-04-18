"""
Natural Language Command Router — Maps plain-text instructions to slash commands.

When the user types something that sounds like a tool invocation in natural
language, this module detects the intent and returns the appropriate slash
command. If no match, returns None (proceed with normal research pipeline).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RouteMatch:
    command: str
    confidence: float
    extracted_args: str = ""

    def full_command(self) -> str:
        if self.extracted_args:
            return f"{self.command} {self.extracted_args}"
        return self.command


# Pattern → (command, confidence)
# Patterns are checked in order; first match wins
ROUTE_PATTERNS: list[tuple[str, str, float]] = [
    # Labs / biomarkers
    (r"(?:import|enter|log|record)\s+(?:my\s+)?(?:labs?|blood\s*work|panel|biomarkers?)\s*[:\-]?\s*(.*)", "/import_labs", 0.9),
    (r"(?:track|record|log)\s+(?:my\s+)?(\w+)\s+([\d.]+)", "/track", 0.85),

    # Interventions
    (r"(?:start|begin)\s+(?:taking\s+)?(\w+)\s*([\d]+\w*/?[dw]?)?\s*(?:for|targeting|to\s+fix)?\s*(\w+)?", "/intervention start", 0.8),
    (r"(?:stop|quit|discontinue)\s+(?:taking\s+)?(\w+)", "/intervention stop", 0.8),
    (r"(?:how(?:'s| is)|check|evaluate|assess)\s+(?:the\s+)?(\w+)\s+(?:protocol|intervention|supplement|going|working)", "/intervention check", 0.85),
    (r"(?:what|which)\s+(?:interventions?|supplements?)\s+(?:am I|are we|is\s+\w+)\s+(?:on|taking|running)", "/intervention list", 0.8),

    # Optimization
    (r"(?:optimize|suggest|recommend)\s+(?:my\s+|a\s+)?(?:supplement\s+)?stack", "/optimize_stack", 0.9),
    (r"(?:screen|check|assess)\s+(?:for\s+)?(?:risks?|red-?s|overtraining|health)", "/risk_screen", 0.85),
    (r"(?:what\s+should\s+I|suggest)\s+research", "/suggest_research", 0.85),

    # Planning
    (r"(?:generate|create|make|build)\s+(?:a\s+)?(\d+)?[- ]?day\s+meal\s*plan", "/meal_plan", 0.9),
    (r"(?:generate|create|make|build)\s+(?:a\s+)?(\d+)?[- ]?week\s+training\s*plan", "/training_plan", 0.85),
    (r"(?:fight|competition|bout)\s+(?:prep|preparation|week)", "/fight_prep", 0.9),
    (r"(?:race|marathon|event)\s+(?:prep|preparation|week)", "/race_prep", 0.9),

    # Views
    (r"(?:show|display|get)\s+(?:me\s+)?(?:a\s+)?snapshot", "/snapshot", 0.9),
    (r"(?:show|display|get)\s+(?:me\s+)?(?:the\s+)?dashboard", "/dashboard", 0.9),
    (r"(?:compare|diff)\s+(\w+)\s+(?:and|vs?\.?|with)\s+(\w+)", "/compare_clients", 0.85),
    (r"(?:show|display|get)\s+(?:me\s+)?team\s+(?:summary|analytics|stats)", "/team", 0.9),
    (r"(?:show|list)\s+(?:my\s+)?(?:watched|subscribed)\s+topics?", "/watched", 0.85),

    # Research
    (r"(?:systematic\s+)?review\s+(?:of\s+|on\s+)(.+)", "/review", 0.8),
    (r"(?:synthesize|synthesis)\s+(?:evidence\s+(?:on|for)\s+)?(.+)", "/synthesize", 0.8),
    (r"(?:design|create)\s+(?:an?\s+)?n[- ]of[- ]1\s+(?:for|on|about)\s+(.+)", "/n_of_1", 0.85),

    # Export
    (r"(?:export|generate|create)\s+(?:a\s+)?pdf", "/pdf", 0.9),
    (r"(?:save|persist)\s+(?:this\s+)?session", "/save_session", 0.85),

    # Profile
    (r"(?:set\s+up|onboard|intake)\s+(?:new\s+)?(?:client|athlete)", "/onboard", 0.85),
    (r"(?:show|display)\s+(?:my\s+)?profile", "/profile", 0.85),

    # Memory
    (r"(?:what\s+do\s+(?:you|we)\s+)?remember", "/memory", 0.7),
    (r"(?:show|check)\s+(?:my\s+)?(?:research\s+)?(?:history|log)", "/log", 0.8),
    (r"(?:show|get)\s+(?:api\s+)?cost", "/cost", 0.85),
    (r"(?:show|run|get)\s+digest", "/digest", 0.85),

    # Help
    (r"(?:help|commands|what\s+can\s+you\s+do)", "/help", 0.9),
]


def route_natural_language(text: str) -> RouteMatch | None:
    """
    Attempt to match natural language input to a slash command.
    Returns None if no confident match found.
    """
    text_lower = text.strip().lower()

    # Skip if it's already a slash command
    if text_lower.startswith("/"):
        return None

    # Skip very short inputs (likely follow-ups)
    if len(text_lower.split()) <= 2:
        return None

    for pattern, command, base_confidence in ROUTE_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            # Extract args from capture groups
            groups = [g for g in match.groups() if g]
            args = " ".join(groups) if groups else ""

            # Adjust confidence for specific patterns
            confidence = base_confidence

            return RouteMatch(
                command=command,
                confidence=confidence,
                extracted_args=args.strip(),
            )

    return None


def format_route_suggestion(match: RouteMatch) -> str:
    """Format a routing suggestion for display to the user."""
    cmd = match.full_command()
    return f"[dim]  → Detected: [cyan]{cmd}[/cyan] (confidence: {match.confidence:.0%})[/dim]"
