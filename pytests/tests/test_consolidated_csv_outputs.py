from __future__ import annotations

import csv
import os
from pathlib import Path


def _csv_path() -> Path:
    return Path(os.getenv("AGENT_CONSOLIDATED_CSV", "outputs/consolidated_validated.csv"))


def _schema_path() -> Path:
    return Path(os.getenv("AGENT_SCHEMA_PATH", "data/parameters.template.csv"))


def _schema_id_count(schema_path: Path) -> int:
    assert schema_path.exists(), f"Missing schema file: {schema_path}"
    text = schema_path.read_text(encoding="utf-8-sig")
    for delimiter in ("\t", ",", ";", "|"):
        reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
        keys = {k.lower().strip(): k for k in (reader.fieldnames or [])}
        id_key = keys.get("id") or keys.get("sr_no")
        if not id_key:
            for normalized, original in keys.items():
                if "id" in normalized and "sr_no" in normalized:
                    id_key = original
                    break
        if not id_key:
            continue
        ids = {
            int(str(row.get(id_key, "")).strip())
            for row in reader
            if str(row.get(id_key, "")).strip().isdigit()
        }
        if ids:
            return len(ids)
    raise AssertionError("Schema must include a parseable ID or sr_no column")


def test_consolidated_csv_exists():
    csv_path = _csv_path()
    assert csv_path.exists(), f"Missing consolidated csv: {csv_path}"


def test_consolidated_csv_has_required_columns():
    csv_path = _csv_path()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
    expected = {
        "company_name",
        "ID",
        "Category",
        "A/C",
        "Parameter",
        "Research Output / Data",
        "Source",
    }
    assert expected.issubset(headers), f"Missing columns: {sorted(expected - headers)}"


def test_consolidated_csv_has_rows_and_numeric_ids():
    csv_path = _csv_path()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows, "Consolidated csv has no data rows"
    for row in rows:
        rid = str(row.get("ID", "")).strip()
        assert rid.isdigit(), f"Non-numeric ID found: {rid}"


def test_each_company_matches_schema_row_count():
    csv_path = _csv_path()
    schema_path = _schema_path()
    expected_count = _schema_id_count(schema_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_company: dict[str, set[int]] = {}
    for row in rows:
        company = str(row.get("company_name", "")).strip()
        rid = str(row.get("ID", "")).strip()
        if company and rid.isdigit():
            by_company.setdefault(company, set()).add(int(rid))
    assert by_company, "No company rows found in consolidated csv"
    for company, ids in by_company.items():
        assert len(ids) == expected_count, (
            f"Company {company} has {len(ids)} unique IDs, expected {expected_count}"
        )


def test_each_company_has_exact_schema_id_set():
    csv_path = _csv_path()
    schema_path = _schema_path()
    assert schema_path.exists(), f"Missing schema file: {schema_path}"

    # Parse expected IDs from schema using the same dialect approach.
    text = schema_path.read_text(encoding="utf-8-sig")
    expected_ids: set[int] = set()
    for delimiter in ("\t", ",", ";", "|"):
        reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
        keys = {k.lower().strip(): k for k in (reader.fieldnames or [])}
        id_key = keys.get("id") or keys.get("sr_no")
        if not id_key:
            continue
        parsed = {
            int(str(row.get(id_key, "")).strip())
            for row in reader
            if str(row.get(id_key, "")).strip().isdigit()
        }
        if parsed:
            expected_ids = parsed
            break
    assert expected_ids, "No schema IDs parsed"

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    by_company: dict[str, set[int]] = {}
    for row in rows:
        company = str(row.get("company_name", "")).strip()
        rid = str(row.get("ID", "")).strip()
        if company and rid.isdigit():
            by_company.setdefault(company, set()).add(int(rid))

    for company, ids in by_company.items():
        assert ids == expected_ids, (
            f"Company {company} has ID mismatch: missing={sorted(expected_ids - ids)[:10]}, "
            f"extra={sorted(ids - expected_ids)[:10]}"
        )
