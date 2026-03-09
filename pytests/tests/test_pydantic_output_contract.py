from __future__ import annotations

from pathlib import Path

from research_agent.schema import load_parameter_specs
from research_agent.validation import collect_row_validation_issues


SCHEMA_FILE = Path("data/parameters.template.csv")


def _valid_rows_for_specs(specs):
    rows = []
    for spec in specs:
        rows.append(
            {
                "ID": str(spec.sr_no),
                "Category": spec.category or "",
                "A/C": spec.ac or "Atomic",
                "Parameter": spec.parameter or spec.column_name,
                "Research Output / Data": "sample_value",
                "Source": "unit_test_source",
            }
        )
    return rows


def test_relaxed_pydantic_accepts_project_output_row_format():
    specs = load_parameter_specs(SCHEMA_FILE)
    subset = specs[:20]
    rows = _valid_rows_for_specs(subset)
    issues = collect_row_validation_issues(rows, subset, strict=False)
    assert issues == {}, f"unexpected relaxed issues: {issues}"


def test_required_field_missing_is_reported():
    specs = load_parameter_specs(SCHEMA_FILE)
    required_spec = next(s for s in specs if s.required)
    rows = [
        {
            "ID": str(required_spec.sr_no),
            "Category": required_spec.category or "",
            "A/C": required_spec.ac or "Atomic",
            "Parameter": required_spec.parameter or required_spec.column_name,
            "Research Output / Data": "Not Found",
            "Source": "unit_test_source",
        }
    ]
    issues = collect_row_validation_issues(rows, [required_spec], strict=False)
    assert required_spec.sr_no in issues
    assert any("required value missing" in msg for msg in issues[required_spec.sr_no])
