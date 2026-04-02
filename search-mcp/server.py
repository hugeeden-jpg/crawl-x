# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "scrapling[all]>=0.4.2",
# ]
# ///

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from ssl_utils import apply_ssl_fix
    apply_ssl_fix()
except ImportError:
    pass

from urllib.parse import quote_plus, urlparse, parse_qs

from scrapling.fetchers import StealthyFetcher
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("search-data")

# ── Helpers ───────────────────────────────────────────────────────────────────

_AD_PATTERNS = ("googleadservices.com", "google.com/aclk", "google.com/search")
_SNIPPET_SELECTORS = ("div.VwiC3b", "div[data-sncf]", "span[class*='st']", "div[style*='-webkit-line-clamp']")


def _clean_href(href: str) -> str:
    if href.startswith("/url?q="):
        q = parse_qs(urlparse(href).query).get("q")
        return q[0] if q else href
    return href


def _is_valid_url(href: str) -> bool:
    if not href.startswith("http"):
        return False
    return not any(pat in href for pat in _AD_PATTERNS)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def search(query: str, num_results: int = 10, language: str = "en") -> str:
    """
    Search Google and return a ranked list of results with title, URL, and snippet.
    Use this tool whenever you need to find a real URL for an unknown website or topic.

    Args:
        query: Search keywords
        num_results: Number of results to return (default 10, max 50)
        language: Google results language, e.g. "en", "zh-CN" (default "en")
    """
    num_results = min(max(1, num_results), 50)
    # Request 2x to account for ads/cards that will be filtered out
    fetch_num = min(num_results * 2, 50)

    search_url = (
        f"https://www.google.com/search"
        f"?q={quote_plus(query)}&num={fetch_num}&hl={language}"
    )

    try:
        page = await StealthyFetcher.async_fetch(
            search_url,
            headless=True,
            network_idle=False,
            timeout=30000,
        )
    except Exception as e:
        return f"Error: failed to fetch Google search results — {e}"

    results = []
    # Iterate all containers without slicing: Google embeds ads/knowledge cards
    # inside div.g, so the actual count of valid results is unpredictable. Slicing
    # to fetch_num would defeat the 2x buffer requested via ?num=fetch_num.
    containers = page.css("div.g")

    for container in containers:
        if len(results) >= num_results:
            break

        h3 = container.css_first("h3")
        if not h3:
            continue
        title = h3.get_all_text(strip=True)
        if not title:
            continue

        a = container.css_first("a[href]")
        if not a:
            continue
        href = _clean_href(a.attrib.get("href", ""))
        if not _is_valid_url(href):
            continue

        snippet = ""
        for sel in _SNIPPET_SELECTORS:
            s = container.css_first(sel)
            if s:
                text = s.get_all_text(strip=True)
                if len(text) > 20:
                    snippet = text[:300]
                    break

        results.append({"title": title, "url": href, "snippet": snippet})

    if not results:
        return f"No results found for: {query}"

    lines = [f'Search results for "{query}" ({len(results)} results):', ""]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        if r["snippet"]:
            lines.append(f"   Snippet: {r['snippet']}")
        lines.append("")

    return "\n".join(lines).rstrip()


if __name__ == "__main__":
    mcp.run()
