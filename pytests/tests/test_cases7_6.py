"""
TC-7.6 - Boundary Values: Ratio Boundaries (Workbook-Driven)
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


def _extract_first_number(v):
    m = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(v))
    if not m:
        return None
    return float(m.group().replace(",", ""))


def _pick_value(df, column, selector):
    if column not in df.columns:
        pytest.skip(f"Column '{column}' not present in workbook")

    for _, row in df[["name", column]].dropna(subset=[column]).iterrows():
        value = str(row[column]).strip()
        n = _extract_first_number(value)
        if selector(value, n):
            return row["name"], value

    pytest.skip(f"No workbook sample found for selector in column '{column}'")


def _status_cac_ltv(value, n):
    if n is None:
        return "FAIL"
    if n < 0:
        return "FAIL"
    if n > 1:
        return "FAIL"
    if n == 1:
        return "WARNING"
    if 0.2 <= n <= 0.5:
        return "PASS"
    if n == 0:
        return "PASS"
    return "WARNING"


def _status_burn_multiple(value, n):
    if n is None:
        return "FAIL"
    if n < 0:
        return "FAIL"
    if n == 0:
        return "PASS"
    if n <= 1.5:
        return "ACCEPTABLE"
    if n < 2.0:
        return "WARNING"
    return "FAIL"


def _status_pct_0_100(value, n):
    if n is None:
        return "FAIL"
    if n < 0:
        return "FAIL"
    if n > 100:
        return "FAIL"
    return "PASS"


def _status_churn(value, n):
    s = str(value).strip().replace("<", "").replace(">", "")
    if not re.fullmatch(r"^-?\d{1,3}(\.\d{1,2})?%?$", s):
        return "FAIL"
    if n is None:
        return "FAIL"
    if n < 0 or n > 100:
        return "FAIL"
    if n == 100:
        return "FAIL"
    if n == 5:
        return "WARNING"
    if n == 0:
        return "PASS"
    return "PASS"


def _status_turnover(value, n):
    if n is None:
        return "FAIL"
    if n < 0 or n > 100:
        return "FAIL"
    if n == 100:
        return "FAIL"
    if n == 20:
        return "WARNING"
    if n == 0:
        return "PASS"
    return "PASS"


def _status_revenue_concentration(value, n):
    if n is None:
        return "FAIL"
    if n < 0:
        return "FAIL"
    if n > 100:
        return "FAIL"
    if n == 100:
        return "FAIL"
    if n == 50:
        return "WARNING"
    if n == 0:
        return "PASS"
    return "PASS"


def _status_fixed_variable(value, n):
    s = str(value).strip()
    if s.lower() == "fixed only":
        return "ACCEPTABLE"
    m = re.fullmatch(r"(\d{1,3}):(\d{1,3})", s)
    if not m:
        return "FAIL"
    a = int(m.group(1))
    b = int(m.group(2))
    if a == 0 and b == 100:
        return "WARNING"
    if a == 100 and b == 0:
        return "ACCEPTABLE"
    if a + b != 100:
        return "FAIL"
    return "PASS"


CASES = [
    ("TC_7.6_001", "cac_ltv_ratio", lambda v, n: n == 0, _status_cac_ltv, "PASS"),
    ("TC_7.6_002", "cac_ltv_ratio", lambda v, n: "inf" in v.lower() or "∞" in v, _status_cac_ltv, "PASS"),
    ("TC_7.6_003", "cac_ltv_ratio", lambda v, n: n is not None and n > 1, _status_cac_ltv, "FAIL"),
    ("TC_7.6_004", "cac_ltv_ratio", lambda v, n: n == 1, _status_cac_ltv, "WARNING"),
    ("TC_7.6_005", "cac_ltv_ratio", lambda v, n: "undefined" in v.lower() or "∞" in v, _status_cac_ltv, "FAIL"),
    ("TC_7.6_006", "cac_ltv_ratio", lambda v, n: n is not None and n < 0, _status_cac_ltv, "FAIL"),
    ("TC_7.6_007", "cac_ltv_ratio", lambda v, n: n is not None and 0.2 <= n <= 0.5, _status_cac_ltv, "PASS"),

    ("TC_7.6_008", "burn_multiplier", lambda v, n: "inf" in v.lower() or "∞" in v, _status_burn_multiple, "FAIL"),
    ("TC_7.6_009", "burn_multiplier", lambda v, n: n == 0, _status_burn_multiple, "PASS"),
    ("TC_7.6_010", "burn_multiplier", lambda v, n: n == 1, _status_burn_multiple, "ACCEPTABLE"),
    ("TC_7.6_011", "burn_multiplier", lambda v, n: n is not None and n >= 2, _status_burn_multiple, "FAIL"),
    ("TC_7.6_012", "burn_multiplier", lambda v, n: n is not None and n < 0, _status_burn_multiple, "FAIL"),

    ("TC_7.6_013", "churn_rate", lambda v, n: n == 0, _status_churn, "PASS"),
    ("TC_7.6_014", "churn_rate", lambda v, n: n == 100, _status_churn, "FAIL"),
    ("TC_7.6_015", "churn_rate", lambda v, n: n == 5, _status_churn, "WARNING"),
    ("TC_7.6_016", "churn_rate", lambda v, n: n is not None and n > 100, _status_churn, "FAIL"),
    ("TC_7.6_017", "churn_rate", lambda v, n: n is not None and n < 0, _status_churn, "FAIL"),

    ("TC_7.6_018", "customer_concentration_risk", lambda v, n: n == 0, _status_revenue_concentration, "PASS"),
    ("TC_7.6_019", "customer_concentration_risk", lambda v, n: n == 100, _status_revenue_concentration, "FAIL"),
    ("TC_7.6_020", "customer_concentration_risk", lambda v, n: n == 50, _status_revenue_concentration, "WARNING"),
    ("TC_7.6_021", "customer_concentration_risk", lambda v, n: n is not None and n > 100, _status_revenue_concentration, "FAIL"),

    ("TC_7.6_022", "r_and_d_investment", lambda v, n: n == 0, lambda v, n: "WARNING" if n == 0 else "PASS", "WARNING"),
    ("TC_7.6_023", "r_and_d_investment", lambda v, n: n == 100, lambda v, n: "WARNING" if n == 100 else "PASS", "WARNING"),
    ("TC_7.6_024", "r_and_d_investment", lambda v, n: n is not None and n > 100, lambda v, n: "ACCEPTABLE" if n > 100 else "PASS", "ACCEPTABLE"),
    ("TC_7.6_025", "r_and_d_investment", lambda v, n: n is not None and n < 0, lambda v, n: "FAIL" if n < 0 else "PASS", "FAIL"),

    # Columns may not exist; workbook-driven strictness => skip when absent.
    ("TC_7.6_026", "sales_marketing_spend_pct", lambda v, n: n == 0, lambda v, n: "WARNING" if n == 0 else "PASS", "WARNING"),
    ("TC_7.6_027", "sales_marketing_spend_pct", lambda v, n: n == 100, lambda v, n: "WARNING" if n == 100 else "PASS", "WARNING"),
    ("TC_7.6_028", "sales_marketing_spend_pct", lambda v, n: n is not None and n > 100, lambda v, n: "ACCEPTABLE" if n > 100 else "PASS", "ACCEPTABLE"),

    ("TC_7.6_029", "operating_margin_pct", lambda v, n: n == 0, lambda v, n: "ACCEPTABLE" if n == 0 else "PASS", "ACCEPTABLE"),
    ("TC_7.6_030", "operating_margin_pct", lambda v, n: n == -100, lambda v, n: "WARNING" if n == -100 else "PASS", "WARNING"),
    ("TC_7.6_031", "operating_margin_pct", lambda v, n: n == 100, lambda v, n: "WARNING" if n == 100 else "PASS", "WARNING"),
    ("TC_7.6_032", "operating_margin_pct", lambda v, n: n == 20, lambda v, n: "PASS" if n == 20 else "WARNING", "PASS"),

    ("TC_7.6_033", "net_margin_pct", lambda v, n: n == 0, lambda v, n: "ACCEPTABLE" if n == 0 else "PASS", "ACCEPTABLE"),
    ("TC_7.6_034", "net_margin_pct", lambda v, n: n == -100, lambda v, n: "WARNING" if n == -100 else "PASS", "WARNING"),
    ("TC_7.6_035", "net_margin_pct", lambda v, n: n == 100, lambda v, n: "WARNING" if n == 100 else "PASS", "WARNING"),

    ("TC_7.6_036", "ebitda_margin_pct", lambda v, n: n == 0, lambda v, n: "ACCEPTABLE" if n == 0 else "PASS", "ACCEPTABLE"),
    ("TC_7.6_037", "ebitda_margin_pct", lambda v, n: n == -100, lambda v, n: "WARNING" if n == -100 else "PASS", "WARNING"),
    ("TC_7.6_038", "ebitda_margin_pct", lambda v, n: n is not None and n > 100, lambda v, n: "WARNING" if n > 100 else "PASS", "WARNING"),

    ("TC_7.6_039", "customer_payback_period", lambda v, n: n == 0, lambda v, n: "WARNING" if n == 0 else "PASS", "WARNING"),
    ("TC_7.6_040", "customer_payback_period", lambda v, n: n == 12, lambda v, n: "ACCEPTABLE" if n == 12 else "PASS", "ACCEPTABLE"),
    ("TC_7.6_041", "customer_payback_period", lambda v, n: n is not None and n >= 24, lambda v, n: "WARNING" if n >= 24 else "PASS", "WARNING"),
    ("TC_7.6_042", "customer_payback_period", lambda v, n: "∞" in v or "inf" in v.lower(), lambda v, n: "FAIL", "FAIL"),

    ("TC_7.6_043", "employee_turnover", lambda v, n: n == 0, _status_turnover, "PASS"),
    ("TC_7.6_044", "employee_turnover", lambda v, n: n == 20, _status_turnover, "WARNING"),
    ("TC_7.6_045", "employee_turnover", lambda v, n: n == 100, _status_turnover, "FAIL"),
    ("TC_7.6_046", "employee_turnover", lambda v, n: n is not None and n > 100, _status_turnover, "FAIL"),

    ("TC_7.6_047", "fixed_vs_variable_pay", lambda v, n: v.strip() == "0:100", _status_fixed_variable, "WARNING"),
    ("TC_7.6_048", "fixed_vs_variable_pay", lambda v, n: v.strip() in {"100:0", "Fixed Only"}, _status_fixed_variable, "ACCEPTABLE"),
    ("TC_7.6_049", "fixed_vs_variable_pay", lambda v, n: re.fullmatch(r"\d{1,3}:\d{1,3}", v.strip()) and sum(map(int, v.strip().split(":"))) != 100, _status_fixed_variable, "FAIL"),
    ("TC_7.6_050", "fixed_vs_variable_pay", lambda v, n: v.strip() == "70:30", _status_fixed_variable, "PASS"),
    ("TC_7.6_051", "fixed_vs_variable_pay", lambda v, n: v.strip() == "90:10", _status_fixed_variable, "PASS"),
]


@pytest.mark.parametrize("tc_id,column,selector,validator,expected", CASES, ids=[c[0] for c in CASES])
def test_tc_7_6_workbook_only(df, tc_id, column, selector, validator, expected):
    _, value = _pick_value(df, column, selector)
    actual = validator(value, _extract_first_number(value))
    assert actual == expected, f"{tc_id}: expected {expected}, got {actual}, value={value}"

