"""
Shared SSL certificate bundle detection for crawl-x MCP servers.

Priority: Apple Silicon Homebrew → Intel Homebrew → certifi (bundled with requests)
"""

import os
from pathlib import Path

_BREW_PATHS = (
    "/opt/homebrew/etc/openssl@3/cert.pem",  # macOS Apple Silicon
    "/usr/local/etc/openssl@3/cert.pem",     # macOS Intel
)


def _detect() -> str | None:
    for p in _BREW_PATHS:
        if Path(p).exists():
            return p
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None


CA_BUNDLE: str | None = _detect()


def apply_ssl_fix() -> None:
    """Set CURL_CA_BUNDLE and REQUESTS_CA_BUNDLE if not already set."""
    if CA_BUNDLE:
        os.environ.setdefault("CURL_CA_BUNDLE", CA_BUNDLE)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", CA_BUNDLE)
