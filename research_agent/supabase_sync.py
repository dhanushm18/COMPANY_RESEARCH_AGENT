from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

try:
    from psycopg import connect
    from psycopg import sql
except Exception:  # pragma: no cover - import is validated at runtime in deployment
    connect = None
    sql = None

from .db_push_export import STAGING_EXPORT_COLUMNS

SUPABASE_CONNECTION_ENV = "SUPABASE_CONNECTION_STRING"
PROVIDER_JSONS_TABLE = "agent_company_jsons"
CONSOLIDATED_TABLE = "consolidated_companies"


def maybe_sync_outputs_to_supabase(
    *,
    provider_json_dir: str | Path,
    consolidated_payload: dict[str, Any],
    ready_records: list[dict[str, Any]],
) -> dict[str, Any]:
    connection_string = os.getenv(SUPABASE_CONNECTION_ENV, "").strip()
    if not connection_string:
        return {
            "enabled": False,
            "skipped": True,
            "reason": f"{SUPABASE_CONNECTION_ENV} is not set",
        }

    return sync_outputs_to_supabase(
        connection_string=connection_string,
        provider_json_dir=provider_json_dir,
        consolidated_payload=consolidated_payload,
        ready_records=ready_records,
    )


def sync_outputs_to_supabase(
    *,
    connection_string: str,
    provider_json_dir: str | Path,
    consolidated_payload: dict[str, Any],
    ready_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if connect is None or sql is None:
        raise RuntimeError(
            "psycopg is required for Supabase sync. Install dependencies with `uv sync` or `pip install -r requirements.txt`."
        )

    provider_rows = _load_provider_json_rows(provider_json_dir)
    consolidated_rows = _build_consolidated_rows(consolidated_payload, ready_records)
    normalized_connection_string = _normalize_connection_string(connection_string)

    with connect(normalized_connection_string) as conn:
        with conn.cursor() as cur:
            _ensure_provider_jsons_table(cur)
            _ensure_consolidated_table(cur)
            provider_upserts = _upsert_provider_jsons(cur, provider_rows)
            consolidated_upserts = _upsert_consolidated_rows(cur, consolidated_rows)
        conn.commit()

    return {
        "enabled": True,
        "skipped": False,
        "provider_json_table": PROVIDER_JSONS_TABLE,
        "consolidated_table": CONSOLIDATED_TABLE,
        "provider_json_rows": provider_upserts,
        "consolidated_rows": consolidated_upserts,
    }


def _normalize_connection_string(connection_string: str) -> str:
    if "://" not in connection_string:
        return connection_string

    scheme, rest = connection_string.split("://", 1)
    if "/" not in rest:
        return connection_string

    authority, tail = rest.split("/", 1)
    if "@" not in authority or ":" not in authority:
        return connection_string

    credentials, host = authority.rsplit("@", 1)
    if ":" not in credentials:
        return connection_string

    username, password = credentials.split(":", 1)
    normalized_user = quote(unquote(username), safe="")
    normalized_password = quote(unquote(password), safe="")
    return f"{scheme}://{normalized_user}:{normalized_password}@{host}/{tail}"


def _load_provider_json_rows(provider_json_dir: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(Path(provider_json_dir).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "company_name": str(payload.get("company_name", "")).strip(),
                "provider": str(payload.get("provider", "")).strip(),
                "generated_at": payload.get("generated_at"),
                "row_count": int(payload.get("row_count", 0) or 0),
                "source_file": str(path.as_posix()),
                "payload": json.dumps(payload),
                "validation": json.dumps(payload.get("validation", {})),
            }
        )
    return rows


def _build_consolidated_rows(
    consolidated_payload: dict[str, Any],
    ready_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    generated_by_company: dict[str, Any] = {}
    rows_by_company: dict[str, Any] = {}
    for company in consolidated_payload.get("companies", []):
        company_name = str(company.get("company_name", "")).strip()
        generated_by_company[company_name] = company.get("generated_at")
    for company in consolidated_payload.get("consolidated_rows", []):
        company_name = str(company.get("company_name", "")).strip()
        rows_by_company[company_name] = company

    consolidated_rows: list[dict[str, Any]] = []
    data_columns = [c for c in STAGING_EXPORT_COLUMNS if c != "company_id"]
    for ready_record in ready_records:
        company_id = int(ready_record["company_id"])
        source_company_name = str(ready_record.get("name", "")).strip()
        raw_payload = rows_by_company.get(source_company_name, {"company_name": source_company_name, "rows": []})
        row: dict[str, Any] = {
            "company_id": company_id,
            "source_company_name": source_company_name,
            "generated_at": generated_by_company.get(source_company_name),
            "raw_payload": json.dumps(raw_payload),
            "ready_record": json.dumps(ready_record),
        }
        for column in data_columns:
            row[column] = str(ready_record.get(column, "") or "")
        consolidated_rows.append(row)
    return consolidated_rows


def _ensure_provider_jsons_table(cur: Any) -> None:
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PROVIDER_JSONS_TABLE} (
            id BIGSERIAL PRIMARY KEY,
            company_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            generated_at TIMESTAMPTZ NULL,
            row_count INTEGER NOT NULL DEFAULT 0,
            source_file TEXT NOT NULL,
            payload JSONB NOT NULL,
            validation JSONB NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT {PROVIDER_JSONS_TABLE}_company_provider_key UNIQUE (company_name, provider)
        )
        """
    )


def _ensure_consolidated_table(cur: Any) -> None:
    data_columns = [c for c in STAGING_EXPORT_COLUMNS if c != "company_id"]
    columns_sql = [
        sql.SQL("{} TEXT").format(sql.Identifier(column))
        for column in data_columns
    ]
    query = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {table_name} (
            company_id INTEGER PRIMARY KEY,
            source_company_name TEXT NOT NULL,
            generated_at TIMESTAMPTZ NULL,
            raw_payload JSONB NOT NULL,
            ready_record JSONB NOT NULL,
            {data_columns},
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    ).format(
        table_name=sql.Identifier(CONSOLIDATED_TABLE),
        data_columns=sql.SQL(", ").join(columns_sql),
    )
    cur.execute(query)


def _upsert_provider_jsons(cur: Any, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    cur.executemany(
        f"""
        INSERT INTO {PROVIDER_JSONS_TABLE} (
            company_name,
            provider,
            generated_at,
            row_count,
            source_file,
            payload,
            validation
        )
        VALUES (
            %(company_name)s,
            %(provider)s,
            %(generated_at)s,
            %(row_count)s,
            %(source_file)s,
            %(payload)s::jsonb,
            %(validation)s::jsonb
        )
        ON CONFLICT (company_name, provider) DO UPDATE SET
            generated_at = EXCLUDED.generated_at,
            row_count = EXCLUDED.row_count,
            source_file = EXCLUDED.source_file,
            payload = EXCLUDED.payload,
            validation = EXCLUDED.validation,
            updated_at = NOW()
        """,
        rows,
    )
    return len(rows)


def _upsert_consolidated_rows(cur: Any, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    data_columns = [c for c in STAGING_EXPORT_COLUMNS if c != "company_id"]
    insert_columns = ["company_id", "source_company_name", "generated_at", "raw_payload", "ready_record", *data_columns]
    update_columns = ["source_company_name", "generated_at", "raw_payload", "ready_record", *data_columns]

    insert_sql = sql.SQL(", ").join(sql.Identifier(column) for column in insert_columns)
    values_sql = []
    for column in insert_columns:
        if column in {"raw_payload", "ready_record"}:
            values_sql.append(sql.SQL("%({})s::jsonb").format(sql.SQL(column)))
        else:
            values_sql.append(sql.SQL("%({})s").format(sql.SQL(column)))
    update_sql = sql.SQL(", ").join(
        sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(column))
        for column in update_columns
    )
    query = sql.SQL(
        """
        INSERT INTO {table_name} ({insert_columns})
        VALUES ({values})
        ON CONFLICT (company_id) DO UPDATE SET
            {update_columns},
            updated_at = NOW()
        """
    ).format(
        table_name=sql.Identifier(CONSOLIDATED_TABLE),
        insert_columns=insert_sql,
        values=sql.SQL(", ").join(values_sql),
        update_columns=update_sql,
    )
    cur.executemany(query, rows)
    return len(rows)
