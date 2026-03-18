#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "yfinance>=0.2.0",
#   "requests>=2.31.0",
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
import requests
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from mcp.server.fastmcp import FastMCP

CONFIG_FILE = Path.home() / ".config" / "market-data-mcp" / "config.json"
FINNHUB_BASE = "https://finnhub.io/api/v1"

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


def finnhub_get(endpoint: str, params: dict) -> dict:
    key = load_finnhub_key()
    if not key:
        raise ValueError("Finnhub API key not configured. Use configure() tool.")
    headers = {"X-Finnhub-Token": key}
    r = requests.get(f"{FINNHUB_BASE}{endpoint}", params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def configure(finnhub_api_key: str) -> str:
    """Save Finnhub API key to config file (~/.config/market-data-mcp/config.json)"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"finnhub_api_key": finnhub_api_key}, indent=2))
    return f"Finnhub API key saved to {CONFIG_FILE}"


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


if __name__ == "__main__":
    mcp.run()
