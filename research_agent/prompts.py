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
- Never use newline, bullets, numbering, or markdown lists inside a cell.

3. Output Format:
- Return result as a Markdown table.
- Required columns: ID, Category, A/C, Parameter, Research Output / Data, Source
- Keep exact row count equal to the number of schema rows.
- Output ONLY one table, no extra explanation text before or after.
- IDs must be present exactly once each.
- `Research Output / Data` must be plain text only:
  - no markdown links (`[text](url)`)
  - no image markdown (`![alt](url)`)
  - no code blocks
- For URL fields, return raw URL string only.

4. Quality & Validation Rules:
- Respect min/max constraints implied by schema intent.
- Respect datatype intent (Integer/Decimal/Percent/URL/Email/Phone where applicable).
- Respect enum-like constraints when categories are clearly bounded.
- If uncertain, give best estimate in valid format rather than invalid prose.
- If impossible, return exactly: Not Found

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


def parameter_regeneration_prompt(
    company_name: str,
    spec: ParameterSpec,
    validation_errors: list[str] | None = None,
) -> str:
    errors = validation_errors or []
    errors_text = "; ".join(errors) if errors else "N/A"
    return f"""You are a corporate research analyst.
Regenerate exactly one parameter value for the company below.

Company: {company_name}
ID: {spec.sr_no}
Category: {spec.category}
Parameter: {spec.parameter or spec.column_name}
A/C: {spec.ac}
Description: {spec.description}
Data Type: {spec.data_type}
Nullability: {spec.nullability}
Regex Pattern: {spec.regex_pattern}
Min: {spec.minimum_element}
Max: {spec.maximum_element}
Validation Errors to Fix: {errors_text}

Rules:
- If A/C is Composite, separate multiple values with semicolon only.
- If exact fact is unavailable, estimate professionally.
- If no estimate possible, return exactly: Not Found
- Return plain value only (no markdown link/image/code/quotes).
- Must satisfy datatype/enum/required constraints implied above.
- Return plain text only. No markdown, no table, no JSON, no quotes.
"""
