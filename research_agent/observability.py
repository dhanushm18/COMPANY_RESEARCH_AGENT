from __future__ import annotations

import os


def configure_langsmith() -> bool:
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGSMITH_API")
    if not api_key:
        return False

    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    os.environ.setdefault("LANGSMITH_PROJECT", "research-agent")
    return True
