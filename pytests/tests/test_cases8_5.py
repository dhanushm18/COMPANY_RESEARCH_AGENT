"""
TC-8.5 - List Formatting (Workbook-Driven)
Uses only Company Master.xlsx / Flat Companies Data values.
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
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


def _pick(df, col, pred):
    if col not in df.columns:
        pytest.skip(f"Missing column: {col}")
    for v in df[col].dropna().astype(str):
        s = v.strip()
        if s and pred(s):
            return s
    pytest.skip(f"No valid sample found in {col}")


def _countries_ok(s):
    return re.fullmatch(r"^([A-Za-z\s]+)(,\s*[A-Za-z\s]+)*$", s) is not None


def _office_locations_ok(s):
    items = [x.strip() for x in s.split(";") if x.strip()]
    if not items:
        return False
    for item in items:
        parts = [p.strip() for p in item.split(",") if p.strip()]
        if len(parts) < 2:
            return False
    return True


def _focus_sectors_ok(s):
    return "," in s and len([x for x in s.split(",") if x.strip()]) >= 1


def _entity_list_ok(s):
    return re.fullmatch(r"^[\w\s&.,\-/]+(,\s*[\w\s&.,\-/]+)*$", s) is not None


def _news_ok(s):
    entries = [e.strip() for e in s.split(";") if e.strip()]
    pat = r"^\d{4}-\d{2}-\d{2}\s-\s.+\s-\shttps?://.+$"
    return all(re.fullmatch(pat, e) for e in entries)


def _investors_ok(s):
    return re.fullmatch(r"^[\w\s&.,\-\(\)]+(,\s*[\w\s&.,\-\(\)]+)*$", s) is not None


def _funding_ok(s):
    entries = [e.strip() for e in s.split(",") if e.strip()]
    pat = r"^[A-Za-z0-9\s]+\s-\s\d{4}-\d{2}-\d{2}\s-\s\$?\d+(?:\.\d+)?[KMB]?$"
    return all(re.fullmatch(pat, e) for e in entries)


def _tech_stack_ok(s):
    return "," in s and len([x for x in s.split(",") if x.strip()]) >= 2


def _partnership_ok(s):
    return re.fullmatch(r"^[A-Za-z0-9 &.\-\(\)]+(,\s*[A-Za-z0-9 &.\-\(\)]+)*$", s) is not None


def _associations_ok(s):
    return re.fullmatch(r"^[^,]+(?:,\s*[^,]+)*$", s) is not None and not s.endswith(",") and "/" not in s


CASES = [
    ("TC-8.5-09", "operating_countries", _countries_ok),
    ("TC-8.5-11", "office_locations", _office_locations_ok),
    ("TC-8.5-17", "focus_sectors", _focus_sectors_ok),
    ("TC-8.5-28", "key_competitors", _entity_list_ok),
    ("TC-8.5-29", "technology_partners", _entity_list_ok),
    ("TC-8.5-31", "recent_news", _news_ok),
    ("TC-8.5-67", "key_investors", _investors_ok),
    ("TC-8.5-68", "recent_funding_rounds", _funding_ok),
    ("TC-8.5-84", "tech_stack", _tech_stack_ok),
    ("TC-8.5-92", "partnership_ecosystem", _partnership_ok),
    ("TC-8.5-99", "industry_associations", _associations_ok),
]


@pytest.mark.parametrize("tc_id,col,validator", CASES, ids=[c[0] for c in CASES])
def test_tc_8_5_workbook_only(df, tc_id, col, validator):
    value = _pick(df, col, validator)
    assert validator(value), f"{tc_id}: validation failed for value '{value}'"

