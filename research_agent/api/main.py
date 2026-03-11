from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import Body
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from research_agent.api.schemas import RunPipelineRequest, RunPipelineResponse
from research_agent.api.service import run_pipeline
from research_agent.observability import configure_langsmith

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> None:
        return None


app = FastAPI(title="Research Agent API", version="0.1.0")
load_dotenv()
configure_langsmith()
RUNS: dict[str, dict] = {}


def _has_any_env(*names: str) -> bool:
    return any(bool(os.getenv(name)) for name in names)


def _missing_provider_keys(providers: list[str]) -> dict[str, str]:
    missing: dict[str, str] = {}
    provider_set = {p.strip().lower() for p in providers if p.strip()}
    if "groq" in provider_set and not _has_any_env("GROQ_API_KEY"):
        missing["groq"] = "GROQ_API_KEY is required"
    if "gemini" in provider_set and not _has_any_env("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        missing["gemini"] = "GEMINI_API_KEY or GOOGLE_API_KEY is required"
    if "baseten" in provider_set and not _has_any_env("BASETEN_API_KEY", "BASETEN_API"):
        missing["baseten"] = "BASETEN_API_KEY or BASETEN_API is required"
    return missing


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/providers")
async def health_providers() -> dict[str, bool]:
    return {
        "groq": _has_any_env("GROQ_API_KEY"),
        "gemini": _has_any_env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "baseten": _has_any_env("BASETEN_API_KEY", "BASETEN_API"),
    }


@app.post("/pipeline/run", response_model=RunPipelineResponse)
async def pipeline_run(
    payload: Annotated[RunPipelineRequest, Body(default_factory=RunPipelineRequest)],
) -> RunPipelineResponse:
    try:
        missing = _missing_provider_keys(payload.providers)
        if missing:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Missing API keys for requested providers.",
                    "missing": missing,
                },
            )
        return await run_in_threadpool(run_pipeline, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pipeline failed: {exc}") from exc


@app.post("/pipeline/run-async")
async def pipeline_run_async(
    payload: Annotated[RunPipelineRequest, Body(default_factory=RunPipelineRequest)],
) -> dict:
    missing = _missing_provider_keys(payload.providers)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Missing API keys for requested providers.",
                "missing": missing,
            },
        )

    run_id = str(uuid4())
    RUNS[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    payload_copy = payload.model_copy(deep=True)

    async def _execute() -> None:
        RUNS[run_id]["status"] = "running"
        RUNS[run_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        try:
            result = await run_in_threadpool(run_pipeline, payload_copy)
            RUNS[run_id]["status"] = "completed"
            RUNS[run_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
            RUNS[run_id]["result"] = result.model_dump()
        except Exception as exc:
            RUNS[run_id]["status"] = "failed"
            RUNS[run_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
            RUNS[run_id]["error"] = str(exc)

    import asyncio

    asyncio.create_task(_execute())
    return {"run_id": run_id, "status": "queued"}


@app.get("/pipeline/status/{run_id}")
async def pipeline_status(run_id: str) -> dict:
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
    return run
