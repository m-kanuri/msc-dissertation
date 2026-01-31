from __future__ import annotations

import os
from typing import List

from openai import OpenAI


def get_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Run:\n"
            "  export OPENAI_API_KEY='sk-...'\n"
            "Then retry."
        )
    return OpenAI()


def get_model(default: str = "gpt-4o-mini") -> str:
    return os.getenv("OPENAI_MODEL", default)


def embed_text(text: str, *, model: str = "text-embedding-3-small") -> List[float]:
    """
    Returns a single embedding vector for the given text.
    Uses OpenAI embeddings API.
    """
    client = get_client()
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding
