from __future__ import annotations

import argparse
import csv
from pathlib import Path

from research_agent.db_push_export import (
    STAGING_EXPORT_COLUMNS,
    write_ready_for_db_csv,
    write_ready_for_db_json,
)


def _read_dict_csv_with_fallback(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    encodings = ["utf-8-sig", "cp1252", "latin-1"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
            return fieldnames, rows
        except UnicodeDecodeError as exc:
            last_err = exc
            continue
    raise RuntimeError(f"Unable to decode CSV with supported encodings: {path}") from last_err


def build_records_from_wide_csv(input_csv: Path, company_id_start: int = 1) -> list[dict[str, str | int]]:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    fieldnames, source_rows = _read_dict_csv_with_fallback(input_csv)

    data_columns = [c for c in STAGING_EXPORT_COLUMNS if c != "company_id"]
    by_position = list(zip(data_columns, fieldnames))

    records: list[dict[str, str | int]] = []
    for idx, source in enumerate(source_rows, start=company_id_start):
        rec: dict[str, str | int] = {c: "" for c in STAGING_EXPORT_COLUMNS}
        rec["company_id"] = idx

        for target_col, source_col in by_position:
            rec[target_col] = (source.get(source_col, "") or "").strip()

        if not rec.get("name") and fieldnames:
            rec["name"] = (source.get(fieldnames[0], "") or "").strip()
        records.append(rec)

    return records


def main() -> int:
    p = argparse.ArgumentParser(description="Create DB-ready files from outputs/consolidated.csv")
    p.add_argument("--input-csv", default="outputs/consolidated.csv")
    p.add_argument("--output-csv", default="outputs/ready_for_db_push.csv")
    p.add_argument("--output-json", default="outputs/ready_for_db_push.json")
    p.add_argument("--company-id-start", type=int, default=1)
    args = p.parse_args()

    input_csv = Path(args.input_csv)
    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)

    records = build_records_from_wide_csv(input_csv, company_id_start=args.company_id_start)
    out_csv = write_ready_for_db_csv(output_csv, records)
    out_json = write_ready_for_db_json(output_json, records)

    print(f"input_csv={input_csv}")
    print(f"ready_db_csv={out_csv}")
    print(f"ready_db_json={out_json}")
    print(f"records={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
