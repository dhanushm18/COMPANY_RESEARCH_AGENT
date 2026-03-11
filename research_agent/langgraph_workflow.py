from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from research_agent.collector import (
    build_failed_provider_payload,
    collect_company_data,
    combine_rows_payload,
    regenerate_specific_parameters,
    write_individual_file,
)
from research_agent.consolidator import consolidate_individual_jsons, write_consolidated, write_consolidated_csv
from research_agent.db_push_export import (
    build_ready_for_db_records,
    write_ready_for_db_csv,
    write_ready_for_db_json,
)
from research_agent.schema import ParameterSpec, load_parameter_specs
from research_agent.supabase_sync import maybe_sync_outputs_to_supabase
from research_agent.validation import (
    collect_row_validation_issues,
    validate_rows_against_specs,
    validate_schema_specs,
)


class WorkflowState(TypedDict, total=False):
    schema_path: str
    companies_path: str
    output_dir: str
    providers: list[str]
    model: str | None
    method: str
    consolidate_provider: str
    strict_validation: bool
    output_file: str
    output_csv: str
    ready_db_csv: str
    ready_db_json: str
    company_id_start: int
    pytest_target: str
    pytest_target_agent2: str
    agent1_retry_limit: int
    specs: list[ParameterSpec]
    companies: list[dict[str, Any]]
    provider_payloads: dict[str, list[dict[str, Any]]]
    provider_output_files: list[str]
    merged_company_files: list[str]
    pydantic_validation: dict[str, Any]
    pytest_validation: dict[str, Any]
    pytest_regeneration: dict[str, Any]
    pytest_validation_agent2: dict[str, Any]
    consolidated_payload: dict[str, Any]
    consolidated_json_path: str
    consolidated_csv_path: str
    ready_db_csv_path: str
    ready_db_json_path: str
    supabase_sync: dict[str, Any]


