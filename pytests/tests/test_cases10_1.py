"""
TC-10.1 - Knowledge Cutoff Events (Workbook-Driven)
Uses only Company Master.xlsx / Flat Companies Data.
"""

from pathlib import Path
import re

import pandas as pd
import pytest

FILE_PATH = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"

CEO_NAME_REGEX = r"^[A-Za-z\s.\-']+$"
LINKEDIN_REGEX = r"^https?://(www\.)?linkedin\.com/in/[A-Za-z0-9_\-]+/?$"


@pytest.fixture(scope="module")
def df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


def _pick_row(df, predicate):
    for _, row in df.iterrows():
        if predicate(row):
            return row
    return None


def _contains_2025(text):
    return isinstance(text, str) and "2025" in text


def _is_primitive(v):
    return isinstance(v, (str, int, float, bool))


def _assert_record_wide_validity(row):
    populated = 0
    for v in row.values:
        if pd.isna(v):
            continue
        populated += 1
        assert _is_primitive(v), f"Non-primitive populated field type: {type(v).__name__}"

    # Complete entity record check: ensure sufficient parameter coverage.
    assert populated >= 20, f"Insufficient populated fields for complete-entity validation: {populated}"


@pytest.mark.parametrize("test_id", ["TC-10.1-01", "TC-10.1-02", "TC-10.1-03", "TC-10.1-04"])
def test_tc_10_1_workbook_only(df, test_id):
    if test_id == "TC-10.1-01":
        needed = ["ceo_name", "ceo_linkedin_url", "recent_news"]
        for c in needed:
            if c not in df.columns:
                pytest.skip(f"Missing column: {c}")

        row = _pick_row(
            df,
            lambda r: _contains_2025(r.get("recent_news"))
            and isinstance(r.get("ceo_name"), str)
            and isinstance(r.get("ceo_linkedin_url"), str),
        )
        if row is None:
            pytest.skip("No 2025 leadership-transition candidate found")

        _assert_record_wide_validity(row)
        assert re.fullmatch(CEO_NAME_REGEX, str(row["ceo_name"])) is not None
        assert re.fullmatch(LINKEDIN_REGEX, str(row["ceo_linkedin_url"])) is not None
        assert "2025" in str(row["recent_news"])

    elif test_id == "TC-10.1-02":
        needed = ["recent_funding_rounds", "valuation"]
        for c in needed:
            if c not in df.columns:
                pytest.skip(f"Missing column: {c}")

        row = _pick_row(
            df,
            lambda r: _contains_2025(r.get("recent_funding_rounds")) and pd.notna(r.get("valuation")),
        )
        if row is None:
            pytest.skip("No 2025 funding event with valuation found")

        _assert_record_wide_validity(row)
        assert "2025" in str(row["recent_funding_rounds"])
        val = row["valuation"]
        assert isinstance(val, (int, float, str))

    elif test_id == "TC-10.1-03":
        needed = ["recent_news", "product_pipeline", "innovation_roadmap"]
        for c in needed:
            if c not in df.columns:
                pytest.skip(f"Missing column: {c}")

        row = _pick_row(
            df,
            lambda r: _contains_2025(r.get("recent_news"))
            and (
                _contains_2025(r.get("product_pipeline"))
                or _contains_2025(r.get("innovation_roadmap"))
            ),
        )
        if row is None:
            pytest.skip("No 2025 launch + roadmap transition candidate found")

        _assert_record_wide_validity(row)
        assert "2025" in str(row["recent_news"])
        assert (
            "2025" in str(row["product_pipeline"]) or "2025" in str(row["innovation_roadmap"])
        )

    elif test_id == "TC-10.1-04":
        needed = ["exit_strategy_history", "name", "short_name"]
        for c in needed:
            if c not in df.columns:
                pytest.skip(f"Missing column: {c}")

        row = _pick_row(
            df,
            lambda r: isinstance(r.get("exit_strategy_history"), str)
            and "2025" in str(r.get("exit_strategy_history"))
            and re.search(r"acquir|ipo", str(r.get("exit_strategy_history")), re.I),
        )
        if row is None:
            pytest.skip("No post-cutoff acquisition/IPO candidate found")

        _assert_record_wide_validity(row)
        assert re.search(r"acquir|ipo", str(row["exit_strategy_history"]), re.I)
        assert isinstance(row["name"], str)

    else:
        pytest.fail(f"Unknown test id: {test_id}")

