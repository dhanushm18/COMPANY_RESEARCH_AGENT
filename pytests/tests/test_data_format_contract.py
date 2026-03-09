from __future__ import annotations

import csv
from pathlib import Path

from research_agent.schema import load_parameter_specs
from research_agent.validation import validate_schema_specs


SCHEMA_FILE = Path("data/parameters.template.csv")
SAMPLE_CSV = Path("pytests/data/sample_companies.csv")
CONSOLIDATED_CSV = Path("outputs/consolidated_validated.csv")


def _read_csv_headers(path: Path) -> list[str]:
    assert path.exists(), f"Missing csv: {path}"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def test_schema_contract_is_valid():
    specs = load_parameter_specs(SCHEMA_FILE)
    assert specs, "schema has no rows"
    issues = validate_schema_specs(specs)
    assert not issues, f"schema validation issues: {issues[:10]}"


def test_sample_companies_csv_has_expected_contract_columns():
    headers = set(_read_csv_headers(SAMPLE_CSV))
    expected = {
        "name",
        "short_name",
        "category",
        "incorporation_year",
        "overview_text",
        "website_url",
    }
    assert expected.issubset(headers), f"missing sample csv columns: {sorted(expected - headers)}"


def test_consolidated_csv_contract_columns():
    headers = set(_read_csv_headers(CONSOLIDATED_CSV))
    expected = {
        "company_name",
        "ID",
        "Category",
        "A/C",
        "Parameter",
        "Research Output / Data",
        "Source",
    }
    assert expected.issubset(headers), f"missing consolidated csv columns: {sorted(expected - headers)}"
