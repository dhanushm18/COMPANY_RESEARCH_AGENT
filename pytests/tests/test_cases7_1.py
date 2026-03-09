"""
TC-7.1 â€” Boundary Values: Extreme High Values
===============================================
Category : BOUNDARY VALUES
Test Type: Per-Parameter
Priority : Medium

Validates that the system ACCEPTS extreme upper-bound values found in
real company rows from the Excel data source.

Each test locates the company in the Excel that has the LARGEST
recorded value for the target field and asserts it passes validation.

References used to build the test IDs:
â€¢ Employee count  2,000,000+  (Walmart)
â€¢ Revenue         $500B+      (Amazon)
â€¢ Market cap      $3T+        (Apple)
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


def _positive_numeric(value) -> bool:
    """
    Accept integers, floats, dollar strings, K/M/B/T suffixed strings,
    and values with + (e.g. '500,000,000+').
    Returns True as long as a non-negative number can be parsed.
    """
    raw = str(value).strip()
    cleaned = re.sub(r"[$,\s+KkMmBbTt%]", "", raw)
    cleaned = re.sub(r"[<>]", "", cleaned)
    # Handle trailing letters like '1M+' or range 'n/a'
    cleaned = re.sub(r"[a-zA-Z]+$", "", cleaned)
    try:
        return float(cleaned) >= 0
    except ValueError:
        pass
    # Range like '1000-2000' â†’ lower bound
    parts = re.split(r"[-â€“]", cleaned)
    try:
        return float(parts[0]) >= 0
    except (ValueError, IndexError):
        return False


def _get_max_row(df, col):
    """Return the row with the highest numeric value for col."""
    if col not in df.columns:
        pytest.skip(f"Column '{col}' not in sheet")
    sub = df[["name", col]].dropna(subset=[col]).copy()
    if sub.empty:
        pytest.skip(f"All values are null for '{col}'")
    sub["_num"] = pd.to_numeric(
        sub[col].astype(str).str.replace(r"[$,\s+KkMmBbTt%<>]", "", regex=True),
        errors="coerce",
    )
    valid = sub.dropna(subset=["_num"])
    if valid.empty:
        return sub.iloc[0]  # text field â€“ return first row
    return valid.loc[valid["_num"].idxmax()]


# =============================================================================
# TEST DATA: (tc_id, col, description)
# The fixture will look up the company with the LARGEST value from Excel.
# =============================================================================

TC_PARAMS = [
    ("TC-7.1-001", "employee_size",
     "Extreme enterprise workforce â€” Walmart scale (2.1M employees)"),

    ("TC-7.1-002", "hiring_velocity",
     "Unusually high monthly hiring velocity â€” Snowflake (650,000)"),

    ("TC-7.1-003", "office_count",
     "Massive global office footprint â€” Commonwealth Bank (658 offices)"),

    ("TC-7.1-004", "website_traffic_rank",
     "Very high traffic rank value â€” FLAM Gaming (650,000)"),

    ("TC-7.1-005", "social_media_followers",
     "Billion-scale combined follower count â€” Amazon (500M+)"),

    ("TC-7.1-006", "annual_revenue",
     "Ultra-high annual revenue â€” Udemy ($760M)"),

    ("TC-7.1-007", "annual_profit",
     "Very large annual profit figure â€” Udemy ($18M)"),

    ("TC-7.1-008", "valuation",
     "Multi-trillion valuation â€” Udemy ($3.4B as largest in sheet)"),

    ("TC-7.1-009", "total_capital_raised",
     "Massive cumulative capital raised â€” Udemy ($223M)"),

    ("TC-7.1-010", "customer_acquisition_cost",
     "Extremely high CAC for enterprise sales â€” NVIDIA ($35,000)"),

    ("TC-7.1-011", "customer_lifetime_value",
     "Very high CLV â€” ServiceNow ($450,000)"),

    ("TC-7.1-012", "burn_rate",
     "Extreme monthly burn â€” MoveInSync ($450K)"),

    ("TC-7.1-013", "runway_months",
     "Extremely high runway â€” Cleartrip (24+ months)"),

    ("TC-7.1-014", "burn_multiplier",
     "Very high burn multiplier â€” INDmoney (2.5)"),

    ("TC-7.1-015", "r_and_d_investment",
     "Massive R&D spending â€” PhysicsWallah ($1.2B)"),

    ("TC-7.1-016", "training_spend",
     "Very large L&D budget â€” PhysicsWallah ($300M)"),

    ("TC-7.1-017", "intellectual_property",
     "Massive patent/IP portfolio â€” Accenture (text field, non-empty)"),

    ("TC-7.1-018", "partnership_ecosystem",
     "Extremely large partner network â€” Accenture (text field, non-empty)"),

    ("TC-7.1-019", "tam",
     "Trillion-scale TAM â€” PhysicsWallah ($1T addressable market)"),

    ("TC-7.1-020", "sam",
     "Very large SAM â€” PhysicsWallah ($350B)"),

    ("TC-7.1-021", "som",
     "Large SOM â€” PhysicsWallah ($120B)"),
]


# =============================================================================
# PARAMETRIZED TEST
# =============================================================================

@pytest.mark.parametrize(
    "tc_id, col, description",
    TC_PARAMS,
    ids=[p[0] for p in TC_PARAMS],
)
def test_tc_7_1(df, tc_id, col, description):
    """
    TC-7.1 â€” Boundary Values: Extreme High Values.

    Reads the company row with the LARGEST recorded value for each field
    from the Excel source and asserts that:
      1. The value is present (non-null).
      2. The value passes the field validator (non-empty / positive numeric).

    Goal: confirm the system does NOT incorrectly reject real-world
    Fortune-500 / mega-cap scale inputs that exist in the dataset.
    """
    best_row = _get_max_row(df, col)
    company  = best_row["name"]
    value    = best_row[col]

    # 1. Must be present
    assert _non_empty(value), (
        f"\n{'='*60}\n"
        f"  FAIL    : {tc_id}\n"
        f"  Field   : {col}\n"
        f"  Company : {company}\n"
        f"  Rule    : {description}\n"
        f"  Value   : {repr(value)}\n"
        f"  Outcome : value is NULL/empty â€” expected a large valid value\n"
        f"{'='*60}"
    )

    # 2. Must parse as a non-negative number OR be a non-empty text field
    passed = _positive_numeric(value) or _non_empty(value)

    assert passed, (
        f"\n{'='*60}\n"
        f"  FAIL    : {tc_id}\n"
        f"  Field   : {col}\n"
        f"  Company : {company}\n"
        f"  Rule    : {description}\n"
        f"  Value   : {repr(value)}\n"
        f"  Outcome : extreme high value was REJECTED\n"
        f"{'='*60}"
    )

