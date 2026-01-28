from __future__ import annotations

import os

from openai import OpenAI


def get_client() -> OpenAI:
    # OpenAI SDK reads OPENAI_API_KEY automatically from env.
    # We still check explicitly to fail fast with a clear message.
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Run:\n" "  export OPENAI_API_KEY='sk-...'\n" "Then retry."
        )
    return OpenAI()


def get_model(default: str = "gpt-4o-mini") -> str:
    return os.getenv("OPENAI_MODEL", default)
