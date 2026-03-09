from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from .schema import ParameterSpec

MISSING_TOKENS = {
    "",
    "not found",
    "n/a",
    "na",
    "unknown",
    "null",
    "none",
    "-",
}


class ParameterSpecModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sr_no: int
    column_name: str
    ac: str
    minimum_element: int | None = None
    maximum_element: int | None = None
    regex_pattern: str = ""
    nullability: str = ""
    data_type: str = ""

    @field_validator("sr_no")
    @classmethod
    def _sr_no_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("sr_no must be > 0")
        return v

    @field_validator("column_name")
    @classmethod
    def _column_name_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("column_name is required")
        return v.strip()

    @field_validator("ac")
    @classmethod
    def _ac_allowed(cls, v: str) -> str:
        normalized = (v or "").strip().lower()
        if normalized not in {"atomic", "composite"}:
            raise ValueError("ac must be Atomic or Composite")
        return "Atomic" if normalized == "atomic" else "Composite"

    @model_validator(mode="after")
    def _min_max_valid(self) -> "ParameterSpecModel":
        if (
            self.minimum_element is not None
            and self.maximum_element is not None
            and self.minimum_element > self.maximum_element
        ):
            raise ValueError("minimum_element cannot exceed maximum_element")
        return self


class OutputRowModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ID: str
    Category: str
    A_C: str
    Parameter: str
    Research_Output_Data: str
    Source: str

    @field_validator("ID")
    @classmethod
    def _id_required(cls, v: str) -> str:
        if not str(v).strip().isdigit():
            raise ValueError("ID must be numeric")
        return str(v).strip()

    @field_validator("A_C")
    @classmethod
    def _ac_allowed(cls, v: str) -> str:
        n = (v or "").strip().lower()
        if n not in {"atomic", "composite"}:
            raise ValueError("A/C must be Atomic or Composite")
        return "Atomic" if n == "atomic" else "Composite"

    @field_validator("Parameter", "Research_Output_Data", "Source")
    @classmethod
    def _required_text(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("field cannot be empty")
        return str(v).strip()


def _extract_enum_values(regex_pattern: str) -> list[str]:
    raw = (regex_pattern or "").strip().strip("`")
    # strict enum pattern only, e.g. ^(A|B|C)$
    m = re.fullmatch(r"^\^\(([^)]+)\)\$$", raw)
    if not m:
        return []
    return [x.strip() for x in m.group(1).split("|") if x.strip()]


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in MISSING_TOKENS


def validate_schema_specs(specs: list[ParameterSpec]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[int] = set()
    seen_cols: set[str] = set()

    for s in specs:
        try:
            ParameterSpecModel.model_validate(
                {
                    "sr_no": s.sr_no,
                    "column_name": s.column_name,
                    "ac": s.ac,
                    "minimum_element": s.minimum_element,
                    "maximum_element": s.maximum_element,
                    "regex_pattern": s.regex_pattern,
                    "nullability": s.nullability,
                    "data_type": s.data_type,
                }
            )
        except ValidationError as e:
            issues.append(f"schema row {s.sr_no}: {e.errors()[0]['msg']}")

        if s.sr_no in seen_ids:
            issues.append(f"duplicate sr_no: {s.sr_no}")
        seen_ids.add(s.sr_no)

        key = s.column_name.strip().lower()
        if key in seen_cols:
            issues.append(f"duplicate column_name: {s.column_name}")
        seen_cols.add(key)

    return issues


def validate_rows_against_specs(
    rows: list[dict[str, Any]],
    specs: list[ParameterSpec],
    strict: bool = False,
) -> list[str]:
    details = collect_row_validation_issues(rows, specs, strict=strict)
    issues: list[str] = []
    for sid, errs in sorted(details.items()):
        for err in errs:
            issues.append(f"ID {sid}: {err}")
    return issues


def collect_row_validation_issues(
    rows: list[dict[str, Any]],
    specs: list[ParameterSpec],
    strict: bool = False,
) -> dict[int, list[str]]:
    by_id: dict[int, list[str]] = {}
    spec_by_id = {s.sr_no: s for s in specs}
    row_by_id: dict[int, dict[str, Any]] = {}

    for idx, row in enumerate(rows, start=1):
        mapped = {
            "ID": row.get("ID", ""),
            "Category": row.get("Category", ""),
            "A_C": row.get("A/C", ""),
            "Parameter": row.get("Parameter", ""),
            "Research_Output_Data": row.get("Research Output / Data", ""),
            "Source": row.get("Source", ""),
        }
        try:
            parsed = OutputRowModel.model_validate(mapped)
        except ValidationError as e:
            rid = str(row.get("ID", "")).strip()
            if rid.isdigit():
                by_id.setdefault(int(rid), []).append(f"row#{idx}: {e.errors()[0]['msg']}")
            continue

        sid = int(parsed.ID)
        spec = spec_by_id.get(sid)
        if not spec:
            by_id.setdefault(sid, []).append(f"row#{idx}: unknown ID")
            continue

        if sid in row_by_id:
            by_id.setdefault(sid, []).append("duplicate row for ID")
            continue

        normalized_row = {
            "ID": parsed.ID,
            "Category": parsed.Category,
            "A/C": parsed.A_C,
            "Parameter": parsed.Parameter,
            "Research Output / Data": parsed.Research_Output_Data,
            "Source": parsed.Source,
        }
        row_by_id[sid] = normalized_row

        if strict:
            field_errors = spec.validate(parsed.Research_Output_Data)
            for ferr in field_errors:
                by_id.setdefault(sid, []).append(ferr)

            enum_values = _extract_enum_values(spec.regex_pattern)
            if enum_values and not _is_missing(parsed.Research_Output_Data):
                if (spec.ac or "").strip().lower() == "composite":
                    parts = [p.strip() for p in parsed.Research_Output_Data.split(";") if p.strip()]
                    for p in parts:
                        if p not in enum_values:
                            by_id.setdefault(sid, []).append(f"'{p}' not in enum {enum_values}")
                else:
                    if parsed.Research_Output_Data not in enum_values:
                        by_id.setdefault(sid, []).append(
                            f"'{parsed.Research_Output_Data}' not in enum {enum_values}"
                        )

    for s in specs:
        row = row_by_id.get(s.sr_no)
        if not row:
            by_id.setdefault(s.sr_no, []).append("missing row")
            continue
        value = str(row.get("Research Output / Data", "")).strip()
        if s.required and _is_missing(value):
            by_id.setdefault(s.sr_no, []).append("required value missing")

    return by_id