def _load_companies(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload.get("companies", [])
    if isinstance(payload, list):
        return payload
    raise ValueError("companies file must be a list or {'companies': [...]}")


def _node_load_inputs(state: WorkflowState) -> WorkflowState:
    specs = load_parameter_specs(state["schema_path"])
    schema_issues = validate_schema_specs(specs)
    if schema_issues:
        raise ValueError("[before_generation] schema correctness failed:\n- " + "\n- ".join(schema_issues[:20]))
    companies = _load_companies(state["companies_path"])
    print(f"[langgraph] schema validation passed rows={len(specs)}", flush=True)
    print(
        f"[langgraph] inputs companies={len(companies)} providers={state['providers']}",
        flush=True,
    )
    return {"specs": specs, "companies": companies}


def _node_agent1_collect(state: WorkflowState) -> WorkflowState:
    specs = state["specs"]
    providers = state["providers"]
    output_dir = state["output_dir"]
    model = state.get("model")

    provider_payloads: dict[str, list[dict[str, Any]]] = {}
    provider_output_files: list[str] = []
    merged_files: list[str] = []
    issue_count = 0

    for company in state["companies"]:
        company_name = company["company_name"]
        print(f"[agent1] collect company={company_name}", flush=True)
        payloads: list[dict[str, Any]] = []

        for provider in providers:
            print(f"[agent1] -> provider={provider} start", flush=True)
            try:
                provider_model = model if len(providers) == 1 else None
                payload = collect_company_data(
                    company_name=company_name,
                    specs=specs,
                    provider=provider,
                    model=provider_model,
                )
            except Exception as exc:
                payload = build_failed_provider_payload(
                    company_name=company_name,
                    specs=specs,
                    provider=provider,
                    error=str(exc),
                )
            payloads.append(payload)
            issue_count += int(((payload.get("validation") or {}).get("issue_count", 0)))

            provider_json_dir = Path(output_dir) / "provider_json"
            provider_path = write_individual_file(provider_json_dir, f"{company_name}__{provider}", payload)
            provider_output_files.append(str(provider_path))
            print(f"[agent1] -> provider={provider} done rows={payload.get('row_count', 0)}", flush=True)

        merged = combine_rows_payload(company_name, payloads)
        merged_path = write_individual_file(output_dir, company_name, merged)
        merged_files.append(str(merged_path))
        provider_payloads[company_name] = payloads
        print(f"[agent1] merged company={company_name} rows={merged.get('row_count', 0)}", flush=True)

    pydantic_summary = {
        "phase": "after_generation",
        "companies": len(state["companies"]),
        "issue_count": issue_count,
        "passed": issue_count == 0,
    }
    print(f"[agent1] pydantic_validation issues={issue_count}", flush=True)

    return {
        "provider_payloads": provider_payloads,
        "provider_output_files": provider_output_files,
        "merged_company_files": merged_files,
        "pydantic_validation": pydantic_summary,
    }


def _node_pytest_validation(state: WorkflowState) -> WorkflowState:
    target = state.get("pytest_target", "pytests/tests/test_agent1_outputs.py")
    env = os.environ.copy()
    env["AGENT_OUTPUT_DIR"] = state["output_dir"]
    env["AGENT_SCHEMA_PATH"] = state["schema_path"]
    env["AGENT_PROVIDERS"] = ",".join(state["providers"])
    env["AGENT_MERGED_FILES"] = json.dumps(state.get("merged_company_files", []))
    env["AGENT_PROVIDER_FILES"] = json.dumps(state.get("provider_output_files", []))
    # Prevent loading unrelated top-level conftest.py (which may require extra deps).
    cmd = [sys.executable, "-m", "pytest", "-q", "--confcutdir", "pytests/tests", target]

    print(f"[agent1] pytest_validation start target={target}", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    passed = proc.returncode == 0
    summary = {
        "phase": "after_generation",
        "passed": passed,
        "returncode": proc.returncode,
        "target": target,
        "stdout": proc.stdout.strip()[-4000:],
        "stderr": proc.stderr.strip()[-4000:],
        "skipped": False,
    }
    print(f"[agent1] pytest_validation passed={passed} returncode={proc.returncode}", flush=True)
    return {"pytest_validation": summary}


def _node_agent1_regenerate_failed(state: WorkflowState) -> WorkflowState:
    pytest_summary = state.get("pytest_validation", {})
    pydantic_summary = state.get("pydantic_validation", {})
    needs_retry = (not pytest_summary.get("passed", False)) or (not pydantic_summary.get("passed", False))
    if not needs_retry:
        summary = {
            "triggered": False,
            "updated_companies": 0,
            "updated_provider_files": 0,
            "updated_merged_files": 0,
            "failed_parameter_ids": {},
            "rerun_pytest_passed": pytest_summary.get("passed", False),
            "rerun_pytest_returncode": pytest_summary.get("returncode", 0),
        }
        print("[agent1] regeneration skipped (pydantic+pytest passed)", flush=True)
        return {"pytest_regeneration": summary}

    retry_limit = int(state.get("agent1_retry_limit", 1))
    if retry_limit < 1:
        retry_limit = 1

    specs = state["specs"]
    providers = state["providers"]
    output_dir = Path(state["output_dir"])
    provider_json_dir = output_dir / "provider_json"
    model = state.get("model")

    provider_payloads = state.get("provider_payloads", {})
    total_updated_provider_files = 0
    attempts_run = 0
    failed_parameter_ids_by_attempt: list[dict[str, list[int]]] = []
    merged_files: list[str] = state.get("merged_company_files", [])
    provider_files: list[str] = state.get("provider_output_files", [])
    latest_pytest = pytest_summary

    for attempt in range(1, retry_limit + 1):
        attempts_run = attempt
        print(f"[agent1] regeneration attempt={attempt}/{retry_limit}", flush=True)
        merged_files = []
        provider_files = []
        failed_parameter_ids: dict[str, list[int]] = {}
        updated_provider_files_this_attempt = 0

        for company in state["companies"]:
            company_name = company["company_name"]
            company_payloads = provider_payloads.get(company_name, [])
            updated_payloads: list[dict[str, Any]] = []
            company_failed_ids: set[int] = set()

            # Build a company-level failed ID set first so we regenerate the same
            # parameters across all LLM providers before consolidation.
            for provider_payload in company_payloads:
                rows = provider_payload.get("rows", [])
                issues_by_id = collect_row_validation_issues(rows, specs)
                company_failed_ids.update(issues_by_id.keys())
            company_failed_ids_sorted = sorted(company_failed_ids)

            for provider_payload in company_payloads:
                provider = str(provider_payload.get("provider", "")).strip().lower()
                if provider not in providers:
                    updated_payloads.append(provider_payload)
                    continue

                rows = provider_payload.get("rows", [])
                failed_parameter_ids[f"{company_name}::{provider}"] = company_failed_ids_sorted
                if company_failed_ids_sorted:
                    print(
                        f"[agent1] pytest-triggered regeneration(all_llms) company={company_name} provider={provider} ids={company_failed_ids_sorted[:20]}",
                        flush=True,
                    )
                    try:
                        new_rows = regenerate_specific_parameters(
                            company_name=company_name,
                            rows=rows,
                            specs=specs,
                            provider=provider,
                            model=model,
                            failed_ids=company_failed_ids_sorted,
                        )
                        post_issues = validate_rows_against_specs(new_rows, specs)
                        updated_payload = {
                            **provider_payload,
                            "row_count": len(new_rows),
                            "rows": new_rows,
                            "validation": {
                                "phase": "after_generation",
                                "issue_count": len(post_issues),
                                "issues": post_issues,
                                "regenerated_after_pytest": True,
                            },
                        }
                        updated_provider_files_this_attempt += 1
                    except Exception as exc:
                        existing_issues = list((provider_payload.get("validation", {}) or {}).get("issues", []))
                        existing_issues.append(f"regeneration_error: {exc}")
                        updated_payload = {
                            **provider_payload,
                            "validation": {
                                "phase": "after_generation",
                                "issue_count": len(existing_issues),
                                "issues": existing_issues,
                                "regenerated_after_pytest": False,
                            },
                        }
                        print(
                            f"[agent1] regeneration failed company={company_name} provider={provider} error={exc}",
                            flush=True,
                        )
                else:
                    updated_payload = provider_payload

                provider_path = write_individual_file(provider_json_dir, f"{company_name}__{provider}", updated_payload)
                provider_files.append(str(provider_path))
                updated_payloads.append(updated_payload)

            merged = combine_rows_payload(company_name, updated_payloads)
            merged_path = write_individual_file(output_dir, company_name, merged)
            merged_files.append(str(merged_path))
            provider_payloads[company_name] = updated_payloads

        total_updated_provider_files += updated_provider_files_this_attempt
        failed_parameter_ids_by_attempt.append(failed_parameter_ids)

        total_issues = 0
        for cps in provider_payloads.values():
            for payload in cps:
                total_issues += int(((payload.get("validation") or {}).get("issue_count", 0)))
        pydantic_refresh = {
            "phase": "after_generation",
            "companies": len(state["companies"]),
            "issue_count": total_issues,
            "passed": total_issues == 0,
            "post_pytest_regeneration": True,
        }

        target = state.get("pytest_target", "pytests/tests/test_agent1_outputs.py")
        env = os.environ.copy()
        env["AGENT_OUTPUT_DIR"] = state["output_dir"]
        env["AGENT_SCHEMA_PATH"] = state["schema_path"]
        env["AGENT_PROVIDERS"] = ",".join(state["providers"])
        env["AGENT_MERGED_FILES"] = json.dumps(merged_files)
        env["AGENT_PROVIDER_FILES"] = json.dumps(provider_files)
        cmd = [sys.executable, "-m", "pytest", "-q", "--confcutdir", "pytests/tests", target]
        print(f"[agent1] pytest_validation rerun attempt={attempt} start target={target}", flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        passed = proc.returncode == 0
        latest_pytest = {
            "phase": "after_generation",
            "passed": passed,
            "returncode": proc.returncode,
            "target": target,
            "stdout": proc.stdout.strip()[-4000:],
            "stderr": proc.stderr.strip()[-4000:],
            "skipped": False,
            "after_regeneration": True,
            "attempt": attempt,
        }
        print(
            f"[agent1] pytest_validation rerun attempt={attempt} passed={passed} returncode={proc.returncode}",
            flush=True,
        )

        if pydantic_refresh["passed"] and passed:
            print(f"[agent1] regeneration converged at attempt={attempt}", flush=True)
            break
    else:
        # If loop exhausted, keep latest pydantic refresh computed in final attempt.
        total_issues = 0
        for cps in provider_payloads.values():
            for payload in cps:
                total_issues += int(((payload.get("validation") or {}).get("issue_count", 0)))
        pydantic_refresh = {
            "phase": "after_generation",
            "companies": len(state["companies"]),
            "issue_count": total_issues,
            "passed": total_issues == 0,
            "post_pytest_regeneration": True,
        }

    regen_summary = {
        "triggered": True,
        "attempts_run": attempts_run,
        "retry_limit": retry_limit,
        "updated_companies": len(state["companies"]),
        "updated_provider_files": total_updated_provider_files,
        "updated_merged_files": len(merged_files),
        "failed_parameter_ids": failed_parameter_ids_by_attempt,
        "rerun_pytest_passed": latest_pytest.get("passed", False),
        "rerun_pytest_returncode": latest_pytest.get("returncode", -1),
    }

    return {
        "provider_payloads": provider_payloads,
        "provider_output_files": provider_files,
        "merged_company_files": merged_files,
        "pydantic_validation": pydantic_refresh,
        "pytest_validation": latest_pytest,
        "pytest_regeneration": regen_summary,
    }


def _node_agent2_consolidate(state: WorkflowState) -> WorkflowState:
    print(
        f"[agent2] consolidate method={state['method']} provider={state['consolidate_provider']}",
        flush=True,
    )
    consolidated = consolidate_individual_jsons(
        input_dir=state["output_dir"],
        specs=state["specs"],
        method=state["method"],
        provider=state["consolidate_provider"],
        model=state.get("model"),
        strict_validation=state["strict_validation"],
    )
    out_json = write_consolidated(state["output_file"], consolidated)
    out_csv = write_consolidated_csv(state["output_csv"], consolidated)
    ready_records = build_ready_for_db_records(
        consolidated_payload=consolidated,
        specs=state["specs"],
        company_id_start=int(state.get("company_id_start", 1)),
    )
    ready_csv = write_ready_for_db_csv(state["ready_db_csv"], ready_records)
    ready_json = write_ready_for_db_json(state["ready_db_json"], ready_records)
    print(f"[agent2] wrote json={out_json}", flush=True)
    print(f"[agent2] wrote csv={out_csv}", flush=True)
    print(f"[agent2] wrote ready_db_csv={ready_csv}", flush=True)
    print(f"[agent2] wrote ready_db_json={ready_json}", flush=True)

    total_pydantic_issues = 0
    for c in consolidated.get("companies", []):
        total_pydantic_issues += int(((c.get("pydantic_validation") or {}).get("issue_count", 0)))
    print(f"[agent2] pydantic_validation issues={total_pydantic_issues}", flush=True)

    target = state.get("pytest_target_agent2", "pytests/tests/test_consolidated_csv_outputs.py")
    env = os.environ.copy()
    env["AGENT_CONSOLIDATED_CSV"] = str(out_csv)
    env["AGENT_SCHEMA_PATH"] = state["schema_path"]
    cmd = [sys.executable, "-m", "pytest", "-q", "--confcutdir", "pytests/tests", target]
    if total_pydantic_issues > 0:
        supabase_sync = maybe_sync_outputs_to_supabase(
            provider_json_dir=Path(state["output_dir"]) / "provider_json",
            consolidated_payload=consolidated,
            ready_records=ready_records,
        )
        if supabase_sync.get("enabled"):
            print(
                "[agent2] supabase_sync "
                f"provider_rows={supabase_sync.get('provider_json_rows', 0)} "
                f"consolidated_rows={supabase_sync.get('consolidated_rows', 0)}",
                flush=True,
            )
        else:
            print(f"[agent2] supabase_sync skipped: {supabase_sync.get('reason', 'not enabled')}", flush=True)
        summary = {
            "phase": "during_consolidation",
            "passed": False,
            "returncode": -1,
            "target": target,
            "stdout": "",
            "stderr": "Skipped pytest: pydantic validation failed before pytest.",
            "retry_with_llm": False,
            "skipped": True,
        }
        print("[agent2] pytest_validation skipped due to pydantic failure", flush=True)
        return {
            "consolidated_payload": consolidated,
            "consolidated_json_path": str(out_json),
            "consolidated_csv_path": str(out_csv),
            "ready_db_csv_path": str(ready_csv),
            "ready_db_json_path": str(ready_json),
            "supabase_sync": supabase_sync,
            "pytest_validation_agent2": summary,
        }

    print(f"[agent2] pytest_validation start target={target}", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    passed = proc.returncode == 0
    summary = {
        "phase": "during_consolidation",
        "passed": passed,
        "returncode": proc.returncode,
        "target": target,
        "stdout": proc.stdout.strip()[-4000:],
        "stderr": proc.stderr.strip()[-4000:],
        "retry_with_llm": False,
        "skipped": False,
    }

    if not passed:
        print("[agent2] pytest failed; retrying consolidation with llm method", flush=True)
        consolidated = consolidate_individual_jsons(
            input_dir=state["output_dir"],
            specs=state["specs"],
            method="llm",
            provider=state["consolidate_provider"],
            model=state.get("model"),
            strict_validation=state["strict_validation"],
        )
        out_json = write_consolidated(state["output_file"], consolidated)
        out_csv = write_consolidated_csv(state["output_csv"], consolidated)
        ready_records = build_ready_for_db_records(
            consolidated_payload=consolidated,
            specs=state["specs"],
            company_id_start=int(state.get("company_id_start", 1)),
        )
        ready_csv = write_ready_for_db_csv(state["ready_db_csv"], ready_records)
        ready_json = write_ready_for_db_json(state["ready_db_json"], ready_records)
        env["AGENT_CONSOLIDATED_CSV"] = str(out_csv)
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        passed = proc.returncode == 0
        summary = {
            "phase": "during_consolidation",
            "passed": passed,
            "returncode": proc.returncode,
            "target": target,
            "stdout": proc.stdout.strip()[-4000:],
            "stderr": proc.stderr.strip()[-4000:],
            "retry_with_llm": True,
            "skipped": False,
        }
        print(f"[agent2] llm_retry wrote json={out_json}", flush=True)
        print(f"[agent2] llm_retry wrote csv={out_csv}", flush=True)
        print(f"[agent2] llm_retry wrote ready_db_csv={ready_csv}", flush=True)
        print(f"[agent2] llm_retry wrote ready_db_json={ready_json}", flush=True)

    supabase_sync = maybe_sync_outputs_to_supabase(
        provider_json_dir=Path(state["output_dir"]) / "provider_json",
        consolidated_payload=consolidated,
        ready_records=ready_records,
    )
    if supabase_sync.get("enabled"):
        print(
            "[agent2] supabase_sync "
            f"provider_rows={supabase_sync.get('provider_json_rows', 0)} "
            f"consolidated_rows={supabase_sync.get('consolidated_rows', 0)}",
            flush=True,
        )
    else:
        print(f"[agent2] supabase_sync skipped: {supabase_sync.get('reason', 'not enabled')}", flush=True)

    print(f"[agent2] pytest_validation passed={passed} returncode={proc.returncode}", flush=True)
    return {
        "consolidated_payload": consolidated,
        "consolidated_json_path": str(out_json),
        "consolidated_csv_path": str(out_csv),
        "ready_db_csv_path": str(ready_csv),
        "ready_db_json_path": str(ready_json),
        "supabase_sync": supabase_sync,
        "pytest_validation_agent2": summary,
    }


def build_research_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_inputs", _node_load_inputs)
    graph.add_node("agent1_collect", _node_agent1_collect)
    graph.add_node("agent1_pytest_validation", _node_pytest_validation)
    graph.add_node("agent1_regenerate_failed", _node_agent1_regenerate_failed)
    graph.add_node("agent2_consolidate", _node_agent2_consolidate)
    graph.add_edge(START, "load_inputs")
    graph.add_edge("load_inputs", "agent1_collect")
    graph.add_edge("agent1_collect", "agent1_pytest_validation")
    graph.add_edge("agent1_pytest_validation", "agent1_regenerate_failed")
    graph.add_edge("agent1_regenerate_failed", "agent2_consolidate")
    graph.add_edge("agent2_consolidate", END)
    return graph.compile()


def run_langgraph_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    providers = [p.strip().lower() for p in args.providers.split(",") if p.strip()]
    if not providers:
        raise ValueError("at least one provider is required")
    app = build_research_graph()
    initial_state: WorkflowState = {
        "schema_path": args.schema,
        "companies_path": args.companies,
        "output_dir": args.output_dir,
        "providers": providers,
        "model": args.model,
        "method": args.method,
        "consolidate_provider": args.provider,
        "strict_validation": args.strict_validation,
        "output_file": args.output_file,
        "output_csv": args.output_csv,
        "ready_db_csv": args.ready_db_csv,
        "ready_db_json": args.ready_db_json,
        "company_id_start": getattr(args, "company_id_start", 1),
        "pytest_target": "pytests/tests/test_agent1_outputs.py",
        "pytest_target_agent2": "pytests/tests/test_consolidated_csv_outputs.py",
        "agent1_retry_limit": getattr(args, "agent1_retry_limit", 1),
    }
    return app.invoke(initial_state)


# LangGraph Studio entrypoint
graph = build_research_graph()
