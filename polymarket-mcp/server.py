# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""Polymarket MCP — read-only prediction market data via Gamma API (no key required)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from ssl_utils import apply_ssl_fix
    apply_ssl_fix()
except ImportError:
    pass

import requests
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://gamma-api.polymarket.com"
mcp = FastMCP("polymarket-mcp")

PERIOD_FIELD = {
    "24h": "volume24hr",
    "7d": "volume1wk",
    "30d": "volume1mo",
    "all": "volumeNum",
}


def _fmt_usd(val) -> str:
    try:
        v = float(val)
        if v >= 1_000_000:
            return f"${v/1_000_000:.2f}M"
        if v >= 1_000:
            return f"${v/1_000:.1f}K"
        return f"${v:,.0f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_pct(val) -> str:
    try:
        return f"{float(val)*100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _status(item: dict) -> str:
    if item.get("closed"):
        return "closed"
    if item.get("archived"):
        return "archived"
    if item.get("active"):
        return "active"
    return "unknown"


def _parse_outcomes(market: dict) -> list[tuple[str, str]]:
    """Return list of (outcome_label, price_pct) pairs."""
    try:
        outcomes = json.loads(market.get("outcomes", "[]"))
        prices = json.loads(market.get("outcomePrices", "[]"))
        return [(o, _fmt_pct(p)) for o, p in zip(outcomes, prices)]
    except (json.JSONDecodeError, TypeError):
        return []


def _format_market_brief(m: dict, rank: int | None = None, period_field: str | None = None) -> str:
    lines = []
    prefix = f"#{rank} " if rank is not None else ""
    lines.append(f"{prefix}{m.get('question', '—')}")
    op = _parse_outcomes(m)
    if op:
        lines.append("  Odds:  " + "  |  ".join(f"{o}: {p}" for o, p in op))
    vol_24h = _fmt_usd(m.get("volume24hr", 0))
    vol_total = _fmt_usd(m.get("volumeNum", m.get("volume", 0)))
    lines.append(f"  Vol 24h: {vol_24h}  |  Total: {vol_total}  |  Liquidity: {_fmt_usd(m.get('liquidityNum', m.get('liquidity', 0)))}")
    if period_field and period_field not in ("volume24hr", "volumeNum"):
        lines.append(f"  Vol ({period_field}): {_fmt_usd(m.get(period_field, 0))}")
    lines.append(f"  Status: {_status(m)}  |  Ends: {m.get('endDateIso', m.get('endDate', '—'))[:10]}")
    cat = m.get("category", "")
    if cat:
        lines.append(f"  Category: {cat}")
    slug = m.get("slug", "")
    if slug:
        lines.append(f"  URL: https://polymarket.com/event/{slug}")
    return "\n".join(lines)


