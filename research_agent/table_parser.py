from __future__ import annotations

import csv
import io
from typing import Any


EXPECTED_HEADERS = ["ID", "Category", "A/C", "Parameter", "Research Output / Data", "Source"]


def _normalize_header(h: str) -> str:
    return h.strip().lower().replace("  ", " ")


def parse_markdown_table(md: str) -> list[dict[str, Any]]:
    lines = [ln.strip() for ln in md.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    content = "\n".join(ln.strip().strip("|") for ln in lines)
    reader = csv.reader(io.StringIO(content), delimiter="|")
    rows = [list(map(str.strip, r)) for r in reader if r]
    if not rows:
        return []

    headers = rows[0]
    norm_headers = [_normalize_header(h) for h in headers]
    out: list[dict[str, Any]] = []
    for r in rows[1:]:
        # Skip markdown separator rows
        if all(set(cell) <= {"-", ":"} for cell in r):
            continue
        rec = {headers[i]: (r[i] if i < len(r) else "") for i in range(len(headers))}
        mapped = {
            "ID": rec.get(headers[norm_headers.index("id")], "") if "id" in norm_headers else "",
            "Category": rec.get(headers[norm_headers.index("category")], "") if "category" in norm_headers else "",
            "A/C": rec.get(headers[norm_headers.index("a/c")], "") if "a/c" in norm_headers else "",
            "Parameter": rec.get(headers[norm_headers.index("parameter")], "") if "parameter" in norm_headers else "",
            "Research Output / Data": rec.get(
                headers[norm_headers.index("research output / data")], ""
            )
            if "research output / data" in norm_headers
            else "",
            "Source": rec.get(headers[norm_headers.index("source")], "") if "source" in norm_headers else "",
        }
        out.append(mapped)
    return out


def to_markdown_table(rows: list[dict[str, Any]]) -> str:
    header = "| " + " | ".join(EXPECTED_HEADERS) + " |"
    sep = "| " + " | ".join(["---"] * len(EXPECTED_HEADERS)) + " |"
    body = []
    for r in rows:
        vals = [str(r.get(h, "")).replace("\n", " ").strip() for h in EXPECTED_HEADERS]
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep, *body])

