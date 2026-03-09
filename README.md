# Research Agent: Multi-LLM Data Generation + Consolidation

This agent automates your two-manual-prompt workflow with JSON outputs:
1. Generate research rows using three providers (Groq, Gemini, Baseten).
2. Consolidate multi-provider outputs into one golden record (163 rows).

## Setup
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

Required env vars:
- `GROQ_API_KEY`
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`)
- `BASETEN_API_KEY` (or `BASETEN_API`)

Optional model overrides:
- `GROQ_MODEL` (default from library)
- `GEMINI_MODEL` (default `gemini-2.0-flash`)
- `BASETEN_MODEL` (default `deepseek-ai/DeepSeek-V3-0324`)

Optional base URLs:
- `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com/v1beta/openai/`)
- `BASETEN_BASE_URL` (default `https://inference.baseten.co/v1`)

## Input Files
- Schema: `data/parameters.template.csv` (TSV/CSV supported; includes `ID/sr_no`, `Parameter/column_name`, `A/C`, Min/Max)
- Companies: `data/companies.json`

Example companies file:
```json
[
  { "company_name": "Blinkit" }
]
```

## Run

Single command (full pipeline):
```powershell
uv run python main.py
```
This runs a `LangGraph` workflow:
- Agent 1: collect from all providers, run Pydantic validation, run pytest validation, and if validation fails regenerate only failed parameter IDs and rerun pytest
- Agent 2: consolidate into final record

Default inputs:
- schema: `data/parameters.template.csv`
- companies: `data/companies.json`
- providers: `groq,gemini,baseten`
- output: `outputs/consolidated_validated.csv` (final)

If this is first run, install deps once:
```powershell
uv sync
```

1. Generation from selected providers:
```powershell
python main.py collect --companies data/companies.json --schema data/parameters.template.csv --providers groq,gemini,baseten
```


2. Consolidate to 163 rows with selection logic:
```powershell
python main.py consolidate --schema data/parameters.template.csv --input-dir outputs/individual_json --output-file outputs/consolidated_validated.json --output-csv outputs/consolidated_validated.csv --method deterministic
```

Note: default validation is relaxed (to avoid false errors from regex/type mismatches in narrative fields).
Use strict checks only if needed:
```powershell
python main.py consolidate --strict-validation
```

Optional LLM reconciliation using your second prompt pattern (JSON input/output):
```powershell
python main.py consolidate --schema data/parameters.template.csv --input-dir outputs/individual_json --output-file outputs/consolidated_validated.json --method llm --provider groq
```

## What gets created
- `outputs/individual_json/provider_json/<company>__<provider>.json`: parsed provider output
- `outputs/individual_json/<company>.json`: merged raw rows (~489)
- `outputs/consolidated_validated.csv`: final golden output
- `outputs/consolidated_validated.json`: validation summary (supporting artifact)

## Consolidation Logic Implemented
- Drop `Not Found` / `N/A` / `Unknown` / blank when alternatives exist.
- Pick most complete candidate for each ID.
- Keep selected `Source` with selected data.
- Keep one row per ID (1..163) only.
- No fabrication, no cross-row merging.

## Validation Layers (Pydantic)
- `before_generation`:
  - Schema correctness checks (required schema fields, duplicate IDs/columns, min/max sanity, A/C validity).
- `after_generation`:
  - Row-level checks (required output fields, ID numeric, A/C validity, source presence, type/enum checks from schema).
  - Failed parameters are re-generated per-ID automatically.
- `during_consolidation`:
  - Re-validates consolidated rows with the same Pydantic checks.
  - Any failed IDs are re-generated per-ID and replaced.
  - Consolidated CSV is validated with pytest; if that validation fails, consolidation is retried using `llm` method.
