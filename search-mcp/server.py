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


def _clean_href(href: str) -> str:
    if href.startswith("/url?q="):
        q = parse_qs(urlparse(href).query).get("q")
        return q[0] if q else href
    return href


def _is_valid_url(href: str) -> bool:
    if not href.startswith("http"):
        return False
    return not any(pat in href for pat in _AD_PATTERNS)


def _extract_snippet(node, title: str) -> str:
    """Walk up ancestors to find a container with description text.
    Filters out the title, URL breadcrumbs, and short labels (e.g. 'Read more').
    """
    for _ in range(8):
        if node is None:
            break
        lines = [l.strip() for l in node.get_all_text(strip=True).splitlines() if l.strip()]
        snippet_lines = [
            l for l in lines
            if l != title
            and not l.startswith("http")
            and "›" not in l
            and len(l) >= 30
        ]
        if snippet_lines:
            return " ".join(snippet_lines)[:300].replace("\xa0", " ")
        node = node.parent if hasattr(node, "parent") else None
    return ""


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

    # Use stable semantic anchors: #rso (organic results) or #search as fallback.
    # CSS module class names like .MjjYud are obfuscated and can change at any time.
    # Within the results root, find all h3 (titles) and walk up ancestors for URL
    # and snippet — this is resilient to Google's DOM structure changes.
    rso_list = page.css("#rso") or page.css("#search")
    if not rso_list:
        return "Error: could not find results section on page (possible CAPTCHA)"

    results = []
    for h3 in rso_list[0].css("h3"):
        if len(results) >= num_results:
            break

        title = h3.get_all_text(strip=True)
        if not title or len(title) < 5:
            continue

        # Walk up to find the nearest ancestor link
        href = ""
        for anc in h3.iterancestors():
            v = anc.attrib.get("href", "")
            if v:
                href = _clean_href(v)
                break
        if not _is_valid_url(href):
            continue

        snippet = _extract_snippet(h3.parent, title)
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
