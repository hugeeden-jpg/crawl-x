#!/usr/bin/env python3
"""
Final validation for the three fixed fiscaldata tools.
Run with: uv run tests/test_fiscaldata.py
"""
# /// script
# dependencies = ["requests>=2.31.0"]
# ///

import re
import requests

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
TIMEOUT = 15


def get(path, params=None):
    return requests.get(BASE + path, params=params or {}, timeout=TIMEOUT)


def print_section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")


# ── 1. get_treasury_auctions ─────────────────────────────────────────────
print_section("get_treasury_auctions — high_yield + total_accepted + auction_date")
r = get("/v1/accounting/od/auctions_query", {
    "fields": "auction_date,security_type,security_term,offering_amt,total_accepted,total_tendered,bid_to_cover_ratio,high_yield,int_rate",
    "filter": "auction_date:gte:2026-02-01,auction_date:lte:2026-03-25",  # exclude today (no results yet)
    "sort": "-auction_date",
    "page[size]": 5,
})
if r.status_code == 200:
    rows = r.json().get("data", [])
    print(f"  ✅ {r.status_code}  rows={len(rows)}")
    print(f"  {'Auction':<12} {'Type':<6} {'Term':<22} {'Offer($B)':>10} {'Accept($B)':>11} {'B/C':>6} {'HiYld%':>8} {'Coupon%':>8}")
    for row in rows[:5]:
        offer  = f"{float(row['offering_amt'] or 0)/1e9:>10,.1f}" if row.get('offering_amt') not in (None,'null') else f"{'N/A':>10}"
        accept = f"{float(row['total_accepted'] or 0)/1e9:>11,.1f}" if row.get('total_accepted') not in (None,'null') else f"{'N/A':>11}"
        print(f"  {row.get('auction_date','')[:10]:<12} {row.get('security_type',''):<6} {row.get('security_term',''):<22} "
              f"{offer} {accept} {row.get('bid_to_cover_ratio',''):>6} {row.get('high_yield',''):>8} {row.get('int_rate',''):>8}")
else:
    print(f"  ❌ {r.status_code} {r.text[:300]}")


# ── 2. get_tga_balance (DTS daily) ───────────────────────────────────────
print_section("get_tga_balance — DTS open_today_bal (daily, $M → $B)")
r = get("/v1/accounting/dts/operating_cash_balance", {
    "fields": "record_date,open_today_bal",
    "filter": "record_date:gte:2026-03-01,account_type:eq:Treasury General Account (TGA) Closing Balance",
    "sort": "-record_date",
    "page[size]": 10,
})
if r.status_code == 200:
    rows = r.json().get("data", [])
    print(f"  ✅ {r.status_code}  rows={len(rows)}")
    print(f"  {'Date':<14} {'Balance($B)':>12} {'DoD($B)':>10}")
    for i, row in enumerate(rows):
        v = float(row['open_today_bal']) / 1e3
        if i + 1 < len(rows):
            chg = v - float(rows[i+1]['open_today_bal']) / 1e3
            chg_s = f"{chg:>+9.1f}"
        else:
            chg_s = ""
        print(f"  {row['record_date']:<14} {v:>12,.1f} {chg_s}")
else:
    print(f"  ❌ {r.status_code} {r.text[:300]}")


# ── 3. get_federal_budget ────────────────────────────────────────────────
print_section("get_federal_budget — latest publication, FY structure")

# Step 1: get latest record_date
r1 = get("/v1/accounting/mts/mts_table_1", {"fields": "record_date", "sort": "-record_date", "page[size]": 1})
latest_date = r1.json()["data"][0]["record_date"] if r1.status_code == 200 else None
print(f"  Latest publication: {latest_date}")

# Step 2: fetch all rows for that date
r2 = get("/v1/accounting/mts/mts_table_1", {
    "fields": "line_code_nbr,classification_desc,current_month_gross_rcpt_amt,current_month_gross_outly_amt",
    "filter": f"record_date:eq:{latest_date}",
    "sort": "line_code_nbr",
    "page[size]": 200,
})
if r2.status_code == 200:
    rows = r2.json().get("data", [])
    _month_num = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,
                  "July":7,"August":8,"September":9,"October":10,"November":11,"December":12}
    current_fy = None
    monthly_data = []
    rows.sort(key=lambda r: int(r.get("line_code_nbr", 0)))
    for row in rows:
        desc  = row.get("classification_desc","").strip()
        rcpt  = row.get("current_month_gross_rcpt_amt")
        outly = row.get("current_month_gross_outly_amt")
        fy_m = re.match(r"FY (\d{4})", desc)
        if fy_m:
            current_fy = int(fy_m.group(1))
            continue
        if desc == "Year-to-Date" or not rcpt or rcpt == "null":
            continue
        if desc in _month_num and current_fy:
            cal_month = _month_num[desc]
            cal_year  = current_fy - 1 if cal_month >= 10 else current_fy
            ym = f"{cal_year:04d}-{cal_month:02d}"
            monthly_data.append((ym, float(rcpt)/1e9, float(outly)/1e9))
    monthly_data.sort(key=lambda x: x[0], reverse=True)
    print(f"  ✅ {r2.status_code}  {len(monthly_data)} monthly data points")
    print(f"  {'Month':<10} {'Receipts($B)':>13} {'Outlays($B)':>13} {'Deficit($B)':>13}")
    for ym, r_v, o_v in monthly_data[:12]:
        print(f"  {ym:<10} {r_v:>13,.1f} {o_v:>13,.1f} {o_v-r_v:>+13,.1f}")
else:
    print(f"  ❌ {r2.status_code} {r2.text[:300]}")
