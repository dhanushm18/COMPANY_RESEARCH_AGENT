"""
TC-8.6 - Text Length Validation (Workbook-Driven)
Uses only Company Master.xlsx / Flat Companies Data values.
"""

from pathlib import Path

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
        if pred(v):
            return v
    pytest.skip(f"No matching sample in {col}")


CASES = [
    ("TC-8.6.1", "short_name", lambda s: len(s) < 50, lambda s: len(s) < 50, True),
    ("TC-8.6.2", "short_name", lambda s: len(s) > 50, lambda s: len(s) <= 50, False),
    ("TC-8.6.3", "overview_text", lambda s: 200 <= len(s) <= 500, lambda s: 200 <= len(s) <= 500, True),
    ("TC-8.6.4", "overview_text", lambda s: len(s) < 200, lambda s: 200 <= len(s) <= 500, False),
    ("TC-8.6.5", "core_value_proposition", lambda s: len(s) <= 2000, lambda s: len(s) <= 2000, True),
    ("TC-8.6.6", "mission_statement", lambda s: len(s) <= 500, lambda s: len(s) <= 500, True),
    ("TC-8.6.7", "sustainability_csr", lambda s: len(s) <= 2000, lambda s: len(s) <= 2000, True),
    ("TC-8.6.8", "crisis_behavior", lambda s: len(s) > 2000, lambda s: len(s) <= 2000, False),
]


@pytest.mark.parametrize("tc_id,col,selector,validator,expected", CASES, ids=[c[0] for c in CASES])
def test_tc_8_6_workbook_only(df, tc_id, col, selector, validator, expected):
    value = _pick(df, col, selector)
    actual = validator(value)
    assert actual == expected, f"{tc_id}: expected {expected}, got {actual}, len={len(value)}"

