from __future__ import annotations

import json
import os
from pathlib import Path


def _paths_from_env(key: str) -> list[Path]:
    raw = os.getenv(key, "").strip()
    if not raw:
        return []
    try:
        values = json.loads(raw)
        if isinstance(values, list):
            return [Path(str(v)) for v in values if str(v).strip()]
    except json.JSONDecodeError:
        return []
    return []


def _providers() -> list[str]:
    raw = os.getenv("AGENT_PROVIDERS", "groq,gemini,baseten")
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def test_output_dir_exists():
    output_dir = Path(os.getenv("AGENT_OUTPUT_DIR", "outputs/individual_json"))
    assert output_dir.exists(), f"Missing output directory: {output_dir}"


def test_provider_json_files_exist():
    provider_files = _paths_from_env("AGENT_PROVIDER_FILES")
    assert provider_files, "No provider json files were passed from Agent 1"
    for f in provider_files:
        assert f.exists(), f"Missing provider json file: {f}"


def test_each_provider_has_output():
    provider_files = _paths_from_env("AGENT_PROVIDER_FILES")
    files = [f.name.lower() for f in provider_files]
    for provider in _providers():
        assert any(name.endswith(f"__{provider}.json") for name in files), f"Missing output for provider={provider}"


def test_merged_company_files_have_rows():
    merged_files = _paths_from_env("AGENT_MERGED_FILES")
    assert merged_files, "No merged per-company JSON files were passed from Agent 1"
    for f in merged_files:
        assert f.exists(), f"Merged file not found: {f}"
        payload = json.loads(f.read_text(encoding="utf-8"))
        rows = payload.get("rows", [])
        assert isinstance(rows, list), f"rows must be a list in {f}"
        assert len(rows) > 0, f"rows must not be empty in {f}"
