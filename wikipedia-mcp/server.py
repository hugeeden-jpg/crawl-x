#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "wikipedia>=1.4.0",
# ]
# ///
"""
Wikipedia MCP Server — English Wikipedia via wikipedia Python library.
Full article content is written to ~/.cache/wikipedia-mcp/ for agent file reading.
"""

import re
import warnings
from pathlib import Path

# Suppress BeautifulSoup parser warning from wikipedia library internals
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ssl_utils import apply_ssl_fix  # noqa: E402
apply_ssl_fix()

import wikipedia
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("wikipedia-data")

CACHE_DIR = Path.home() / ".cache" / "wikipedia-mcp"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

wikipedia.set_lang("en")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_filename(title: str) -> str:
    name = title.replace(" ", "_")
    name = re.sub(r"[^\w\-.]", "", name)
    return name[:200] + ".md"


def _cache_path(title: str) -> Path:
    return CACHE_DIR / _safe_filename(title)


def _fmt_disambig(title: str, e: wikipedia.DisambiguationError) -> str:
    options = "\n".join(f"  - {opt}" for opt in e.options[:15])
    return (
        f"'{title}' is ambiguous. Did you mean one of these?\n{options}\n\n"
        f"Re-call with one of the specific titles above."
    )


def _fmt_page_error(title: str) -> str:
    return f"Article not found: '{title}'. Try search_wikipedia to find the correct title."


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_wikipedia(query: str, limit: int = 10) -> str:
    """
    Search Wikipedia and return a list of matching article titles.

    Args:
        query: Search term
        limit: Maximum number of results to return (default 10, max 20)
    """
    limit = min(max(1, limit), 20)
    try:
        results = wikipedia.search(query, results=limit)
        if not results:
            return f"No results found for: {query}"
        lines = [f"Search results for '{query}':", ""]
        for i, title in enumerate(results, 1):
            lines.append(f"{i}. {title}")
        return "\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"


@mcp.tool()
def get_summary(title: str, sentences: int = 5) -> str:
    """
    Get the introductory summary of a Wikipedia article.

    Args:
        title: Article title (exact or close match)
        sentences: Number of sentences to return (default 5)
    """
    try:
        summary = wikipedia.summary(title, sentences=sentences, auto_suggest=False)
        return f"# {title}\n\n{summary}"
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error fetching summary: {e}"


@mcp.tool()
def get_article(title: str) -> str:
    """
    Fetch the full text of a Wikipedia article and save it to a local cache file.
    Returns the file path, character count, and URL — use the Read tool to view content.

    Args:
        title: Article title
    """
    try:
        page = wikipedia.page(title, auto_suggest=False)
        content = f"# {page.title}\n\nURL: {page.url}\n\n{page.content}"
        path = _cache_path(page.title)
        path.write_text(content, encoding="utf-8")
        return (
            f"Article cached successfully.\n\n"
            f"title: {page.title}\n"
            f"file_path: {path}\n"
            f"char_count: {len(content)}\n"
            f"url: {page.url}\n\n"
            f"Use the Read tool with the file_path above to view the full content.\n"
            f"Cache note: call get_article again to refresh; manually clear with: rm ~/.cache/wikipedia-mcp/*.md"
        )
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error fetching article: {e}"


@mcp.tool()
def get_sections(title: str) -> str:
    """
    Get the section structure of a Wikipedia article with a preview of each section's content.

    Args:
        title: Article title
    """
    try:
        page = wikipedia.page(title, auto_suggest=False)
        lines = [f"# Sections of '{page.title}'", ""]

        # Split raw content on == headers (level 2+) to extract sections
        raw = page.content
        parts = re.split(r"\n(={2,}[^=]+={2,})\n", raw)

        if len(parts) <= 1:
            intro = raw[:500].strip()
            lines.append(f"**Introduction**\n{intro}{'...' if len(raw) > 500 else ''}")
        else:
            intro_raw = parts[0].strip()
            intro = intro_raw[:500]
            lines.append(f"**Introduction**\n{intro}{'...' if len(intro_raw) > 500 else ''}")
            lines.append("")

            for i in range(1, len(parts) - 1, 2):
                header = parts[i].strip("= ").strip()
                section_raw = parts[i + 1].strip() if i + 1 < len(parts) else ""
                body = section_raw[:500]
                lines.append(f"**{header}**")
                if body:
                    lines.append(f"{body}{'...' if len(section_raw) > 500 else ''}")
                lines.append("")

        return "\n".join(lines)
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error fetching sections: {e}"


@mcp.tool()
def get_links(title: str, limit: int = 50) -> str:
    """
    Get the internal Wikipedia links contained within an article.

    Args:
        title: Article title
        limit: Maximum number of links to return (default 50)
    """
    try:
        page = wikipedia.page(title, auto_suggest=False)
        links = page.links[:limit]
        if not links:
            return f"No internal links found in '{title}'."
        lines = [f"Internal links in '{page.title}' (showing {len(links)}):", ""]
        for link in links:
            lines.append(f"  - {link}")
        return "\n".join(lines)
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error fetching links: {e}"


@mcp.tool()
def get_related_topics(title: str, limit: int = 10) -> str:
    """
    Get topics related to a Wikipedia article, derived from its categories and links.

    Args:
        title: Article title
        limit: Maximum number of related topics (default 10)
    """
    try:
        page = wikipedia.page(title, auto_suggest=False)
        categories = page.categories[:limit]
        lines = [f"Related topics for '{page.title}':", ""]

        if categories:
            lines.append("**Categories:**")
            for cat in categories:
                lines.append(f"  - {cat}")
            lines.append("")

        categories_set = set(categories)
        sample_links = [link for link in page.links if link not in categories_set][:limit]
        if sample_links:
            lines.append("**Related articles (sample):**")
            for link in sample_links:
                lines.append(f"  - {link}")

        return "\n".join(lines)
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error fetching related topics: {e}"


@mcp.tool()
def extract_key_facts(title: str, count: int = 5) -> str:
    """
    Extract key facts from a Wikipedia article's summary as a numbered list of sentences.

    Args:
        title: Article title
        count: Number of key facts to extract (default 5)
    """
    try:
        summary = wikipedia.summary(title, sentences=max(count * 2, 10), auto_suggest=False)
        raw_sentences = re.split(r"(?<=[.!?])\s+", summary.strip())
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 20][:count]

        if not sentences:
            return f"Could not extract facts from '{title}'."

        lines = [f"Key facts about '{title}':", ""]
        for i, fact in enumerate(sentences, 1):
            lines.append(f"{i}. {fact}")
        return "\n".join(lines)
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error extracting facts: {e}"


@mcp.tool()
def get_coordinates(title: str) -> str:
    """
    Get the geographic coordinates (latitude, longitude) of a location article.

    Args:
        title: Article title (a place, landmark, geographic feature, etc.)
    """
    try:
        page = wikipedia.page(title, auto_suggest=False)
        try:
            coords = page.coordinates
        except KeyError:
            coords = None
        if coords is None:
            return (
                f"No coordinates found for '{page.title}'. "
                f"This article may not represent a geographic location."
            )
        lat, lon = coords
        return (
            f"Coordinates for '{page.title}':\n\n"
            f"  latitude:  {lat}\n"
            f"  longitude: {lon}\n"
            f"  url:       {page.url}"
        )
    except wikipedia.DisambiguationError as e:
        return _fmt_disambig(title, e)
    except wikipedia.PageError:
        return _fmt_page_error(title)
    except Exception as e:
        return f"Error fetching coordinates: {e}"


if __name__ == "__main__":
    mcp.run()