@mcp.tool()
def search_markets(
    query: str = "",
    category: str = "",
    limit: int = 10,
    active_only: bool = True,
) -> str:
    """Search Polymarket prediction markets by keyword, with optional category filter.

    Args:
        query: Search keyword, e.g. "Trump", "Bitcoin", "NBA Finals". Empty returns all.
        category: Filter by category slug, e.g. "politics", "sports", "crypto". Empty = all.
            Note: Gamma API market objects don't include category/tag fields, so this filter
            has no effect for markets. Use get_events(category=...) for reliable category filtering.
        limit: Number of results to return (default 10, max 100).
        active_only: If True, only return active (not closed/resolved) markets.
    """
    try:
        limit = min(int(limit), 100)
        # Gamma API doesn't support full-text search; fetch a larger batch and filter client-side
        fetch_limit = 500 if query else limit
        params: dict = {"limit": fetch_limit, "order": "volume24hr", "ascending": "false"}
        if active_only:
            params["active"] = "true"
            params["closed"] = "false"

        resp = requests.get(f"{BASE_URL}/markets", params=params, timeout=15)
        resp.raise_for_status()
        markets = resp.json()

        # Client-side filters (API ignores server-side tag/category params)
        if query:
            q_lower = query.lower()
            markets = [
                m for m in markets
                if q_lower in m.get("question", "").lower()
                or q_lower in m.get("description", "").lower()
                or q_lower in m.get("slug", "").lower()
            ]
        if category:
            cat_lower = category.lower()
            markets = [
                m for m in markets
                if cat_lower in m.get("category", "").lower()
                or any(
                    cat_lower in t.get("label", "").lower()
                    for ev in m.get("events", [])
                    for t in ev.get("tags", [])
                )
            ]
        markets = markets[:limit]

        if not markets:
            return "No markets found."

        lines = [f"Polymarket Markets — {len(markets)} result(s)" + (f' for "{query}"' if query else "")]
        lines.append("=" * 60)
        for i, m in enumerate(markets, 1):
            lines.append(_format_market_brief(m, rank=i))
            lines.append("")
        return "\n".join(lines).rstrip()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_market(market_id: str) -> str:
    """Get full details for a single Polymarket market by ID.

    Args:
        market_id: Market ID string (e.g. "540816"). Obtain from search_markets or get_events.
    """
    try:
        resp = requests.get(f"{BASE_URL}/markets/{market_id}", timeout=15)
        resp.raise_for_status()
        m = resp.json()

        lines = [f"Market: {m.get('question', '—')}"]
        lines.append("=" * 60)

        # Outcomes
        op = _parse_outcomes(m)
        if op:
            lines.append("Outcomes:")
            for label, pct in op:
                lines.append(f"  {label}: {pct}")

        # Volume & liquidity
        lines.append(f"\nVolume 24h:  {_fmt_usd(m.get('volume24hr', 0))}")
        lines.append(f"Volume 7d:   {_fmt_usd(m.get('volume1wk', 0))}")
        lines.append(f"Volume 30d:  {_fmt_usd(m.get('volume1mo', 0))}")
        lines.append(f"Volume All:  {_fmt_usd(m.get('volumeNum', m.get('volume', 0)))}")
        lines.append(f"Liquidity:   {_fmt_usd(m.get('liquidityNum', m.get('liquidity', 0)))}")
        lines.append(f"Spread:      {_fmt_pct(m.get('spread', 0))}")

        # Status & dates
        lines.append(f"\nStatus:    {_status(m)}")
        lines.append(f"Ends:      {m.get('endDateIso', m.get('endDate', '—'))[:10]}")
        lines.append(f"Created:   {m.get('createdAt', '—')[:10]}")
        lines.append(f"Category:  {m.get('category', '—')}")

        # Event info
        events = m.get("events", [])
        if events:
            ev = events[0]
            lines.append(f"\nEvent:     {ev.get('title', '—')} (ID: {ev.get('id', '—')})")

        # Description
        desc = m.get("description", "")
        if desc:
            lines.append(f"\nDescription:\n{desc[:500]}{'...' if len(desc) > 500 else ''}")

        slug = m.get("slug", "")
        if slug:
            lines.append(f"\nURL: https://polymarket.com/event/{slug}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_events(
    query: str = "",
    category: str = "",
    limit: int = 10,
    active_only: bool = True,
) -> str:
    """Get Polymarket events (each event groups multiple related markets).

    Args:
        query: Search keyword, e.g. "election", "World Cup". Empty returns all.
        category: Filter by category, e.g. "politics", "sports", "crypto". Empty = all.
        limit: Number of events to return (default 10, max 100).
        active_only: If True, only return active (not closed/resolved) events.
    """
    try:
        limit = min(int(limit), 100)
        fetch_limit = 500 if (query or category) else limit
        params: dict = {"limit": fetch_limit, "order": "volume24hr", "ascending": "false"}
        if active_only:
            params["active"] = "true"
            params["closed"] = "false"

        resp = requests.get(f"{BASE_URL}/events", params=params, timeout=15)
        resp.raise_for_status()
        events = resp.json()

        # Client-side filters (API ignores server-side tag/category params)
        if query:
            q_lower = query.lower()
            events = [
                e for e in events
                if q_lower in e.get("title", "").lower()
                or q_lower in e.get("description", "").lower()
                or q_lower in e.get("slug", "").lower()
            ]
        if category:
            cat_lower = category.lower()
            events = [
                e for e in events
                if any(cat_lower in t.get("label", "").lower() for t in e.get("tags", []))
            ]
        events = events[:limit]

        if not events:
            return "No events found."

        lines = [f"Polymarket Events — {len(events)} result(s)" + (f' for "{query}"' if query else "")]
        lines.append("=" * 60)

        for i, ev in enumerate(events, 1):
            markets = ev.get("markets", [])
            lines.append(f"#{i} {ev.get('title', '—')}")
            lines.append(f"  Category: {ev.get('category', '—')}  |  Status: {_status(ev)}")
            lines.append(f"  Vol 24h: {_fmt_usd(ev.get('volume24hr', 0))}  |  Total: {_fmt_usd(ev.get('volume', 0))}  |  Liquidity: {_fmt_usd(ev.get('liquidity', 0))}")
            lines.append(f"  Ends: {ev.get('endDate', '—')[:10]}  |  Markets: {len(markets)}")
            if markets:
                lines.append("  Top markets:")
                for m in markets[:5]:
                    op = _parse_outcomes(m)
                    odds_str = "  |  ".join(f"{o}: {p}" for o, p in op[:3]) if op else "—"
                    lines.append(f"    • {m.get('question', '—')}")
                    if odds_str != "—":
                        lines.append(f"      {odds_str}")
                if len(markets) > 5:
                    lines.append(f"    ... and {len(markets)-5} more markets")
            ev_slug = ev.get("slug", "")
            if ev_slug:
                lines.append(f"  URL: https://polymarket.com/event/{ev_slug}")
            lines.append("")

        return "\n".join(lines).rstrip()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_trending_markets(
    period: str = "24h",
    category: str = "",
    limit: int = 10,
) -> str:
    """Get top trending Polymarket markets ranked by trading volume.

    Args:
        period: Volume period for ranking: "24h" (default), "7d", "30d", or "all".
        category: Filter by category, e.g. "politics", "sports", "crypto". Empty = all.
            Note: category filtering is not effective for markets (no tag data in market objects).
            Use get_events(category=...) for reliable category filtering.
        limit: Number of results (default 10, max 100).
    """
    try:
        period = period.lower()
        order_field = PERIOD_FIELD.get(period, "volume24hr")

        fetch_limit = 500 if category else min(int(limit), 100)
        params: dict = {
            "limit": fetch_limit,
            "order": order_field,
            "ascending": "false",
            "active": "true",
            "closed": "false",
        }

        resp = requests.get(f"{BASE_URL}/markets", params=params, timeout=15)
        resp.raise_for_status()
        markets = resp.json()

        # Client-side category filter (API ignores server-side tag/category params)
        if category:
            cat_lower = category.lower()
            markets = [
                m for m in markets
                if cat_lower in m.get("category", "").lower()
                or any(
                    cat_lower in t.get("label", "").lower()
                    for ev in m.get("events", [])
                    for t in ev.get("tags", [])
                )
            ]
        markets = markets[:min(int(limit), 100)]

        if not markets:
            return "No trending markets found."

        period_label = {"24h": "24 hours", "7d": "7 days", "30d": "30 days", "all": "all time"}.get(period, period)
        lines = [f"Polymarket Trending Markets — Top {len(markets)} by volume ({period_label})"]
        lines.append("=" * 60)
        for i, m in enumerate(markets, 1):
            lines.append(_format_market_brief(m, rank=i, period_field=order_field))
            lines.append("")
        return "\n".join(lines).rstrip()
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
