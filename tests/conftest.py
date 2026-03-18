"""
Shared fixtures and helpers for crawl-x regression tests.

Run all tests:          pytest
Skip slow (scraping):   pytest -m "not slow"
Only fast free-API:     pytest -m "integration and not slow"
"""

import importlib.util
import json
import os
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent


# ── server loader ─────────────────────────────────────────────────────────────

def load_server(mcp_dir: str):
    """Import a server.py from a sibling MCP directory as a module."""
    path = REPO / mcp_dir / "server.py"
    name = mcp_dir.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── key / credential detection ────────────────────────────────────────────────

def has_fred_key() -> bool:
    if os.environ.get("FRED_API_KEY"):
        return True
    cfg = Path.home() / ".config" / "macro-mcp" / "config.json"
    return cfg.exists() and bool(json.loads(cfg.read_text()).get("fred_api_key"))


def has_finnhub_key() -> bool:
    if os.environ.get("FINNHUB_API_KEY"):
        return True
    cfg = Path.home() / ".config" / "market-data-mcp" / "config.json"
    return cfg.exists() and bool(json.loads(cfg.read_text()).get("finnhub_api_key"))



def has_quiver_key() -> bool:
    if os.environ.get("QUIVER_API_KEY"):
        return True
    cfg = Path.home() / ".config" / "sentiment-mcp" / "config.json"
    return cfg.exists() and bool(json.loads(cfg.read_text()).get("quiver_api_key"))


def has_glassnode_key() -> bool:
    return bool(os.environ.get("GLASSNODE_API_KEY"))


def has_xai_key() -> bool:
    if os.environ.get("XAI_API_KEY"):
        return True
    cfg = Path.home() / ".config" / "grok-mcp" / "config.json"
    return cfg.exists() and bool(json.loads(cfg.read_text()).get("api_key"))


# ── shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def market_data():
    return load_server("market-data-mcp")


@pytest.fixture(scope="session")
def macro():
    return load_server("macro-mcp")


@pytest.fixture(scope="session")
def crypto():
    return load_server("crypto-mcp")


@pytest.fixture(scope="session")
def sentiment():
    return load_server("sentiment-mcp")


@pytest.fixture(scope="session")
def scrape():
    return load_server("scrape-mcp")


@pytest.fixture(scope="session")
def grok():
    return load_server("grok-mcp")


# ── rate-limit / transient-error helper ──────────────────────────────────────

_TRANSIENT = ("timeout", "timed out", "connection", "429", "too many requests", "rate limit")


def skip_if_rate_limited(result: str):
    """Call after any free-tier API result; skips the test on transient errors."""
    if result.startswith("Error:") and any(w in result.lower() for w in _TRANSIENT):
        pytest.skip(f"Transient API error (rate-limit/network): {result[:120]}")
