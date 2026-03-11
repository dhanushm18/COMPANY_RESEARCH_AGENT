from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .observability import configure_langsmith
from .schema import load_parameter_specs
from .validation import validate_schema_specs

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> None:
        return None


DEFAULT_SCHEMA = "data/parameters.template.csv"
DEFAULT_COMPANIES = "data/companies.json"
DEFAULT_OUTPUT_DIR = "outputs/individual_json"
DEFAULT_CONSOLIDATED = "outputs/consolidated_validated.json"
DEFAULT_CONSOLIDATED_CSV = "outputs/consolidated_validated.csv"
DEFAULT_READY_DB_CSV = "outputs/ready_for_db_push.csv"
DEFAULT_READY_DB_JSON = "outputs/ready_for_db_push.json"
DEFAULT_TEST_CSV = "pytests/data/sample_companies.csv"
DEFAULT_TEST_XLSX = "pytests/data/sample_companies.xlsx"
DEFAULT_TEST_SHEET = "Flat Companies Data"
DEFAULT_PROVIDERS = "groq,gemini,baseten"
PROVIDER_CHOICES = ["groq", "gemini", "baseten"]
DEFAULT_AGENT2_PYTEST_TARGET = "pytests/tests/test_consolidated_csv_outputs.py"


def _load_companies(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload.get("companies", [])
    if isinstance(payload, list):
        return payload
    raise ValueError("companies file must be a list or {'companies': [...]}")


def cmd_collect(args: argparse.Namespace) -> int:
    try:
        from .collector import (
            build_failed_provider_payload,
            collect_company_data,
            combine_rows_payload,
            write_individual_file,
        )
    except ModuleNotFoundError as exc:
        missing = str(exc).replace("No module named ", "").strip("'")
        raise RuntimeError(
            f"Missing dependency: {missing}. Install dependencies first with "
            "`uv sync` or `pip install -r requirements.txt`."
        ) from exc

    specs = load_parameter_specs(args.schema)
    schema_issues = validate_schema_specs(specs)
    if schema_issues:
        raise ValueError(
            "[before_generation] schema correctness failed:\n- " + "\n- ".join(schema_issues[:20])
        )
    print(f"[before_generation] schema validation passed rows={len(specs)}", flush=True)
    companies = _load_companies(args.companies)
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    print(f"[collect] schema_rows={len(specs)} companies={len(companies)} providers={providers}", flush=True)

    for company in companies:
        company_name = company["company_name"]
        print(f"[collect] company={company_name}", flush=True)
        provider_payloads: list[dict[str, Any]] = []
        for provider in providers:
            print(f"[collect] -> provider={provider} start", flush=True)
            try:
                provider_model = args.model if len(providers) == 1 else None
                payload = collect_company_data(
                    company_name=company_name,
                    specs=specs,
                    provider=provider,
                    model=provider_model,
                )
            except Exception as exc:
                print(f"[collect] -> provider={provider} failed: {exc}", flush=True)
                payload = build_failed_provider_payload(
                    company_name=company_name,
                    specs=specs,
                    provider=provider,
                    error=str(exc),
                )
            provider_payloads.append(payload)
            provider_json_dir = Path(args.output_dir) / "provider_json"
            write_individual_file(provider_json_dir, f"{company_name}__{provider}", payload)
            print(f"[collect] -> provider={provider} done rows={payload.get('row_count', 0)}", flush=True)
            pv = payload.get("validation", {})
            if pv:
                print(
                    f"[after_generation] provider={provider} issues={pv.get('issue_count', 0)}",
                    flush=True,
                )

        combined = combine_rows_payload(company_name, provider_payloads)
        out = write_individual_file(args.output_dir, company_name, combined)
        print(f"[collect] wrote: {out} rows={combined.get('row_count', 0)}", flush=True)
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    from .consolidator import consolidate_individual_jsons, write_consolidated, write_consolidated_csv
    from .db_push_export import (
        build_ready_for_db_records,
        write_ready_for_db_csv,
        write_ready_for_db_json,
    )
    from .supabase_sync import maybe_sync_outputs_to_supabase

    specs = load_parameter_specs(args.schema)
    schema_issues = validate_schema_specs(specs)
    if schema_issues:
        raise ValueError(
            "[before_generation] schema correctness failed:\n- " + "\n- ".join(schema_issues[:20])
        )
    print(f"[before_generation] schema validation passed rows={len(specs)}", flush=True)
    print(
        f"[consolidate] method={args.method} provider={args.provider} input_dir={args.input_dir}",
        flush=True,
    )
    consolidated = consolidate_individual_jsons(
        args.input_dir,
        specs,
        method=args.method,
        provider=args.provider,
        model=args.model,
        strict_validation=args.strict_validation,
    )
    out_json = write_consolidated(args.output_file, consolidated)
    out_csv = write_consolidated_csv(args.output_csv, consolidated)
    ready_records = build_ready_for_db_records(
        consolidated_payload=consolidated,
        specs=specs,
        company_id_start=args.company_id_start,
    )
    ready_csv = write_ready_for_db_csv(args.ready_db_csv, ready_records)
    ready_json = write_ready_for_db_json(args.ready_db_json, ready_records)
    print(f"[consolidate] wrote: {out_json}", flush=True)
    print(f"[consolidate] wrote: {out_csv}", flush=True)
    print(f"[consolidate] wrote: {ready_csv}", flush=True)
    print(f"[consolidate] wrote: {ready_json}", flush=True)
    print(
        f"[consolidate] records={consolidated['record_count']} errors={consolidated['total_validation_errors']}",
        flush=True,
    )
    total_pydantic_issues = 0
    for c in consolidated.get("companies", []):
        total_pydantic_issues += ((c.get("pydantic_validation", {}) or {}).get("issue_count", 0))
    print(
        f"[during_consolidation] pydantic_issues={total_pydantic_issues}",
        flush=True,
    )
    if total_pydantic_issues > 0:
        supabase_sync = maybe_sync_outputs_to_supabase(
            provider_json_dir=Path(args.input_dir) / "provider_json",
            consolidated_payload=consolidated,
            ready_records=ready_records,
        )
        if supabase_sync.get("enabled"):
            print(
                "[consolidate] supabase_sync "
                f"provider_rows={supabase_sync.get('provider_json_rows', 0)} "
                f"consolidated_rows={supabase_sync.get('consolidated_rows', 0)}",
                flush=True,
            )
        else:
            print(f"[consolidate] supabase_sync skipped: {supabase_sync.get('reason', 'not enabled')}", flush=True)
    if total_pydantic_issues > 0:
        print("[consolidate] pytest_validation skipped: pydantic validation failed before pytest", flush=True)
        return 1

    env = os.environ.copy()
    env["AGENT_CONSOLIDATED_CSV"] = str(out_csv)
    env["AGENT_SCHEMA_PATH"] = str(args.schema)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--confcutdir",
        "pytests/tests",
        DEFAULT_AGENT2_PYTEST_TARGET,
    ]
    print(f"[consolidate] pytest_validation start target={DEFAULT_AGENT2_PYTEST_TARGET}", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    passed = proc.returncode == 0
    print(f"[consolidate] pytest_validation passed={passed} returncode={proc.returncode}", flush=True)
    if not passed:
        print("[consolidate] pytest failed; retrying with llm method", flush=True)
        consolidated = consolidate_individual_jsons(
            args.input_dir,
            specs,
            method="llm",
            provider=args.provider,
            model=args.model,
            strict_validation=args.strict_validation,
        )
        out_json = write_consolidated(args.output_file, consolidated)
        out_csv = write_consolidated_csv(args.output_csv, consolidated)
        ready_records = build_ready_for_db_records(
            consolidated_payload=consolidated,
            specs=specs,
            company_id_start=args.company_id_start,
        )
        ready_csv = write_ready_for_db_csv(args.ready_db_csv, ready_records)
        ready_json = write_ready_for_db_json(args.ready_db_json, ready_records)
        env["AGENT_CONSOLIDATED_CSV"] = str(out_csv)
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        passed = proc.returncode == 0
        print(f"[consolidate] llm_retry wrote: {out_json}", flush=True)
        print(f"[consolidate] llm_retry wrote: {out_csv}", flush=True)
        print(f"[consolidate] llm_retry wrote: {ready_csv}", flush=True)
        print(f"[consolidate] llm_retry wrote: {ready_json}", flush=True)
        print(f"[consolidate] llm_retry pytest passed={passed} returncode={proc.returncode}", flush=True)

    supabase_sync = maybe_sync_outputs_to_supabase(
        provider_json_dir=Path(args.input_dir) / "provider_json",
        consolidated_payload=consolidated,
        ready_records=ready_records,
    )
    if supabase_sync.get("enabled"):
        print(
            "[consolidate] supabase_sync "
            f"provider_rows={supabase_sync.get('provider_json_rows', 0)} "
            f"consolidated_rows={supabase_sync.get('consolidated_rows', 0)}",
            flush=True,
        )
    else:
        print(f"[consolidate] supabase_sync skipped: {supabase_sync.get('reason', 'not enabled')}", flush=True)
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    from .langgraph_workflow import run_langgraph_pipeline

    print("[run_all] starting langgraph pipeline", flush=True)
    state = run_langgraph_pipeline(args)
    pydantic_summary = state.get("pydantic_validation", {})
    pytest_summary = state.get("pytest_validation", {})
    regen_summary = state.get("pytest_regeneration", {})
    pytest_summary_agent2 = state.get("pytest_validation_agent2", {})
    consolidated = state.get("consolidated_payload", {})
    ready_db_csv_path = state.get("ready_db_csv_path", "")
    ready_db_json_path = state.get("ready_db_json_path", "")
    print(
        f"[run_all] agent1_pydantic issues={pydantic_summary.get('issue_count', 0)} passed={pydantic_summary.get('passed', False)}",
        flush=True,
    )
    print(
        f"[run_all] agent1_pytest passed={pytest_summary.get('passed', False)} returncode={pytest_summary.get('returncode', -1)}",
        flush=True,
    )
    print(
        f"[run_all] agent1_regeneration triggered={regen_summary.get('triggered', False)} updated_provider_files={regen_summary.get('updated_provider_files', 0)} rerun_pytest_passed={regen_summary.get('rerun_pytest_passed', pytest_summary.get('passed', False))}",
        flush=True,
    )
    print(
        f"[run_all] agent1_regeneration attempts_run={regen_summary.get('attempts_run', 0)} retry_limit={regen_summary.get('retry_limit', getattr(args, 'agent1_retry_limit', 1))}",
        flush=True,
    )
    print(
        f"[run_all] agent2 records={consolidated.get('record_count', 0)} errors={consolidated.get('total_validation_errors', 0)}",
        flush=True,
    )
    print(
        f"[run_all] agent2_pytest passed={pytest_summary_agent2.get('passed', False)} returncode={pytest_summary_agent2.get('returncode', -1)} retry_with_llm={pytest_summary_agent2.get('retry_with_llm', False)}",
        flush=True,
    )
    if ready_db_csv_path:
        print(f"[run_all] ready_db_csv={ready_db_csv_path}", flush=True)
    if ready_db_json_path:
        print(f"[run_all] ready_db_json={ready_db_json_path}", flush=True)
    print("[run_all] completed", flush=True)
    return 0


def cmd_format_llm_test_data(args: argparse.Namespace) -> int:
    from .llm_test_data_formatter import prepare_flat_companies_from_consolidated

    summary = prepare_flat_companies_from_consolidated(
        schema_path=args.schema,
        consolidated_csv=args.consolidated_csv,
        out_csv=args.out_csv,
        out_xlsx=args.out_xlsx,
        sheet_name=args.sheet_name,
        tc63_company_name=args.tc63_company_name,
    )
    print(
        f"[format_llm_test_data] companies={summary['companies']} columns={summary['columns']}",
        flush=True,
    )
    print(f"[format_llm_test_data] wrote csv: {summary['csv_path']}", flush=True)
    print(f"[format_llm_test_data] wrote xlsx: {summary['xlsx_path']}", flush=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Research data collector and validator")
    p.add_argument("--schema", default=DEFAULT_SCHEMA, help="CSV/TSV/JSON schema file for parameters")
    p.add_argument("--companies", default=DEFAULT_COMPANIES, help="JSON file with company_name list")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output folder for merged per-company JSON")
    p.add_argument("--providers", default=DEFAULT_PROVIDERS, help="Comma-separated providers to run for generation")
    p.add_argument("--output-file", default=DEFAULT_CONSOLIDATED, help="Consolidated JSON output")
    p.add_argument("--output-csv", default=DEFAULT_CONSOLIDATED_CSV, help="Final consolidated CSV output")
    p.add_argument("--ready-db-csv", default=DEFAULT_READY_DB_CSV, help="Wide staging-company CSV ready for DB push")
    p.add_argument("--ready-db-json", default=DEFAULT_READY_DB_JSON, help="Wide staging-company JSON ready for DB push")
    p.add_argument("--company-id-start", type=int, default=1, help="Starting company_id for ready-for-db export")
    p.add_argument("--method", default="deterministic", choices=["deterministic", "llm"], help="Consolidation strategy")
    p.add_argument("--provider", default="groq", choices=PROVIDER_CHOICES, help="LLM provider for llm method")
    p.add_argument("--model", default=None, help="Optional explicit model name")
    p.add_argument("--strict-validation", action="store_true", help="Enable strict regex/type/length validation")
    p.add_argument(
        "--agent1-retry-limit",
        type=int,
        default=1,
        help="How many regeneration+pytest retries to run before consolidation (default: 1)",
    )

    sub = p.add_subparsers(dest="command", required=False)

    collect = sub.add_parser("collect", help="Generate individual company JSON files")
    collect.add_argument("--schema", default=DEFAULT_SCHEMA, help="CSV/TSV/JSON schema file for parameters")
    collect.add_argument("--companies", required=True, help="JSON file with company_name list")
    collect.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output folder for merged per-company JSON")
    collect.add_argument(
        "--providers",
        default=DEFAULT_PROVIDERS,
        help="Comma-separated providers to run for generation",
    )
    collect.add_argument("--model", default=None, help="Optional explicit model name")
    collect.set_defaults(func=cmd_collect)

    consolidate = sub.add_parser("consolidate", help="Validate and build consolidated JSON")
    consolidate.add_argument("--schema", default=DEFAULT_SCHEMA, help="CSV/TSV/JSON schema file for parameters")
    consolidate.add_argument("--input-dir", default=DEFAULT_OUTPUT_DIR, help="Input folder with per-company JSON")
    consolidate.add_argument("--output-file", default=DEFAULT_CONSOLIDATED, help="Consolidated JSON output")
    consolidate.add_argument("--output-csv", default=DEFAULT_CONSOLIDATED_CSV, help="Final consolidated CSV output")
    consolidate.add_argument("--ready-db-csv", default=DEFAULT_READY_DB_CSV, help="Wide staging-company CSV ready for DB push")
    consolidate.add_argument("--ready-db-json", default=DEFAULT_READY_DB_JSON, help="Wide staging-company JSON ready for DB push")
    consolidate.add_argument("--company-id-start", type=int, default=1, help="Starting company_id for ready-for-db export")
    consolidate.add_argument("--method", default="deterministic", choices=["deterministic", "llm"], help="Consolidation strategy")
    consolidate.add_argument("--provider", default="groq", choices=PROVIDER_CHOICES, help="LLM provider for llm method")
    consolidate.add_argument("--model", default=None, help="Optional explicit model name")
    consolidate.add_argument("--strict-validation", action="store_true", help="Enable strict regex/type/length validation")
    consolidate.set_defaults(func=cmd_consolidate)

    format_data = sub.add_parser(
        "format-llm-test-data",
        help="Format consolidated LLM output into workbook/csv shape expected by test_cases6.3-10.1",
    )
    format_data.add_argument("--schema", default=DEFAULT_SCHEMA, help="Schema file for parameter ID to column mapping")
    format_data.add_argument("--consolidated-csv", default=DEFAULT_CONSOLIDATED_CSV, help="Consolidated csv output from agent pipeline")
    format_data.add_argument("--out-csv", default=DEFAULT_TEST_CSV, help="Target csv path used by tests")
    format_data.add_argument("--out-xlsx", default=DEFAULT_TEST_XLSX, help="Target xlsx path used by tests")
    format_data.add_argument("--sheet-name", default=DEFAULT_TEST_SHEET, help="Excel sheet name")
    format_data.add_argument("--tc63-company-name", default=None, help="Optional company name remap for TC-6.3 selector")
    format_data.set_defaults(func=cmd_format_llm_test_data)

    return p


def main() -> int:
    load_dotenv()
    if configure_langsmith():
        print("[observability] LangSmith tracing enabled", flush=True)
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "command", None):
        return args.func(args)

    if not Path(args.companies).exists():
        raise FileNotFoundError(
            f"default run expects companies file at '{args.companies}'. "
            "Create it or run with --companies <path>."
        )
    return cmd_run_all(args)
