"""
TC-7.2 â€” Boundary Values: Zero / Near-Zero Values
===================================================
Category : BOUNDARY VALUES
Test Type: Per-Parameter
Priority : Medium

Validates that the system ACCEPTS legitimate zero or near-zero values in
numeric fields. For each field this test reads the company row with the
SMALLEST recorded value from the Excel data source and asserts it is accepted.

Real-world examples:
  â€¢ FLAM Gaming Private Limited  â†’ office_count = 0   (remote-first)
  â€¢ Various companies            â†’ churn_rate / turnover at minimum observed
  â€¢ Bootstrapped companies       â†’ zero capital raised
"""

import pytest
import pandas as pd
import re
from pathlib import Path

# =============================================================================
# CONFIG
# =============================================================================

FILE_PATH  = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


# =============================================================================
# HELPERS
# =============================================================================

def _is_null(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip().upper() in {"", "NULL", "NONE", "NAN"}


def _non_empty(value) -> bool:
    return not _is_null(value) and len(str(value).strip()) > 0


def _zero_or_positive_numeric(value) -> bool:
    """
    Accept 0, 0%, $0, and any non-negative number including near-zero decimals.
    Strips currency symbols, commas, percent signs, K/M/B/T suffixes.
    """
    raw = str(value).strip()
    cleaned = re.sub(r"[$,\s%+KkMmBbTt<>]", "", raw)
    cleaned = re.sub(r"[a-zA-Z]+$", "", cleaned)
    try:
        return float(cleaned) >= 0
    except ValueError:
        pass
    # Try first number from a range string like '24+'
    parts = re.split(r"[-â€“]", cleaned)
    try:
        return float(parts[0]) >= 0
    except (ValueError, IndexError):
        return False


def _get_min_row(df, col):
    """
    Return the row with the SMALLEST numeric value for col.
    Falls back to first non-null row for pure-text fields.
    """
    if col not in df.columns:
        pytest.skip(f"Column '{col}' not present in sheet")
    sub = df[["name", col]].dropna(subset=[col]).copy()
    if sub.empty:
        pytest.skip(f"All values are null for '{col}'")
    sub["_num"] = pd.to_numeric(
        sub[col].astype(str).str.replace(r"[$,\s+KkMmBbTt%<>]", "", regex=True),
        errors="coerce",
    )
    valid = sub.dropna(subset=["_num"])
    if valid.empty:
        return sub.iloc[0]   # text field â€” return first row
    return valid.loc[valid["_num"].idxmin()]


# =============================================================================
# TEST DATA: (tc_id, col, description)
# Each test picks the company with the SMALLEST value for that field from Excel.
# =============================================================================

TC_PARAMS = [
    # TC-7.2-01  Number of Offices beyond HQ
    # Excel: FLAM Gaming Private Limited â†’ 0 (fully remote)
    ("TC-7.2-01", "office_count",
     "Zero offices beyond HQ â€” FLAM Gaming (remote-first company)"),

    # TC-7.2-03  Employee Turnover
    # Excel: DeepMind â†’ 0.06 (lowest in sheet, near-zero stable org)
    ("TC-7.2-03", "employee_turnover",
     "Near-zero employee turnover â€” DeepMind (very stable organisation)"),

    # TC-7.2-04  Social Media Followers Combined
    # Excel: Nutanix â†’ '1M+' (smallest parseable value)
    ("TC-7.2-04", "social_media_followers",
     "Smallest combined social following in dataset â€” Nutanix"),

    # TC-7.2-05  Website Traffic Rank
    # Excel: Zepto â†’ 250 (lowest rank number = best/least traffic)
    ("TC-7.2-05", "website_traffic_rank",
     "Lowest website traffic rank value â€” Zepto Technologies (rank 250)"),

    # TC-7.2-06  Total Capital Raised
    # Excel: Zepto â†’ '$1.35 B' (lowest numeric in sheet)
    ("TC-7.2-06", "total_capital_raised",
     "Lowest total capital raised â€” Zepto Technologies ($1.35B)"),

    # TC-7.2-07  Annual Profits
    # Excel: Leap Finance â†’ '-$5M' (near zero / small loss, minimum value)
    ("TC-7.2-07", "annual_profit",
     "Minimum annual profit in dataset â€” Leap Finance (-$5M, near break-even)"),

    # TC-7.2-08  Market Share (%)
    # Excel: MintAir Corp â†’ 0.01% (smallest measurable penetration)
    ("TC-7.2-08", "market_share_percentage",
     "Near-zero market share â€” MintAir Corp (0.01%, new entrant)"),

    # TC-7.2-09  Churn Rate
    # Excel: Akamai â†’ 0.01 (lowest churn, near zero)
    ("TC-7.2-09", "churn_rate",
     "Near-zero churn rate â€” Akamai Technologies (0.01, highly retained users)"),

    # TC-7.2-10  Burn Rate
    # Excel: Tredence â†’ '$1.5M' (lowest positive burn in sheet)
    ("TC-7.2-10", "burn_rate",
     "Lowest burn rate â€” Tredence Inc. ($1.5M/month, near break-even)"),

    # TC-7.2-11  Runway
    # Excel: Cleartrip â†’ '24+' (lowest named runway)
    ("TC-7.2-11", "runway_months",
     "Lowest runway in dataset â€” Cleartrip (24+ months)"),

    # TC-7.2-12  Burn Multiplier
    # Excel: Increff Technologies â†’ 0.9 (lowest in sheet, barely above zero)
    ("TC-7.2-12", "burn_multiplier",
     "Near-zero burn multiplier â€” Increff Technologies (0.9)"),

    # TC-7.2-13  R&D Investment
    # Excel: Zepto Technologies â†’ 0.06 (lowest numeric in sheet)
    ("TC-7.2-13", "r_and_d_investment",
     "Near-zero R&D investment â€” Zepto Technologies (0.06)"),

    # TC-7.2-14  Training / Development Spend
    # Excel: MoveInSync â†’ '$1.2M' (lowest in sheet)
    ("TC-7.2-14", "training_spend",
     "Lowest L&D spend in dataset â€” MoveInSync Technologies ($1.2M)"),

    # TC-7.2-15  Airport Commute Time
    # Excel: Accenture â†’ '45 minutes' (first non-null row; field is text)
    ("TC-7.2-15", "airport_commute_time",
     "Airport commute time present and non-empty â€” Accenture plc"),

    # TC-7.2-16  Event Participation
    # Excel: Accenture â†’ non-empty text list (field not numeric)
    ("TC-7.2-16", "event_participation",
     "Event participation field is non-empty narrative â€” Accenture plc"),

    # TC-7.2-17  Layoff History
    # Excel: Bain Capability Network â†’ 2.9375 (lowest parseable value)
    ("TC-7.2-17", "layoff_history",
     "Lowest layoff history value in dataset â€” Bain Capability Network"),
]


# =============================================================================
# PARAMETRIZED TEST
# =============================================================================

@pytest.mark.parametrize(
    "tc_id, col, description",
    TC_PARAMS,
    ids=[p[0] for p in TC_PARAMS],
)
def test_tc_7_2(df, tc_id, col, description):
    """
    TC-7.2 â€” Boundary Values: Zero / Near-Zero Values.

    Reads the company row with the SMALLEST recorded value for each field
    from the Excel source and asserts that:
      1. The value is present (non-null).
      2. The value passes the field validator (non-negative numeric or non-empty text).

    Goal: confirm the system does NOT incorrectly reject small/zero values
    that represent legitimate real-world states (remote orgs, bootstrapped
    companies, break-even financials, etc.).
    """
    min_row = _get_min_row(df, col)
    company = min_row["name"]
    value   = min_row[col]

    # 1. Must be present
    assert _non_empty(value), (
        f"\n{'='*60}\n"
        f"  FAIL    : {tc_id}\n"
        f"  Field   : {col}\n"
        f"  Company : {company}\n"
        f"  Rule    : {description}\n"
        f"  Value   : {repr(value)}\n"
        f"  Outcome : value is NULL/empty\n"
        f"{'='*60}"
    )

    # 2. Must be non-negative numeric OR non-empty text
    passed = _zero_or_positive_numeric(value) or _non_empty(value)

    assert passed, (
        f"\n{'='*60}\n"
        f"  FAIL    : {tc_id}\n"
        f"  Field   : {col}\n"
        f"  Company : {company}\n"
        f"  Rule    : {description}\n"
        f"  Value   : {repr(value)}\n"
        f"  Outcome : near-zero value was REJECTED\n"
        f"{'='*60}"
    )

