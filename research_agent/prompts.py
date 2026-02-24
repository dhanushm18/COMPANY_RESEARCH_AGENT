from __future__ import annotations

from .schema import ParameterSpec


def _schema_table(specs: list[ParameterSpec]) -> str:
    header = (
        "ID\tCategory\tDescription\tParameter\tContent Type to Generate\t"
        "Composite elements - Minimum\tComposite elements - Maximum\tA/C"
    )
    rows = [header]
    for s in specs:
        rows.append(
            "\t".join(
                [
                    str(s.sr_no),
                    s.category or "",
                    s.description or "",
                    s.parameter or s.column_name,
                    s.content_type or "",
                    "" if s.composite_min is None else str(s.composite_min),
                    "" if s.composite_max is None else str(s.composite_max),
                    s.ac or "",
                ]
            )
        )
    return "\n".join(rows)


def generation_prompt(company_name: str, specs: list[ParameterSpec]) -> str:
    return f"""# ROLE ASSIGNMENT

You are an expert Corporate Intelligence Analyst and Data Researcher. Your task is to conduct comprehensive web research to generate a detailed data profile for a specific target company.

# INPUT DATA

1. Target Company: {company_name}
2. Data Schema: table below.

# LOGIC & FORMATTING RULES (CRITICAL)

1. Research & Accuracy:
- Search the web for current, accurate information.
- If exact data is unavailable, provide a professional estimate based on industry benchmarks or similar companies.
- Never leave a field blank. If absolutely no data or estimate is possible, write "Not Found".

2. Atomic vs. Composite Fields (Column "A/C"):
- IF ATOMIC: response must be a single value.
- IF COMPOSITE: response can contain multiple values.
- Use semicolon separator for composite values only.

3. Output Format:
- Return result as a Markdown table.
- Required columns: ID, Category, A/C, Parameter, Research Output / Data, Source
- Keep exact row count equal to the number of schema rows.

# DATA SCHEMA
{_schema_table(specs)}

# TASK EXECUTION
Perform the research for the Target Company using the Data Schema above. Generate the final output table now.
"""


def consolidation_prompt(raw_dataset_json: str) -> str:
    return f"""# ROLE ASSIGNMENT
You are a Data Reconciliation and Validation Engine. Your sole purpose is to process raw datasets, analyze duplicate entries, and consolidate them into a single "Golden Record" master file.

# INPUT DATA
You will be provided with a raw list with duplicate entries.
Columns: ID, Category, A/C, Parameter, Research Output / Data, Source

# THE OBJECTIVE
Reduce the input to exactly one unique row per ID by selecting the best existing row only.

# SELECTION LOGIC (ALGORITHM)
1. Eliminate Empty/Failed Data: Discard rows where 'Research Output / Data' is "Not Found", "N/A", "Unknown", or blank.
2. Maximize Completeness: Select the one that is more detailed, specific, or precise while respecting Atomic vs Composite.
3. Source Validation: Keep Source paired with selected data.
4. Consistency: If versions are identical, output one.

# ZERO FABRICATION POLICY
- DO NOT generate new text.
- DO NOT search the internet.
- DO NOT combine parts of different answers.
- ONLY select existing lines provided.

# OUTPUT FORMAT
Return consolidated table in Markdown with headers:
| ID | Category | A/C | Parameter | Research Output / Data | Source |

# INPUT DATASET (JSON)
{raw_dataset_json}

# EXECUTION
Perform consolidation now. Return JSON only in this exact shape:
{{
  "rows": [
    {{
      "ID": "string",
      "Category": "string",
      "A/C": "string",
      "Parameter": "string",
      "Research Output / Data": "string",
      "Source": "string"
    }}
  ]
}}
"""
