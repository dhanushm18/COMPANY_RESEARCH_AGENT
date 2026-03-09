from __future__ import annotations

import csv
from pathlib import Path

from research_agent.schema import load_parameter_specs
from research_agent.validation import collect_row_validation_issues, validate_schema_specs


SCHEMA_FILE = Path("data/parameters.template.csv")
CSV_FILE = Path("pytests/data/sample_companies.csv")


def _first_company_row() -> dict[str, str]:
    assert CSV_FILE.exists(), f"Missing csv: {CSV_FILE}"
    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader, None)
    assert row is not None, "sample_companies.csv has no rows"
    return {str(k): str(v or "") for k, v in row.items()}


def _rows_from_company_sample(specs):
    src = _first_company_row()
    source = "sample_csv"
    mapping = {
        "Company Name": "name",
        "Short Name": "short_name",
        "Logo": "logo_url",
        "Category": "category",
        "Year of Incorporation": "incorporation_year",
        "Overview of the Company": "overview_text",
        "Nature of Company": "nature_of_company",
        "Company Headquarters": "headquarters_address",
        "Countries Operating In": "operating_countries",
        "Number of Offices (beyond HQ)": "office_count",
        "Office Locations": "office_locations",
        "Employee Size": "employee_size",
    }
    rows = []
    for spec in specs:
        sample_key = mapping.get(spec.column_name)
        if not sample_key:
            continue
        rows.append(
            {
                "ID": str(spec.sr_no),
                "Category": spec.category,
                "A/C": spec.ac,
                "Parameter": spec.column_name,
                "Research Output / Data": src.get(sample_key, ""),
                "Source": source,
            }
        )
    return rows


def test_schema_template_passes_pydantic_checks():
    specs = load_parameter_specs(SCHEMA_FILE)
    issues = validate_schema_specs(specs)
    assert not issues, f"schema validation issues found: {issues[:5]}"


def test_row_validation_accepts_real_data_in_relaxed_mode():
    specs = load_parameter_specs(SCHEMA_FILE)
    subset = [s for s in specs if s.sr_no <= 12]
    rows = _rows_from_company_sample(subset)
    issues = collect_row_validation_issues(rows, subset, strict=False)
    assert issues == {}, f"unexpected relaxed-mode issues: {issues}"


def test_row_validation_flags_bad_required_value_in_strict_mode():
    specs = load_parameter_specs(SCHEMA_FILE)
    target = next(s for s in specs if s.sr_no == 5)
    rows = [
        {
            "ID": str(target.sr_no),
            "Category": target.category,
            "A/C": target.ac,
            "Parameter": target.column_name,
            "Research Output / Data": "abcd",
            "Source": "unit_test",
        }
    ]
    issues = collect_row_validation_issues(rows, [target], strict=True)
    assert target.sr_no in issues
    assert any("regex mismatch" in x or "not integer" in x for x in issues[target.sr_no])
