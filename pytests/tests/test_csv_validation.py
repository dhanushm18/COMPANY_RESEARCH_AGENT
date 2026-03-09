
def test_csv_file_exists_and_loads(csv_path, csv_df):
    assert csv_path.exists()
    assert len(csv_df) > 0


def test_csv_has_expected_core_columns(csv_df):
    expected = {"name", "category", "incorporation_year", "overview_text", "website_url"}
    assert expected.issubset(set(csv_df.columns))


def test_csv_excel_row_count_consistency(csv_df, excel_df):
    assert len(csv_df) == len(excel_df)
