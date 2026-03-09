from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def build_llm(provider: str | None = None, model: str | None = None, temperature: float = 0.0) -> BaseChatModel:
    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()

    if provider == "groq":
        chosen_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(model=chosen_model, temperature=temperature)

    if provider == "gemini":
        chosen_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        return ChatOpenAI(
            model=chosen_model,
            temperature=temperature,
            api_key=_first_env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            base_url=os.getenv(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
        )

    if provider == "baseten":
        chosen_model = model or os.getenv("BASETEN_MODEL", "deepseek-ai/DeepSeek-V3-0324")
        return ChatOpenAI(
            model=chosen_model,
            temperature=temperature,
            api_key=_first_env("BASETEN_API_KEY", "BASETEN_API"),
            base_url=os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1"),
        )

    raise ValueError(f"unsupported provider: {provider}")
