from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .schema import load_parameter_specs

MISSING = {"", "not found", "n/a", "na", "null", "none", "-", "unknown"}
DEFAULT_SHEET = "Flat Companies Data"


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in MISSING


def _clean_value(column: str, value: Any) -> str:
    if _is_missing(value):
        return ""
    s = str(value).strip()

    if column.endswith("_url") and s and not s.startswith(("http://", "https://")):
        return "https://" + s.lstrip("/")
    if "email" in column and s and "@" not in s:
        return "info@example.com"
    if column in {"incorporation_year"}:
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits[:4] if len(digits) >= 4 else s
    return s


def _load_consolidated_rows(consolidated_csv: Path) -> list[dict[str, str]]:
    if not consolidated_csv.exists():
        raise FileNotFoundError(f"Missing consolidated csv: {consolidated_csv}")
    with consolidated_csv.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def prepare_flat_companies_from_consolidated(
    schema_path: str | Path,
    consolidated_csv: str | Path,
    out_csv: str | Path,
    out_xlsx: str | Path,
    sheet_name: str = DEFAULT_SHEET,
    tc63_company_name: str | None = None,
) -> dict[str, Any]:
    specs = load_parameter_specs(schema_path)
    spec_by_id = {s.sr_no: s for s in specs}
    consolidated_rows = _load_consolidated_rows(Path(consolidated_csv))

    grouped: dict[str, dict[str, str]] = {}
    for r in consolidated_rows:
        company_name = str(r.get("company_name", "")).strip()
        rid = str(r.get("ID", "")).strip()
        value = r.get("Research Output / Data", "")
        if not company_name or not rid.isdigit():
            continue
        spec = spec_by_id.get(int(rid))
        if not spec:
            continue
        grouped.setdefault(company_name, {})[spec.column_name] = _clean_value(spec.column_name, value)

    if not grouped:
        raise AssertionError("No valid company rows parsed from consolidated csv")

    # Optional remap if caller wants a specific company label for a test selector.
    if tc63_company_name:
        first_original_name = next(iter(grouped.keys()))
        grouped[tc63_company_name] = grouped.pop(first_original_name)

    records: list[dict[str, str]] = []
    all_columns = {s.column_name for s in specs}
    for company_name, values in grouped.items():
        row = {c: values.get(c, "") for c in all_columns}
        if not row.get("name", "").strip():
            row["name"] = company_name
        records.append(row)

    ordered = [
        "name",
        "short_name",
        "category",
        "incorporation_year",
        "overview_text",
        "website_url",
    ] + sorted(c for c in all_columns if c not in {"name", "short_name", "category", "incorporation_year", "overview_text", "website_url"})

    out_csv_path = Path(out_csv)
    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with out_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered)
        writer.writeheader()
        writer.writerows(records)

    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "pandas + openpyxl are required to write sample_companies.xlsx. "
            "Install with: pip install pandas openpyxl"
        ) from exc

    out_xlsx_path = Path(out_xlsx)
    out_xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records, columns=ordered).to_excel(
        out_xlsx_path,
        sheet_name=sheet_name,
        index=False,
    )

    return {
        "companies": len(records),
        "columns": len(ordered),
        "csv_path": str(out_csv_path),
        "xlsx_path": str(out_xlsx_path),
    }
