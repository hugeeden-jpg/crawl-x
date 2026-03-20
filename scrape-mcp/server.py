#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
#   "beautifulsoup4>=4.12.0",
#   "scrapling[all]>=0.4.2",
#   "plotly>=5.0.0",
# ]
# ///
"""
Scrape MCP Server
OpenInsider (insider trades) - requests + BeautifulSoup via http://
Capitol Trades (congressional trades) - Scrapling StealthyFetcher
CME FedWatch (Fed rate probabilities) - Scrapling StealthyFetcher
"""

import os
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ssl_utils import apply_ssl_fix  # noqa: E402
apply_ssl_fix()

import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

try:
    from scrapling.fetchers import StealthyFetcher
    from playwright.sync_api import Page
except ImportError:
    StealthyFetcher = None
    Page = None

mcp = FastMCP("financial-scraper")


@mcp.tool()
def get_insider_trades(ticker: str = None, trade_type: str = "P", days: int = 30) -> str:
    """
    Get insider trades from OpenInsider.com (purchases and/or sales)

    Args:
        ticker: Stock ticker to filter by (optional, omit for all recent trades)
        trade_type: P=Purchase, S=Sale, A=All (default: P)
        days: Look back this many days (default: 30)
    """
    try:
        # Always use the screener URL (consistent column layout, http:// required)
        sym_param = ticker.upper() if ticker else ""
        url = (
            f"http://openinsider.com/screener?s={sym_param}"
            f"&o=&pl=&ph=&ll=&lh=&fd={days}&fdr=&td=0&tdr="
            f"&fdlyl=&fdlyh=&daysago=&xp=1&xs=1"
            f"&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999"
            f"&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh="
            f"&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&Action=0"
        )

        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"class": "tinytable"})
        if not table:
            return f"No insider trades found on OpenInsider" + (f" for {ticker.upper()}" if ticker else "") + f" (last {days}d)"

        tbody = table.find("tbody")
        if not tbody:
            return "No data rows found"
        rows = tbody.find_all("tr")

        # Two column layouts depending on whether company name is included:
        #   16-col (ticker search): D | filing | trade | ticker | insider | title | type | price | qty | owned | Δown | value | 1d..
        #   17-col (no ticker):     D | filing | trade | ticker | company | insider | title | type | price | qty | owned | Δown | value | 1d..
        first_row_cols = len(rows[0].find_all("td")) if rows else 16
        if first_row_cols >= 17:
            COLS = {
                "filing_date": 0, "trade_date": 1, "ticker": 2, "company": 3,
                "insider": 4, "title": 5, "type": 6, "price": 7,
                "qty": 8, "owned": 9, "value": 11,
            }
        else:
            COLS = {
                "filing_date": 0, "trade_date": 1, "ticker": 2,
                "insider": 3, "title": 4, "type": 5, "price": 6,
                "qty": 7, "owned": 8, "value": 10,
            }

        lines = [
            f"=== Insider Trades" + (f": {ticker.upper()}" if ticker else "")
            + f" (type={trade_type}, last {days}d) ===\n"
        ]
        lines.append(f"{'Trade Date':<12} {'Ticker':<7} {'Insider':<26} {'Title':<22} {'Type':<14} {'Qty':>10} {'Price':>8} {'Value':>12}")
        lines.append("-" * 115)

        cutoff = (datetime.now() - timedelta(days=days)).date()
        count = 0

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            # First col is a checkbox/link — skip it
            cols = cols[1:]
            if len(cols) < 12:
                continue

            def cell(key):
                return cols[COLS[key]].get_text(strip=True)

            tx_type_raw = cell("type")
            tx_code = tx_type_raw.split(" - ")[0].strip()

            # Filter by trade_type unless "A" (all)
            if trade_type != "A" and tx_code != trade_type:
                continue

            trade_date_str = cell("trade_date")
            try:
                if datetime.strptime(trade_date_str[:10], "%Y-%m-%d").date() < cutoff:
                    continue
            except Exception:
                pass

            sym      = cell("ticker")[:6]
            insider  = cell("insider")[:25]
            title    = cell("title")[:21]
            price    = cell("price")[:7]
            qty      = cell("qty")[:9]
            value    = cell("value")[:11]

            lines.append(
                f"{trade_date_str[:10]:<12} {sym:<7} {insider:<26} {title:<22}"
                f" {tx_type_raw[:13]:<14} {qty:>10} {price:>8} {value:>12}"
            )
            count += 1
            if count >= 40:
                break

        if count == 0:
            lines.append("No trades found matching criteria.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error scraping OpenInsider: {e}"


@mcp.tool()
async def get_congressional_trades(ticker: str = None, politician: str = None, days: int = 30) -> str:
    """
    Get congressional stock trades from Capitol Trades

    Args:
        ticker: Filter by ticker symbol (optional)
        politician: Filter by politician name (optional)
        days: Look back this many days (default: 30)
    """
    try:
        url = "https://www.capitoltrades.com/trades"
        params = []
        if ticker:
            params.append(f"symbol={ticker.upper()}")
        if politician:
            params.append(f"politician={politician.replace(' ', '+')}")
        if params:
            url += "?" + "&".join(params)

        captured_data = {}

        def intercept_api(page: Page):
            def on_response(response):
                url_r = response.url
                if "capitoltrades.com/api" in url_r and "trades" in url_r:
                    try:
                        captured_data["trades"] = response.json()
                    except Exception:
                        pass

            page.on("response", on_response)
            page.wait_for_timeout(4000)

        def _fetch_capitol():
            StealthyFetcher.fetch(
                url,
                network_idle=True,
                page_action=intercept_api,
                timeout=45000,
                headless=True,
            )

        await asyncio.to_thread(_fetch_capitol)

        # Try to parse captured API data
        if captured_data.get("trades"):
            raw = captured_data["trades"]
            trades_list = raw if isinstance(raw, list) else raw.get("data", raw.get("trades", []))
        else:
            trades_list = []

        lines = [f"=== Congressional Trades" + (f": {ticker.upper()}" if ticker else "") + f" (last {days}d) ===\n"]

        if not trades_list:
            # Fall back to HTML parsing
            page = await asyncio.to_thread(StealthyFetcher.fetch, url, network_idle=True, timeout=45000, headless=True)
            rows = page.css("tr")
            if not rows:
                return "Could not retrieve congressional trades data from Capitol Trades"
            lines.append(f"{'Date':<12} {'Politician':<25} {'Ticker':<8} {'Type':<6} {'Amount'}")
            lines.append("-" * 60)
            count = 0
            for row in rows[1:]:
                cells = row.css("td")
                if len(cells) < 5:
                    continue
                texts = [c.get_all_text(strip=True) for c in cells]
                # Capitol Trades columns: politician, published, traded, asset (ticker name), type, amount
                pol_name   = texts[0][:24] if len(texts) > 0 else ""
                date_str   = texts[2][:10] if len(texts) > 2 else (texts[1][:10] if len(texts) > 1 else "")
                sym        = texts[3].split()[0][:7] if len(texts) > 3 and texts[3] else ""
                tx_type    = texts[4][:5]  if len(texts) > 4 else ""
                amount     = texts[5][:15] if len(texts) > 5 else ""
                lines.append(f"{date_str:<12} {pol_name:<25} {sym:<8} {tx_type:<6} {amount}")
                count += 1
                if count >= 30:
                    break
            return "\n".join(lines)

        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        lines.append(f"{'Date':<12} {'Politician':<25} {'Party':<5} {'Ticker':<8} {'Type':<6} {'Amount'}")
        lines.append("-" * 65)
        count = 0
        for trade in trades_list:
            date_str = trade.get("transactionDate", trade.get("date", ""))
            if date_str:
                try:
                    ts = datetime.strptime(date_str[:10], "%Y-%m-%d").timestamp()
                    if ts < cutoff:
                        continue
                except Exception:
                    pass
            politician_name = trade.get("politician", {})
            if isinstance(politician_name, dict):
                politician_name = politician_name.get("name", "Unknown")
            politician_name = str(politician_name)[:24]
            party = str(trade.get("party", ""))[:4]
            sym = str(trade.get("ticker", trade.get("symbol", "")))[:7]
            tx_type = str(trade.get("type", trade.get("transaction", "")))[:5]
            amount = str(trade.get("amount", trade.get("size", "")))
            lines.append(f"{date_str[:10]:<12} {politician_name:<25} {party:<5} {sym:<8} {tx_type:<6} {amount}")
            count += 1
            if count >= 30:
                break
        return "\n".join(lines)
    except Exception as e:
        return f"Error scraping Capitol Trades: {e}"


@mcp.tool()
async def get_fed_rate_probabilities() -> str:
    """
    Get Fed funds rate probabilities from CME FedWatch Tool
    Returns next FOMC meeting date and probability distribution across rate outcomes
    """
    try:
        CME_URL = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html"
        TABLE_SEL = "#MainContent_pnlContainer > div.ui-widget-info > div > div > div > div > div.margin-bottom-sm > table"
        captured = {}

        def fetch_fedwatch(page: Page):
            def _extract(frame):
                try:
                    frame.wait_for_selector(TABLE_SEL, timeout=20000)
                    captured["html"] = frame.inner_html("#MainContent_pnlContainer")
                except Exception:
                    captured["html"] = frame.content()

            # iframe may already be loaded when page_action fires — check first
            qs = next((f for f in page.frames if "quikstrike" in f.url), None)
            if qs:
                _extract(qs)
                return

            # not yet loaded — wait for the navigation event
            try:
                frame = page.wait_for_event(
                    "framenavigated",
                    predicate=lambda f: "quikstrike" in f.url,
                    timeout=30000,
                )
                _extract(frame)
            except Exception:
                pass

        def _fetch():
            StealthyFetcher.fetch(
                CME_URL,
                network_idle=False,
                page_action=fetch_fedwatch,
                timeout=60000,
                headless=True,
            )

        await asyncio.to_thread(_fetch)

        html = captured.get("html", "")
        if not html:
            return "Could not load QuikStrike frame from CME FedWatch page"

        from scrapling.parser import Selector
        doc = Selector(html)
        lines = ["=== CME FedWatch — Fed Rate Probabilities ===\n"]

        tables = doc.css("div.margin-bottom-sm > table")
        if not tables:
            tables = doc.css("table")
        if not tables:
            lines.append(doc.get_all_text(strip=True)[:3000])
            return "\n".join(lines)

        for table in tables:
            rows = table.css("tr")
            if not rows:
                continue
            parsed = []
            for row in rows:
                cells = row.css("td, th")
                texts = [c.get_all_text(strip=True) for c in cells]
                if any(texts):
                    parsed.append(texts)
            if not parsed:
                continue
            col_count = max(len(r) for r in parsed)
            widths = [max(len(r[i]) if i < len(r) else 0 for r in parsed) for i in range(col_count)]
            for i, row in enumerate(parsed):
                lines.append("  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)))
                if i == 0:
                    lines.append("-" * (sum(widths) + 2 * (col_count - 1)))
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error scraping CME FedWatch: {e}"


@mcp.tool()
async def get_circle_reserves() -> str:
    """
    Get USDC and EURC reserve data from Circle's transparency page (circle.com/transparency).
    Shows circulation, total reserves, reserve composition categories,
    and issuance/redemption flows (7d, 30d, 365d).
    """
    if StealthyFetcher is None:
        return "Error: scrapling not installed. Run: uvx scrapling install"
    try:
        page = await StealthyFetcher.async_fetch(
            "https://www.circle.com/transparency",
            headless=True,
            network_idle=True,
            timeout=30000,
        )

        main = page.css("main")
        text = (main[0] if main else page).get_all_text()

        date_m = re.search(r'As of ([A-Z][a-z]+ \d+, \d{4})', text)
        as_of = date_m.group(1) if date_m else "N/A"

        lines = [f"=== Circle Transparency — Reserves (as of {as_of}) ===\n"]

        # ── USDC ──
        usdc_m = re.search(
            r'In circulation\s*\$([\d.]+[BM])\s*Total Reserves\s*\$([\d.]+[BM])', text
        )
        if usdc_m:
            lines.append("--- USDC ---")
            lines.append(f"In Circulation:  ${usdc_m.group(1)}")
            lines.append(f"Total Reserves:  ${usdc_m.group(2)}")

        lines.append("\nReserve Composition:")
        for cat in [
            "Other Bank Deposits",
            "Deposits at Systemically Important Institutions",
            "Overnight Reverse Treasury Repo",
            "<3-Month Treasuries",
        ]:
            if cat in text:
                lines.append(f"  • {cat}")

        usdc_flow_m = re.search(
            r'7 Day Change\s*Issued\s*\$([\d.]+[BM])\s*Redeemed\s*\$([\d.]+[BM])\s*([+\-]\$[\d.]+[BM]).*?'
            r'30 Day Change\s*Issued\s*\$([\d.]+[BM])\s*Redeemed\s*\$([\d.]+[BM])\s*([+\-]\$[\d.]+[BM]).*?'
            r'365 Day Change\s*Issued\s*\$([\d.]+[BM])\s*Redeemed\s*\$([\d.]+[BM])\s*([+\-]\$[\d.]+[BM])',
            text, re.DOTALL,
        )
        if usdc_flow_m:
            g = usdc_flow_m.groups()
            lines.append("\nIssuance & Redemption:")
            lines.append(f"{'Period':<10} {'Issued':>10} {'Redeemed':>10} {'Net':>10}")
            lines.append("-" * 44)
            lines.append(f"{'7 Day':<10} ${g[0]:>8} ${g[1]:>8} {g[2]:>10}")
            lines.append(f"{'30 Day':<10} ${g[3]:>8} ${g[4]:>8} {g[5]:>10}")
            lines.append(f"{'365 Day':<10} ${g[6]:>8} ${g[7]:>8} {g[8]:>10}")

        # ── EURC ──
        eurc_m = re.search(
            r'In circulation\s*€([\d.]+[BM])\s*Total Reserves\s*\d*\s*€([\d.]+[BM])', text
        )
        if eurc_m:
            lines.append("\n--- EURC ---")
            lines.append(f"In Circulation:  €{eurc_m.group(1)}")
            lines.append(f"Total Reserves:  €{eurc_m.group(2)}")

        eurc_flow_m = re.search(
            r'7 Day Change\s*Issued\s*€([\d.]+[BM])\s*Redeemed\s*€([\d.]+[BM])\s*([+\-]€[\d.]+[BM]).*?'
            r'30 Day Change\s*Issued\s*€([\d.]+[BM])\s*Redeemed\s*€([\d.]+[BM])\s*([+\-]€[\d.]+[BM]).*?'
            r'365 Day Change\s*Issued\s*€([\d.]+[BM])\s*Redeemed\s*€([\d.]+[BM])\s*([+\-]€[\d.]+[BM])',
            text, re.DOTALL,
        )
        if eurc_flow_m:
            g = eurc_flow_m.groups()
            lines.append("\nIssuance & Redemption:")
            lines.append(f"{'Period':<10} {'Issued':>12} {'Redeemed':>12} {'Net':>12}")
            lines.append("-" * 50)
            lines.append(f"{'7 Day':<10} €{g[0]:>9} €{g[1]:>9} {g[2]:>10}")
            lines.append(f"{'30 Day':<10} €{g[3]:>9} €{g[4]:>9} {g[5]:>10}")
            lines.append(f"{'365 Day':<10} €{g[6]:>9} €{g[7]:>9} {g[8]:>10}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error scraping Circle transparency: {e}"


@mcp.tool()
def search_theblock(query: str, size: int = 10, fetch_body: bool = False, fetch_index: int = 1) -> str:
    """
    Search articles on The Block (theblock.co) and optionally fetch full article body.

    Args:
        query: Search query string
        size: Number of results to return (default: 10, max: 50)
        fetch_body: If True, fetch and return the full body of the article at fetch_index (default: False)
        fetch_index: 1-based index of the article to fetch body for (default: 1 = first result)
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(
            "https://www.theblock.co/api/tbco/search",
            params={"query": query, "start": 0, "size": min(size, 50)},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        entities = data.get("entities", [])
        if not entities:
            return f"No results found for '{query}'"

        lines = [f"=== The Block: '{query}' ({len(entities)} results) ===\n"]
        lines.append(f"{'#':<3} {'Date':<14} {'Author':<20} {'Title'}")
        lines.append("-" * 90)

        for i, item in enumerate(entities, 1):
            title = item.get("title", "")[:50]
            date = item.get("publishedFormattedMid", "")
            authors = item.get("authors") or []
            author = authors[0].get("name", "") if authors else ""
            lines.append(f"{i:<3} {date:<14} {author[:19]:<20} {title}")

        if fetch_body and entities:
            idx = max(1, min(fetch_index, len(entities))) - 1
            first_id = entities[idx].get("id")
            if first_id:
                r2 = requests.get(
                    f"https://www.theblock.co/api/tbco/post/{first_id}",
                    headers=headers,
                    timeout=15,
                )
                r2.raise_for_status()
                post_data = r2.json()
                scripts = post_data.get("data", {}).get("meta", {}).get("script", [])
                body = ""
                for s in scripts:
                    if not isinstance(s, dict):
                        continue
                    # articleBody lives inside the nested "json" object
                    candidate = s.get("json") or s
                    if isinstance(candidate, dict) and candidate.get("articleBody"):
                        body = candidate["articleBody"]
                        break
                if body:
                    lines.append(f"\n=== Full Article: {entities[idx].get('title', '')} ===\n")
                    lines.append(body[:5000] + ("..." if len(body) > 5000 else ""))
                else:
                    lines.append("\n[Could not extract article body]")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching The Block: {e}"


# ── QuiverQuant congressional trading ────────────────────────────────────────

_CACHE_DIR = Path.home() / ".cache" / "scrape-mcp"


def _qv_cache_json(ticker: str, date_str: str) -> Path:
    return _CACHE_DIR / f"quiverquant_{ticker.upper()}_{date_str}.json"


def _qv_chart_path(ticker: str, date_str: str) -> Path:
    return _CACHE_DIR / f"quiverquant_{ticker.upper()}_{date_str}.html"


def _qv_csv_path(ticker: str, date_str: str) -> Path:
    return _CACHE_DIR / f"quiverquant_{ticker.upper()}_{date_str}.csv"


def _qv_load_cache(ticker: str) -> dict | None:
    today = datetime.now().strftime("%Y-%m-%d")
    p = _qv_cache_json(ticker, today)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def _qv_save_cache(ticker: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    _qv_cache_json(ticker, today).write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


def _qv_parse_raw(raw: str, ticker: str) -> dict:
    """Parse raw SSR HTML → {traces: list, table: list[dict]}"""
    from scrapling.parser import Selector

    # ── Plotly traces ──────────────────────────────────────────────────────
    traces = []
    inline_scripts = re.findall(r"<script(?:[^>]*?)>(.*?)</script>", raw, re.DOTALL)
    for body in inline_scripts:
        if "Plotly.newPlot" not in body:
            continue
        np_m = re.search(r"Plotly\.newPlot\(\s*['\"]?[\w-]+['\"]?\s*,\s*(\[)", body)
        if not np_m:
            continue
        start = np_m.start(1)
        depth, end = 0, start
        for j, ch in enumerate(body[start:], start):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        try:
            traces = json.loads(body[start : end + 1])
        except json.JSONDecodeError:
            pass
        break

    # ── Congress trades table ──────────────────────────────────────────────
    rows = []
    doc = Selector(raw)
    tables = doc.css("table.table-congress")
    if tables:
        for row in tables[0].css("tbody tr"):
            cells = [td.get_all_text(separator="|", strip=True) for td in row.css("td")]
            if len(cells) < 5:
                continue
            c0 = [p.strip() for p in cells[0].split("|")]
            sym     = c0[0] if c0 else ""
            company = c0[1] if len(c0) > 1 else ""

            c1 = [p.strip() for p in cells[1].split("|")]
            txn_type = c1[0] if c1 else ""
            amount   = c1[1] if len(c1) > 1 else ""

            c2 = [p.strip() for p in cells[2].split("|")]
            pol_name      = c2[0] if c2 else ""
            chamber_party = c2[1] if len(c2) > 1 else ""

            rows.append({
                "ticker":        sym,
                "company":       company,
                "type":          txn_type,
                "amount":        amount,
                "politician":    pol_name,
                "chamber_party": chamber_party,
                "filed":         cells[3] if len(cells) > 3 else "",
                "traded":        cells[4] if len(cells) > 4 else "",
                "description":   cells[5] if len(cells) > 5 else "",
            })

    return {"ticker": ticker.upper(), "traces": traces, "table": rows}


async def _qv_fetch(ticker: str) -> dict:
    captured = {}
    url = f"https://www.quiverquant.com/congresstrading/stock/{ticker.upper()}"

    def page_action(page):
        captured["html"] = page.evaluate(f"fetch('{url}').then(r => r.text())")

    def _run():
        StealthyFetcher.fetch(
            url, headless=True, network_idle=True,
            page_action=page_action, timeout=60000,
        )

    await asyncio.to_thread(_run)
    raw = captured.get("html", "")
    if not raw:
        raise RuntimeError("No HTML captured from QuiverQuant")
    return _qv_parse_raw(raw, ticker)


def _qv_write_csv(ticker: str, date_str: str, table: list) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _qv_csv_path(ticker, date_str)
    if not table:
        p.write_text("no data\n", encoding="utf-8")
        return p
    headers = list(table[0].keys())
    lines = [",".join(f'"{h}"' for h in headers)]
    for row in table:
        lines.append(",".join(
            f'"{str(row.get(h, "")).replace(chr(34), chr(39))}"' for h in headers
        ))
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _qv_write_chart(ticker: str, date_str: str, traces: list) -> Path | None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _qv_chart_path(ticker, date_str)

    _COLORS = {
        "Closing Price":   ("#94a3b8", "lines"),
        "Stock Sales":     ("#ef4444", "markers"),
        "Stock Purchases": ("#22c55e", "markers"),
    }
    fig = go.Figure()
    for trace in traces:
        name      = trace.get("name", "")
        x         = trace.get("x", [])
        y         = trace.get("y", [])
        raw_text  = trace.get("text", [])
        text      = [t[0] if isinstance(t, list) else t for t in raw_text]
        color, mode = _COLORS.get(name, ("#818cf8", "markers"))
        if mode == "lines":
            fig.add_trace(go.Scatter(
                x=x, y=y, name=name, mode=mode,
                line=dict(color=color, width=1),
            ))
        else:
            fig.add_trace(go.Scatter(
                x=x, y=y, name=name, mode=mode,
                marker=dict(color=color, size=9, symbol="circle"),
                text=text, hovertemplate="%{text}<extra></extra>",
            ))

    fig.update_layout(
        title=f"Congressional Trading — {ticker.upper()}",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode="closest",
        template="plotly_dark",
        height=600,
    )
    fig.write_html(str(p))
    return p


@mcp.tool()
async def get_quiverquant_congress(
    ticker: str,
    use_cache: bool = True,
    output: str = "both",
) -> str:
    """
    Get congressional trading data for a stock from QuiverQuant.
    Saves a Plotly chart (HTML, auto-opened in browser) and/or a CSV file.

    Args:
        ticker: Stock ticker symbol (e.g. GOOGL, AAPL)
        use_cache: Use today's cached data if available (default True).
                   Set False to force a fresh fetch.
        output: What to generate — "chart" | "csv" | "both" (default "both")
    """
    import subprocess
    from collections import Counter

    try:
        ticker = ticker.upper()
        today  = datetime.now().strftime("%Y-%m-%d")

        # ── Load or fetch ──────────────────────────────────────────────────
        data         = None
        cache_status = "miss"
        if use_cache:
            data = _qv_load_cache(ticker)
            if data:
                cache_status = "hit"
        if data is None:
            data = await _qv_fetch(ticker)
            _qv_save_cache(ticker, data)
            cache_status = "fetched"

        traces = data.get("traces", [])
        table  = data.get("table", [])

        # ── Summary stats ──────────────────────────────────────────────────
        total     = len(table)
        purchases = sum(1 for r in table if "Purchase" in r.get("type", ""))
        sales     = sum(1 for r in table if "Sale"     in r.get("type", ""))

        pol_counts = Counter(r["politician"] for r in table)
        top_pols   = pol_counts.most_common(5)

        cutoff = (datetime.now() - timedelta(days=90)).date()
        recent = []
        for r in table:
            try:
                if datetime.strptime(r["traded"], "%b %d, %Y").date() >= cutoff:
                    recent.append(r)
            except Exception:
                pass

        lines = [f"=== QuiverQuant Congressional Trades: {ticker} ===\n"]
        lines.append(f"Cache: {cache_status}  |  As of: {today}")
        lines.append(f"Total: {total}  |  Purchases: {purchases}  |  Sales: {sales}\n")

        if top_pols:
            lines.append("Top politicians by trade count:")
            for pol, cnt in top_pols:
                lines.append(f"  {pol:<30} {cnt} trades")
            lines.append("")

        if recent:
            lines.append(f"Recent trades (last 90d): {len(recent)}")
            lines.append(f"{'Traded':<15} {'Politician':<28} {'Type':<10} {'Amount'}")
            lines.append("-" * 75)
            for r in recent[:20]:
                lines.append(
                    f"{r['traded'][:14]:<15} {r['politician'][:27]:<28}"
                    f" {r['type'][:9]:<10} {r['amount']}"
                )
            if len(recent) > 20:
                lines.append(f"  ... ({len(recent) - 20} more — see CSV)")
        else:
            lines.append("No trades in last 90 days.")

        # ── CSV ────────────────────────────────────────────────────────────
        if output in ("csv", "both"):
            csv_p = _qv_write_csv(ticker, today, table)
            lines.append(f"\nCSV  : {csv_p}")

        # ── Chart ──────────────────────────────────────────────────────────
        if output in ("chart", "both"):
            chart_p = _qv_write_chart(ticker, today, traces)
            if chart_p:
                lines.append(f"Chart: {chart_p}")
                try:
                    subprocess.Popen(["open", str(chart_p)])
                    lines.append("       (opened in browser)")
                except Exception:
                    pass
            else:
                lines.append("Chart: plotly not installed — run: uv pip install plotly")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching QuiverQuant data for {ticker}: {e}"


@mcp.tool()
def clear_quiverquant_cache(ticker: str = None) -> str:
    """
    Clear local QuiverQuant cache files (.json, .html, .csv).

    Args:
        ticker: Clear only this ticker's cache (optional).
                If omitted, clears all QuiverQuant cache files.
    """
    if not _CACHE_DIR.exists():
        return "Cache directory does not exist — nothing to clear."
    pattern = f"quiverquant_{ticker.upper()}_*" if ticker else "quiverquant_*"
    files = sorted(_CACHE_DIR.glob(pattern))
    if not files:
        return f"No cache files found{' for ' + ticker.upper() if ticker else ''}."
    for f in files:
        f.unlink()
    noun = f" for {ticker.upper()}" if ticker else ""
    return (
        f"Cleared {len(files)} cache file(s){noun}:\n"
        + "\n".join(f"  {f.name}" for f in files)
    )


if __name__ == "__main__":
    mcp.run()
