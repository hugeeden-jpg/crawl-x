#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
Macro MCP Server - FRED API + SEC EDGAR
Federal Reserve data, economic indicators, SEC filings, 13F holdings
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

CONFIG_FILE = Path.home() / ".config" / "macro-mcp" / "config.json"
FRED_BASE = "https://api.stlouisfed.org/fred"
EDGAR_BASE = "https://data.sec.gov"
EDGAR_EFTS = "https://efts.sec.gov"
EDGAR_HEADERS = {"User-Agent": "financial-research-mcp/1.0 contact@example.com"}

mcp = FastMCP("macro-data")


def _date_in_quarter(date_str: str, period: str) -> bool:
    """Return True if date_str (YYYY-MM-DD) falls within the given period (e.g. '2024Q3')."""
    try:
        year = int(period[:4])
        q = int(period[5])
        month = int(date_str[5:7])
        file_year = int(date_str[:4])
        q_start = (q - 1) * 3 + 1
        q_end = q_start + 2
        # 13F filings are typically filed within 45 days of quarter end, so check year+quarter range
        return file_year == year and q_start <= month <= q_end + 1
    except (ValueError, IndexError):
        return False

KEY_SERIES = {
    "DFF": "Fed Funds Rate (Daily)",
    "CPIAUCSL": "CPI (All Urban Consumers, SA)",
    "GDP": "GDP (Billions USD, SA Annual Rate)",
    "UNRATE": "Unemployment Rate",
    "M2SL": "M2 Money Supply (Billions USD, SA)",
    "DGS10": "10-Year Treasury Yield",
    "DEXUSEU": "EUR/USD Exchange Rate",
}


