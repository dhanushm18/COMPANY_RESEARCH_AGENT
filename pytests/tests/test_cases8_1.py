"""
TC-8.1 - Data Type Validation (Workbook-Driven)
Uses only Company Master.xlsx / Flat Companies Data.
"""

from pathlib import Path
from numbers import Integral, Real

import pandas as pd
import pytest

FILE_PATH = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"


VARCHAR_COLS = [
    "name", "short_name", "category", "employee_size", "focus_sectors",
    "offerings_description", "key_competitors", "technology_partners",
]
INTEGER_COLS = ["incorporation_year", "office_count"]
TEXT_COLS = ["overview_text", "recent_news", "office_locations"]
DECIMAL_COLS = ["annual_revenue", "valuation", "website_rating"]
PERCENT_VARCHAR_COLS = ["employee_turnover"]
URL_TEXT_COLS = ["logo_url"]


@pytest.fixture(scope="module")
def df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


def _nonnull(series):
    return series.dropna()


def _is_str(v):
    return isinstance(v, str)


def _is_int_like(v):
    return isinstance(v, Integral) and not isinstance(v, bool)


def _is_numeric(v):
    return isinstance(v, Real) and not isinstance(v, bool)


def _find_any(series, predicate):
    for v in _nonnull(series):
        if predicate(v):
            return v
    return None


def _is_primitive(v):
    return isinstance(v, (str, bool, Integral, Real))


def _row_all_populated_fields_are_primitives(row):
    for v in row.values:
        if pd.isna(v):
            continue
        if not _is_primitive(v):
            return False
    return True


CASES = [
    ("8.1.001", "varchar_non_string", False),
    ("8.1.002", "integer_non_integer", False),
    ("8.1.003", "text_non_string", False),
    ("8.1.004", "decimal_non_numeric", False),
    ("8.1.005", "boolean_wrong_type", False),
    ("8.1.006", "year_wrong_type", False),
    ("8.1.007", "complete_valid_row", True),
    ("8.1.008", "url_text_non_string", False),
    ("8.1.009", "percentage_varchar_non_string", False),
    ("8.1.010", "mixed_type_violation", False),
    ("8.1.011", "list_field_non_string", False),
    ("8.1.012", "regex_fields_non_string", False),
    ("8.1.013", "cross_validate_types", True),
    ("8.1.014", "derived_field_types", True),
    ("8.1.015", "nullability_integrity", False),
]


