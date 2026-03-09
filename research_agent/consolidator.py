from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

from .prompts import consolidation_prompt
from .schema import ParameterSpec
from .validation import collect_row_validation_issues, validate_rows_against_specs


INVALID_VALUES = {"", "not found", "n/a", "na", "unknown", "null", "none", "-"}


def _is_invalid(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in INVALID_VALUES


def _ac_expected_count(ac: str, value: str) -> int:
    if not value.strip():
        return 0
    if ac.strip().lower().startswith("atomic"):
        return 1
    return len([x for x in value.split(";") if x.strip()])


def _score_row(row: dict[str, Any], spec: ParameterSpec) -> tuple[int, int, int]:
    value = str(row.get("Research Output / Data", "")).strip()
    source = str(row.get("Source", "")).strip()
    if _is_invalid(value):
        return (-1, -1, -1)

    count = _ac_expected_count(spec.ac, value)
    max_len = len(value)
    source_score = 1 if source else 0
    return (count, max_len, source_score)


def consolidate_rows_for_company(raw_rows: list[dict[str, Any]], specs: list[ParameterSpec]) -> list[dict[str, Any]]:
    by_id: dict[int, list[dict[str, Any]]] = {}
    for r in raw_rows:
        rid = str(r.get("ID", "")).strip()
        if rid.isdigit():
            by_id.setdefault(int(rid), []).append(r)

    out: list[dict[str, Any]] = []
    for spec in specs:
        candidates = by_id.get(spec.sr_no, [])
        if not candidates:
            out.append(
                {
                    "ID": str(spec.sr_no),
                    "Category": spec.category,
                    "A/C": spec.ac,
                    "Parameter": spec.parameter or spec.column_name,
                    "Research Output / Data": "Not Found",
                    "Source": "",
                }
            )
            continue

        valid = [c for c in candidates if not _is_invalid(c.get("Research Output / Data"))]
        pool = valid if valid else candidates
        best = sorted(pool, key=lambda c: _score_row(c, spec), reverse=True)[0]
        out.append(
            {
                "ID": str(spec.sr_no),
                "Category": best.get("Category", spec.category),
                "A/C": best.get("A/C", spec.ac),
                "Parameter": best.get("Parameter", spec.parameter or spec.column_name),
                "Research Output / Data": best.get("Research Output / Data", ""),
                "Source": best.get("Source", ""),
            }
        )
    return out


def _rows_to_json(rows: list[dict[str, Any]]) -> str:
    headers = ["ID", "Category", "A/C", "Parameter", "Research Output / Data", "Source"]
    cleaned = [{h: r.get(h, "") for h in headers} for r in rows]
    return json.dumps({"rows": cleaned}, ensure_ascii=False)


def consolidate_rows_for_company_llm(
    raw_rows: list[dict[str, Any]],
    specs: list[ParameterSpec],
    provider: str,
    model: str | None,
) -> list[dict[str, Any]]:
    from langchain_core.messages import HumanMessage

    from .llm_provider import build_llm

    llm = build_llm(provider=provider, model=model, temperature=0.0)
    prompt = consolidation_prompt(_rows_to_json(raw_rows))
    resp = llm.invoke([HumanMessage(content=prompt)])
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json", "", 1).strip()
    try:
        parsed_payload = json.loads(content)
        rows = parsed_payload.get("rows", []) if isinstance(parsed_payload, dict) else []
    except json.JSONDecodeError:
        return consolidate_rows_for_company(raw_rows, specs)
    valid_ids = {s.sr_no for s in specs}
    parsed = [r for r in rows if isinstance(r, dict) and str(r.get("ID", "")).strip().isdigit() and int(str(r["ID"]).strip()) in valid_ids]
    if len(parsed) < len(specs):
        return consolidate_rows_for_company(raw_rows, specs)
    # enforce one per ID
    chosen: dict[int, dict[str, Any]] = {}
    for r in parsed:
        rid = int(str(r["ID"]).strip())
        if rid not in chosen:
            chosen[rid] = r
    if len(chosen) < len(specs):
        return consolidate_rows_for_company(raw_rows, specs)
    return [chosen[s.sr_no] for s in specs]


def validate_company_record(record: dict[str, Any], specs: list[ParameterSpec], strict_validation: bool = False) -> dict[str, Any]:
    rows = record.get("rows", [])
    errors: list[dict[str, Any]] = []
    pydantic_issues = validate_rows_against_specs(rows, specs)
    row_by_id = {int(str(r["ID"]).strip()): r for r in rows if str(r.get("ID", "")).strip().isdigit()}

    for spec in specs:
        chosen = row_by_id.get(spec.sr_no)
        if not chosen:
            errors.append({"sr_no": spec.sr_no, "column_name": spec.column_name, "errors": ["missing row"]})
            continue
        value = chosen.get("Research Output / Data")
        field_errors: list[str] = []
        if strict_validation:
            field_errors = spec.validate(value)
            if _is_invalid(value):
                field_errors.append("empty_or_not_found")
            if spec.ac and spec.ac.lower().startswith("atomic"):
                parts = [p for p in str(value or "").split(";") if p.strip()]
                if len(parts) > 1:
                    field_errors.append("atomic_has_multiple_values")
        if field_errors:
            errors.append({"sr_no": spec.sr_no, "column_name": spec.column_name, "errors": field_errors, "value": value})

    return {
        "company_name": record.get("company_name"),
        "generated_at": record.get("generated_at"),
        "is_valid": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "pydantic_validation": {
            "phase": "during_consolidation",
            "issue_count": len(pydantic_issues),
            "issues": pydantic_issues,
        },
        "rows": rows,
    }


def regenerate_failed_rows(
    company_name: str,
    rows: list[dict[str, Any]],
    specs: list[ParameterSpec],
    provider: str,
    model: str | None,
) -> list[dict[str, Any]]:
    from langchain_core.messages import HumanMessage

    from .collector import PROVIDER_SOURCE_LABEL
    from .llm_provider import build_llm
    from .prompts import parameter_regeneration_prompt

    issues_by_id = collect_row_validation_issues(rows, specs)
    if not issues_by_id:
        return rows
    print(
        f"[during_consolidation] company={company_name} regenerating_failed_parameters={len(issues_by_id)}",
        flush=True,
    )

    llm = build_llm(provider=provider, model=model, temperature=0.0)
    source_label = PROVIDER_SOURCE_LABEL.get(provider.lower(), provider)
    row_by_id = {
        int(str(r.get("ID", "")).strip()): r
        for r in rows
        if str(r.get("ID", "")).strip().isdigit()
    }
    spec_by_id = {s.sr_no: s for s in specs}
    for sid in sorted(issues_by_id.keys()):
        spec = spec_by_id.get(sid)
        if not spec:
            continue
        prompt = parameter_regeneration_prompt(
            company_name,
            spec,
            validation_errors=issues_by_id.get(sid, []),
        )
        resp = llm.invoke([HumanMessage(content=prompt)])
        value = resp.content if isinstance(resp.content, str) else str(resp.content)
        value = value.strip() or "Not Found"
        row_by_id[sid] = {
            "ID": str(spec.sr_no),
            "Category": spec.category or "",
            "A/C": spec.ac or "",
            "Parameter": spec.parameter or spec.column_name,
            "Research Output / Data": value,
            "Source": source_label,
        }
    return [row_by_id[s.sr_no] for s in specs if s.sr_no in row_by_id]


def consolidate_individual_jsons(
    input_dir: str | Path,
    specs: list[ParameterSpec],
    method: str = "deterministic",
    provider: str = "groq",
    model: str | None = None,
    strict_validation: bool = False,
) -> dict[str, Any]:
    p = Path(input_dir)
    files = sorted(p.glob("*.json"))
    companies: list[dict[str, Any]] = []
    total_errors = 0

    for f in files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        if method == "llm":
            consolidated_rows = consolidate_rows_for_company_llm(
                payload.get("rows", []), specs, provider=provider, model=model
            )
        else:
            consolidated_rows = consolidate_rows_for_company(payload.get("rows", []), specs)
        row_payload = {
            "company_name": payload.get("company_name"),
            "generated_at": payload.get("generated_at"),
            "rows": consolidated_rows,
        }
        consolidated_rows = regenerate_failed_rows(
            company_name=payload.get("company_name", ""),
            rows=consolidated_rows,
            specs=specs,
            provider=provider,
            model=model,
        )
        row_payload["rows"] = consolidated_rows
        validated = validate_company_record(row_payload, specs, strict_validation=strict_validation)
        total_errors += validated["error_count"]
        companies.append(validated)

    consolidated_rows = [
        {"company_name": c.get("company_name"), "rows": c.get("rows", [])}
        for c in companies
    ]

    return {
        "consolidation_method": method,
        "strict_validation": strict_validation,
        "row_count_target": len(specs),
        "record_count": len(companies),
        "total_validation_errors": total_errors,
        "consolidated_rows": consolidated_rows,
        "companies": companies,
    }


def write_consolidated(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_consolidated_csv(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    headers = ["company_name", "ID", "Category", "A/C", "Parameter", "Research Output / Data", "Source"]
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for company in payload.get("consolidated_rows", []):
            company_name = company.get("company_name", "")
            for row in company.get("rows", []):
                writer.writerow(
                    {
                        "company_name": company_name,
                        "ID": row.get("ID", ""),
                        "Category": row.get("Category", ""),
                        "A/C": row.get("A/C", ""),
                        "Parameter": row.get("Parameter", ""),
                        "Research Output / Data": row.get("Research Output / Data", ""),
                        "Source": row.get("Source", ""),
                    }
                )
    return out
