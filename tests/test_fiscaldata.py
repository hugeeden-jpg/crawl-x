#!/usr/bin/env python3
"""
Quick connectivity test for fiscaldata.treasury.gov endpoints.
Run with: uv run tests/test_fiscaldata.py
"""
# /// script
# dependencies = ["requests>=2.31.0"]
# ///

import requests
import sys

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
TIMEOUT = 15


def get(path, params=None):
    return requests.get(BASE + path, params=params or {}, timeout=TIMEOUT)


def print_result(name, r):
    print(f"\n{'='*65}")
    print(f"  {name}")
    if r.status_code == 200:
        data = r.json()
        rows = data.get("data", [])
        total = data.get("meta", {}).get("total-count", "?")
        print(f"  ✅ {r.status_code}  rows={len(rows)}  total={total}")
        if rows:
            print(f"  fields: {list(rows[0].keys())}")
            for row in rows[:2]:
                print(f"  {row}")
    else:
        print(f"  ❌ {r.status_code}  {r.text[:300]}")


# ── 1. Auctions (v1, record_date) ───────────────────────────────────────────
print_result(
    "auctions_query /v1 — record_date filter, correct fields",
    get("/v1/accounting/od/auctions_query", {
        "fields": "record_date,security_type,security_term,offering_amt,bid_to_cover_ratio,accepted_comp_bid_rate_amt,total_accepted_amt,indirect_bid_pct_accepted",
        "filter": "record_date:gte:2026-02-01,record_date:lte:2026-03-26",
        "sort": "-record_date",
        "page[size]": 5,
    }),
)

# ── 2. Upcoming auctions (v1) ────────────────────────────────────────────────
print_result(
    "upcoming_auctions /v1",
    get("/v1/accounting/od/upcoming_auctions", {"sort": "auction_date", "page[size]": 3}),
)

# ── 3. National debt ─────────────────────────────────────────────────────────
print_result(
    "debt_to_penny /v2",
    get("/v2/accounting/od/debt_to_penny", {
        "fields": "record_date,tot_pub_debt_out_amt",
        "sort": "-record_date",
        "page[size]": 3,
    }),
)

# ── 4. Federal budget — mts_table_1, correct fields ─────────────────────────
print_result(
    "mts_table_1 /v1 — correct fields",
    get("/v1/accounting/mts/mts_table_1", {
        "fields": "record_date,line_code_nbr,classification_desc,current_month_gross_rcpt_amt,current_month_gross_outly_amt",
        "filter": "line_code_nbr:in:(10,20,30,80)",
        "sort": "-record_date",
        "page[size]": 8,
    }),
)

# ── 5. TGA via DTS (daily, restored) ────────────────────────────────────────
print_result(
    "TGA via DTS /v1 (daily)",
    get("/v1/accounting/dts/operating_cash_balance", {
        "fields": "record_date,account_type,close_today_bal,open_today_bal",
        "filter": "record_date:gte:2026-03-01",
        "sort": "-record_date",
        "page[size]": 5,
    }),
)

# ── 6. Avg interest rates ────────────────────────────────────────────────────
print_result(
    "avg_interest_rates /v2",
    get("/v2/accounting/od/avg_interest_rates", {
        "fields": "record_date,security_type_desc,avg_interest_rate_amt",
        "sort": "-record_date",
        "page[size]": 5,
    }),
)
