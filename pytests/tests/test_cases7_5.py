"""
TC-7.5 - Boundary Values: Date Boundaries
=========================================
Category : BOUNDARY VALUES
Test Type: Specific-Parameters
Priority : Low

Excel-driven tests for temporal/date boundaries. Inputs are selected from
Company Master.xlsx (Flat Companies Data). If a required boundary pattern
is not present in the workbook, the specific test is skipped.
"""

from pathlib import Path
from datetime import date
import re

import pandas as pd
import pytest


FILE_PATH = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"
CURRENT_YEAR = date.today().year


@pytest.fixture(scope="module")
def df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


def _extract_years(text):
    """Extract 4-digit years (1800-2199) from mixed text."""
    raw = str(text)
    out = []
    for y in re.findall(r"(?<!\d)(18\d{2}|19\d{2}|20\d{2}|21\d{2})(?!\d)", raw):
        try:
            out.append(int(y))
        except ValueError:
            continue
    return out


def _pick_input(df, column, selector):
    if column not in df.columns:
        pytest.skip(f"Column '{column}' not found in {SHEET_NAME}")

    for _, row in df[["name", column]].dropna(subset=[column]).iterrows():
        value = str(row[column]).strip()
        years = _extract_years(value)
        low = value.lower()

        if selector == "year_lt_1800" and any(y < 1800 for y in years):
            return row["name"], value

        if selector == "year_eq_2000" and any(y == 2000 for y in years):
            return row["name"], value

        if selector == "year_future" and any(y > CURRENT_YEAR for y in years):
            return row["name"], value

        if selector == "year_lt_1900" and any(y < 1900 for y in years):
            return row["name"], value

        if selector == "planned_future" and ("plan" in low or "planned" in low) and any(y > CURRENT_YEAR for y in years):
            return row["name"], value

        if selector == "acquired_historical" and "acquir" in low and any(y <= CURRENT_YEAR for y in years):
            return row["name"], value

        if selector == "roadmap_past" and any(y < CURRENT_YEAR for y in years):
            return row["name"], value

        if selector == "roadmap_future" and any(y >= CURRENT_YEAR for y in years):
            return row["name"], value

        if selector == "projection_past" and any(y <= CURRENT_YEAR for y in years):
            return row["name"], value

        if selector == "projection_future" and any(y > CURRENT_YEAR for y in years):
            return row["name"], value

    pytest.skip(f"No '{selector}' sample found in workbook for column '{column}'")


