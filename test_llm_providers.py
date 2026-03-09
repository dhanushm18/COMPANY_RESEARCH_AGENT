from __future__ import annotations

import argparse
import sys

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> None:
        return None

from langchain_core.messages import HumanMessage

from research_agent.llm_provider import build_llm


def _excerpt(text: str, max_chars: int) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def test_provider(provider: str, model: str | None, prompt: str, max_chars: int) -> tuple[bool, str]:
    try:
        llm = build_llm(provider=provider, model=model, temperature=0.0)
        resp = llm.invoke([HumanMessage(content=prompt)])
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        if not content.strip():
            return False, "empty response"
        return True, _excerpt(content, max_chars)
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Quick check for LLM provider connectivity.")
    parser.add_argument(
        "--providers",
        default="groq,gemini,baseten",
        help="Comma-separated providers to test (e.g., groq,gemini,baseten).",
    )
    parser.add_argument("--model", default=None, help="Optional single model override for all tested providers.")
    parser.add_argument("--prompt", default="Reply with exactly: OK", help="Prompt to send to each provider.")
    parser.add_argument("--max-chars", type=int, default=160, help="Max response chars to print.")
    args = parser.parse_args()

    providers = [p.strip().lower() for p in args.providers.split(",") if p.strip()]
    if not providers:
        print("No providers specified.")
        return 2

    print(f"Testing providers: {providers}")
    failures = 0

    for provider in providers:
        ok, detail = test_provider(
            provider=provider,
            model=args.model,
            prompt=args.prompt,
            max_chars=args.max_chars,
        )
        if ok:
            print(f"[PASS] {provider}: {detail}")
        else:
            failures += 1
            print(f"[FAIL] {provider}: {detail}")

    print(f"Summary: total={len(providers)} pass={len(providers) - failures} fail={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
