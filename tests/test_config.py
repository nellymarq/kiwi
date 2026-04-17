"""Tests for config management."""

import json
import os
import pytest
from pathlib import Path
from tools.config import (
    load_config, save_config, validate_config,
    first_run_check, create_default_config, _deep_merge,
    DEFAULT_CONFIG, CONFIG_PATH,
)


@pytest.fixture
def clean_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("tools.config.CONFIG_PATH", config_path)
    return config_path


def test_load_defaults_no_file(clean_config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("NCBI_API_KEY", raising=False)
    monkeypatch.delenv("FDC_API_KEY", raising=False)
    config = load_config()
    assert config["fdc_api_key"] == "DEMO_KEY"
    assert config["brand"]["name"] == "Kiwi Performance Research"


def test_load_from_file(clean_config):
    clean_config.write_text(json.dumps({
        "brand": {"practitioner": "Nelson RDN"},
    }))
    config = load_config()
    assert config["brand"]["practitioner"] == "Nelson RDN"
    assert config["brand"]["name"] == "Kiwi Performance Research"  # default preserved


def test_env_var_overrides(clean_config, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    config = load_config()
    assert config["anthropic_api_key"] == "test-key-123"


def test_save_config(clean_config):
    save_config({"test": True})
    assert clean_config.exists()
    data = json.loads(clean_config.read_text())
    assert data["test"] is True


def test_validate_missing_key(clean_config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = load_config()
    warnings = validate_config(config)
    assert any("Anthropic" in w for w in warnings)


def test_validate_demo_key(clean_config, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    config = load_config()
    warnings = validate_config(config)
    assert any("DEMO_KEY" in w for w in warnings)


def test_first_run_check(clean_config):
    assert first_run_check()
    create_default_config()
    assert not first_run_check()


def test_deep_merge():
    base = {"a": 1, "nested": {"x": 10, "y": 20}}
    override = {"b": 2, "nested": {"y": 99}}
    _deep_merge(base, override)
    assert base["a"] == 1
    assert base["b"] == 2
    assert base["nested"]["x"] == 10
    assert base["nested"]["y"] == 99
