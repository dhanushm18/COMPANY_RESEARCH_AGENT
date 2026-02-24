from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


def build_llm(provider: str | None = None, model: str | None = None, temperature: float = 0.0) -> BaseChatModel:
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

    if provider == "openai":
        chosen_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=chosen_model, temperature=temperature)

    if provider == "groq":
        chosen_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(model=chosen_model, temperature=temperature)

    if provider == "gemini":
        chosen_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return ChatGoogleGenerativeAI(model=chosen_model, temperature=temperature)

    raise ValueError(f"unsupported provider: {provider}")
