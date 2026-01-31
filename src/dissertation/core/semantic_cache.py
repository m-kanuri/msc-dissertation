from __future__ import annotations

import hashlib
import re

from dissertation.models.schemas import Epic
from dissertation.core.openai_client import embed_text, get_model
from dissertation.core.cache_store import get_cached_by_hash, get_cached_by_similarity, store_bundle
from dissertation.agents.generator_agent import generate_with_openai, GeneratedBundle



def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _cache_input(epic: Epic) -> str:
    glossary = "\n".join([f"- {g.term}: {g.definition}" for g in epic.glossary]) or "(none)"
    constraints = "\n".join([f"- {c}" for c in epic.constraints]) or "(none)"
    return f"Epic ID: {epic.epic_id}\n\n{epic.text}\n\nConstraints:\n{constraints}\n\nGlossary:\n{glossary}"


def generate_bundle_cached(epic: Epic) -> tuple[GeneratedBundle, dict]:
    raw = _cache_input(epic)
    norm = _normalize(raw)
    h = _hash(norm)

    # 1) exact hit
    cached = get_cached_by_hash(h)
    if cached:
        return GeneratedBundle.model_validate(cached), {"cache_hit": "hash"}

    # 2) semantic hit
    emb = embed_text(norm)
    sim_hit = get_cached_by_similarity(emb, min_similarity=0.60)
    if sim_hit:
        cached_json, sim = sim_hit
        if sim >= 0.80:
            return (
                GeneratedBundle.model_validate(cached_json),
                {"cache_hit": "semantic_reuse", "similarity": float(sim)},
            )
        else:
            # placeholder: refresh path (you can add later)
            return (
                GeneratedBundle.model_validate(cached_json),
                {"cache_hit": "semantic_refresh_needed", "similarity": float(sim)},
            )

    # 3) miss → generate
    bundle = generate_with_openai(epic)

    # 4) store
    store_bundle(
        raw_text=raw,
        normalized_text=norm,
        text_hash=h,
        embedding=emb,
        bundle_json=bundle.model_dump(),
        model=get_model(),
        prompt_version="v1",
    )

    return bundle, {"cache_hit": "miss"}
