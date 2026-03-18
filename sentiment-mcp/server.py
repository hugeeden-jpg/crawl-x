#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
Sentiment MCP Server - Alternative.me + Quiver Quantitative
Social sentiment, fear/greed index, congressional trades, WSB mentions
"""

import os
import json
from pathlib import Path

# requests uses certifi by default; on macOS + Homebrew openssl the chain may not verify.
_brew_ca = Path("/opt/homebrew/etc/openssl@3/cert.pem")
if _brew_ca.exists():
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_brew_ca))

import requests
from datetime import datetime

from mcp.server.fastmcp import FastMCP

CONFIG_FILE = Path.home() / ".config" / "sentiment-mcp" / "config.json"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
QUIVER_BASE = "https://api.quiverquant.com/beta"

mcp = FastMCP("sentiment-data")


def load_config() -> dict:
    cfg = {}
    cfg["quiver_api_key"] = os.environ.get("QUIVER_API_KEY", "")

    if CONFIG_FILE.exists():
        file_cfg = json.loads(CONFIG_FILE.read_text())
        if not cfg["quiver_api_key"]:
            cfg["quiver_api_key"] = file_cfg.get("quiver_api_key", "")
    return cfg


@mcp.tool()
def configure(quiver_api_key: str) -> str:
    """Save Quiver API key to config file"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({
        "quiver_api_key": quiver_api_key,
    }, indent=2))
    return f"Credentials saved to {CONFIG_FILE}"


@mcp.tool()
def get_fear_greed_index(days: int = 1) -> str:
    """
    Get the Crypto Fear & Greed Index from Alternative.me

    Args:
        days: Number of days of history (1-30, default: 1)
    """
    try:
        r = requests.get(FEAR_GREED_URL, params={"limit": days, "format": "json"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        fng_data = data.get("data", [])

        lines = ["=== Crypto Fear & Greed Index ===\n"]
        lines.append(f"{'Date':<14} {'Score':>6} {'Classification'}")
        lines.append("-" * 40)
        for entry in fng_data:
            value = entry.get("value", "N/A")
            classification = entry.get("value_classification", "N/A")
            ts = int(entry.get("timestamp", 0))
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "N/A"

            emoji = ""
            if isinstance(value, str) and value.isdigit():
                v = int(value)
                if v < 25:
                    emoji = "😱 "
                elif v < 45:
                    emoji = "😨 "
                elif v < 55:
                    emoji = "😐 "
                elif v < 75:
                    emoji = "😊 "
                else:
                    emoji = "🤑 "
            lines.append(f"{date:<14} {value:>6}  {emoji}{classification}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_congressional_trades(ticker: str = None, days: int = 30) -> str:
    """
    Get recent congressional stock trades from Quiver Quantitative

    Args:
        ticker: Filter by ticker symbol (optional)
        days: Look back this many days (default: 30)
    """
    try:
        cfg = load_config()
        if not cfg["quiver_api_key"]:
            return "Quiver API key not configured. Use configure() tool."

        headers = {
            "Authorization": f"Token {cfg['quiver_api_key']}",
            "Accept": "application/json",
        }

        if ticker:
            url = f"{QUIVER_BASE}/live/congresstrading/{ticker.upper()}"
        else:
            url = f"{QUIVER_BASE}/live/congresstrading"

        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        trades = r.json()

        cutoff = datetime.now().timestamp() - days * 86400
        lines = [f"=== Congressional Trades" + (f": {ticker.upper()}" if ticker else "") + f" (last {days}d) ===\n"]
        lines.append(f"{'Date':<12} {'Politician':<25} {'Party':<5} {'Ticker':<8} {'Type':<6} {'Amount'}")
        lines.append("-" * 70)
        count = 0
        for trade in trades:
            date_str = trade.get("Date", trade.get("TransactionDate", ""))
            if date_str:
                try:
                    ts = datetime.strptime(date_str[:10], "%Y-%m-%d").timestamp()
                    if ts < cutoff:
                        continue
                except Exception:
                    pass
            politician = str(trade.get("Representative", trade.get("Senator", "Unknown")))[:24]
            party = str(trade.get("Party", ""))[:4]
            sym = str(trade.get("Ticker", ""))[:7]
            tx_type = str(trade.get("Transaction", ""))[:5]
            amount = str(trade.get("Range", trade.get("Amount", "")))
            lines.append(f"{date_str[:10]:<12} {politician:<25} {party:<5} {sym:<8} {tx_type:<6} {amount}")
            count += 1
            if count >= 30:
                break
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_wsb_mentions(ticker: str) -> str:
    """
    Get WallStreetBets mention count and sentiment from Quiver Quantitative

    Args:
        ticker: Stock ticker symbol (e.g. GME, NVDA, TSLA)
    """
    try:
        cfg = load_config()
        if not cfg["quiver_api_key"]:
            return "Quiver API key not configured. Use configure() tool."

        headers = {
            "Authorization": f"Token {cfg['quiver_api_key']}",
            "Accept": "application/json",
        }
        r = requests.get(
            f"{QUIVER_BASE}/live/wallstreetbets/{ticker.upper()}",
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        lines = [f"=== WSB Mentions: {ticker.upper()} ===\n"]
        if isinstance(data, list):
            lines.append(f"{'Date':<14} {'Mentions':>9} {'Sentiment':>11} {'Rank':>6}")
            lines.append("-" * 45)
            for entry in data[:20]:
                date = entry.get("Date", "")[:10]
                mentions = entry.get("Mentions", entry.get("Count", "N/A"))
                sentiment = entry.get("Sentiment", "N/A")
                rank = entry.get("Rank", "N/A")
                lines.append(f"{date:<14} {str(mentions):>9} {str(sentiment):>11} {str(rank):>6}")
        else:
            lines.append(json.dumps(data, indent=2)[:2000])
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_insider_sentiment(ticker: str) -> str:
    """
    Get insider trading sentiment summary from Quiver Quantitative

    Args:
        ticker: Stock ticker symbol
    """
    try:
        cfg = load_config()
        if not cfg["quiver_api_key"]:
            return "Quiver API key not configured. Use configure() tool."

        headers = {
            "Authorization": f"Token {cfg['quiver_api_key']}",
            "Accept": "application/json",
        }
        r = requests.get(
            f"{QUIVER_BASE}/live/insiders/{ticker.upper()}",
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        lines = [f"=== Insider Trading: {ticker.upper()} ===\n"]
        if isinstance(data, list):
            lines.append(f"{'Date':<12} {'Name':<30} {'Title':<25} {'Type':<8} {'Shares':>10} {'Value':>14}")
            lines.append("-" * 102)
            for entry in data[:20]:
                date = entry.get("Date", entry.get("FiledDate", ""))[:10]
                name = str(entry.get("Name", ""))[:29]
                title = str(entry.get("Title", ""))[:24]
                tx = str(entry.get("AcquiredDisposed", entry.get("Transaction", "")))[:7]
                shares = entry.get("Shares", "N/A")
                value = entry.get("Value", "N/A")
                lines.append(f"{date:<12} {name:<30} {title:<25} {tx:<8} {str(shares):>10} {str(value):>14}")
        else:
            lines.append(json.dumps(data, indent=2)[:2000])
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
