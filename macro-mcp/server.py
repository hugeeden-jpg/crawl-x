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

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ssl_utils import apply_ssl_fix  # noqa: E402
apply_ssl_fix()

import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta, date as _date

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
    cfg = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    cfg["fred_api_key"] = fred_api_key
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
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


# ── BLS (Bureau of Labor Statistics) ─────────────────────────────────────────

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

BLS_SERIES_CATALOG = {
    "cpi_all":            ("CUUR0000SA0",            "CPI All Items (Urban)"),
    "cpi_core":           ("CUUR0000SA0L1E",          "CPI Core (ex Food & Energy)"),
    "cpi_food":           ("CUUR0000SAF1",             "CPI Food"),
    "cpi_energy":         ("CUUR0000SA0E",             "CPI Energy"),
    "cpi_shelter":        ("CUUR0000SAH1",             "CPI Shelter"),
    "cpi_medical":        ("CUUR0000SAM",              "CPI Medical Care"),
    "cpi_transportation": ("CUUR0000SAT",              "CPI Transportation"),
    "ppi_final":          ("WPSFD4",                   "PPI Final Demand"),
    "ppi_core":           ("WPUFD49104",               "PPI Core Final Demand (ex Food & Energy)"),
    "ppi_goods":          ("WPSFD49",                  "PPI Final Demand Goods"),
    "ppi_services":       ("WPSFD49116",               "PPI Final Demand Services"),
    "nfp_total":          ("CES0000000001",            "Nonfarm Payrolls (Total, thousands)"),
    "nfp_private":        ("CES0500000001",            "Nonfarm Payrolls (Private)"),
    "unemployment":       ("LNS14000000",              "Unemployment Rate (%)"),
    "u6":                 ("LNS13327709",              "U-6 Underemployment Rate (%)"),
    "participation":      ("LNS11300000",              "Labor Force Participation Rate (%)"),
    "avg_hourly_wages":   ("CES0500000003",            "Avg Hourly Earnings, Private ($/hr)"),
    "avg_weekly_hours":   ("CES0500000002",            "Avg Weekly Hours, Private"),
    "jolts_openings":     ("JTS000000000000000JOL",   "JOLTS Job Openings (thousands)"),
    "jolts_quits":        ("JTS000000000000000QUL",   "JOLTS Quits Rate (%)"),
}


