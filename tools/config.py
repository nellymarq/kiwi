"""
Config Management — Load settings from ~/.kiwi/config.json.

Replaces environment variable dependency for API keys and defaults.
Falls back to env vars if config.json doesn't exist.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".kiwi" / "config.json"

DEFAULT_CONFIG = {
    "anthropic_api_key": "",
    "ncbi_api_key": "",
    "fdc_api_key": "DEMO_KEY",
    "brand": {
        "name": "Kiwi Performance Research",
        "tagline": "Evidence-Based Sports Nutrition & Performance Science",
        "practitioner": "",
        "organization": "",
        "primary_color": "#0a5c36",
        "accent_color": "#1f4068",
    },
    "research": {
        "pubmed_max_results": 6,
        "openalex_max_results": 4,
        "epmc_max_results": 3,
        "semantic_scholar_max_results": 3,
        "years_back": 8,
    },
    "memory": {
        "episodic_limit": 50,
        "semantic_stale_days": 90,
    },
}


def load_config() -> dict[str, Any]:
    """Load config from file, merge with defaults, fall back to env vars."""
    config = dict(DEFAULT_CONFIG)

    if CONFIG_PATH.exists():
        try:
            user_config = json.loads(CONFIG_PATH.read_text())
            _deep_merge(config, user_config)
        except (json.JSONDecodeError, OSError):
            pass

    # Env var overrides (highest priority)
    if os.environ.get("ANTHROPIC_API_KEY"):
        config["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("NCBI_API_KEY"):
        config["ncbi_api_key"] = os.environ["NCBI_API_KEY"]
    if os.environ.get("FDC_API_KEY"):
        config["fdc_api_key"] = os.environ["FDC_API_KEY"]

    return config


def save_config(config: dict[str, Any]):
    """Save config to file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def _deep_merge(base: dict, override: dict):
    """Merge override into base (mutates base)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def validate_config(config: dict) -> list[str]:
    """Return list of warnings about the config."""
    warnings = []
    if not config.get("anthropic_api_key"):
        warnings.append("No Anthropic API key configured (set ANTHROPIC_API_KEY env var or in config.json)")
    if config.get("fdc_api_key") == "DEMO_KEY":
        warnings.append("Using USDA FoodData Central DEMO_KEY (30 req/hour limit). Set FDC_API_KEY for higher limits.")
    return warnings


def first_run_check() -> bool:
    """Returns True if this appears to be first run (no config file)."""
    return not CONFIG_PATH.exists()


def create_default_config():
    """Write default config.json for user to customize."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
