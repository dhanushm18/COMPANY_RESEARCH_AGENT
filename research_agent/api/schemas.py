from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class RunPipelineRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "schema": "data/parameters.template.csv",
                "companies": "data/companies.json",
                "providers": ["groq", "gemini", "baseten"],
                "method": "deterministic",
                "provider": "groq",
                "strict_validation": False,
                "agent1_retry_limit": 1,
            }
        },
    )

    schema_path: str = Field(default="data/parameters.template.csv", alias="schema")
    companies: str = Field(default="data/companies.json")
    output_dir: str = Field(default="outputs/individual_json")
    providers: list[Literal["groq", "gemini", "baseten"]] = Field(
        default_factory=lambda: ["groq", "gemini", "baseten"],
        min_length=1,
    )
    output_file: str = Field(default="outputs/consolidated_validated.json")
    output_csv: str = Field(default="outputs/consolidated_validated.csv")
    ready_db_csv: str = Field(default="outputs/ready_for_db_push.csv")
    ready_db_json: str = Field(default="outputs/ready_for_db_push.json")
    company_id_start: int = Field(default=1, ge=1)
    method: Literal["deterministic", "llm"] = "deterministic"
    provider: Literal["groq", "gemini", "baseten"] = "groq"
    model: str | None = None
    strict_validation: bool = False
    agent1_retry_limit: int = Field(default=1, ge=1)

class RunPipelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    run_id: str
    pydantic_validation: dict
    pytest_validation: dict
    pytest_regeneration: dict
    pytest_validation_agent2: dict
    consolidated_json_path: str | None = None
    consolidated_csv_path: str | None = None
    ready_db_csv_path: str | None = None
    ready_db_json_path: str | None = None
    state: dict
