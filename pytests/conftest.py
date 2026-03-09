from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path("pytests/data")
EXCEL_FILE = DATA_DIR / "sample_companies.xlsx"
CSV_FILE = DATA_DIR / "sample_companies.csv"
SHEET_NAME = "Flat Companies Data"


@pytest.fixture(scope="session")
def workbook_path() -> Path:
    assert EXCEL_FILE.exists(), f"Missing workbook: {EXCEL_FILE}"
    return EXCEL_FILE


@pytest.fixture(scope="session")
def csv_path() -> Path:
    assert CSV_FILE.exists(), f"Missing csv: {CSV_FILE}"
    return CSV_FILE


@pytest.fixture(scope="session")
def excel_df(workbook_path: Path):
    return pd.read_excel(workbook_path, sheet_name=SHEET_NAME)


@pytest.fixture(scope="session")
def csv_df(csv_path: Path):
    return pd.read_csv(csv_path)