def validate_incorporation_year(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Incorporation year missing"
    year = years[0]
    if year < 1800:
        return False, "Rejected. Business rule: year must be >= 1800"
    if year > CURRENT_YEAR:
        return False, "Rejected. Incorporation year cannot be in the future"
    return True, "Accepted. Valid 4-digit historical year"


def validate_historical_date_not_too_old(value):
    """Used where future must be rejected and pre-1900 is treated invalid."""
    years = _extract_years(value)
    if not years:
        return False, "Rejected. No parseable date/year found"
    year = years[0]
    if year > CURRENT_YEAR:
        return False, "Rejected. Date must be historical"
    if year < 1900:
        return False, "Rejected. Outside acceptable historical timeframe"
    return True, "Accepted. Valid historical date"


def validate_funding_date(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Funding date missing"
    year = years[0]
    if year > CURRENT_YEAR:
        return False, "Rejected. Funding dates cannot be future-dated"
    return True, "Accepted. Valid historical funding"


def validate_layoff_history(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Layoff date missing"
    year = years[0]
    if year > CURRENT_YEAR:
        return False, "Rejected. Layoff history must be historical"
    if year < 1900:
        return False, "Rejected. Invalid or unrealistic historical record"
    return True, "Accepted. Valid historical layoff record"


def validate_event_participation(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Event year missing"
    year = years[0]
    if year > CURRENT_YEAR:
        return False, "Rejected. Field tracks completed participation only"
    return True, "Accepted. Valid historical event"


def validate_exit_strategy(value):
    low = str(value).lower()
    years = _extract_years(value)

    if "plan" in low or "planned" in low:
        if years and any(y > CURRENT_YEAR for y in years):
            return True, "Accepted. Future exit plans allowed when marked planned"

    if "acquir" in low:
        if years and any(y <= CURRENT_YEAR for y in years):
            return True, "Accepted. Valid historical exit event"

    # If it has a future year without plan language, reject.
    if years and any(y > CURRENT_YEAR for y in years):
        return False, "Rejected. Future exit event requires planned disclaimer"

    return True, "Accepted"


def validate_emergency_preparedness(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Drill date missing"
    year = years[0]
    if year > CURRENT_YEAR:
        return False, "Rejected. Completed drills cannot be future-dated"
    return True, "Accepted. Valid historical drill"


def validate_innovation_roadmap(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Roadmap date missing"
    if any(y < CURRENT_YEAR for y in years):
        return False, "Rejected. Roadmap must be future-oriented"
    if any(y >= CURRENT_YEAR for y in years):
        return True, "Accepted. Valid future roadmap"
    return False, "Rejected. Invalid roadmap timeline"


def validate_future_projections(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Projection year missing"
    if any(y <= CURRENT_YEAR for y in years):
        return False, "Rejected. Projections must reference future years"
    return True, "Accepted. Valid forward-looking projection"


def validate_case_studies(value):
    years = _extract_years(value)
    if not years:
        return False, "Rejected. Case study date missing"
    year = years[0]
    if year > CURRENT_YEAR:
        return False, "Rejected. Case studies must be historical"
    return True, "Accepted. Valid historical proof point"


TEST_CASES_7_5 = [
    ("Year of Incorporation", "incorporation_year", "TC-7.5-01", "Validate very old incorporation year below allowed minimum", "year_lt_1800", False),
    ("Year of Incorporation", "incorporation_year", "TC-7.5-02", "Validate Y2K boundary year", "year_eq_2000", True),
    ("Year of Incorporation", "incorporation_year", "TC-7.5-03", "Validate future incorporation year", "year_future", False),
    ("Recent News", "recent_news", "TC-7.5-04", "Validate future-dated news event", "year_future", False),
    ("Recent News", "recent_news", "TC-7.5-05", "Validate very old news entry", "year_lt_1900", False),
    ("Recent News", "recent_news", "TC-7.5-06", "Validate Y2K-era news entry", "year_eq_2000", True),
    ("Recent Funding Rounds", "recent_funding_rounds", "TC-7.5-07", "Validate future funding round date", "year_future", False),
    ("Recent Funding Rounds", "recent_funding_rounds", "TC-7.5-08", "Validate Y2K-era funding round", "year_eq_2000", True),
    ("Layoff History", "layoff_history", "TC-7.5-09", "Validate future layoff record", "year_future", False),
    ("Layoff History", "layoff_history", "TC-7.5-10", "Validate unrealistically old layoff record", "year_lt_1900", False),
    ("Event Participation", "event_participation", "TC-7.5-11", "Validate future event participation", "year_future", False),
    ("Event Participation", "event_participation", "TC-7.5-12", "Validate Y2K-era event participation", "year_eq_2000", True),
    ("Exit Strategy / History", "exit_strategy_history", "TC-7.5-13", "Validate future IPO plan with disclaimer", "planned_future", True),
    ("Exit Strategy / History", "exit_strategy_history", "TC-7.5-14", "Validate historical acquisition", "acquired_historical", True),
    ("Emergency Response Preparedness", "emergency_preparedness", "TC-7.5-15", "Validate future emergency drill recorded as completed", "year_future", False),
    ("Emergency Response Preparedness", "emergency_preparedness", "TC-7.5-16", "Validate Y2K-era emergency drill", "year_eq_2000", True),
    ("Innovation Roadmap", "innovation_roadmap", "TC-7.5-17", "Validate roadmap containing past milestone", "roadmap_past", False),
    ("Innovation Roadmap", "innovation_roadmap", "TC-7.5-18", "Validate roadmap with future milestone", "roadmap_future", True),
    ("Future Projections", "future_projections", "TC-7.5-19", "Validate projection using past year", "projection_past", False),
    ("Future Projections", "future_projections", "TC-7.5-20", "Validate future financial projection", "projection_future", True),
    ("Case Studies / Public Success Stories", "case_studies", "TC-7.5-21", "Validate future-dated case study", "year_future", False),
    ("Case Studies / Public Success Stories", "case_studies", "TC-7.5-22", "Validate Y2K-era case study", "year_eq_2000", True),
]


@pytest.mark.parametrize(
    "column_name, sheet_column, test_id, test_case_description, selector, expected_accepted",
    TEST_CASES_7_5,
    ids=[tc[2] for tc in TEST_CASES_7_5],
)
def test_tc_7_5_date_boundaries(
    df,
    column_name,
    sheet_column,
    test_id,
    test_case_description,
    selector,
    expected_accepted,
):
    company, input_data = _pick_input(df, sheet_column, selector)

    if column_name == "Year of Incorporation":
        accepted, message = validate_incorporation_year(input_data)
    elif column_name == "Recent News":
        accepted, message = validate_historical_date_not_too_old(input_data)
    elif column_name == "Recent Funding Rounds":
        accepted, message = validate_funding_date(input_data)
    elif column_name == "Layoff History":
        accepted, message = validate_layoff_history(input_data)
    elif column_name == "Event Participation":
        accepted, message = validate_event_participation(input_data)
    elif column_name == "Exit Strategy / History":
        accepted, message = validate_exit_strategy(input_data)
    elif column_name == "Emergency Response Preparedness":
        accepted, message = validate_emergency_preparedness(input_data)
    elif column_name == "Innovation Roadmap":
        accepted, message = validate_innovation_roadmap(input_data)
    elif column_name == "Future Projections":
        accepted, message = validate_future_projections(input_data)
    elif column_name == "Case Studies / Public Success Stories":
        accepted, message = validate_case_studies(input_data)
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

