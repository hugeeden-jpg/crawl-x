---
name: macro-mcp
description: >
  Access macroeconomic data and government filings. Use for Fed Funds Rate, CPI,
  GDP, unemployment, M2, treasury yields, EUR/USD, and any FRED economic series.
  Also provides SEC EDGAR company search, filing retrieval, and 13F holdings.
---

# Macro Data MCP

Federal Reserve economic data (FRED) + SEC EDGAR filings.

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

Get a free FRED API key at: https://fredaccount.stlouisfed.org/

Claude Desktop config:
```json
{
  "macro-data": {
    "command": "uv",
    "args": ["run", "/Users/eden/crawl-x/macro-mcp/server.py"],
    "env": {"FRED_API_KEY": "your_key_here"}
  }
}
```

## Tools

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(fred_api_key)` | — | Save FRED API key |
| `get_key_indicators()` | Yes | Fed Funds, CPI, GDP, Unemployment, M2, 10Y, EUR/USD |
| `search_fred_series(keywords, limit)` | Yes | Find FRED series by keyword |
| `get_fred_data(series_id, start_date, end_date)` | Yes | Get time series data |
| `search_edgar_company(company_name)` | No | Find company CIK + ticker |
| `get_recent_filings(ticker_or_cik, form_type, limit)` | No | List recent SEC filings |
| `get_13f_holdings(cik, period)` | No | Fund holdings from 13F |
| `get_filing_text(accession_number, section)` | No | Get filing text content |

## Key FRED Series IDs

| Series ID | Description |
|-----------|-------------|
| DFF | Federal Funds Rate (Daily) |
| CPIAUCSL | CPI (All Urban, Seasonally Adjusted) |
| GDP | Gross Domestic Product |
| UNRATE | Unemployment Rate |
| M2SL | M2 Money Supply |
| DGS10 | 10-Year Treasury Yield |
| DGS2 | 2-Year Treasury Yield |
| DEXUSEU | EUR/USD Exchange Rate |
| T10Y2Y | 10Y-2Y Yield Spread (Recession Indicator) |
| BAMLH0A0HYM2 | High Yield Spread |

## Usage Patterns

**Morning macro brief:**
```
get_key_indicators() → get_fred_data("DFF") → get_fred_data("T10Y2Y")
```

**Institutional research:**
```
search_edgar_company("Berkshire Hathaway")
→ get_recent_filings("0001067983", "13F-HR")
→ get_13f_holdings("0001067983")
```

## Notes
- FRED updates: varies by series (daily/weekly/monthly/quarterly)
- SEC EDGAR: no rate limits but requires User-Agent header (auto-set)
- 13F filings are due 45 days after quarter end
