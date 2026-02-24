from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .schema import load_parameter_specs

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

        combined = combine_rows_payload(company_name, provider_payloads)
        out = write_individual_file(args.output_dir, company_name, combined)
        print(f"[collect] wrote: {out} rows={combined.get('row_count', 0)}", flush=True)
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    from .consolidator import consolidate_individual_jsons, write_consolidated, write_consolidated_csv

    specs = load_parameter_specs(args.schema)
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
    print(f"[consolidate] wrote: {out_json}", flush=True)
    print(f"[consolidate] wrote: {out_csv}", flush=True)
    print(
        f"[consolidate] records={consolidated['record_count']} errors={consolidated['total_validation_errors']}",
        flush=True,
    )
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    print("[run_all] starting full pipeline", flush=True)
    collect_args = argparse.Namespace(
        schema=args.schema,
        companies=args.companies,
        output_dir=args.output_dir,
        providers=args.providers,
        model=args.model,
    )
    consolidate_args = argparse.Namespace(
        schema=args.schema,
        input_dir=args.output_dir,
        output_file=args.output_file,
        output_csv=args.output_csv,
        method=args.method,
        provider=args.provider,
        model=args.model,
        strict_validation=args.strict_validation,
    )
    cmd_collect(collect_args)
    rc = cmd_consolidate(consolidate_args)
    print("[run_all] completed", flush=True)
    return rc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Research data collector and validator")
    p.add_argument("--schema", default=DEFAULT_SCHEMA, help="CSV/TSV/JSON schema file for parameters")
    p.add_argument("--companies", default=DEFAULT_COMPANIES, help="JSON file with company_name list")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output folder for merged per-company JSON")
    p.add_argument("--providers", default="openai,groq,gemini", help="Comma-separated providers to run for generation")
    p.add_argument("--output-file", default=DEFAULT_CONSOLIDATED, help="Consolidated JSON output")
    p.add_argument("--output-csv", default=DEFAULT_CONSOLIDATED_CSV, help="Final consolidated CSV output")
    p.add_argument("--method", default="deterministic", choices=["deterministic", "llm"], help="Consolidation strategy")
    p.add_argument("--provider", default="openai", choices=["openai", "groq", "gemini"], help="LLM provider for llm method")
    p.add_argument("--model", default=None, help="Optional explicit model name")
    p.add_argument("--strict-validation", action="store_true", help="Enable strict regex/type/length validation")

    sub = p.add_subparsers(dest="command", required=False)

    collect = sub.add_parser("collect", help="Generate individual company JSON files")
    collect.add_argument("--schema", default=DEFAULT_SCHEMA, help="CSV/TSV/JSON schema file for parameters")
    collect.add_argument("--companies", required=True, help="JSON file with company_name list")
    collect.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output folder for merged per-company JSON")
    collect.add_argument(
        "--providers",
        default="openai,groq,gemini",
        help="Comma-separated providers to run for generation",
    )
    collect.add_argument("--model", default=None, help="Optional explicit model name")
    collect.set_defaults(func=cmd_collect)

    consolidate = sub.add_parser("consolidate", help="Validate and build consolidated JSON")
    consolidate.add_argument("--schema", default=DEFAULT_SCHEMA, help="CSV/TSV/JSON schema file for parameters")
    consolidate.add_argument("--input-dir", default=DEFAULT_OUTPUT_DIR, help="Input folder with per-company JSON")
    consolidate.add_argument("--output-file", default=DEFAULT_CONSOLIDATED, help="Consolidated JSON output")
    consolidate.add_argument("--output-csv", default=DEFAULT_CONSOLIDATED_CSV, help="Final consolidated CSV output")
    consolidate.add_argument("--method", default="deterministic", choices=["deterministic", "llm"], help="Consolidation strategy")
    consolidate.add_argument("--provider", default="openai", choices=["openai", "groq", "gemini"], help="LLM provider for llm method")
    consolidate.add_argument("--model", default=None, help="Optional explicit model name")
    consolidate.add_argument("--strict-validation", action="store_true", help="Enable strict regex/type/length validation")
    consolidate.set_defaults(func=cmd_consolidate)

    return p


def main() -> int:
    load_dotenv()
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