def _load_bls_key() -> str:
    key = os.environ.get("BLS_API_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        return cfg.get("bls_api_key", "")
    return ""


def _bls_fetch(series_ids: list, start_year: int, end_year: int) -> dict:
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "calculations": True,
        "annualaverage": False,
    }
    api_key = _load_bls_key()
    if api_key:
        payload["registrationkey"] = api_key
    r = requests.post(BLS_API, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        msg = " | ".join(data.get("message", ["Unknown BLS error"]))
        raise ValueError(f"BLS API error: {msg}")
    result = {}
    for s in data.get("Results", {}).get("series", []):
        result[s["seriesID"]] = s.get("data", [])
    return result


def _period_label(year: str, period: str) -> str:
    month_map = {
        "M01": "Jan", "M02": "Feb", "M03": "Mar", "M04": "Apr",
        "M05": "May", "M06": "Jun", "M07": "Jul", "M08": "Aug",
        "M09": "Sep", "M10": "Oct", "M11": "Nov", "M12": "Dec",
        "Q01": "Q1",  "Q02": "Q2",  "Q03": "Q3",  "Q04": "Q4",
    }
    return f"{year}-{month_map.get(period, period)}"


@mcp.tool()
def configure_bls(bls_api_key: str) -> str:
    """Save BLS API key (optional, increases rate limits). Register free at https://www.bls.gov/developers/

    Args:
        bls_api_key: Your BLS public API key (free registration)
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    cfg["bls_api_key"] = bls_api_key
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    return f"BLS API key saved to {CONFIG_FILE}"


@mcp.tool()
def get_cpi(months: int = 24, breakdown: bool = False) -> str:
    """Get US Consumer Price Index (CPI) — headline and core. Main inflation gauge watched by the Fed.

    Args:
        months: Number of months of history to show (max 96)
        breakdown: If True, also show Food, Energy, Shelter, Medical sub-components
    """
    try:
        today = _date.today()
        start_year = today.year - (months // 12 + 2)
        series = ["CUUR0000SA0", "CUUR0000SA0L1E"]
        if breakdown:
            series += ["CUUR0000SAF1", "CUUR0000SA0E", "CUUR0000SAH1", "CUUR0000SAM"]
        raw = _bls_fetch(series, start_year, today.year)
        headline = raw.get("CUUR0000SA0", [])[:months]
        core = {f"{r['year']}-{r['period']}": r for r in raw.get("CUUR0000SA0L1E", [])}
        header = f"{'Date':<12} {'Headline':>10} {'MoM%':>7} {'YoY%':>7} {'Core':>8} {'Core MoM%':>11} {'Core YoY%':>11}"
        if breakdown:
            header += f" {'Food':>8} {'Energy':>8} {'Shelter':>9} {'Medical':>9}"
        lines = ["US Consumer Price Index (CPI)", "=" * len(header), header, "-" * len(header)]
        for row in headline:
            key = f"{row['year']}-{row['period']}"
            label = _period_label(row["year"], row["period"])
            val = float(row["value"])
            calcs = row.get("calculations", {}).get("pct_changes", {})
            mom = calcs.get("1", "")
            yoy = calcs.get("12", "")
            mom_s = f"{float(mom):>+6.2f}%" if mom else f"{'N/A':>7}"
            yoy_s = f"{float(yoy):>+6.2f}%" if yoy else f"{'N/A':>7}"
            core_row = core.get(key, {})
            core_val = float(core_row.get("value", 0)) if core_row else 0
            core_calcs = core_row.get("calculations", {}).get("pct_changes", {}) if core_row else {}
            core_mom = core_calcs.get("1", "")
            core_yoy = core_calcs.get("12", "")
            core_mom_s = f"{float(core_mom):>+9.2f}%" if core_mom else f"{'N/A':>10}"
            core_yoy_s = f"{float(core_yoy):>+9.2f}%" if core_yoy else f"{'N/A':>10}"
            line = f"{label:<12} {val:>10.3f} {mom_s:>7} {yoy_s:>7} {core_val:>8.3f} {core_mom_s:>11} {core_yoy_s:>11}"
            if breakdown:
                def get_val(sid, k=key):
                    entry = next((r for r in raw.get(sid, []) if f"{r['year']}-{r['period']}" == k), None)
                    return f"{float(entry['value']):>8.3f}" if entry else f"{'N/A':>8}"
                line += f" {get_val('CUUR0000SAF1')} {get_val('CUUR0000SA0E')} {get_val('CUUR0000SAH1'):>9} {get_val('CUUR0000SAM'):>9}"
            lines.append(line)
        lines.append("\nNote: Index base = 1982-84 = 100. Core excludes food & energy.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_ppi(months: int = 18) -> str:
    """Get US Producer Price Index (PPI) — upstream inflation, leads CPI by 1-3 months.

    Args:
        months: Number of months of history to show
    """
    try:
        today = _date.today()
        start_year = today.year - (months // 12 + 2)
        raw = _bls_fetch(["WPSFD4", "WPUFD49104", "WPSFD49", "WPSFD49116"], start_year, today.year)
        final = raw.get("WPSFD4", [])[:months]
        core = {f"{r['year']}-{r['period']}": r for r in raw.get("WPUFD49104", [])}
        goods = {f"{r['year']}-{r['period']}": r for r in raw.get("WPSFD49", [])}
        svc = {f"{r['year']}-{r['period']}": r for r in raw.get("WPSFD49116", [])}
        header = f"{'Date':<12} {'Final Demand':>13} {'MoM%':>7} {'YoY%':>7} {'Core':>8} {'Goods':>8} {'Services':>10}"
        lines = ["US Producer Price Index (PPI)", "=" * len(header), header, "-" * len(header)]
        for row in final:
            key = f"{row['year']}-{row['period']}"
            label = _period_label(row["year"], row["period"])
            val = float(row["value"])
            calcs = row.get("calculations", {}).get("pct_changes", {})
            mom = calcs.get("1", "")
            yoy = calcs.get("12", "")
            mom_s = f"{float(mom):>+6.2f}%" if mom else f"{'N/A':>7}"
            yoy_s = f"{float(yoy):>+6.2f}%" if yoy else f"{'N/A':>7}"
            def pick(d, k=key): return f"{float(d[k]['value']):>8.3f}" if k in d else f"{'N/A':>8}"
            lines.append(f"{label:<12} {val:>13.3f} {mom_s:>7} {yoy_s:>7} {pick(core)} {pick(goods)} {pick(svc):>10}")
        lines.append("\nNote: PPI Final Demand measures prices received by domestic producers at first point of sale.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_jobs_report(months: int = 18) -> str:
    """Get US employment data: Nonfarm Payrolls (NFP), unemployment rate, wages, hours worked.

    Args:
        months: Number of months of history to show
    """
    try:
        today = _date.today()
        start_year = today.year - (months // 12 + 2)
        raw = _bls_fetch(
            ["CES0000000001", "LNS14000000", "CES0500000003", "CES0500000002", "LNS11300000"],
            start_year, today.year,
        )
        nfp = raw.get("CES0000000001", [])[:months]
        unemp = {f"{r['year']}-{r['period']}": r for r in raw.get("LNS14000000", [])}
        wages = {f"{r['year']}-{r['period']}": r for r in raw.get("CES0500000003", [])}
        hours = {f"{r['year']}-{r['period']}": r for r in raw.get("CES0500000002", [])}
        partic = {f"{r['year']}-{r['period']}": r for r in raw.get("LNS11300000", [])}
        header = f"{'Date':<12} {'NFP (k)':>9} {'MoM':>7} {'Unemp%':>8} {'Wages($/h)':>11} {'WoW%':>7} {'Hours':>7} {'Partic%':>8}"
        lines = ["US Jobs Report (BLS)", "=" * len(header), header, "-" * len(header)]
        for row in nfp:
            key = f"{row['year']}-{row['period']}"
            label = _period_label(row["year"], row["period"])
            val = float(row["value"])
            mom = row.get("calculations", {}).get("net_changes", {}).get("1", "")
            mom_s = f"{float(mom):>+6.0f}k" if mom else f"{'N/A':>7}"
            u = f"{float(unemp[key]['value']):>7.1f}%" if key in unemp else f"{'N/A':>8}"
            w = f"{float(wages[key]['value']):>10.2f}" if key in wages else f"{'N/A':>11}"
            wc = wages.get(key, {}).get("calculations", {}).get("pct_changes", {}).get("1", "")
            ws = f"{float(wc):>+6.2f}%" if wc else f"{'N/A':>7}"
            h = f"{float(hours[key]['value']):>7.1f}" if key in hours else f"{'N/A':>7}"
            p = f"{float(partic[key]['value']):>7.1f}%" if key in partic else f"{'N/A':>8}"
            lines.append(f"{label:<12} {val:>9,.0f} {mom_s:>7} {u:>8} {w:>11} {ws:>7} {h:>7} {p:>8}")
        lines.append("\nNote: NFP = net new jobs in thousands. Consensus forecasts usually ±100k.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_jolts(months: int = 18) -> str:
    """Get JOLTS data: job openings, hires, quits, layoffs. Leading indicator for labor market tightness.

    Args:
        months: Number of months of history
    """
    try:
        today = _date.today()
        start_year = today.year - (months // 12 + 2)
        raw = _bls_fetch(
            ["JTS000000000000000JOL", "JTS000000000000000HIL",
             "JTS000000000000000QUL", "JTS000000000000000LDL"],
            start_year, today.year,
        )
        openings = raw.get("JTS000000000000000JOL", [])[:months]
        hires = {f"{r['year']}-{r['period']}": r for r in raw.get("JTS000000000000000HIL", [])}
        quits = {f"{r['year']}-{r['period']}": r for r in raw.get("JTS000000000000000QUL", [])}
        layoffs = {f"{r['year']}-{r['period']}": r for r in raw.get("JTS000000000000000LDL", [])}
        header = f"{'Date':<12} {'Openings(k)':>12} {'Hires(k)':>10} {'Quits(k)':>10} {'Layoffs(k)':>12} {'O/H Ratio':>10}"
        lines = ["JOLTS — Job Openings and Labor Turnover", "=" * len(header), header, "-" * len(header)]
        for row in openings:
            key = f"{row['year']}-{row['period']}"
            label = _period_label(row["year"], row["period"])
            o = float(row["value"])
            h = float(hires[key]["value"]) if key in hires else 0
            q = float(quits[key]["value"]) if key in quits else 0
            l = float(layoffs[key]["value"]) if key in layoffs else 0
            ratio = o / h if h > 0 else 0
            lines.append(f"{label:<12} {o:>12,.0f} {h:>10,.0f} {q:>10,.0f} {l:>12,.0f} {ratio:>10.2f}")
        lines.append("\nNote: O/H Ratio > 1 = more openings than hires (tight labor market).")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_bls_series(series_id: str, months: int = 24) -> str:
    """Fetch any arbitrary BLS series by its series ID.

    Args:
        series_id: BLS series ID, e.g. 'CUUR0000SA0' for CPI. Find IDs at https://www.bls.gov/help/hlpforma.htm
        months: Number of months of history
    """
    try:
        today = _date.today()
        start_year = today.year - (months // 12 + 2)
        raw = _bls_fetch([series_id], start_year, today.year)
        rows = raw.get(series_id, [])[:months]
        if not rows:
            return f"No data found for series '{series_id}'"
        header = f"{'Date':<12} {'Value':>12} {'MoM Chg':>10} {'MoM%':>8} {'YoY%':>8}"
        lines = [f"BLS Series: {series_id}", "=" * len(header), header, "-" * len(header)]
        for row in rows:
            label = _period_label(row["year"], row["period"])
            val = row.get("value", "")
            calcs = row.get("calculations", {})
            pct = calcs.get("pct_changes", {})
            net = calcs.get("net_changes", {})
            mom_net = net.get("1", "")
            mom_pct = pct.get("1", "")
            yoy_pct = pct.get("12", "")
            net_s = f"{float(mom_net):>+9.3f}" if mom_net else f"{'N/A':>10}"
            mom_s = f"{float(mom_pct):>+7.2f}%" if mom_pct else f"{'N/A':>8}"
            yoy_s = f"{float(yoy_pct):>+7.2f}%" if yoy_pct else f"{'N/A':>8}"
            lines.append(f"{label:<12} {float(val):>12.3f} {net_s} {mom_s} {yoy_s}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def list_bls_series() -> str:
    """List all pre-configured BLS series IDs and their descriptions. Use get_bls_series() to fetch any."""
    lines = ["Pre-configured BLS Series", "=" * 60,
             f"{'Key':<26} {'Series ID':<26} {'Description'}"]
    categories = {
        "CPI (Inflation)": [k for k in BLS_SERIES_CATALOG if k.startswith("cpi")],
        "PPI (Producer Prices)": [k for k in BLS_SERIES_CATALOG if k.startswith("ppi")],
        "Employment": [k for k in BLS_SERIES_CATALOG if k.startswith("nfp") or k in ("unemployment", "u6", "participation")],
        "Wages & Hours": [k for k in BLS_SERIES_CATALOG if "wage" in k or "hour" in k],
        "JOLTS": [k for k in BLS_SERIES_CATALOG if k.startswith("jolts")],
    }
    for cat, keys in categories.items():
        lines.append(f"\n  {cat}")
        for k in keys:
            sid, desc = BLS_SERIES_CATALOG[k]
            lines.append(f"  {k:<26} {sid:<26} {desc}")
    lines.append("\nUse get_bls_series(series_id=...) to fetch any series directly.")
    return "\n".join(lines)


# ── US Treasury ───────────────────────────────────────────────────────────────

FISCAL_BASE = "https://api.fiscaldata.treasury.gov/services/api/v1"
TREASURY_NS = "http://www.w3.org/2005/Atom"
TREASURY_PROPS_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices"
TREASURY_META_NS  = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"

YIELD_CURVE_FIELDS = [
    ("BC_1MONTH", "1M"), ("BC_2MONTH", "2M"), ("BC_3MONTH", "3M"), ("BC_6MONTH", "6M"),
    ("BC_1YEAR",  "1Y"), ("BC_2YEAR",  "2Y"), ("BC_3YEAR",  "3Y"), ("BC_5YEAR",  "5Y"),
    ("BC_7YEAR",  "7Y"), ("BC_10YEAR", "10Y"), ("BC_20YEAR", "20Y"), ("BC_30YEAR", "30Y"),
]
REAL_YIELD_FIELDS = [
    ("TC_5YEAR", "5Y"), ("TC_7YEAR", "7Y"), ("TC_10YEAR", "10Y"),
    ("TC_20YEAR", "20Y"), ("TC_30YEAR", "30Y"),
]


def _fetch_yield_xml(data_type: str, year_month: str) -> list:
    url = (
        f"https://home.treasury.gov/resource-center/data-chart-center/"
        f"interest-rates/pages/xml?data={data_type}&field_tdr_date_value_month={year_month}"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    rows = []
    for entry in root.findall(f"{{{TREASURY_NS}}}entry"):
        content = entry.find(f"{{{TREASURY_NS}}}content")
        if content is None:
            continue
        props = content.find(f"{{{TREASURY_META_NS}}}properties")
        if props is None:
            continue
        row = {}
        for child in props:
            tag = child.tag.replace(f"{{{TREASURY_PROPS_NS}}}", "")
            row[tag] = child.text or ""
        rows.append(row)
    return rows


def _fiscal_get(endpoint: str, params: dict) -> dict:
    r = requests.get(f"{FISCAL_BASE}{endpoint}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def get_yield_curve(months: int = 1) -> str:
    """Get US Treasury nominal yield curve (1M to 30Y). Shows recent daily rates and key spreads.

    Args:
        months: How many months of data to fetch (1–6). 1 = current month only.
    """
    try:
        today = _date.today()
        all_rows = []
        for i in range(months):
            d = today.replace(day=1) - timedelta(days=i * 28)
            all_rows.extend(_fetch_yield_xml("daily_treasury_yield_curve", d.strftime("%Y%m")))
        all_rows.sort(key=lambda x: x.get("NEW_DATE", ""), reverse=True)
        seen, unique = set(), []
        for row in all_rows:
            d = row.get("NEW_DATE", "")[:10]
            if d not in seen:
                seen.add(d)
                unique.append(row)
        tenors = [t for _, t in YIELD_CURVE_FIELDS]
        header = f"{'Date':<12}" + "".join(f"{t:>7}" for t in tenors)
        lines = ["US Treasury Nominal Yield Curve (%)", "=" * len(header), header, "-" * len(header)]
        for row in unique[:30]:
            date_str = row.get("NEW_DATE", "")[:10]
            vals = []
            for field, _ in YIELD_CURVE_FIELDS:
                v = row.get(field, "")
                vals.append(f"{float(v):>7.2f}" if v else f"{'N/A':>7}")
            lines.append(f"{date_str:<12}" + "".join(vals))
        if unique:
            r0 = unique[0]
            y2  = float(r0.get("BC_2YEAR",  0) or 0)
            y10 = float(r0.get("BC_10YEAR", 0) or 0)
            y3m = float(r0.get("BC_3MONTH", 0) or 0)
            y30 = float(r0.get("BC_30YEAR", 0) or 0)
            lines += ["",
                f"Key Spreads (latest: {unique[0].get('NEW_DATE','')[:10]})",
                f"  2s10s spread:  {y10 - y2:+.2f}bps  ({'inverted' if y10 < y2 else 'normal'})",
                f"  3m10y spread:  {y10 - y3m:+.2f}bps  ({'inverted' if y10 < y3m else 'normal'})",
                f"  10s30s spread: {y30 - y10:+.2f}bps",
            ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_real_yield_curve(months: int = 1) -> str:
    """Get US Treasury real (inflation-adjusted) yield curve from TIPS. Negative = financial repression.

    Args:
        months: How many months of data to fetch (1–6)
    """
    try:
        today = _date.today()
        all_rows = []
        for i in range(months):
            d = today.replace(day=1) - timedelta(days=i * 28)
            all_rows.extend(_fetch_yield_xml("daily_treasury_real_yield_curve", d.strftime("%Y%m")))
        all_rows.sort(key=lambda x: x.get("NEW_DATE", ""), reverse=True)
        seen, unique = set(), []
        for row in all_rows:
            d = row.get("NEW_DATE", "")[:10]
            if d not in seen:
                seen.add(d)
                unique.append(row)
        tenors = [t for _, t in REAL_YIELD_FIELDS]
        header = f"{'Date':<12}" + "".join(f"{t:>8}" for t in tenors)
        lines = ["US Treasury Real Yield Curve / TIPS (%)", "=" * len(header), header, "-" * len(header)]
        for row in unique[:20]:
            date_str = row.get("NEW_DATE", "")[:10]
            vals = []
            for field, _ in REAL_YIELD_FIELDS:
                v = row.get(field, "")
                vals.append(f"{float(v):>+8.2f}" if v else f"{'N/A':>8}")
            lines.append(f"{date_str:<12}" + "".join(vals))
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_breakeven_inflation(months: int = 1) -> str:
    """Calculate breakeven inflation rates (nominal yield minus real yield). Market's inflation expectation.

    Args:
        months: How many months of history to show
    """
    try:
        today = _date.today()
        nom_rows: dict = {}
        real_rows: dict = {}
        for i in range(max(months, 1)):
            d = today.replace(day=1) - timedelta(days=i * 28)
            ym = d.strftime("%Y%m")
            for row in _fetch_yield_xml("daily_treasury_yield_curve", ym):
                nom_rows[row.get("NEW_DATE", "")[:10]] = row
            for row in _fetch_yield_xml("daily_treasury_real_yield_curve", ym):
                real_rows[row.get("NEW_DATE", "")[:10]] = row
        common_dates = sorted(set(nom_rows) & set(real_rows), reverse=True)[:30]
        lines = ["US Treasury Breakeven Inflation Rates (%)", "=" * 60,
                 f"{'Date':<12} {'5Y BE':>8} {'10Y BE':>8} {'20Y BE':>8} {'30Y BE':>8}"]
        for date in common_dates:
            n = nom_rows[date]
            rv = real_rows[date]
            def be(nf, rf, _n=n, _r=rv):
                nv = _n.get(nf, "")
                rv2 = _r.get(rf, "")
                return f"{float(nv) - float(rv2):>+8.2f}" if nv and rv2 else f"{'N/A':>8}"
            lines.append(f"{date:<12}{be('BC_5YEAR','TC_5YEAR')}{be('BC_10YEAR','TC_10YEAR')}{be('BC_20YEAR','TC_20YEAR')}{be('BC_30YEAR','TC_30YEAR')}")
        lines.append("\nNote: Breakeven = nominal yield − real yield = market's expected inflation over that horizon")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_tga_balance(days: int = 30) -> str:
    """Get US Treasury General Account (TGA) daily cash balance. TGA decrease injects liquidity into banking system.

    Args:
        days: Number of recent days to show (max 365)
    """
    try:
        end = _date.today()
        start = end - timedelta(days=days)
        data = _fiscal_get("/accounting/dts/operating_cash_balance", {
            "fields": "record_date,open_today_bal,close_today_bal,account_type",
            "filter": f"record_date:gte:{start},record_date:lte:{end},account_type:eq:Treasury General Account (TGA) Closing Balance",
            "sort": "-record_date",
            "page[size]": min(days, 365),
        })
        rows = data.get("data", [])
        if not rows:
            data = _fiscal_get("/accounting/dts/operating_cash_balance", {
                "fields": "record_date,open_today_bal,close_today_bal,account_type",
                "filter": f"record_date:gte:{start},record_date:lte:{end}",
                "sort": "-record_date",
                "page[size]": 200,
            })
            rows = [r for r in data.get("data", []) if "TGA" in r.get("account_type", "")]
        if not rows:
            return "No TGA balance data found for the requested period."
        lines = ["US Treasury General Account (TGA) Balance", "=" * 55,
                 f"{'Date':<14} {'Open ($B)':>12} {'Close ($B)':>12} {'Change ($B)':>13}"]
        for row in rows:
            date = row.get("record_date", "")[:10]
            open_ = row.get("open_today_bal", "")
            close = row.get("close_today_bal", "")
            try:
                o = float(open_) / 1e3
                c = float(close) / 1e3
                lines.append(f"{date:<14} {o:>12,.1f} {c:>12,.1f} {c - o:>+12,.1f}")
            except Exception:
                lines.append(f"{date:<14} {open_:>12} {close:>12}")
        lines.append("\nNote: TGA decrease injects liquidity into banking system (bullish risk assets)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_treasury_auctions(days: int = 30) -> str:
    """Get recent US Treasury debt auction results: bills, notes, bonds, TIPS.

    Args:
        days: Look back this many days for auction results
    """
    try:
        end = _date.today()
        start = end - timedelta(days=days)
        data = _fiscal_get("/accounting/od/upcoming_auctions", {
            "fields": "security_type,security_term,offering_amt,auction_date,issue_date,maturity_date",
            "filter": f"auction_date:gte:{start},auction_date:lte:{end}",
            "sort": "-auction_date",
            "page[size]": 50,
        })
        rows = data.get("data", [])
        lines = [f"US Treasury Auctions (last {days} days)", "=" * 70,
                 f"{'Auction Date':<14} {'Type':<8} {'Term':<12} {'Offering ($B)':>14} {'Issue Date':<14} {'Maturity':<12}"]
        for row in rows:
            amt = row.get("offering_amt", "")
            try:
                amt_fmt = f"${float(amt) / 1e3:>12,.1f}B"
            except Exception:
                amt_fmt = f"{amt:>13}"
            lines.append(
                f"{row.get('auction_date','')[:10]:<14} "
                f"{row.get('security_type','')[:7]:<8} "
                f"{row.get('security_term',''):<12} "
                f"{amt_fmt:>14} "
                f"{row.get('issue_date','')[:10]:<14} "
                f"{row.get('maturity_date','')[:10]:<12}"
            )
        if not rows:
            lines.append(f"No auction data found for last {days} days.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_fed_balance_sheet(months: int = 6) -> str:
    """Get Federal Reserve balance sheet size (WALCL via FRED public CSV) — tracks QE/QT progress.

    Args:
        months: Number of months of weekly data to show
    """
    try:
        limit = months * 5
        r = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": "WALCL"},
            timeout=20,
        )
        r.raise_for_status()
        lines_raw = r.text.strip().split("\n")
        data_rows = [ln.split(",") for ln in lines_raw[1:] if ln]
        data_rows.sort(key=lambda x: x[0], reverse=True)
        recent = data_rows[:limit]
        lines = ["Federal Reserve Balance Sheet (WALCL)", "=" * 45,
                 f"{'Date':<14} {'Total Assets ($B)':>20} {'WoW Chg ($B)':>14}"]
        for i, (date, val) in enumerate(recent):
            try:
                v = float(val) / 1e3
                chg_str = f"{v - float(recent[i + 1][1]) / 1e3:>+13,.1f}" if i + 1 < len(recent) else f"{'':>14}"
                lines.append(f"{date:<14} {v:>20,.1f} {chg_str}")
            except Exception:
                lines.append(f"{date:<14} {val:>20}")
        lines.append("\nNote: Rising = QE (expansionary), Falling = QT (tightening)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ── SEC EDGAR Extended ────────────────────────────────────────────────────────

def _get_cik(ticker: str) -> str:
    """Resolve ticker to zero-padded 10-digit CIK via company_tickers.json."""
    r = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=EDGAR_HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    ticker_upper = ticker.upper()
    for item in r.json().values():
        if item["ticker"] == ticker_upper:
            return str(item["cik_str"]).zfill(10)
    raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR")


@mcp.tool()
def search_filings(query: str, form_type: str = "", date_range: str = "", limit: int = 10) -> str:
    """Full-text search across all SEC EDGAR filings.

    Args:
        query: Search keywords or company name
        form_type: Filter by form type, e.g. '10-K', '10-Q', '8-K', 'S-1', '13F-HR', 'DEF 14A'
        date_range: Date range as 'YYYY-MM-DD,YYYY-MM-DD' (startDate,endDate). Leave empty for all time.
        limit: Number of results to return (max 40)
    """
    try:
        params = {"q": f'"{query}"'}
        if form_type:
            params["forms"] = form_type
        if date_range and "," in date_range:
            parts = [p.strip() for p in date_range.split(",")]
            params["dateRange"] = "custom"
            params["startdt"] = parts[0]
            params["enddt"] = parts[1]
        r = requests.get(
            f"{EDGAR_EFTS}/LATEST/search-index",
            headers=EDGAR_HEADERS,
            params=params,
            timeout=20,
        )
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])[:limit]
        if not hits:
            return f"No filings found for query: '{query}'"
        lines = [f"SEC EDGAR Search: '{query}'" + (f" [{form_type}]" if form_type else ""), "=" * 60]
        for h in hits:
            s = h.get("_source", {})
            names = s.get("display_names", [])
            name = names[0].split("(")[0].strip() if names else ""
            lines.append(
                f"{s.get('file_date',''):<12} {s.get('form',''):<10} "
                f"{name:<35} acc:{s.get('adsh','').replace('-','')}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_company_facts(ticker: str, concept: str = "Revenues") -> str:
    """Get standardized financial facts for a company from XBRL data (SEC EDGAR).

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        concept: XBRL concept name. Common values:
            'Revenues', 'NetIncomeLoss', 'Assets', 'Liabilities',
            'StockholdersEquity', 'OperatingIncomeLoss',
            'EarningsPerShareBasic', 'CommonStockSharesOutstanding',
            'CashAndCashEquivalentsAtCarryingValue', 'LongTermDebt'
    """
    try:
        cik = _get_cik(ticker)
        r = requests.get(
            f"{EDGAR_BASE}/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json",
            headers=EDGAR_HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        label = data.get("label", concept)
        description = data.get("description", "")
        units = data.get("units", {})
        unit_key = "USD" if "USD" in units else (list(units.keys())[0] if units else None)
        if not unit_key:
            return f"No data found for concept '{concept}' at {ticker.upper()}"
        entries = units[unit_key]
        annual = [e for e in entries if e.get("form") in ("10-K", "20-F")]
        annual.sort(key=lambda x: x.get("end", ""), reverse=True)
        lines = [
            f"{ticker.upper()} — {label}",
            f"{description[:100] + '...' if len(description) > 100 else description}",
            "=" * 60,
            f"{'Period End':<14} {'Form':<8} {'Value (' + unit_key + ')':<25} {'Filed':<12}",
            "-" * 60,
        ]
        for e in annual[:10]:
            val = e.get("val", 0)
            val_fmt = f"{val/1e9:.2f}B" if abs(val) >= 1e9 else (f"{val/1e6:.1f}M" if abs(val) >= 1e6 else str(val))
            lines.append(f"{e.get('end',''):<14} {e.get('form',''):<8} {val_fmt:<25} {e.get('filed',''):<12}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_insider_transactions(ticker: str, limit: int = 20) -> str:
    """Get recent insider transactions (Form 4 filings) for a company.

    Args:
        ticker: Stock ticker symbol
        limit: Number of Form 4 entries to return
    """
    try:
        cik = _get_cik(ticker)
        r = requests.get(
            f"{EDGAR_BASE}/submissions/CIK{cik}.json",
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        company_name = data.get("name", ticker.upper())
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        acc = recent.get("accessionNumber", [])
        reporters = recent.get("primaryDocument", [])
        lines = [f"{company_name} — Insider Transactions (Form 4)", "=" * 60,
                 f"{'Filed':<12} {'Accession':<22} {'Document'}"]
        count = 0
        for f, d, a, rep in zip(forms, dates, acc, reporters if reporters else [""] * len(forms)):
            if f != "4":
                continue
            lines.append(f"{d:<12} {a:<22} {rep}")
            count += 1
            if count >= limit:
                break
        if count == 0:
            lines.append("No Form 4 filings found recently.")
        lines.append(f"\nView on EDGAR: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(cik)}&type=4&dateb=&owner=include&count=40")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_company_info(ticker: str) -> str:
    """Get basic company information from SEC EDGAR: CIK, SIC, fiscal year end, exchanges, addresses.

    Args:
        ticker: Stock ticker symbol
    """
    try:
        cik = _get_cik(ticker)
        r = requests.get(
            f"{EDGAR_BASE}/submissions/CIK{cik}.json",
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        name = data.get("name", "")
        sic = data.get("sic", "")
        sic_desc = data.get("sicDescription", "")
        fy_end = data.get("fiscalYearEnd", "")
        state = data.get("stateOfIncorporation", "")
        exchanges = data.get("exchanges", [])
        tickers = data.get("tickers", [])
        phone = data.get("phone", "")
        ba = data.get("addresses", {}).get("business", {})
        address = f"{ba.get('street1','')} {ba.get('city','')} {ba.get('stateOrCountry','')} {ba.get('zipCode','')}".strip()
        lines = [
            f"{'Company:':<20} {name}",
            f"{'CIK:':<20} {int(cik)}",
            f"{'Tickers:':<20} {', '.join(tickers)}",
            f"{'Exchanges:':<20} {', '.join(exchanges)}",
            f"{'SIC:':<20} {sic} — {sic_desc}",
            f"{'Fiscal Year End:':<20} {fy_end}",
            f"{'State of Inc.:':<20} {state}",
            f"{'Phone:':<20} {phone}",
            f"{'Address:':<20} {address}",
            f"\nEDGAR: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(cik)}&type=&dateb=&owner=include&count=40",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
