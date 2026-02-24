from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ParameterSpec:
    sr_no: int
    column_name: str
    category: str
    description: str
    content_type: str
    granularity: str
    minimum_element: int | None
    maximum_element: int | None
    data_owner: str
    confidence_level: str
    criticality: str
    data_volatility: str
    update_frequency: str
    data_type: str
    format_constraints: str
    regex_pattern: str
    nullability: str
    business_rules: str
    data_rules: str
    data_source: str
    validation_mode: str
    test_cases: str
    is_derived_from: str
    derivation_method: str
    ac: str
    parameter: str
    composite_min: int | None
    composite_max: int | None

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "ParameterSpec":
        normalized = {str(k).strip().lower(): v for k, v in row.items() if k is not None}

        def _pick(*keys: str, default: Any = "") -> Any:
            for k in keys:
                if k in normalized and normalized[k] not in (None, ""):
                    return normalized[k]
            return default

        def _int_or_none(v: Any) -> int | None:
            if v is None:
                return None
            s = str(v).strip()
            if not s or s.lower() in {"as needed", "na", "n/a"}:
                return None
            return int(float(s))

        sr_no = _pick("sr_no", "id")
        column_name = _pick("column_name", "parameter")
        min_element = _int_or_none(_pick("minimum_element", "composite elements - minimum", "min"))
        max_element = _int_or_none(_pick("maximum_element", "composite elements - maximum", "max"))

        granularity = str(_pick("granularity")).strip()
        ac_value = str(_pick("a/c", "ac")).strip()
        if not ac_value:
            ac_value = "Composite" if "one to many" in granularity.lower() else "Atomic"

        return cls(
            sr_no=int(str(sr_no).strip()),
            column_name=str(column_name).strip(),
            category=str(_pick("category")).strip(),
            description=str(_pick("description")).strip(),
            content_type=str(_pick("content_type", "content type to generate")).strip(),
            granularity=granularity,
            minimum_element=min_element,
            maximum_element=max_element,
            data_owner=str(_pick("data_owner")).strip(),
            confidence_level=str(_pick("confidence_level")).strip(),
            criticality=str(_pick("criticality")).strip(),
            data_volatility=str(_pick("data_volatility")).strip(),
            update_frequency=str(_pick("update_frequency")).strip(),
            data_type=str(_pick("data_type")).strip(),
            format_constraints=str(_pick("format_constraints")).strip(),
            regex_pattern=str(_pick("regex_pattern")).strip(),
            nullability=str(_pick("nullability")).strip(),
            business_rules=str(_pick("business_rules")).strip(),
            data_rules=str(_pick("data_rules")).strip(),
            data_source=str(_pick("data_source")).strip(),
            validation_mode=str(_pick("validation_mode")).strip(),
            test_cases=str(_pick("test_cases")).strip(),
            is_derived_from=str(_pick("is_dervied_from", "is_derived_from")).strip(),
            derivation_method=str(_pick("derivation_method")).strip(),
            ac=ac_value,
            parameter=str(_pick("parameter", "column_name")).strip(),
            composite_min=min_element,
            composite_max=max_element,
        )

    @property
    def required(self) -> bool:
        return "not null" in self.nullability.lower()

    def _compiled_pattern(self) -> re.Pattern[str] | None:
        raw = self.regex_pattern.strip().strip("`")
        if not raw or raw in {"[]", "N/A"}:
            return None
        try:
            return re.compile(raw)
        except re.error:
            return None

    def validate(self, value: Any) -> list[str]:
        errors: list[str] = []
        if value is None:
            if self.required:
                errors.append("missing required value")
            return errors

        s = str(value).strip()
        if self.required and not s:
            errors.append("required value is empty")
            return errors

        if self.minimum_element is not None and len(s) < self.minimum_element:
            errors.append(f"length<{self.minimum_element}")
        if self.maximum_element is not None and len(s) > self.maximum_element:
            errors.append(f"length>{self.maximum_element}")

        pattern = self._compiled_pattern()
        if pattern is not None and s and not pattern.match(s):
            errors.append("regex mismatch")

        dtype = self.data_type.upper()
        if "INTEGER" in dtype and s:
            if not re.fullmatch(r"-?\d+", s):
                errors.append("not integer")
        if "DECIMAL" in dtype and s:
            if not re.fullmatch(r"-?\d+(?:\.\d+)?", s.replace(",", "")):
                errors.append("not decimal")

        return errors


def load_parameter_specs(path: str | Path) -> list[ParameterSpec]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"schema file not found: {p}")

    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("parameters", [])
        return [ParameterSpec.from_dict(x) for x in data]

    with p.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = []
        for r in reader:
            sr = str((r.get("sr_no") if isinstance(r, dict) else "") or (r.get("ID") if isinstance(r, dict) else "")).strip()
            if not sr:
                continue
            rows.append(ParameterSpec.from_dict(r))
    return rows
