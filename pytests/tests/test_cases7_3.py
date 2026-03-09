"""
TC-7.3 - Boundary Values: Negative Values
=========================================
Category : BOUNDARY VALUES
Test Type: Specific-Parameters
Priority : High

Excel-driven tests for negative-value boundary handling.
Inputs are selected from Company Master.xlsx (Flat Companies Data).
If a required pattern is not present in the sheet for a scenario,
that test is skipped with an explicit reason.
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
    """Extract signed numeric tokens from mixed strings."""
    raw = str(text)
    nums = []
    for token in re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", raw):
        try:
            nums.append(float(token.replace(",", "")))
        except ValueError:
            continue
    return nums


def _is_zero_like(text):
    s = str(text).strip().lower()
    if s in {"0", "0%", "0.0", "0.00"}:
        return True
    return "zero" in s or "break-even" in s or "breakeven" in s


def _pick_input(df, column, scenario):
    """Pick one workbook value for the requested scenario."""
    if column not in df.columns:
        pytest.skip(f"Column '{column}' not found in {SHEET_NAME}")

    for _, row in df[["name", column]].dropna(subset=[column]).iterrows():
        value = str(row[column]).strip()
        nums = _extract_numbers(value)

        if scenario == "negative_numeric" and any(n < 0 for n in nums):
            return row["name"], value

        if scenario == "zero_like":
            has_zero_numeric = any(n == 0 for n in nums)
            if has_zero_numeric or _is_zero_like(value):
                return row["name"], value

        if scenario == "positive_numeric" and any(n > 0 for n in nums):
            return row["name"], value

        if scenario == "nps_minimum" and any(n == -100 for n in nums):
            return row["name"], value

        if scenario == "nps_below_min" and any(n < -100 for n in nums):
            return row["name"], value

    pytest.skip(
        f"No '{scenario}' sample found in workbook for column '{column}'"
    )


def validate_annual_profits(value):
    if _is_zero_like(value):
        return True, "Accepted. Zero/break-even profit is valid"

    nums = _extract_numbers(value)
    if nums:
        return True, "Accepted. Business rule allows negative values to represent losses"
    return False, "Rejected. Value is not numeric"


def validate_yoy_growth(value):
    s = str(value).strip()
    if re.fullmatch(r"^[+-]?\d+(\.\d+)?%$", s):
        return True, "Accepted"

    nums = _extract_numbers(s)
    if nums:
        # Workbook has decimal ratios like 0.03 as well as % strings.
        return True, "Accepted"

    return False, "Rejected. Must be a parseable growth value"


def validate_nps(value):
    nums = _extract_numbers(value)
    if not nums:
        return False, "Rejected. NPS must be numeric"

    nps = int(nums[0])
    if -100 <= nps <= 100:
        return True, "Accepted. NPS valid range is -100 to 100"
    return False, "Rejected. Violates NPS range (-100 to 100)"


def validate_burn_rate(value):
    nums = _extract_numbers(value)
    if not nums:
        return False, "Rejected. Burn rate must be numeric"

    burn = nums[0]
    if burn < 0:
        return True, "Accepted. Represents cash-positive operations"
    if burn == 0:
        return False, "Rejected. Zero burn is ambiguous; use NULL or N/A"
    return True, "Accepted. Represents monthly cash outflow"


TEST_CASES_7_3 = [
    (
        "Annual Profits",
        "annual_profit",
        "TC-7.3-01",
        "Validate negative annual profit (loss-making company)",
        "negative_numeric",
        True,
    ),
    (
        "Annual Profits",
        "annual_profit",
        "TC-7.3-02",
        "Validate zero profit (break-even)",
        "zero_like",
        True,
    ),
    (
        "Annual Profits",
        "annual_profit",
        "TC-7.3-03",
        "Validate positive profit",
        "positive_numeric",
        True,
    ),
    (
        "Year-over-Year Growth Rate",
        "yoy_growth_rate",
        "TC-7.3-04",
        "Validate negative growth (revenue contraction)",
        "negative_numeric",
        True,
    ),
    (
        "Year-over-Year Growth Rate",
        "yoy_growth_rate",
        "TC-7.3-05",
        "Validate zero growth",
        "zero_like",
        True,
    ),
    (
        "Year-over-Year Growth Rate",
        "yoy_growth_rate",
        "TC-7.3-06",
        "Validate positive growth",
        "positive_numeric",
        True,
    ),
    (
        "Net Promoter Score (NPS)",
        "net_promoter_score",
        "TC-7.3-07",
        "Validate negative NPS score",
        "negative_numeric",
        True,
    ),
    (
        "Net Promoter Score (NPS)",
        "net_promoter_score",
        "TC-7.3-08",
        "Validate minimum NPS boundary",
        "nps_minimum",
        True,
    ),
    (
        "Net Promoter Score (NPS)",
        "net_promoter_score",
        "TC-7.3-09",
        "Validate NPS below minimum",
        "nps_below_min",
        False,
    ),
    (
        "Burn Rate",
        "burn_rate",
        "TC-7.3-10",
        "Validate negative burn rate indicating net cash inflow",
        "negative_numeric",
        True,
    ),
    (
        "Burn Rate",
        "burn_rate",
        "TC-7.3-11",
        "Validate zero burn rate",
        "zero_like",
        False,
    ),
    (
        "Burn Rate",
        "burn_rate",
        "TC-7.3-12",
        "Validate positive burn rate",
        "positive_numeric",
        True,
    ),
]


@pytest.mark.parametrize(
    "column_name, sheet_column, test_id, test_case_description, input_selector, expected_accepted",
    TEST_CASES_7_3,
    ids=[tc[2] for tc in TEST_CASES_7_3],
)
def test_tc_7_3_negative_values(
    df,
    column_name,
    sheet_column,
    test_id,
    test_case_description,
    input_selector,
    expected_accepted,
):
    """TC-7.3 using workbook-derived inputs."""
    company, input_data = _pick_input(df, sheet_column, input_selector)

    if column_name == "Annual Profits":
        accepted, message = validate_annual_profits(input_data)
    elif column_name == "Year-over-Year Growth Rate":
        accepted, message = validate_yoy_growth(input_data)
    elif column_name == "Net Promoter Score (NPS)":
        accepted, message = validate_nps(input_data)
    elif column_name == "Burn Rate":
        accepted, message = validate_burn_rate(input_data)
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

