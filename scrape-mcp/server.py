#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
#   "beautifulsoup4>=4.12.0",
#   "scrapling[all]>=0.4.2",
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

_brew_ca = Path("/opt/homebrew/etc/openssl@3/cert.pem")
if _brew_ca.exists():
    # curl_cffi (Scrapling): used by Capitol Trades + CME FedWatch
    os.environ.setdefault("CURL_CA_BUNDLE", str(_brew_ca))
    # requests: used by get_insider_trades
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_brew_ca))

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
            return f"No insider trades table found on OpenInsider" + (f" for {ticker.upper()}" if ticker else "")

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
                lines.append("  ".join(texts[:6]))
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
        captured = {}

        TABLE_SEL = "#MainContent_pnlContainer > div.ui-widget-info > div > div > div > div > div.margin-bottom-sm > table"

        def fetch_fedwatch(page: Page):
            # Wait for the QuikStrike frame to navigate (event-driven, no fixed sleep)
            try:
                page.wait_for_event(
                    "framenavigated",
                    predicate=lambda f: "quikstrike" in f.url,
                    timeout=30000,
                )
            except Exception:
                pass

            # Find the QuikStrike child frame, wait for the exact probability table
            for frame in page.frames:
                if "quikstrike" not in frame.url:
                    continue
                try:
                    frame.wait_for_selector(TABLE_SEL, timeout=20000)
                    captured["html"] = frame.inner_html("#MainContent_pnlContainer")
                except Exception:
                    captured["html"] = frame.content()
                return

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

        soup = BeautifulSoup(html, "html.parser")
        lines = ["=== CME FedWatch — Fed Rate Probabilities ===\n"]

        # Use the known selector path; strip the leading "#MainContent_pnlContainer >"
        # since we already have inner_html of #MainContent_pnlContainer
        tables = soup.select("div.ui-widget-info div.margin-bottom-sm table")
        if not tables:
            # fallback: any table in the container
            tables = soup.find_all("table")
        if not tables:
            lines.append(soup.get_text(separator=" ", strip=True)[:3000])
            return "\n".join(lines)

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue
            parsed = []
            for row in rows:
                cells = row.find_all(["th", "td"])
                texts = [c.get_text(strip=True) for c in cells]
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


if __name__ == "__main__":
    mcp.run()
