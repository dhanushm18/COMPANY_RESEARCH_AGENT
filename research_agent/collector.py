from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from .llm_provider import build_llm
from .prompts import generation_prompt
from .schema import ParameterSpec
from .table_parser import parse_markdown_table

PROVIDER_SOURCE_LABEL = {
    "gemini": "gemini_api",
    "groq": "groq_api",
    "openai": "open_ai_api",
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

    return {
        "company_name": company_name,
        "provider": provider,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "rows": rows,
    }


def write_individual_file(output_dir: str | Path, company_name: str, payload: dict[str, Any]) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in company_name).strip("_")
    out_path = out_dir / f"{safe_name}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def combine_rows_payload(company_name: str, provider_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for p in provider_payloads:
        rows.extend(p.get("rows", []))
    return {
        "company_name": company_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "rows": rows,
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
    }