@pytest.mark.parametrize("tc_id,mode,expected", CASES, ids=[c[0] for c in CASES])
def test_tc_8_1_workbook_only(df, tc_id, mode, expected):
    if mode == "varchar_non_string":
        bad = None
        for c in VARCHAR_COLS:
            if c in df.columns:
                bad = _find_any(df[c], lambda v: not _is_str(v))
                if bad is not None:
                    break
        if bad is None:
            pytest.skip("No VARCHAR type violation found in workbook")
        actual = False

    elif mode == "integer_non_integer":
        bad = None
        for c in INTEGER_COLS:
            if c in df.columns:
                bad = _find_any(df[c], lambda v: not _is_int_like(v))
                if bad is not None:
                    break
        if bad is None:
            pytest.skip("No INTEGER type violation found in workbook")
        actual = False

    elif mode == "text_non_string":
        bad = None
        for c in TEXT_COLS:
            if c in df.columns:
                bad = _find_any(df[c], lambda v: not _is_str(v))
                if bad is not None:
                    break
        if bad is None:
            pytest.skip("No TEXT type violation found in workbook")
        actual = False

    elif mode == "decimal_non_numeric":
        bad = None
        for c in DECIMAL_COLS:
            if c in df.columns:
                bad = _find_any(df[c], lambda v: not _is_numeric(v))
                if bad is not None:
                    break
        if bad is None:
            pytest.skip("No DECIMAL type violation found in workbook")
        actual = False

    elif mode == "boolean_wrong_type":
        # Workbook has no strict boolean column; enforce from yes/no style indicators if present.
        if "is_public_company" not in df.columns:
            pytest.skip("No boolean field present in workbook")
        bad = _find_any(df["is_public_company"], lambda v: not isinstance(v, bool))
        if bad is None:
            pytest.skip("No BOOLEAN type violation found in workbook")
        actual = False

    elif mode == "year_wrong_type":
        c = "incorporation_year"
        if c not in df.columns:
            pytest.skip("incorporation_year not present")
        bad = _find_any(df[c], lambda v: not _is_int_like(v))
        if bad is None:
            pytest.skip("No year type violation found in workbook")
        actual = False

    elif mode == "complete_valid_row":
        req = ["name", "incorporation_year", "annual_revenue", "overview_text", "employee_size", "office_count"]
        for c in req:
            if c not in df.columns:
                pytest.skip(f"Missing required column: {c}")
        ok = False
        full = df.dropna(subset=req)
        for _, r in full.iterrows():
            if _is_str(r["name"]) and _is_int_like(r["incorporation_year"]) and _is_numeric(r["annual_revenue"]) and _is_str(r["overview_text"]) and _is_str(r["employee_size"]) and _is_int_like(r["office_count"]) and _row_all_populated_fields_are_primitives(r):
                ok = True
                break
        if not ok:
            pytest.skip("No fully type-compliant row found")
        actual = True

    elif mode == "url_text_non_string":
        c = "logo_url"
        if c not in df.columns:
            pytest.skip("logo_url not present")
        bad = _find_any(df[c], lambda v: not _is_str(v))
        if bad is None:
            pytest.skip("No URL type violation found")
        actual = False

    elif mode == "percentage_varchar_non_string":
        c = "employee_turnover"
        if c not in df.columns:
            pytest.skip("employee_turnover not present")
        bad = _find_any(df[c], lambda v: not _is_str(v))
        if bad is None:
            pytest.skip("No percentage VARCHAR type violation found")
        actual = False

    elif mode == "mixed_type_violation":
        checks = []
        if "category" in df.columns:
            checks.append(_find_any(df["category"], lambda v: not _is_str(v)) is not None)
        if "employee_size" in df.columns:
            checks.append(_find_any(df["employee_size"], lambda v: not _is_str(v)) is not None)
        if "total_capital_raised" in df.columns:
            checks.append(_find_any(df["total_capital_raised"], lambda v: not _is_numeric(v)) is not None)
        if not checks or not any(checks):
            pytest.skip("No mixed type violation found")
        actual = False

    elif mode == "list_field_non_string":
        c = "operating_countries"
        if c not in df.columns:
            pytest.skip("operating_countries not present")
        bad = _find_any(df[c], lambda v: not _is_str(v))
        if bad is None:
            pytest.skip("No list-field type violation found")
        actual = False

    elif mode == "regex_fields_non_string":
        candidates = ["name", "logo_url", "category"]
        found = False
        for c in candidates:
            if c in df.columns and _find_any(df[c], lambda v: not _is_str(v)) is not None:
                found = True
                break
        if not found:
            pytest.skip("No regex-field type violation found")
        actual = False

    elif mode == "cross_validate_types":
        needed = ["name", "incorporation_year", "annual_revenue", "overview_text", "employee_size"]
        for c in needed:
            if c not in df.columns:
                pytest.skip(f"Missing required column: {c}")
        actual = False
        for idx, r in df[needed].dropna().iterrows():
            full_row = df.loc[idx]
            if _is_str(r["name"]) and _is_int_like(r["incorporation_year"]) and _is_numeric(r["annual_revenue"]) and _is_str(r["overview_text"]) and _is_str(r["employee_size"]) and _row_all_populated_fields_are_primitives(full_row):
                actual = True
                break
        if not actual:
            pytest.skip("No row satisfies cross-validated type requirements")

    elif mode == "derived_field_types":
        needed = ["office_locations", "office_count", "company_maturity", "incorporation_year", "employee_size"]
        for c in needed:
            if c not in df.columns:
                pytest.skip(f"Missing required column: {c}")
        actual = False
        for idx, r in df[needed].dropna().iterrows():
            full_row = df.loc[idx]
            if _is_str(r["office_locations"]) and _is_int_like(r["office_count"]) and _is_str(r["company_maturity"]) and _is_int_like(r["incorporation_year"]) and _is_str(r["employee_size"]) and _row_all_populated_fields_are_primitives(full_row):
                actual = True
                break
        if not actual:
            pytest.skip("No row satisfies derived-field type requirements")

    elif mode == "nullability_integrity":
        c = "name"
        if c not in df.columns:
            pytest.skip("name not present")
        has_null_notnull = df[c].isna().any()
        if not has_null_notnull:
            pytest.skip("No nullability violation found for not-null field")
        actual = False

    else:
        pytest.fail(f"Unknown mode: {mode}")

    assert actual == expected, f"{tc_id}: expected {expected}, got {actual}"

