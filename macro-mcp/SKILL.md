---
name: macro-mcp
description: >
  Access macroeconomic data and government filings. Use for Fed Funds Rate, CPI,
  GDP, unemployment, M2, treasury yields, EUR/USD, and any FRED economic series.
  Also provides BLS labor data (CPI/PPI/NFP/JOLTS), US Treasury yield curve,
  TGA balance, auction results, national debt, federal budget, Fed balance sheet,
  and extended SEC EDGAR tools (full-text search, XBRL facts, insider Form 4, company info).
---

# Macro Data MCP

FRED + BLS + US Treasury + SEC EDGAR — one server for all macro and government data.

## Setup

Dependencies are declared inline (PEP 723) — `uv run` installs them automatically on first use.

- FRED API key (required for FRED tools): https://fredaccount.stlouisfed.org/
- BLS API key (optional, increases rate limits): https://www.bls.gov/developers/

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

### FRED

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure(fred_api_key)` | — | Save FRED API key |
| `get_key_indicators()` | Yes | Fed Funds, CPI, GDP, Unemployment, M2, 10Y, EUR/USD |
| `search_fred_series(keywords, limit)` | Yes | Find FRED series by keyword |
| `get_fred_data(series_id, start_date, end_date)` | Yes | Get time series data |

### BLS (Bureau of Labor Statistics)

| Tool | Key Required | Description |
|------|-------------|-------------|
| `configure_bls(bls_api_key)` | — | Save BLS API key (optional) |
| `get_cpi(months, breakdown)` | No* | CPI headline + core; breakdown adds Food/Energy/Shelter/Medical |
| `get_ppi(months)` | No* | PPI Final Demand + core + goods + services |
| `get_jobs_report(months)` | No* | NFP, unemployment rate, wages, hours, participation |
| `get_jolts(months)` | No* | Job openings, hires, quits, layoffs, O/H ratio |
| `get_bls_series(series_id, months)` | No* | Fetch any BLS series by ID |
| `list_bls_series()` | No | List all pre-configured series IDs |

*No key works (lower rate limit). Key unlocks higher limits.

### US Treasury

| Tool | Key Required | Description |
|------|-------------|-------------|
| `get_yield_curve(months)` | No | Full nominal yield curve 1M–30Y + key spreads (2s10s, 3m10y) |
| `get_real_yield_curve(months)` | No | TIPS real yield curve 5Y–30Y |
| `get_breakeven_inflation(months)` | No | Breakeven inflation = nominal − real |
| `get_tga_balance(days)` | No | Treasury General Account weekly balance (FRED WTREGEN) |
| `get_treasury_auctions(days, security_type)` | No | Auction results: bid-to-cover, high yield, allotted amt |
| `get_national_debt(days)` | No | Daily total public debt outstanding |
| `get_federal_budget(months)` | No | Monthly receipts, outlays, surplus/deficit (MTS) |
| `get_fed_balance_sheet(months)` | No | Fed total assets (WALCL) — QE/QT tracker |

### SEC EDGAR (Basic)

| Tool | Key Required | Description |
|------|-------------|-------------|
| `search_edgar_company(company_name)` | No | Find company CIK + ticker |
| `get_recent_filings(ticker_or_cik, form_type, limit)` | No | List recent SEC filings |
| `get_13f_holdings(cik, period)` | No | Fund holdings from 13F |
| `get_filing_text(accession_number, section)` | No | Get filing text content |

### SEC EDGAR (Extended)

| Tool | Key Required | Description |
|------|-------------|-------------|
| `search_filings(query, form_type, date_range, limit)` | No | Full-text search across all EDGAR filings |
| `get_company_facts(ticker, concept)` | No | XBRL financial facts (Revenues, Assets, NetIncomeLoss…) |
| `get_insider_transactions(ticker, limit)` | No | Form 4 insider buy/sell filings |
| `get_company_info(ticker)` | No | CIK, SIC, exchanges, fiscal year, address |

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
get_key_indicators() → get_yield_curve() → get_breakeven_inflation()
```

**Inflation deep dive:**
```
get_cpi(months=24, breakdown=True) → get_ppi(months=18) → get_fed_balance_sheet(months=12)
```

**Labor market:**
```
get_jobs_report(months=18) → get_jolts(months=18)
```

**Liquidity monitoring:**
```
get_tga_balance(days=60) → get_fed_balance_sheet(months=6)
```

**Institutional research:**
```
search_edgar_company("Berkshire Hathaway")
→ get_recent_filings("0001067983", "13F-HR")
→ get_13f_holdings("0001067983")
```

**Company fundamentals:**
```
get_company_info("NVDA") → get_company_facts("NVDA", "Revenues") → get_insider_transactions("NVDA")
```

## Notes
- FRED updates: varies by series (daily/weekly/monthly/quarterly)
- BLS: monthly releases; CPI ~mid-month, NFP first Friday of month, JOLTS ~5 weeks after month-end
- Treasury yield data: direct from treasury.gov XML feed (no key, usually same-day)
- SEC EDGAR: no rate limits but requires User-Agent header (auto-set)
- 13F filings are due 45 days after quarter end
