# Research Agent: Multi-LLM Data Generation + Consolidation

This agent automates your two-manual-prompt workflow with JSON outputs:
1. Generate research rows using OpenAI, Groq, and Gemini.
2. Consolidate 3x outputs (489 rows) into one golden record (163 rows).

## Setup
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

Required env vars:
- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`

Optional model overrides:
- `OPENAI_MODEL` (default from library)
- `GROQ_MODEL` (default from library)
- `GEMINI_MODEL` (default `gemini-2.0-flash`)

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
This runs `collect` then `consolidate` using defaults:
- schema: `data/parameters.template.csv`
- companies: `data/companies.json`
- providers: `openai,groq,gemini`
- output: `outputs/consolidated_validated.csv` (final)

If this is first run, install deps once:
```powershell
uv sync
```

1. Generation from 3 APIs (OpenAI + Groq + Gemini):
```powershell
python main.py collect --companies data/companies.json --schema data/parameters.template.csv --providers openai,groq,gemini
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
python main.py consolidate --schema data/parameters.template.csv --input-dir outputs/individual_json --output-file outputs/consolidated_validated.json --method llm --provider openai
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
