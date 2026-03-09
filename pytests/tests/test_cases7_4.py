"""
TC-7.4 - Boundary Values: Percentage Bounds
===========================================
Category : BOUNDARY VALUES
Test Type: Specific-Parameters
Priority : High

Excel-driven tests for percentage/range boundaries. Inputs are selected
from Company Master.xlsx (Flat Companies Data). If an exact boundary
sample is not present in the workbook, that specific test is skipped.
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


def _extract_numbers(text):
    raw = str(text)
    nums = []
    for token in re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", raw):
        try:
            nums.append(float(token.replace(",", "")))
        except ValueError:
            continue
    return nums


def _first_number(text):
    nums = _extract_numbers(text)
    return nums[0] if nums else None


def _pick_input(df, column, selector):
    if column not in df.columns:
        pytest.skip(f"Column '{column}' not found in {SHEET_NAME}")

    for _, row in df[["name", column]].dropna(subset=[column]).iterrows():
        value = str(row[column]).strip()
        nums = _extract_numbers(value)
        first = nums[0] if nums else None
        low = value.lower()

        if selector == "pct_eq_0" and first == 0:
            return row["name"], value
        if selector == "pct_eq_100" and first == 100:
            return row["name"], value
        if selector == "pct_gt_100" and first is not None and first > 100:
            return row["name"], value
        if selector == "pct_lt_0" and first is not None and first < 0:
            return row["name"], value
        if selector == "pct_between_0_100" and first is not None and 0 <= first <= 100:
            return row["name"], value

        if selector == "sum_eq_100" and nums and abs(sum(nums) - 100) < 1e-9:
            return row["name"], value
        if selector == "sum_gt_100" and nums and sum(nums) > 100:
            return row["name"], value
        if selector == "sum_lt_100" and nums and sum(nums) < 100:
            return row["name"], value

        if selector == "score_eq_0" and re.fullmatch(r"\s*0\s*", value):
            return row["name"], value
        if selector == "score_eq_100" and re.fullmatch(r"\s*100\s*", value):
            return row["name"], value
        if selector == "score_gt_100" and re.fullmatch(r"\s*\d+\s*", value) and int(value) > 100:
            return row["name"], value

        if selector == "enum_positive" and low == "positive":
            return row["name"], value
        if selector == "enum_neutral" and low == "neutral":
            return row["name"], value
        if selector == "enum_negative" and low == "negative":
            return row["name"], value
        if selector == "enum_invalid" and "positive" in low and low != "positive":
            return row["name"], value

        if selector == "nps_eq_-100" and first == -100:
            return row["name"], value
        if selector == "nps_eq_100" and first == 100:
            return row["name"], value
        if selector == "nps_gt_100" and first is not None and first > 100:
            return row["name"], value

    pytest.skip(f"No '{selector}' sample found in workbook for column '{column}'")


def validate_percentage_0_100(value):
    num = _first_number(value)
    if num is None:
        return False, "Rejected. Percentage value is not numeric"
    if num < 0:
        return False, "Rejected. Percentage cannot be negative"
    if num > 100:
        return False, "Rejected. Violates range constraint (0-100%)"
    return True, "Accepted. Business rule: value between 0-100%"


def validate_yoy_growth(value):
    num = _first_number(value)
    if num is None:
        return False, "Rejected. Growth value is not numeric"
    return True, "Accepted"


def validate_revenue_mix(value):
    nums = _extract_numbers(value)
    if len(nums) < 2:
        return False, "Rejected. Revenue mix requires at least two numeric components"

    total = sum(nums)
    if abs(total - 100) < 1e-9:
        return True, "Accepted. Sum equals 100%"
    if total > 100:
        return False, "Rejected. Sum exceeds 100%"
    return False, "Rejected. Sum below 100%"


def validate_brand_sentiment(value):
    s = str(value).strip()
    low = s.lower()
    if low in {"positive", "neutral", "negative"}:
        return True, "Accepted. Enum value allowed"

    if re.fullmatch(r"\d{1,3}", s):
        score = int(s)
        if 0 <= score <= 100:
            return True, "Accepted. Score maps to 0-100"
        return False, "Rejected. Must map to 0-100 or Enum"

    return False, "Rejected. Not in allowed Enum"


def validate_nps(value):
    num = _first_number(value)
    if num is None:
        return False, "Rejected. NPS must be numeric"
    if num < -100 or num > 100:
        return False, "Rejected. Must be between -100 and 100"
    return True, "Accepted. NPS in valid range"


TEST_CASES_7_4 = [
    ("Market Share (%)", "market_share_percentage", "TC-7.4-01", "Validate minimum market share", "pct_eq_0", True),
    ("Market Share (%)", "market_share_percentage", "TC-7.4-02", "Validate maximum market share", "pct_eq_100", True),
    ("Market Share (%)", "market_share_percentage", "TC-7.4-03", "Validate market share above upper bound", "pct_gt_100", False),
    ("Market Share (%)", "market_share_percentage", "TC-7.4-04", "Validate market share below lower bound", "pct_lt_0", False),
    ("Churn Rate", "churn_rate", "TC-7.4-05", "Validate zero churn", "pct_eq_0", True),
    ("Churn Rate", "churn_rate", "TC-7.4-06", "Validate full churn", "pct_eq_100", True),
    ("Churn Rate", "churn_rate", "TC-7.4-07", "Validate churn beyond upper bound", "pct_gt_100", False),
    ("Churn Rate", "churn_rate", "TC-7.4-08", "Validate churn below lower bound", "pct_lt_0", False),
    ("Employee Turnover", "employee_turnover", "TC-7.4-09", "Validate no employee exits", "pct_eq_0", True),
    ("Employee Turnover", "employee_turnover", "TC-7.4-10", "Validate complete workforce turnover", "pct_eq_100", True),
    ("Employee Turnover", "employee_turnover", "TC-7.4-11", "Validate turnover above upper bound", "pct_gt_100", False),
    ("Employee Turnover", "employee_turnover", "TC-7.4-12", "Validate turnover below lower bound", "pct_lt_0", False),
    ("Year-over-Year Growth Rate", "yoy_growth_rate", "TC-7.4-13", "Validate normal growth", "pct_between_0_100", True),
    ("Year-over-Year Growth Rate", "yoy_growth_rate", "TC-7.4-14", "Validate hypergrowth scenario", "pct_gt_100", True),
    ("Year-over-Year Growth Rate", "yoy_growth_rate", "TC-7.4-15", "Validate negative growth (contraction)", "pct_lt_0", True),
    ("Revenue Mix", "revenue_mix", "TC-7.4-16", "Validate valid revenue mix", "sum_eq_100", True),
    ("Revenue Mix", "revenue_mix", "TC-7.4-17", "Validate revenue mix overflow", "sum_gt_100", False),
    ("Revenue Mix", "revenue_mix", "TC-7.4-18", "Validate incomplete revenue mix", "sum_lt_100", False),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-19", "Validate minimum numeric sentiment score", "score_eq_0", True),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-20", "Validate maximum numeric sentiment score", "score_eq_100", True),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-21", "Validate sentiment score above range", "score_gt_100", False),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-22", "Validate categorical sentiment - Positive", "enum_positive", True),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-23", "Validate categorical sentiment - Neutral", "enum_neutral", True),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-24", "Validate categorical sentiment - Negative", "enum_negative", True),
    ("Brand Sentiment Score", "brand_sentiment_score", "TC-7.4-25", "Validate invalid categorical sentiment", "enum_invalid", False),
    ("Net Promoter Score (NPS)", "net_promoter_score", "TC-7.4-26", "Validate minimum NPS", "nps_eq_-100", True),
    ("Net Promoter Score (NPS)", "net_promoter_score", "TC-7.4-27", "Validate maximum NPS", "nps_eq_100", True),
    ("Net Promoter Score (NPS)", "net_promoter_score", "TC-7.4-28", "Validate NPS overflow", "nps_gt_100", False),
]


@pytest.mark.parametrize(
    "column_name, sheet_column, test_id, test_case_description, selector, expected_accepted",
    TEST_CASES_7_4,
    ids=[tc[2] for tc in TEST_CASES_7_4],
)
def test_tc_7_4_percentage_bounds(
    df,
    column_name,
    sheet_column,
    test_id,
    test_case_description,
    selector,
    expected_accepted,
):
    company, input_data = _pick_input(df, sheet_column, selector)

    if column_name in {"Market Share (%)", "Churn Rate", "Employee Turnover"}:
        accepted, message = validate_percentage_0_100(input_data)
    elif column_name == "Year-over-Year Growth Rate":
        accepted, message = validate_yoy_growth(input_data)
    elif column_name == "Revenue Mix":
        accepted, message = validate_revenue_mix(input_data)
    elif column_name == "Brand Sentiment Score":
        accepted, message = validate_brand_sentiment(input_data)
    elif column_name == "Net Promoter Score (NPS)":
        accepted, message = validate_nps(input_data)
    else:
        pytest.fail(f"{test_id}: Unsupported column '{column_name}'")

    assert accepted == expected_accepted, (
        f"\n{'=' * 60}\n"
        f"  FAIL        : {test_id}\n"
        f"  Company     : {company}\n"
        f"  Column      : {column_name}\n"
        f"  Sheet Col   : {sheet_column}\n"
        f"  Description : {test_case_description}\n"
        f"  Input       : {input_data}\n"
        f"  Expected    : {'Accepted' if expected_accepted else 'Rejected'}\n"
        f"  Actual      : {'Accepted' if accepted else 'Rejected'}\n"
        f"  Validator   : {message}\n"
        f"{'=' * 60}"
    )