def load_fred_key() -> str:
    key = os.environ.get("FRED_API_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        key = cfg.get("fred_api_key", "")
        if key:
            return key
    return ""


def fred_get(endpoint: str, params: dict) -> dict:
    key = load_fred_key()
    if not key:
        raise ValueError("FRED API key not configured. Use configure() tool.")
    params["api_key"] = key
    params["file_type"] = "json"
    r = requests.get(f"{FRED_BASE}{endpoint}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def configure(fred_api_key: str) -> str:
    """Save FRED API key to config file (~/.config/macro-mcp/config.json)"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"fred_api_key": fred_api_key}, indent=2))
    return f"FRED API key saved to {CONFIG_FILE}"


@mcp.tool()
def search_fred_series(keywords: str, limit: int = 10) -> str:
    """
    Search FRED for economic data series by keyword

    Args:
        keywords: Search terms (e.g. "inflation", "unemployment", "gdp")
        limit: Max results to return (default: 10)
    """
    try:
        data = fred_get("/series/search", {"search_text": keywords, "limit": limit})
        series = data.get("seriess", [])
        lines = [f"=== FRED Series Search: '{keywords}' ===\n"]
        lines.append(f"{'Series ID':<20} {'Title':<50} {'Units':<20} {'Freq'}")
        lines.append("-" * 100)
        for s in series:
            sid = s.get("id", "")[:19]
            title = s.get("title", "")[:49]
            units = s.get("units_short", "")[:19]
            freq = s.get("frequency_short", "")
            lines.append(f"{sid:<20} {title:<50} {units:<20} {freq}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_fred_data(series_id: str, start_date: str = None, end_date: str = None) -> str:
    """
    Get time series data from FRED

    Args:
        series_id: FRED series ID (e.g. DFF, CPIAUCSL, GDP, UNRATE, M2SL, DGS10)
        start_date: Start date YYYY-MM-DD (optional)
        end_date: End date YYYY-MM-DD (optional)
    """
    try:
        params = {"series_id": series_id}
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        params["sort_order"] = "desc"
        params["limit"] = 40

        data = fred_get("/series/observations", params)
        obs = data.get("observations", [])

        info_data = fred_get("/series", {"series_id": series_id})
        series_info = info_data.get("seriess", [{}])[0]
        title = series_info.get("title", series_id)
        units = series_info.get("units", "")
        freq = series_info.get("frequency", "")

        lines = [f"=== FRED: {series_id} — {title} ==="]
        lines.append(f"Units: {units} | Frequency: {freq}\n")
        lines.append(f"{'Date':<14} {'Value':>12}")
        lines.append("-" * 28)
        for ob in obs:
            val = ob.get("value", ".")
            val_str = f"{float(val):>12.4f}" if val != "." else f"{'N/A':>12}"
            lines.append(f"{ob['date']:<14} {val_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_key_indicators() -> str:
    """
    Get latest values for key macro indicators:
    Fed Funds Rate, CPI, GDP, Unemployment, M2, 10Y Treasury, EUR/USD
    """
    try:
        lines = ["=== Key Macro Indicators ===\n"]
        lines.append(f"{'Indicator':<40} {'Series ID':<12} {'Latest Value':<16} {'Date'}")
        lines.append("-" * 85)
        for sid, label in KEY_SERIES.items():
            try:
                data = fred_get("/series/observations", {
                    "series_id": sid,
                    "sort_order": "desc",
                    "limit": 1,
                })
                obs = data.get("observations", [{}])[0]
                val = obs.get("value", ".")
                date = obs.get("date", "N/A")
                val_str = f"{float(val):.4f}" if val != "." else "N/A"
                lines.append(f"{label:<40} {sid:<12} {val_str:<16} {date}")
            except Exception as inner_e:
                lines.append(f"{label:<40} {sid:<12} {'Error':<16} {str(inner_e)[:20]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def search_edgar_company(company_name: str) -> str:
    """
    Search SEC EDGAR for a company by name to get CIK, ticker, SIC code

    Args:
        company_name: Company name to search (e.g. "Apple", "Berkshire Hathaway")
    """
    try:
        # Use EDGAR full-text search API
        r = requests.get(
            f"{EDGAR_EFTS}/LATEST/search-index",
            params={"q": f'"{company_name}"', "forms": "10-K", "hits.hits._source": "period_of_report,entity_id,display_names,tickers,file_date"},
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])

        lines = [f"=== EDGAR Company Search: '{company_name}' ===\n"]
        seen_ciks = set()
        lines.append(f"{'CIK':<12} {'Ticker':<8} {'Name':<40}")
        lines.append("-" * 62)
        for hit in hits[:20]:
            src = hit.get("_source", {})
            cik = str(src.get("entity_id", ""))
            if cik in seen_ciks:
                continue
            seen_ciks.add(cik)
            name = src.get("display_names", [""])[0][:39] if src.get("display_names") else ""
            ticker = src.get("tickers", [""])[0] if src.get("tickers") else ""
            lines.append(f"{cik:<12} {ticker:<8} {name:<40}")
        return "\n".join(lines)
    except Exception as e:
        # Fallback: load company tickers JSON
        try:
            r2 = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=EDGAR_HEADERS,
                timeout=15,
            )
            r2.raise_for_status()
            tickers = r2.json()
            query = company_name.lower()
            lines = [f"=== EDGAR Company Search: '{company_name}' ===\n"]
            lines.append(f"{'CIK':<12} {'Ticker':<8} {'Name':<40}")
            lines.append("-" * 62)
            count = 0
            for entry in tickers.values():
                if query in entry.get("title", "").lower():
                    cik = str(entry.get("cik_str", ""))
                    ticker = entry.get("ticker", "")
                    name = entry.get("title", "")[:39]
                    lines.append(f"{cik:<12} {ticker:<8} {name:<40}")
                    count += 1
                    if count >= 15:
                        break
            return "\n".join(lines)
        except Exception as e2:
            return f"Error: {e}; Fallback error: {e2}"


@mcp.tool()
def get_recent_filings(ticker_or_cik: str, form_type: str = "10-K", limit: int = 5) -> str:
    """
    Get recent SEC filings for a company

    Args:
        ticker_or_cik: Stock ticker or CIK number (e.g. AAPL or 0000320193)
        form_type: Filing type: 10-K, 10-Q, 8-K, 13F-HR (default: 10-K)
        limit: Max filings to return (default: 5)
    """
    try:
        # Resolve ticker to CIK if needed
        # Use the static company_tickers.json (~1s) instead of the legacy CGI endpoint (~10s+)
        cik = ticker_or_cik.strip()
        if not cik.isdigit():
            r = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=EDGAR_HEADERS,
                timeout=15,
            )
            r.raise_for_status()
            ticker_upper = cik.upper()
            entry = next(
                (v for v in r.json().values() if v.get("ticker", "").upper() == ticker_upper),
                None,
            )
            if entry:
                cik = str(entry["cik_str"])

        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)
        r = requests.get(
            f"{EDGAR_BASE}/submissions/CIK{cik_padded}.json",
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        company = data.get("name", ticker_or_cik)
        filings = data.get("filings", {}).get("recent", {})

        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])

        lines = [f"=== {company} — Recent {form_type} Filings ===\n"]
        lines.append(f"{'Date':<14} {'Accession Number':<25} {'Form'}")
        lines.append("-" * 50)
        count = 0
        for i, form in enumerate(forms):
            if form == form_type:
                lines.append(f"{dates[i]:<14} {accessions[i]:<25} {form}")
                count += 1
                if count >= limit:
                    break
        if count == 0:
            lines.append(f"No {form_type} filings found")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_13f_holdings(cik: str, period: str = None) -> str:
    """
    Get top holdings from a fund's latest 13F filing

    Args:
        cik: CIK number of the fund (e.g. 0001067983 for Berkshire Hathaway)
        period: Filing period e.g. "2024Q3" (optional, uses latest if not specified)
    """
    try:
        cik_padded = cik.strip().zfill(10)
        r = requests.get(
            f"{EDGAR_BASE}/submissions/CIK{cik_padded}.json",
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        company = data.get("name", cik)

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])

        # Find the latest 13F-HR, optionally matching a quarter (e.g. "2024Q3")
        target_acc = None
        target_date = None
        for i, form in enumerate(forms):
            if form in ("13F-HR", "13F-HR/A"):
                if period is None or _date_in_quarter(dates[i], period):
                    target_acc = accessions[i]
                    target_date = dates[i]
                    break

        if not target_acc:
            return f"No 13F-HR filing found for CIK {cik}" + (f" for period {period}" if period else "")

        acc_clean = target_acc.replace("-", "")
        cik_num = cik_padded.lstrip("0") or "0"
        archive_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{acc_clean}/"

        lines = [f"=== {company} 13F Holdings ({target_date}) ==="]
        lines.append(f"Accession: {target_acc}")
        lines.append(f"\nTo view full holdings, access:")
        lines.append(f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type=13F-HR")
        lines.append(f"\nFiling index: {archive_url}")
        lines.append(f"Use get_filing_text('{target_acc}') for the raw filing content.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_filing_text(accession_number: str, section: str = None) -> str:
    """
    Get text content of an SEC filing (truncated to 8000 chars)

    Args:
        accession_number: Accession number (e.g. 0000320193-24-000123)
        section: Optional section name to search for within the filing
    """
    try:
        # Use EFTS full-text search to resolve accession → company/form metadata
        r = requests.get(
            f"{EDGAR_EFTS}/efts/v1/hits.json",
            params={"q": accession_number, "dateRange": "custom"},
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            return f"Filing {accession_number} not found in EDGAR full-text search"

        src = hits[0].get("_source", {})
        file_date = src.get("file_date", "")
        entity = src.get("display_names", [""])[0] if src.get("display_names") else ""
        form = src.get("form_type", "")
        cik = str(src.get("entity_id", "")).lstrip("0") or "0"

        acc_clean = accession_number.replace("-", "")
        archive_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/"

        lines = [f"=== Filing: {accession_number} ==="]
        lines.append(f"Company: {entity}")
        lines.append(f"Form:    {form}")
        lines.append(f"Filed:   {file_date}")
        lines.append(f"\nFiling index: {archive_url}")

        text_excerpt = str(src)[:8000]
        if section:
            idx = text_excerpt.lower().find(section.lower())
            if idx != -1:
                text_excerpt = text_excerpt[max(0, idx-100):idx+2000]
        lines.append(f"\n--- Metadata Preview ---\n{text_excerpt}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
