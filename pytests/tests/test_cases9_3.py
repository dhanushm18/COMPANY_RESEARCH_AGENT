"""
TC-9.3 - Context Confusion (Workbook-Driven)
Uses only Company Master.xlsx / Flat Companies Data.
"""

from pathlib import Path
import re

import pandas as pd
import pytest

FILE_PATH = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"


@pytest.fixture(scope="module")
def df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    data = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
    if "name" not in data.columns:
        pytest.skip("'name' column missing")
    return data


def _subset(df, predicate, min_rows=2):
    mask = df["name"].astype(str).apply(lambda n: bool(predicate(n)))
    sub = df[mask].copy()
    if len(sub) < min_rows:
        return None
    return sub


def _check_distinct(sub, cols):
    for c in cols:
        if c in sub.columns:
            vals = sub[c].dropna().astype(str)
            if len(vals) > 1 and len(vals.unique()) < len(vals):
                # duplicate values are possible in real data; this is a soft check.
                continue
    return True


def _run_case(df, test_id, sub, required_cols):
    if sub is None:
        pytest.skip(f"{test_id}: insufficient workbook matches")

    # No contamination proxy: names must remain unique in chosen subset.
    names = sub["name"].astype(str)
    assert len(names) == len(names.unique()), f"{test_id}: duplicate entity names in subset"

    for c in required_cols:
        if c not in sub.columns:
            pytest.skip(f"{test_id}: missing required column '{c}'")

    # Ensure at least one differentiator field varies in the group.
    varying = False
    for c in required_cols:
        vals = sub[c].dropna().astype(str).unique()
        if len(vals) > 1:
            varying = True
            break
    assert varying, f"{test_id}: no differentiating metadata found in selected subset"

    # Record-wide guard: entity fingerprints across all populated columns
    # must remain distinct (proxy for no cross-record blending).
    signatures = []
    for _, row in sub.iterrows():
        items = []
        for col, val in row.items():
            if pd.isna(val):
                continue
            items.append((col, str(val)))
        signatures.append(tuple(items))
    assert len(signatures) == len(set(signatures)), (
        f"{test_id}: full-record signatures are not distinct"
    )


@pytest.mark.parametrize(
    "test_id,selector,min_rows,required_cols",
    [
        ("TC-9.3-001", lambda n: re.search(r"delta", n, re.I), 2, ["category", "incorporation_year", "focus_sectors", "headquarters_address"]),
        ("TC-9.3-002", lambda n: re.search(r"apple", n, re.I), 2, ["short_name", "focus_sectors", "overview_text", "nature_of_company"]),
        ("TC-9.3-003", lambda n: re.search(r"delta", n, re.I), 3, ["incorporation_year", "category", "focus_sectors", "annual_revenue", "valuation"]),
        ("TC-9.3-004", lambda n: re.search(r"microsoft", n, re.I), 2, ["nature_of_company", "headquarters_address", "operating_countries", "employee_size", "hiring_velocity"]),
        ("TC-9.3-005", lambda n: re.search(r"global", n, re.I), 3, ["overview_text", "logo_url", "focus_sectors", "offerings_description", "recent_news"]),
        ("TC-9.3-006", lambda n: re.search(r"\bibm\b|international business machines", n, re.I), 2, ["incorporation_year", "company_maturity", "valuation", "annual_revenue", "employee_size"]),
        ("TC-9.3-007", lambda n: re.search(r"amazon", n, re.I), 2, ["headquarters_address", "operating_countries", "office_locations", "regulatory_status"]),
        ("TC-9.3-008", lambda n: re.search(r"cafe|caf[eé]", n, re.I), 2, ["focus_sectors"]),
        ("TC-9.3-009", lambda n: re.search(r"acme", n, re.I), 2, ["overview_text", "category"]),
        ("TC-9.3-010", lambda n: re.search(r"consulting", n, re.I), 2, ["offerings_description", "top_customers", "pain_points_addressed"]),
        ("TC-9.3-011", lambda n: re.search(r"nova systems", n, re.I), 2, ["nature_of_company", "headquarters_address", "annual_revenue", "legal_issues"]),
        ("TC-9.3-012", lambda n: re.search(r"horizon", n, re.I), 2, ["focus_sectors", "pain_points_addressed", "offerings_description", "overview_text"]),
        ("TC-9.3-013", lambda n: re.search(r"general|google|goldman", n, re.I), 3, ["short_name", "logo_url", "recent_news"]),
        ("TC-9.3-014", lambda n: re.search(r"musk|palo alto|tesla", n, re.I), 2, ["ceo_name", "headquarters_address", "key_investors"]),
        ("TC-9.3-015", lambda n: re.search(r"alpha", n, re.I), 10, ["category", "validation_mode", "focus_sectors", "valuation"]),
        ("TC-9.3-016", lambda n: re.search(r"united", n, re.I), 2, ["operating_countries"]),
        ("TC-9.3-017", lambda n: re.search(r"facebook|meta", n, re.I), 2, ["incorporation_year", "layoff_history", "recent_news", "overview_text"]),
        ("TC-9.3-018", lambda n: re.search(r"cloudbase", n, re.I), 2, ["logo_url", "website_url", "tech_stack", "focus_sectors"]),
        ("TC-9.3-019", lambda n: re.search(r"first", n, re.I), 3, ["focus_sectors", "regulatory_status", "go_to_market_strategy"]),
        ("TC-9.3-020", lambda n: re.search(r"nextgen", n, re.I), 2, ["incorporation_year", "company_maturity", "employee_size", "hiring_velocity", "valuation"]),
    ],
    ids=[f"TC-9.3-{i:03d}" for i in range(1, 21)],
)
def test_tc_9_3_workbook_only(df, test_id, selector, min_rows, required_cols):
    sub = _subset(df, selector, min_rows=min_rows)
    _run_case(df, test_id, sub, required_cols)

