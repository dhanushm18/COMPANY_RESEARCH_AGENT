from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from .llm_provider import build_llm
from .prompts import generation_prompt, parameter_regeneration_prompt
from .schema import ParameterSpec
from .table_parser import parse_markdown_table
from .validation import collect_row_validation_issues, validate_rows_against_specs

PROVIDER_SOURCE_LABEL = {
    "baseten": "baseten_api",
    "gemini": "gemini_api",
    "groq": "groq_api",
}


def collect_company_data(
    company_name: str,
    specs: list[ParameterSpec],
    provider: str,
    model: str | None,
) -> dict[str, Any]:
    llm = build_llm(provider=provider, model=model, temperature=0.0)
    prompt = generation_prompt(company_name=company_name, specs=specs)
    resp = llm.invoke([HumanMessage(content=prompt)])
    markdown_table = resp.content if isinstance(resp.content, str) else str(resp.content)
    rows = parse_markdown_table(markdown_table)
    source_label = PROVIDER_SOURCE_LABEL.get(provider.lower(), provider)
    for r in rows:
        r["Source"] = source_label
    expected_ids = {s.sr_no for s in specs}
    rows = [r for r in rows if str(r.get("ID", "")).strip().isdigit() and int(str(r["ID"]).strip()) in expected_ids]
    row_issues_by_id = collect_row_validation_issues(rows, specs)

    # Regenerate only failed parameters
    if row_issues_by_id:
        print(
            f"[after_generation] provider={provider} regenerating_failed_parameters={len(row_issues_by_id)}",
            flush=True,
        )
        row_by_id = {
            int(str(r.get("ID", "")).strip()): r
            for r in rows
            if str(r.get("ID", "")).strip().isdigit()
        }
        spec_by_id = {s.sr_no: s for s in specs}
        for sid in sorted(row_issues_by_id.keys()):
            spec = spec_by_id.get(sid)
            if not spec:
                continue
            regen_value = _regenerate_parameter_value(
                llm,
                company_name,
                spec,
                row_issues_by_id.get(sid, []),
            )
            row_by_id[sid] = {
                "ID": str(spec.sr_no),
                "Category": spec.category or "",
                "A/C": spec.ac or "",
                "Parameter": spec.parameter or spec.column_name,
                "Research Output / Data": regen_value,
                "Source": source_label,
            }
        rows = [row_by_id[s.sr_no] for s in specs if s.sr_no in row_by_id]

    row_issues = validate_rows_against_specs(rows, specs)

    return {
        "company_name": company_name,
        "provider": provider,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "rows": rows,
        "validation": {
            "phase": "after_generation",
            "issue_count": len(row_issues),
            "issues": row_issues,
        },
    }


def _regenerate_parameter_value(
    llm: Any,
    company_name: str,
    spec: ParameterSpec,
    validation_errors: list[str] | None = None,
) -> str:
    prompt = parameter_regeneration_prompt(company_name, spec, validation_errors=validation_errors)
    resp = llm.invoke([HumanMessage(content=prompt)])
    value = resp.content if isinstance(resp.content, str) else str(resp.content)
    value = value.strip()
    if value.startswith("```"):
        value = value.strip("`")
        value = value.replace("text", "", 1).replace("json", "", 1).strip()
    return value or "Not Found"


def regenerate_specific_parameters(
    company_name: str,
    rows: list[dict[str, Any]],
    specs: list[ParameterSpec],
    provider: str,
    model: str | None,
    failed_ids: list[int],
) -> list[dict[str, Any]]:
    if not failed_ids:
        return rows

    llm = build_llm(provider=provider, model=model, temperature=0.0)
    source_label = PROVIDER_SOURCE_LABEL.get(provider.lower(), provider)
    spec_by_id = {s.sr_no: s for s in specs}
    row_by_id = {
        int(str(r.get("ID", "")).strip()): r
        for r in rows
        if str(r.get("ID", "")).strip().isdigit()
    }
    current_issues = collect_row_validation_issues(rows, specs)

    for sid in sorted(set(failed_ids)):
        spec = spec_by_id.get(sid)
        if not spec:
            continue
        regen_value = _regenerate_parameter_value(
            llm,
            company_name,
            spec,
            current_issues.get(sid, []),
        )
        row_by_id[sid] = {
            "ID": str(spec.sr_no),
            "Category": spec.category or "",
            "A/C": spec.ac or "",
            "Parameter": spec.parameter or spec.column_name,
            "Research Output / Data": regen_value,
            "Source": source_label,
        }

    return [row_by_id[s.sr_no] for s in specs if s.sr_no in row_by_id]


def write_individual_file(output_dir: str | Path, company_name: str, payload: dict[str, Any]) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in company_name).strip("_")
    out_path = out_dir / f"{safe_name}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def combine_rows_payload(company_name: str, provider_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    validation_issues: list[str] = []
    for p in provider_payloads:
        rows.extend(p.get("rows", []))
        validation_issues.extend((p.get("validation", {}) or {}).get("issues", []))
    return {
        "company_name": company_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "rows": rows,
        "validation": {
            "phase": "after_generation",
            "issue_count": len(validation_issues),
            "issues": validation_issues,
        },
    }


def build_failed_provider_payload(company_name: str, specs: list[ParameterSpec], provider: str, error: str) -> dict[str, Any]:
    source_label = PROVIDER_SOURCE_LABEL.get(provider.lower(), provider)
    rows = [
        {
            "ID": str(s.sr_no),
            "Category": s.category or "",
            "A/C": s.ac or "",
            "Parameter": s.parameter or s.column_name,
            "Research Output / Data": "Not Found",
            "Source": source_label,
        }
        for s in specs
    ]
    return {
        "company_name": company_name,
        "provider": provider,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "rows": rows,
        "error": error,
        "validation": {
            "phase": "after_generation",
            "issue_count": 1,
            "issues": [f"provider_error: {error}"],
        },
    }
