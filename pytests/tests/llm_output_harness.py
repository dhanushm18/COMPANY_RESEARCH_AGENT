from __future__ import annotations

import csv
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from research_agent.collector import (
    collect_company_data,
    combine_rows_payload,
    regenerate_specific_parameters,
    write_individual_file,
)
from research_agent.consolidator import (
    consolidate_individual_jsons,
    write_consolidated,
    write_consolidated_csv,
)
from research_agent.schema import load_parameter_specs
from research_agent.validation import collect_row_validation_issues, validate_schema_specs

SCHEMA_PATH = Path("data/parameters.template.csv")
COMPANIES_PATH = Path("data/companies.json")
OUTPUT_DIR = Path("outputs/individual_json")
CONSOLIDATED_JSON = Path("outputs/consolidated_validated.json")
CONSOLIDATED_CSV = Path("outputs/consolidated_validated.csv")


def _has_provider_key(provider: str) -> bool:
    p = provider.lower().strip()
    if p == "groq":
        return bool(os.getenv("GROQ_API_KEY"))
    if p == "gemini":
        return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if p == "baseten":
        return bool(os.getenv("BASETEN_API_KEY") or os.getenv("BASETEN_API"))
    return False


def _requested_providers() -> list[str]:
    raw = os.getenv("AGENT_PROVIDERS", "groq,gemini,baseten")
    providers = [p.strip().lower() for p in raw.split(",") if p.strip()]
    return [p for p in providers if _has_provider_key(p)]


def _load_first_company_name() -> str:
    payload = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
    companies = payload if isinstance(payload, list) else payload.get("companies", [])
    if not companies:
        raise AssertionError(f"No companies found in {COMPANIES_PATH}")
    first = companies[0]
    name = str(first.get("company_name", "")).strip()
    if not name:
        raise AssertionError("First company row has empty company_name")
    return name


@lru_cache(maxsize=1)
def run_llm_pipeline_for_tests() -> dict[str, Any]:
    specs = load_parameter_specs(SCHEMA_PATH)
    schema_issues = validate_schema_specs(specs)
    assert not schema_issues, f"Schema invalid: {schema_issues[:5]}"

    providers = _requested_providers()
    if not providers:
        pytest.skip("No LLM provider keys found. Set GROQ_API_KEY/GEMINI_API_KEY/BASETEN_API_KEY.")

    company_name = _load_first_company_name()

    provider_payloads: list[dict[str, Any]] = []
    for provider in providers:
        try:
            payload = collect_company_data(company_name, specs, provider=provider, model=None)
        except Exception as exc:
            pytest.skip(f"LLM generation unavailable for provider={provider}: {exc}")
        provider_payloads.append(payload)
        write_individual_file(OUTPUT_DIR / "provider_json", f"{company_name}__{provider}", payload)

    merged = combine_rows_payload(company_name, provider_payloads)

    rows = merged.get("rows", [])
    initial_issues = collect_row_validation_issues(rows, specs, strict=False)

    regen_provider = os.getenv("AGENT_REGEN_PROVIDER", providers[0])
    attempts = 0
    while initial_issues and attempts < 3:
        attempts += 1
        failed_ids = sorted(initial_issues.keys())
        rows = regenerate_specific_parameters(
            company_name=company_name,
            rows=rows,
            specs=specs,
            provider=regen_provider,
            model=None,
            failed_ids=failed_ids,
        )
        initial_issues = collect_row_validation_issues(rows, specs, strict=False)

    merged["rows"] = rows
    merged["row_count"] = len(rows)
    write_individual_file(OUTPUT_DIR, company_name, merged)

    consolidated = consolidate_individual_jsons(
        OUTPUT_DIR,
        specs,
        method="deterministic",
        provider=regen_provider,
        model=None,
        strict_validation=False,
    )
    if consolidated.get("total_validation_errors", 0) > 0:
        consolidated = consolidate_individual_jsons(
            OUTPUT_DIR,
            specs,
            method="llm",
            provider=regen_provider,
            model=None,
            strict_validation=False,
        )

    write_consolidated(CONSOLIDATED_JSON, consolidated)
    write_consolidated_csv(CONSOLIDATED_CSV, consolidated)

    csv_rows: list[dict[str, str]] = []
    if CONSOLIDATED_CSV.exists():
        with CONSOLIDATED_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            csv_rows = list(csv.DictReader(f))

    return {
        "company_name": company_name,
        "providers": providers,
        "spec_count": len(specs),
        "regen_issue_count": len(initial_issues),
        "merged_row_count": len(rows),
        "consolidated_errors": int(consolidated.get("total_validation_errors", 0)),
        "consolidated_records": int(consolidated.get("record_count", 0)),
        "consolidated_csv_exists": CONSOLIDATED_CSV.exists(),
        "consolidated_csv_row_count": len(csv_rows),
    }


def assert_llm_pipeline_state(test_id: str) -> dict[str, Any]:
    ctx = run_llm_pipeline_for_tests()

    assert ctx["merged_row_count"] == ctx["spec_count"], (
        f"{test_id}: merged row count mismatch "
        f"(got={ctx['merged_row_count']} expected={ctx['spec_count']})"
    )
    assert ctx["regen_issue_count"] == 0, f"{test_id}: regeneration still has validation issues"
    assert ctx["consolidated_records"] >= 1, f"{test_id}: no consolidated company records"
    assert ctx["consolidated_errors"] == 0, f"{test_id}: consolidated validation errors remain"
    assert ctx["consolidated_csv_exists"], f"{test_id}: consolidated csv was not written"
    assert ctx["consolidated_csv_row_count"] >= ctx["spec_count"], (
        f"{test_id}: consolidated csv has too few rows "
        f"(got={ctx['consolidated_csv_row_count']} expected>={ctx['spec_count']})"
    )

    return ctx
