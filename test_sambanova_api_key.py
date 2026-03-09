from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from openai import OpenAI
except Exception as exc:
    print(f"[FAIL] Import error: {exc}")
    raise SystemExit(1)


def main() -> int:
    if load_dotenv:
        load_dotenv()

    api_key = os.getenv("SAMBANOVA_API_KEY") or os.getenv("sambanova_api_key") or os.getenv("SAMBANOVA_API")
    if not api_key:
        print("[FAIL] Missing API key. Set SAMBANOVA_API_KEY in environment/.env")
        return 1

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1/"),
    )

    model = os.getenv("SAMBANOVA_MODEL", "Meta-Llama-3.3-70B-Instruct")
    prompt = os.getenv("SAMBANOVA_PROMPT", "Tell me a joke about artificial intelligence.")

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
    except Exception as exc:
        print(f"[FAIL] API call failed: {exc}")
        return 1

    response = ""
    try:
        for chunk in completion:
            response += chunk.choices[0].delta.content or ""
    except Exception as exc:
        print(f"[FAIL] Stream read failed: {exc}")
        return 1

    if not response.strip():
        print(f"[FAIL] Empty response from model={model}")
        return 1

    print(f"[PASS] model={model} response={response!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
