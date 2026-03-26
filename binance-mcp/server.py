# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from ssl_utils import apply_ssl_fix
    apply_ssl_fix()
except ImportError:
    pass

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("binance-data")

BASE_SPOT   = "https://api.binance.com/api/v3"
BASE_FAPI   = "https://fapi.binance.com/fapi/v1"   # USD-M futures
BASE_FAPI2  = "https://fapi.binance.com/fapi/v2"


def fapi(path: str, params: dict = None) -> dict | list:
    r = requests.get(f"{BASE_FAPI}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def fapi2(path: str, params: dict = None) -> dict | list:
    r = requests.get(f"{BASE_FAPI2}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def spot(path: str, params: dict = None) -> dict | list:
    r = requests.get(f"{BASE_SPOT}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def fmt_symbol(symbol: str) -> str:
    s = symbol.upper().replace("-", "").replace("/", "")
    if not s.endswith("USDT") and not s.endswith("BUSD") and not s.endswith("BTC"):
        s += "USDT"
    return s


# ── Tools ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_funding_rate(symbol: str, limit: int = 10) -> str:
    """Get current and historical funding rates for a Binance USDT-M futures contract.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT', 'ETHUSDT', 'SOLUSDT'. USDT appended if missing.
        limit: Number of historical rate entries to return (max 1000)
    """
    try:
        sym = fmt_symbol(symbol)
        # current premium index (includes next funding rate)
        premium = fapi("/premiumIndex", {"symbol": sym})
        cur_rate = float(premium.get("lastFundingRate", 0)) * 100
        next_time = premium.get("nextFundingTime", "")
        mark_price = float(premium.get("markPrice", 0))
        index_price = float(premium.get("indexPrice", 0))

        # historical funding
        hist = fapi("/fundingRate", {"symbol": sym, "limit": limit})

        lines = [
            f"Binance Futures Funding Rate — {sym}",
            "=" * 55,
            f"{'Mark Price:':<22} {mark_price:,.4f}",
            f"{'Index Price:':<22} {index_price:,.4f}",
            f"{'Current Rate:':<22} {cur_rate:+.4f}%",
            "",
            f"{'Timestamp':<22} {'Funding Rate':>14}",
            "-" * 38,
        ]
        for h in reversed(hist):
            ts = str(h.get("fundingTime", ""))[:10]  # epoch ms → str
            import datetime
            try:
                ts_fmt = datetime.datetime.fromtimestamp(int(ts) / 1000 if len(ts) > 10 else int(ts)).strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts_fmt = ts
            rate = float(h.get("fundingRate", 0)) * 100
            lines.append(f"{ts_fmt:<22} {rate:>+13.4f}%")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_open_interest(symbol: str, period: str = "1d", limit: int = 10) -> str:
    """Get open interest history for a Binance USDT-M futures contract.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT'
        period: Interval — '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d'
        limit: Number of data points (max 500)
    """
    try:
        sym = fmt_symbol(symbol)
        data = fapi("/openInterestHist", {"symbol": sym, "period": period, "limit": limit})
        if isinstance(data, dict) and "code" in data:
            return f"API Error: {data.get('msg', data)}"

        lines = [f"Binance Open Interest History — {sym} ({period})", "=" * 55,
                 f"{'Timestamp':<22} {'OI (contracts)':>18} {'OI (USDT)':>18}"]
        import datetime
        for d in data:
            ts = int(d.get("timestamp", 0))
            ts_fmt = datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
            oi     = float(d.get("sumOpenInterest", 0))
            oi_val = float(d.get("sumOpenInterestValue", 0))
            lines.append(f"{ts_fmt:<22} {oi:>18,.2f} {oi_val/1e6:>17,.1f}M")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_long_short_ratio(symbol: str, period: str = "1d", limit: int = 10) -> str:
    """Get long/short ratio for top trader accounts on Binance futures.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT'
        period: Interval — '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d'
        limit: Number of data points
    """
    try:
        sym = fmt_symbol(symbol)
        # top trader position ratio
        data = fapi("/topLongShortPositionRatio", {"symbol": sym, "period": period, "limit": limit})
        if isinstance(data, dict) and "code" in data:
            return f"API Error: {data.get('msg', data)}"

        import datetime
        lines = [f"Top Trader Long/Short Ratio — {sym} ({period})", "=" * 55,
                 f"{'Timestamp':<22} {'L/S Ratio':>10} {'Long %':>10} {'Short %':>10}"]
        for d in data:
            ts_fmt = datetime.datetime.fromtimestamp(int(d.get("timestamp", 0)) / 1000).strftime("%Y-%m-%d %H:%M")
            ratio  = float(d.get("longShortRatio", 0))
            long_p = float(d.get("longAccount", 0)) * 100
            short_p = float(d.get("shortAccount", 0)) * 100
            lines.append(f"{ts_fmt:<22} {ratio:>10.3f} {long_p:>9.1f}% {short_p:>9.1f}%")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_liquidations_summary(symbol: str = "BTCUSDT") -> str:
    """Get recent forced liquidation orders for a Binance futures contract.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT', 'ETHUSDT'
    """
    try:
        sym = fmt_symbol(symbol)
        data = fapi("/allForceOrders", {"symbol": sym, "limit": 20})
        if isinstance(data, dict) and "code" in data:
            return f"API Error: {data.get('msg', data)}"

        import datetime
        lines = [f"Recent Liquidations — {sym}", "=" * 65,
                 f"{'Time':<22} {'Side':<6} {'Price':>12} {'Qty':>12} {'USD Value':>14}"]
        total_long = total_short = 0.0
        for d in data:
            ts_fmt = datetime.datetime.fromtimestamp(int(d.get("time", 0)) / 1000).strftime("%Y-%m-%d %H:%M")
            side   = d.get("side", "")
            price  = float(d.get("averagePrice", d.get("price", 0)))
            qty    = float(d.get("origQty", 0))
            value  = price * qty
            if side == "BUY":   # forced buy = short liquidation
                total_short += value
            else:
                total_long  += value
            lines.append(f"{ts_fmt:<22} {side:<6} {price:>12,.2f} {qty:>12,.3f} {value/1e3:>13,.1f}K")

        lines += ["", f"  Total LONG  liquidated: ${total_long/1e6:.2f}M",
                      f"  Total SHORT liquidated: ${total_short/1e6:.2f}M"]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_market_stats(symbol: str) -> str:
    """Get 24-hour price statistics for a Binance futures contract.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT', 'SOLUSDT'
    """
    try:
        sym = fmt_symbol(symbol)
        d = fapi("/ticker/24hr", {"symbol": sym})
        if isinstance(d, dict) and "code" in d:
            return f"API Error: {d.get('msg', d)}"

        price    = float(d.get("lastPrice", 0))
        change   = float(d.get("priceChangePercent", 0))
        high     = float(d.get("highPrice", 0))
        low      = float(d.get("lowPrice", 0))
        vol      = float(d.get("volume", 0))
        quote_vol= float(d.get("quoteVolume", 0))
        trades   = int(d.get("count", 0))

        lines = [
            f"24h Stats — {sym}",
            "=" * 40,
            f"{'Last Price:':<18} {price:,.4f}",
            f"{'24h Change:':<18} {change:+.2f}%",
            f"{'24h High:':<18} {high:,.4f}",
            f"{'24h Low:':<18} {low:,.4f}",
            f"{'Volume:':<18} {vol:,.2f} {sym.replace('USDT','')}",
            f"{'Quote Volume:':<18} ${quote_vol/1e6:,.1f}M",
            f"{'Trade Count:':<18} {trades:,}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_top_movers(limit: int = 20) -> str:
    """Get top gainers and losers across all Binance USDT-M futures in the last 24 hours.

    Args:
        limit: Number of top gainers and losers to show each
    """
    try:
        data = fapi("/ticker/24hr")
        if not isinstance(data, list):
            return f"Unexpected response: {data}"

        usdt = [d for d in data if d.get("symbol", "").endswith("USDT")]
        usdt.sort(key=lambda x: float(x.get("priceChangePercent", 0)), reverse=True)

        gainers = usdt[:limit]
        losers  = usdt[-limit:][::-1]

        header = f"{'Symbol':<14} {'Change':>10} {'Last Price':>14} {'Volume (USDT M)':>18}"
        sep = "-" * 58

        lines = [f"Binance Futures — Top {limit} Movers (24h)", "=" * 58, "  TOP GAINERS", sep, header, sep]
        for d in gainers:
            sym    = d.get("symbol","")
            chg    = float(d.get("priceChangePercent", 0))
            price  = float(d.get("lastPrice", 0))
            vol    = float(d.get("quoteVolume", 0)) / 1e6
            lines.append(f"{sym:<14} {chg:>+9.2f}% {price:>14,.4f} {vol:>17,.1f}M")

        lines += ["", "  TOP LOSERS", sep, header, sep]
        for d in losers:
            sym    = d.get("symbol","")
            chg    = float(d.get("priceChangePercent", 0))
            price  = float(d.get("lastPrice", 0))
            vol    = float(d.get("quoteVolume", 0)) / 1e6
            lines.append(f"{sym:<14} {chg:>+9.2f}% {price:>14,.4f} {vol:>17,.1f}M")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_futures_kline(symbol: str, interval: str = "1d", limit: int = 20) -> str:
    """Get OHLCV candlestick data for a Binance USDT-M futures contract.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT'
        interval: Candle interval — '1m','5m','15m','30m','1h','4h','1d','1w'
        limit: Number of candles (max 1500)
    """
    try:
        sym = fmt_symbol(symbol)
        data = fapi("/klines", {"symbol": sym, "interval": interval, "limit": limit})
        if isinstance(data, dict) and "code" in data:
            return f"API Error: {data.get('msg', data)}"

        import datetime
        lines = [f"Klines — {sym} ({interval})", "=" * 72,
                 f"{'Open Time':<22} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12} {'Volume':>12}"]
        for c in data:
            ts_fmt = datetime.datetime.fromtimestamp(int(c[0]) / 1000).strftime("%Y-%m-%d %H:%M")
            o, h, l, cl, vol = float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])
            lines.append(f"{ts_fmt:<22} {o:>12,.4f} {h:>12,.4f} {l:>12,.4f} {cl:>12,.4f} {vol:>12,.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_basis(symbol: str, period: str = "1d", limit: int = 10) -> str:
    """Get futures basis (futures price vs spot index price) history. Positive = futures premium.

    Args:
        symbol: Trading pair, e.g. 'BTCUSDT'
        period: Interval — '5m','15m','30m','1h','2h','4h','6h','12h','1d'
        limit: Number of data points
    """
    try:
        sym = fmt_symbol(symbol)
        data = fapi("/basis", {"symbol": sym, "contractType": "PERPETUAL", "period": period, "limit": limit})
        if isinstance(data, dict) and "code" in data:
            return f"API Error: {data.get('msg', data)}"

        import datetime
        lines = [f"Futures Basis — {sym} ({period})", "=" * 55,
                 f"{'Timestamp':<22} {'Futures Price':>15} {'Index Price':>13} {'Basis %':>10}"]
        for d in data:
            ts_fmt = datetime.datetime.fromtimestamp(int(d.get("timestamp", 0)) / 1000).strftime("%Y-%m-%d %H:%M")
            fp  = float(d.get("futuresPrice", 0))
            ip  = float(d.get("indexPrice", 0))
            basis = float(d.get("basis", 0))
            basis_pct = float(d.get("basisRate", 0)) * 100
            lines.append(f"{ts_fmt:<22} {fp:>15,.4f} {ip:>13,.4f} {basis_pct:>+9.4f}%")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
