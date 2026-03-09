import pandas as pd


def test_excel_file_exists_and_loads(workbook_path):
    assert workbook_path.exists()
    xl = pd.ExcelFile(workbook_path)
    assert "Flat Companies Data" in xl.sheet_names


def test_excel_has_expected_core_columns(excel_df):
    expected = {"name", "category", "incorporation_year", "overview_text", "website_url"}
    assert expected.issubset(set(excel_df.columns))


def test_excel_not_empty(excel_df):
    assert len(excel_df) > 0
