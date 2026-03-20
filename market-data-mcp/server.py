#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "yfinance>=0.2.0",
#   "requests>=2.31.0",
#   "beautifulsoup4>=4.12.0",
# ]
# ///
"""
Market Data MCP Server - yfinance + Finnhub
Stock quotes, financials, news, analyst recommendations
"""

import os
import json
from pathlib import Path

# curl_cffi (used by yfinance) bundles its own CA store and ignores the system one.
# On macOS with Homebrew openssl, point it to the correct cert bundle.
_brew_ca = Path("/opt/homebrew/etc/openssl@3/cert.pem")
if _brew_ca.exists():
    os.environ.setdefault("CURL_CA_BUNDLE", str(_brew_ca))
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_brew_ca))
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from mcp.server.fastmcp import FastMCP

CONFIG_FILE = Path.home() / ".config" / "market-data-mcp" / "config.json"
FINNHUB_BASE = "https://finnhub.io/api/v1"
SIMFIN_BASE = "https://backend.simfin.com/api/v3"

mcp = FastMCP("market-data")


def load_finnhub_key() -> str:
    key = os.environ.get("FINNHUB_API_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        key = cfg.get("finnhub_api_key", "")
        if key:
            return key
    return ""


def load_simfin_key() -> str:
    key = os.environ.get("SIMFIN_API_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        key = cfg.get("simfin_api_key", "")
        if key:
            return key
    return ""


def simfin_get(path: str, params: dict):
    key = load_simfin_key()
    if not key:
        raise ValueError(
            "SimFin API key not configured. Register free at https://simfin.com, "
            "then use configure(simfin_api_key='your_key') tool."
        )
    headers = {"Authorization": f"api-key {key}"}
    r = requests.get(f"{SIMFIN_BASE}{path}", params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def finnhub_get(endpoint: str, params: dict) -> dict:
    key = load_finnhub_key()
    if not key:
        raise ValueError("Finnhub API key not configured. Use configure() tool.")
    headers = {"X-Finnhub-Token": key}
    r = requests.get(f"{FINNHUB_BASE}{endpoint}", params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def configure(finnhub_api_key: str = "", simfin_api_key: str = "") -> str:
    """Save API keys to config file (~/.config/market-data-mcp/config.json)

    Args:
        finnhub_api_key: Finnhub API key (https://finnhub.io)
        simfin_api_key: SimFin API key, register free at https://simfin.com
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    if finnhub_api_key:
        cfg["finnhub_api_key"] = finnhub_api_key
    if simfin_api_key:
        cfg["simfin_api_key"] = simfin_api_key
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    saved = [k for k, v in [("Finnhub", finnhub_api_key), ("SimFin", simfin_api_key)] if v]
    return f"Saved {', '.join(saved) or 'no'} key(s) to {CONFIG_FILE}"


@mcp.tool()
def get_quote(ticker: str) -> str:
    """
    Get current stock quote: price, change%, volume, market cap

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, TSLA, NVDA)
    """
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        prev_close = info.previous_close
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
        volume = info.three_month_average_volume
        market_cap = info.market_cap

        lines = [
            f"=== {ticker.upper()} Quote ===",
            f"Price:      ${price:.2f}",
            f"Change:     {change_pct:+.2f}%",
            f"Prev Close: ${prev_close:.2f}" if prev_close else "",
            f"Avg Volume: {volume:,.0f}" if volume else "",
            f"Market Cap: ${market_cap:,.0f}" if market_cap else "",
        ]
        return "\n".join(l for l in lines if l)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_stock_info(ticker: str) -> str:
    """
    Get company profile: sector, description, PE ratio, EPS, beta

    Args:
        ticker: Stock ticker symbol
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        fields = [
            ("Name", info.get("longName", "N/A")),
            ("Sector", info.get("sector", "N/A")),
            ("Industry", info.get("industry", "N/A")),
            ("Exchange", info.get("exchange", "N/A")),
            ("Currency", info.get("currency", "N/A")),
            ("PE Ratio (TTM)", info.get("trailingPE", "N/A")),
            ("Forward PE", info.get("forwardPE", "N/A")),
            ("EPS (TTM)", info.get("trailingEps", "N/A")),
            ("Beta", info.get("beta", "N/A")),
            ("52W High", info.get("fiftyTwoWeekHigh", "N/A")),
            ("52W Low", info.get("fiftyTwoWeekLow", "N/A")),
            ("Dividend Yield", info.get("dividendYield", "N/A")),
        ]
        lines = [f"=== {ticker.upper()} Company Info ==="]
        for k, v in fields:
            lines.append(f"{k:<20} {v}")
        desc = info.get("longBusinessSummary", "")
        if desc:
            lines.append(f"\nDescription:\n{desc[:500]}...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_stock_history(ticker: str, period: str = "1mo", interval: str = "1d") -> str:
    """
    Get OHLCV price history

    Args:
        ticker: Stock ticker symbol
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y (default: 1mo)
        interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo (default: 1d)
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            return f"No history data for {ticker}"
        lines = [f"=== {ticker.upper()} Price History ({period}, {interval}) ==="]
        lines.append(f"{'Date':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>14}")
        lines.append("-" * 76)
        for idx, row in hist.tail(30).iterrows():
            date_str = str(idx)[:16]
            lines.append(
                f"{date_str:<20} {row['Open']:>10.2f} {row['High']:>10.2f} "
                f"{row['Low']:>10.2f} {row['Close']:>10.2f} {row['Volume']:>14,.0f}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_financials(ticker: str, statement: str = "income") -> str:
    """
    Get financial statements (last 4 quarters)

    Args:
        ticker: Stock ticker symbol
        statement: income, balance, or cashflow (default: income)
    """
    try:
        t = yf.Ticker(ticker)
        if statement == "income":
            df = t.quarterly_income_stmt
            title = "Income Statement"
        elif statement == "balance":
            df = t.quarterly_balance_sheet
            title = "Balance Sheet"
        elif statement == "cashflow":
            df = t.quarterly_cashflow
            title = "Cash Flow Statement"
        else:
            return "Invalid statement type. Use: income, balance, or cashflow"

        if df is None or df.empty:
            return f"No {statement} data for {ticker}"

        lines = [f"=== {ticker.upper()} {title} (Quarterly) ==="]
        col_dates = [str(c)[:10] for c in df.columns[:4]]
        header = f"{'Metric':<40}" + "".join(f"{d:>20}" for d in col_dates)
        lines.append(header)
        lines.append("-" * (40 + 20 * len(col_dates)))

        for idx, row in df.head(20).iterrows():
            metric = str(idx)[:39]
            vals = "".join(
                f"{row.iloc[i]/1e6:>19.1f}M" if i < len(row) and pd.notna(row.iloc[i]) and abs(row.iloc[i]) > 1000
                else f"{'N/A':>20}"
                for i in range(min(4, len(row)))
            )
            lines.append(f"{metric:<40}{vals}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_analyst_recommendations(ticker: str) -> str:
    """
    Get analyst buy/hold/sell recommendations and recent changes

    Args:
        ticker: Stock ticker symbol
    """
    try:
        t = yf.Ticker(ticker)
        rec = t.recommendations
        lines = [f"=== {ticker.upper()} Analyst Recommendations ==="]
        if rec is not None and not rec.empty:
            recent = rec.tail(10)
            lines.append(f"\nRecent Recommendation Changes:")
            lines.append(f"{'Date':<12} {'Firm':<30} {'From':<20} {'To':<20} {'Action'}")
            lines.append("-" * 90)
            for idx, row in recent.iterrows():
                date_str = str(idx)[:10]
                firm = str(row.get("Firm", ""))[:29]
                from_grade = str(row.get("From Grade", ""))[:19]
                to_grade = str(row.get("To Grade", ""))[:19]
                action = str(row.get("Action", ""))
                lines.append(f"{date_str:<12} {firm:<30} {from_grade:<20} {to_grade:<20} {action}")

        summary = t.recommendations_summary
        if summary is not None and not summary.empty:
            lines.append(f"\nCurrent Consensus:")
            for _, row in summary.iterrows():
                lines.append(f"  Period:      {row.get('period', 'N/A')}")
                lines.append(f"  Strong Buy:  {row.get('strongBuy', 0)}")
                lines.append(f"  Buy:         {row.get('buy', 0)}")
                lines.append(f"  Hold:        {row.get('hold', 0)}")
                lines.append(f"  Sell:        {row.get('sell', 0)}")
                lines.append(f"  Strong Sell: {row.get('strongSell', 0)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_market_news(category: str = "general") -> str:
    """
    Get latest market news via Finnhub

    Args:
        category: general, forex, crypto, or merger (default: general)
    """
    try:
        data = finnhub_get("/news", {"category": category})
        lines = [f"=== Market News ({category}) ===\n"]
        for item in data[:10]:
            dt = datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d %H:%M")
            headline = item.get("headline", "")
            summary = item.get("summary", "")[:200]
            source = item.get("source", "")
            lines.append(f"[{dt}] {source}")
            lines.append(f"  {headline}")
            if summary:
                lines.append(f"  {summary}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_company_news(ticker: str, days: int = 7) -> str:
    """
    Get recent company-specific news via Finnhub

    Args:
        ticker: Stock ticker symbol
        days: Number of days back to search (default: 7)
    """
    try:
        end = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        data = finnhub_get("/company-news", {"symbol": ticker.upper(), "from": start, "to": end})
        lines = [f"=== {ticker.upper()} News (last {days} days) ===\n"]
        for item in data[:15]:
            dt = datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d %H:%M")
            headline = item.get("headline", "")
            summary = item.get("summary", "")[:200]
            source = item.get("source", "")
            lines.append(f"[{dt}] {source}")
            lines.append(f"  {headline}")
            if summary:
                lines.append(f"  {summary}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_earnings_calendar(days_ahead: int = 7) -> str:
    """
    Get upcoming earnings announcements with consensus estimates via Finnhub

    Args:
        days_ahead: Days ahead to look for earnings (default: 7)
    """
    try:
        start = datetime.today().strftime("%Y-%m-%d")
        end = (datetime.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        data = finnhub_get("/calendar/earnings", {"from": start, "to": end})
        earnings = data.get("earningsCalendar", [])
        lines = [f"=== Earnings Calendar (next {days_ahead} days) ===\n"]
        lines.append(f"{'Date':<12} {'Ticker':<8} {'Time':<8} {'EPS Est':>10} {'Rev Est':>14}")
        lines.append("-" * 55)
        for item in earnings[:30]:
            date = item.get("date", "")
            symbol = item.get("symbol", "")[:7]
            hour = item.get("hour", "")
            eps_est = item.get("epsEstimate")
            rev_est = item.get("revenueEstimate")
            eps_str = f"${eps_est:.2f}" if eps_est else "N/A"
            rev_str = f"${rev_est/1e6:.0f}M" if rev_est else "N/A"
            lines.append(f"{date:<12} {symbol:<8} {hour:<8} {eps_str:>10} {rev_str:>14}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


_INVESTING_COUNTRY_IDS = "25,32,6,37,72,22,17,39,14,48,10,35,42,43,36,110,11,26,12,46,41,4,5,178"
_INVESTING_CURRENCY_MAP = {
    "US": "USD", "EU": "EUR", "CN": "CNY", "JP": "JPY", "GB": "GBP",
    "AU": "AUD", "CA": "CAD", "NZ": "NZD", "CH": "CHF", "KR": "KRW",
    "HK": "HKD", "SG": "SGD", "IN": "INR", "BR": "BRL", "MX": "MXN",
}

# Dividend calendar country IDs (Investing.com dividend calendar POST body).
# Source: <ul class="countryOption"> in https://cn.investing.com/dividends-calendar/
_DIV_COUNTRY_MAP = {
    "US": "5",   "UK": "4",   "DE": "17",  "FR": "22",  "CA": "6",
    "JP": "35",  "CN": "37",  "AU": "25",  "HK": "39",  "KR": "11",
    "CH": "12",  "NZ": "43",  "SG": "36",  "IN": "14",  "BR": "32",
    "TW": "46",  "SE": "9",   "ES": "26",  "NL": "21",  "IT": "10",
    "NO": "60",  "MY": "42",  "TH": "41",  "ZA": "110", "MX": "7",
    "BE": "34",  "FI": "71",
}
# Default: major markets (US, UK, CN, JP, HK, SG, AU, FR, CA, DE, KR, IN, BR)
_DIV_DEFAULT_COUNTRY_IDS = ["5", "4", "37", "35", "39", "36", "25", "22", "6", "17", "11", "14", "32"]


@mcp.tool()
def get_economic_calendar(days_ahead: int = 7, currency: str = "") -> str:
    """
    Get upcoming economic events (CPI, NFP, GDP, FOMC, PMI, etc.) via Investing.com.
    No API key required. Covers 24 major economies.

    Args:
        days_ahead: Days ahead to look for events (default: 7)
        currency: Filter by currency code, e.g. "USD", "EUR", "CNY" (default: all).
                  Also accepts country codes: "US", "EU", "CN", "JP", "GB".
    """
    try:
        now = datetime.utcnow()
        start = now.strftime("%Y-%m-%dT00:00:00.000+00:00")
        end = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%dT23:59:59.999+00:00")

        r = requests.get(
            "https://endpoints.investing.com/pd-instruments/v1/calendars/economic/events/occurrences",
            params={
                "domain_id": "6",
                "limit": "500",
                "start_date": start,
                "end_date": end,
                "country_ids": _INVESTING_COUNTRY_IDS,
            },
            headers={
                "accept": "*/*",
                "referer": "https://cn.investing.com/",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        events_df = pd.DataFrame(data.get("events", []))
        occ_df = pd.DataFrame(data.get("occurrences", []))

        if events_df.empty or occ_df.empty:
            return "No economic events found for the specified period."

        df = occ_df.merge(
            events_df[["event_id", "event_translated", "importance", "currency", "category"]],
            on="event_id",
            how="left",
        )

        # Normalize currency filter (accept both "US" and "USD")
        cur_filter = _INVESTING_CURRENCY_MAP.get(currency.upper(), currency.upper()) if currency else ""
        if cur_filter:
            df = df[df["currency"].str.upper() == cur_filter]

        df = df.sort_values("occurrence_time").reset_index(drop=True)

        impact_label = {"high": "[H]", "medium": "[M]", "low": "[L]"}
        beat_label = {"positive": "+", "negative": "-", "neutral": "="}

        def fmt_val(v, unit, precision):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return "N/A"
            try:
                prec = int(precision) if pd.notna(precision) else 2
                return f"{float(v):.{prec}f}{unit or ''}"
            except Exception:
                return str(v)

        title_suffix = f", {cur_filter}" if cur_filter else ""
        lines = [f"=== Economic Calendar (next {days_ahead} days{title_suffix}) — {len(df)} events ===\n"]
        lines.append(f"{'UTC Time':<17} {'CCY':<5} {'Imp':<4} {'Event':<42} {'Prev':>12} {'Forecast':>12} {'Actual':>12} {'vs Est'}")
        lines.append("-" * 112)

        for _, row in df.iterrows():
            try:
                dt = datetime.fromisoformat(row["occurrence_time"].replace("Z", "+00:00"))
                time_str = dt.strftime("%m-%d %H:%M UTC")
            except Exception:
                time_str = str(row["occurrence_time"])[:16]

            ccy = str(row.get("currency", ""))[:4]
            imp = impact_label.get(str(row.get("importance", "")).lower(), "   ")
            name = str(row.get("event_translated", ""))[:41]
            unit_raw = row.get("unit")
            unit = "" if unit_raw is None or (isinstance(unit_raw, float) and pd.isna(unit_raw)) else str(unit_raw)
            prec = row.get("precision")
            prev = fmt_val(row.get("previous"), unit, prec)
            forecast = fmt_val(row.get("forecast"), unit, prec)
            actual = fmt_val(row.get("actual"), unit, prec)
            beat = beat_label.get(str(row.get("actual_to_forecast", "")), " ")
            ref_raw = row.get("reference_period")
            ref = "" if ref_raw is None or (isinstance(ref_raw, float) and pd.isna(ref_raw)) else str(ref_raw)

            name_full = f"{name} {ref}".strip()[:41]
            lines.append(f"{time_str:<17} {ccy:<5} {imp:<4} {name_full:<42} {prev:>12} {forecast:>12} {actual:>12}  {beat}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_ipo_calendar(days_ahead: int = 30) -> str:
    """
    Get upcoming IPO listings with price range, shares offered, and exchange via Finnhub

    Args:
        days_ahead: Days ahead to look for IPOs (default: 30)
    """
    try:
        start = datetime.today().strftime("%Y-%m-%d")
        end = (datetime.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        data = finnhub_get("/calendar/ipo", {"from": start, "to": end})
        ipos = data.get("ipoCalendar", [])
        lines = [f"=== IPO Calendar (next {days_ahead} days) ===\n"]
        lines.append(f"{'Date':<12} {'Ticker':<8} {'Exchange':<10} {'Shares':>12} {'Price Range':<18} {'Status':<12} Name")
        lines.append("-" * 100)
        for item in sorted(ipos, key=lambda x: x.get("date", "")):
            date = item.get("date", "")
            symbol = item.get("symbol", "N/A")[:7]
            exchange = item.get("exchange", "")[:9]
            shares = item.get("numberOfShares")
            shares_str = f"{shares/1e6:.1f}M" if shares else "N/A"
            price = item.get("price")
            price_str = f"${price}" if price else "N/A"
            status = item.get("status", "")[:11]
            name = item.get("name", "")[:30]
            lines.append(f"{date:<12} {symbol:<8} {exchange:<10} {shares_str:>12} {price_str:<18} {status:<12} {name}")
        if not ipos:
            lines.append("No IPOs found for the specified period.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_dividend_calendar(
    ticker: str = "",
    timeframe: str = "thisWeek",
    country: str = "",
) -> str:
    """
    Dividend calendar in two modes:

    1. Per-stock (ticker provided): upcoming ex-dividend date, payment date, and
       recent dividend history for that ticker via yfinance.

    2. Market-wide (no ticker): all stocks going ex-dividend in the given timeframe,
       scraped from Investing.com. Shows company, ex-div date, dividend amount,
       frequency, payment date, and yield.

    Args:
        ticker:    Stock ticker for per-stock mode (e.g. AAPL). Leave empty for market scan.
        timeframe: Market-wide mode only — one of "today", "tomorrow", "thisWeek", "nextWeek".
                   Default "thisWeek".
        country:   Market-wide mode only — filter by country code, e.g. US, UK, DE, FR,
                   CA, JP, CN, AU, HK, KR, CH, NZ, SG, IN, BR, TW, SE, ES, NL, IT, NO,
                   MY, TH, ZA, MX, BE, FI. Leave empty for all major markets.
    """
    # ── Per-stock mode ────────────────────────────────────────────────────────
    if ticker:
        try:
            t = yf.Ticker(ticker.upper())
            lines = [f"=== Dividend Calendar: {ticker.upper()} ===\n"]

            try:
                cal = t.calendar
                ex_div = cal.get("Ex-Dividend Date", "N/A")
                pay_date = cal.get("Dividend Date", "N/A")
                lines.append("Upcoming:")
                lines.append(f"  Ex-Dividend Date : {ex_div}")
                lines.append(f"  Payment Date     : {pay_date}")
            except Exception:
                lines.append("Upcoming: N/A")

            divs = t.dividends
            if divs is not None and not divs.empty:
                lines.append("\nRecent Dividend History (last 8 payments):")
                lines.append(f"{'Date':<14} {'Amount':>10}")
                lines.append("-" * 26)
                for dt, amount in divs.tail(8).items():
                    date_str = str(dt.date()) if hasattr(dt, "date") else str(dt)[:10]
                    lines.append(f"{date_str:<14} ${amount:.4f}")

                info = t.fast_info
                price = getattr(info, "last_price", None)
                if price and len(divs) >= 4:
                    annual = float(divs.tail(4).sum())
                    yield_pct = annual / price * 100
                    lines.append(f"\nTrailing 4-payment annualized: ${annual:.4f} ({yield_pct:.2f}% yield at ${price:.2f})")
            else:
                lines.append("\nNo dividend history found.")

            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    # ── Market-wide mode ──────────────────────────────────────────────────────
    try:
        valid_tabs = {"today", "tomorrow", "thisWeek", "nextWeek"}
        tab = timeframe if timeframe in valid_tabs else "thisWeek"

        # Build country_ids list for POST body
        country_upper = country.upper()
        if country_upper and country_upper in _DIV_COUNTRY_MAP:
            cids = [_DIV_COUNTRY_MAP[country_upper]]
        else:
            cids = _DIV_DEFAULT_COUNTRY_IDS

        body_parts = [f"country%5B%5D={cid}" for cid in cids]
        body_parts += [f"currentTab={tab}", "limit_from=0"]
        body = "&".join(body_parts)

        r = requests.post(
            "https://cn.investing.com/dividends-calendar/Service/getCalendarFilteredData",
            headers={
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "x-requested-with": "XMLHttpRequest",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "referer": "https://cn.investing.com/dividends-calendar/",
            },
            data=body,
            timeout=15,
        )
        r.raise_for_status()
        payload = r.json()

        rows_num = payload.get("rows_num", 0)
        date_from = payload.get("dateFrom", "")
        date_to = payload.get("dateTo", "")
        html = payload.get("data", "")

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all("tr")

        lines = [f"=== Dividend Calendar ({tab}) ==="]
        if date_from == date_to:
            lines.append(f"Date: {date_from}  |  Results: {rows_num}")
        else:
            lines.append(f"Period: {date_from} → {date_to}  |  Results: {rows_num}")
        if country_upper and country_upper in _DIV_COUNTRY_MAP:
            lines.append(f"Filter: {country_upper}")
        lines.append("")
        lines.append(f"{'Company':<35} {'Ticker':<8} {'Ex-Div':<14} {'Dividend':>10} {'Freq':<6} {'Pay Date':<14} {'Yield':>7}  Country")
        lines.append("-" * 110)

        count = 0
        for row in rows:
            # Skip date-header rows
            if row.get("tablesorterdivider") is not None:
                continue
            tds = row.find_all("td")
            if len(tds) < 7:
                continue

            # td[0]: country flag
            flag_span = tds[0].find("span")
            country_name = flag_span.get("title", "") if flag_span else ""

            # td[1]: company name + ticker
            name_span = tds[1].find("span", class_="earnCalCompanyName")
            company_name = name_span.get_text(strip=True) if name_span else tds[1].get_text(strip=True)
            ticker_a = tds[1].find("a", class_="bold")
            sym = ticker_a.get_text(strip=True) if ticker_a else ""

            # td[2]: ex-dividend date
            ex_date = tds[2].get_text(strip=True)

            # td[3]: dividend amount
            div_amount = tds[3].get_text(strip=True)

            # td[4]: frequency (span title)
            freq_span = tds[4].find("span")
            freq = freq_span.get("title", "") if freq_span else tds[4].get_text(strip=True)

            # td[5]: payment date
            pay_date = tds[5].get_text(strip=True)

            # td[6]: yield
            div_yield = tds[6].get_text(strip=True)

            company_col = company_name[:34]
            lines.append(
                f"{company_col:<35} {sym:<8} {ex_date:<14} {div_amount:>10} {freq:<6} {pay_date:<14} {div_yield:>7}  {country_name}"
            )
            count += 1

        if count == 0:
            lines.append("No dividend events found for the selected period/country.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_options_expiry(ticker: str) -> str:
    """
    Get available options expiration dates and open interest summary for a stock via yfinance

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, SPY, TSLA)
    """
    try:
        t = yf.Ticker(ticker.upper())
        expirations = t.options
        if not expirations:
            return f"No options data found for {ticker.upper()}"

        lines = [f"=== Options Expiry Calendar: {ticker.upper()} ===\n"]
        lines.append(f"{'Expiry':<14} {'Days Out':>9} {'Calls OI':>10} {'Puts OI':>10} {'Total OI':>10} {'P/C Ratio':>10}")
        lines.append("-" * 65)

        today = datetime.today().date()
        for exp in expirations[:20]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days_out = (exp_date - today).days
                chain = t.option_chain(exp)
                calls_oi = int(chain.calls["openInterest"].sum()) if not chain.calls.empty else 0
                puts_oi = int(chain.puts["openInterest"].sum()) if not chain.puts.empty else 0
                total_oi = calls_oi + puts_oi
                pc_ratio = f"{puts_oi / calls_oi:.2f}" if calls_oi > 0 else "N/A"
                lines.append(f"{exp:<14} {days_out:>9} {calls_oi:>10,} {puts_oi:>10,} {total_oi:>10,} {pc_ratio:>10}")
            except Exception:
                lines.append(f"{exp:<14} {'N/A':>9}")

        lines.append(f"\nTotal expiration dates available: {len(expirations)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_price_target(ticker: str) -> str:
    """
    Get analyst consensus price target for a stock via Finnhub.
    Shows mean/median target, high/low range, and upside% from current price.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, NVDA, TSLA)
    """
    try:
        t = yf.Ticker(ticker.upper())
        info = t.info
        price = getattr(t.fast_info, "last_price", None)

        mean = info.get("targetMeanPrice")
        median = info.get("targetMedianPrice")
        high = info.get("targetHighPrice")
        low = info.get("targetLowPrice")
        num_analysts = info.get("numberOfAnalystOpinions")

        if not any([mean, median, high, low]):
            return f"No analyst price target data available for {ticker.upper()}"

        lines = [f"=== {ticker.upper()} Analyst Price Target ===\n"]
        if price:
            lines.append(f"Current Price:   ${price:.2f}")
        if num_analysts:
            lines.append(f"# Analysts:      {num_analysts}")
        if mean:
            upside = (mean - price) / price * 100 if price else None
            upside_str = f"  ({upside:+.1f}% upside)" if upside is not None else ""
            lines.append(f"Consensus Mean:  ${mean:.2f}{upside_str}")
        if median:
            med_upside = (median - price) / price * 100 if price else None
            med_str = f"  ({med_upside:+.1f}% upside)" if med_upside is not None else ""
            lines.append(f"Median Target:   ${median:.2f}{med_str}")
        if high:
            lines.append(f"High Target:     ${high:.2f}")
        if low:
            lines.append(f"Low Target:      ${low:.2f}")
        if high and low and price:
            lines.append(f"Target Range:    ${low:.2f} — ${high:.2f}  (±{(high-low)/2/price*100:.1f}% spread)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_short_interest(ticker: str) -> str:
    """
    Get short interest data for a stock via yfinance:
    short float%, short ratio (days to cover), shares short, month-over-month change.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, GME, NVDA)
    """
    try:
        info = yf.Ticker(ticker.upper()).info

        shares_short = info.get("sharesShort")
        shares_short_prior = info.get("sharesShortPriorMonth")
        short_ratio = info.get("shortRatio")
        short_pct_float = info.get("shortPercentOfFloat")
        float_shares = info.get("floatShares")
        shares_out = info.get("sharesOutstanding")
        date_short = info.get("dateShortInterest")

        if not any(v is not None for v in [short_pct_float, short_ratio, shares_short]):
            return f"No short interest data available for {ticker.upper()}"

        lines = [f"=== {ticker.upper()} Short Interest ===\n"]

        if date_short:
            try:
                date_str = datetime.fromtimestamp(date_short).strftime("%Y-%m-%d")
            except Exception:
                date_str = str(date_short)[:10]
            lines.append(f"Report Date:          {date_str}")

        if short_pct_float is not None:
            risk = " ⚠ HIGH" if short_pct_float > 0.20 else (" ELEVATED" if short_pct_float > 0.10 else "")
            lines.append(f"Short Float %:        {short_pct_float*100:.2f}%{risk}")
        if short_ratio is not None:
            lines.append(f"Days to Cover:        {short_ratio:.1f} days")
        if shares_short is not None:
            lines.append(f"Shares Short:         {shares_short:,.0f}")
        if shares_short_prior is not None:
            lines.append(f"Shares Short (prev):  {shares_short_prior:,.0f}")
            if shares_short:
                chg = (shares_short - shares_short_prior) / shares_short_prior * 100
                direction = "▲" if chg > 0 else "▼"
                lines.append(f"Month-over-Month:     {direction} {abs(chg):.1f}%")
        if float_shares is not None:
            lines.append(f"Float Shares:         {float_shares:,.0f}")
        if shares_out is not None:
            lines.append(f"Shares Outstanding:   {shares_out:,.0f}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_options_chain(
    ticker: str,
    expiry: str = "",
    option_type: str = "both",
) -> str:
    """
    Get full options chain with IV and Max Pain for a stock via yfinance.
    Shows top strikes by open interest for the given expiry date.

    Args:
        ticker:      Stock ticker symbol (e.g. AAPL, SPY, TSLA)
        expiry:      Expiry date YYYY-MM-DD (default: nearest expiry).
                     Use get_options_expiry() to see all available dates.
        option_type: "calls", "puts", or "both" (default: "both")
    """
    try:
        t = yf.Ticker(ticker.upper())
        expirations = t.options
        if not expirations:
            return f"No options data for {ticker.upper()}"

        chain = None
        if expiry and expiry in expirations:
            exp = expiry
        elif expiry:
            return f"Expiry {expiry} not available. Nearest dates: {', '.join(expirations[:5])}"
        else:
            # Skip today; scan up to 12 future expiries, pick the one with the most OI
            today_str = datetime.today().strftime("%Y-%m-%d")
            future = [e for e in expirations if e > today_str]
            best_exp = future[0] if future else expirations[0]
            best_oi = -1
            for candidate in future[:12]:
                try:
                    c = t.option_chain(candidate)
                    total_oi = int(c.calls["openInterest"].sum()) + int(c.puts["openInterest"].sum())
                    if total_oi > best_oi:
                        best_oi = total_oi
                        best_exp = candidate
                        chain = c
                    if total_oi >= 5000:  # good enough, stop early
                        break
                except Exception:
                    continue
            exp = best_exp

        if chain is None:
            chain = t.option_chain(exp)
        price = getattr(t.fast_info, "last_price", None)

        def calc_max_pain(calls_df, puts_df) -> float | None:
            # Filter out strikes more than 50% away from current price (noise removal)
            if price:
                lo, hi = price * 0.5, price * 1.5
                calls_df = calls_df[(calls_df["strike"] >= lo) & (calls_df["strike"] <= hi)]
                puts_df = puts_df[(puts_df["strike"] >= lo) & (puts_df["strike"] <= hi)]
            # Require at least 500 total OI in range — otherwise result is meaningless
            total_filtered_oi = int(calls_df["openInterest"].sum()) + int(puts_df["openInterest"].sum())
            if total_filtered_oi < 500:
                return None
            all_strikes = sorted(set(calls_df["strike"].tolist() + puts_df["strike"].tolist()))
            if not all_strikes:
                return None
            best_strike, best_pain = all_strikes[0], float("inf")
            for s in all_strikes:
                c_loss = float(((s - calls_df["strike"]).clip(lower=0) * calls_df["openInterest"]).sum())
                p_loss = float(((puts_df["strike"] - s).clip(lower=0) * puts_df["openInterest"]).sum())
                total = c_loss + p_loss
                if total < best_pain:
                    best_pain, best_strike = total, s
            return best_strike

        def fmt_chain(df, label):
            rows = [f"\n{label}:"]
            rows.append(f"{'Strike':>8} {'Last':>8} {'Bid':>7} {'Ask':>7} {'IV':>7} {'OI':>9} {'Volume':>8}  ITM")
            rows.append("-" * 68)
            top = df.sort_values("openInterest", ascending=False).head(25).sort_values("strike")
            for _, row in top.iterrows():
                strike = row.get("strike", 0)
                last = row.get("lastPrice", 0) or 0
                bid = row.get("bid", 0) or 0
                ask = row.get("ask", 0) or 0
                iv = row.get("impliedVolatility")
                oi = int(row.get("openInterest", 0) or 0)
                vol_raw = row.get("volume")
                vol = int(vol_raw) if pd.notna(vol_raw) else 0
                itm = "✓" if row.get("inTheMoney", False) else ""
                iv_str = f"{iv*100:.1f}%" if iv is not None and pd.notna(iv) else "N/A"
                rows.append(
                    f"{strike:>8.2f} {last:>8.2f} {bid:>7.2f} {ask:>7.2f} {iv_str:>7} {oi:>9,} {vol:>8,}  {itm}"
                )
            return rows

        lines = [f"=== {ticker.upper()} Options Chain — Expiry: {exp} ==="]
        if price:
            lines.append(f"Current Price: ${price:.2f}")

        max_pain = calc_max_pain(chain.calls, chain.puts)
        if max_pain is not None:
            distance = (max_pain - price) / price * 100 if price else 0
            lines.append(f"Max Pain:      ${max_pain:.2f}  ({distance:+.1f}% from current)")

        total_call_oi = int(chain.calls["openInterest"].sum()) if not chain.calls.empty else 0
        total_put_oi = int(chain.puts["openInterest"].sum()) if not chain.puts.empty else 0
        pc = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        lines.append(f"Total OI:      Calls {total_call_oi:,}  |  Puts {total_put_oi:,}  |  P/C {pc:.2f}")

        if option_type in ("calls", "both"):
            lines.extend(fmt_chain(chain.calls, "Calls (top 25 by OI)"))
        if option_type in ("puts", "both"):
            lines.extend(fmt_chain(chain.puts, "Puts (top 25 by OI)"))

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_news_sentiment(ticker: str) -> str:
    """
    Get Finnhub news sentiment and buzz score for a stock

    Args:
        ticker: Stock ticker symbol
    """
    try:
        data = finnhub_get("/news-sentiment", {"symbol": ticker.upper()})
        buzz = data.get("buzz", {})
        sentiment = data.get("sentiment", {})
        lines = [f"=== {ticker.upper()} News Sentiment ===\n"]
        lines.append("Buzz Metrics:")
        lines.append(f"  Articles (7d):     {buzz.get('articlesInLastWeek', 'N/A')}")
        lines.append(f"  Buzz Score:        {buzz.get('buzz', 'N/A')}")
        lines.append(f"  Weekly Average:    {buzz.get('weeklyAverage', 'N/A')}")
        lines.append("\nSentiment Scores:")
        lines.append(f"  Bearish:           {sentiment.get('bearishPercent', 'N/A')}")
        lines.append(f"  Bullish:           {sentiment.get('bullishPercent', 'N/A')}")
        lines.append(f"  Sector Avg Bull:   {data.get('sectorAverageBullishPercent', 'N/A')}")
        lines.append(f"  Sector Avg Bear:   {data.get('sectorAverageBearishPercent', 'N/A')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_simfin_financials(ticker: str, statement: str = "income", period: str = "ttm") -> str:
    """
    Get standardized financial statements via SimFin (requires free API key from simfin.com)

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, TSLA, NVDA)
        statement: income, balance, cashflow, or derived (default: income)
        period: ttm, q1, q2, q3, q4, fy, h1, h2 (default: ttm)
    """
    try:
        stmt_map = {"income": "pl", "balance": "bs", "cashflow": "cf", "derived": "derived"}
        stmt_code = stmt_map.get(statement.lower())
        if not stmt_code:
            return "Invalid statement. Use: income, balance, cashflow, or derived"

        valid_periods = {"ttm", "q1", "q2", "q3", "q4", "fy", "h1", "h2", "nine_month"}
        period_lower = period.lower()
        if period_lower not in valid_periods:
            return f"Invalid period. Use: ttm, q1, q2, q3, q4, fy, h1, h2"

        params: dict = {"ticker": ticker.upper(), "statements": stmt_code}
        if period_lower == "ttm":
            params["ttm"] = "true"
        else:
            params["period"] = period_lower

        data = simfin_get("/companies/statements/verbose", params)
        if not data:
            return f"Company not found: {ticker}"

        entry = data[0]
        stmts = entry.get("statements", [])
        if not stmts or not stmts[0].get("data"):
            return f"No {statement} data for {ticker} ({period})"

        row = stmts[0]["data"][-1]  # most recent period
        currency = entry.get("currency", "USD")

        title_map = {
            "income": "Income Statement (P&L)", "balance": "Balance Sheet",
            "cashflow": "Cash Flow Statement", "derived": "Derived Ratios & Indicators",
        }
        period_label = "TTM" if period_lower == "ttm" else period.upper()
        lines = [f"=== {ticker.upper()} {title_map[statement]} ({period_label}) — SimFin ==="]
        lines.append(
            f"Period: {row.get('Fiscal Period', '')} FY{row.get('Fiscal Year', '')} | "
            f"Report Date: {row.get('Report Date', '')} | Currency: {currency}\n"
        )
        lines.append(f"{'Metric':<50} {'Value':>18}")
        lines.append("-" * 70)

        SKIP = {"Fiscal Period", "Fiscal Year", "Report Date", "Publish Date",
                "Restated", "Source", "TTM", "Value Check", "Data Model"}
        for k, v in row.items():
            if k in SKIP or v is None:
                continue
            name = str(k)[:49]
            if isinstance(v, (int, float)) and abs(v) >= 1000:
                val_str = f"${v / 1e6:>16.1f}M"
            elif isinstance(v, float):
                val_str = f"{v:>18.4f}"
            else:
                val_str = f"{str(v):>18}"
            lines.append(f"{name:<50} {val_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
