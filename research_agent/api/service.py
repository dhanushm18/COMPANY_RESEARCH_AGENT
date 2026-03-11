from __future__ import annotations

from dataclasses import asdict, is_dataclass
from argparse import Namespace
from pathlib import Path
from typing import Any
from uuid import uuid4

from research_agent.api.schemas import RunPipelineRequest, RunPipelineResponse
from research_agent.langgraph_workflow import run_langgraph_pipeline


def _to_namespace(payload: RunPipelineRequest) -> Namespace:
    return Namespace(
        schema=payload.schema_path,
        companies=payload.companies,
        output_dir=payload.output_dir,
        providers=",".join(payload.providers),
        output_file=payload.output_file,
        output_csv=payload.output_csv,
        ready_db_csv=payload.ready_db_csv,
        ready_db_json=payload.ready_db_json,
        company_id_start=payload.company_id_start,
        method=payload.method,
        provider=payload.provider,
        model=payload.model,
        strict_validation=payload.strict_validation,
        agent1_retry_limit=payload.agent1_retry_limit,
    )


def run_pipeline(payload: RunPipelineRequest) -> RunPipelineResponse:
    run_id = str(uuid4())
    args = _to_namespace(payload)
    state: dict[str, Any] = run_langgraph_pipeline(args)
    safe_state = _json_safe(state)
    return RunPipelineResponse(
        run_id=run_id,
        pydantic_validation=safe_state.get("pydantic_validation", {}),
        pytest_validation=safe_state.get("pytest_validation", {}),
        pytest_regeneration=safe_state.get("pytest_regeneration", {}),
        pytest_validation_agent2=safe_state.get("pytest_validation_agent2", {}),
        consolidated_json_path=safe_state.get("consolidated_json_path"),
        consolidated_csv_path=safe_state.get("consolidated_csv_path"),
        ready_db_csv_path=safe_state.get("ready_db_csv_path"),
        ready_db_json_path=safe_state.get("ready_db_json_path"),
        state=safe_state,
    )


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value
