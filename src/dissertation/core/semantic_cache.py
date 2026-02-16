from __future__ import annotations

import hashlib
import re

from dissertation.agents.generator_agent import (
    GeneratedBundle,
    generate_with_openai,
)
from dissertation.core.cache_store import (
    get_cached_by_hash,
    get_cached_by_similarity,
    store_bundle,
)
from dissertation.core.openai_client import embed_text, get_model
from dissertation.models.schemas import Epic

# ---- Policy thresholds (cache_policy_v1) ----
REUSE_THRESHOLD = 0.92
ADAPT_THRESHOLD = 0.75
POLICY_VERSION = "cache_policy_v1"


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _cache_input(epic: Epic) -> str:
    glossary = "\n".join([f"- {g.term}: {g.definition}" for g in epic.glossary]) or "(none)"
    constraints = "\n".join([f"- {c}" for c in epic.constraints]) or "(none)"
    return f"Epic ID: {epic.epic_id}\n\n{epic.text}\n\nConstraints:\n{constraints}\n\nGlossary:\n{glossary}"


def _user_message(cache_hit: str, similarity: float | None = None) -> str:
    if cache_hit == "hash":
        return "Exact match found. Reusing cached bundle to save time and cost."
    if cache_hit == "semantic_reuse":
        return f"Found a very close match (similarity {similarity:.2f}). Reusing a previous bundle."
    if cache_hit == "semantic_adapt":
        return f"Found a similar epic (similarity {similarity:.2f}). Adapting a previous bundle to fit this epic."
    return "No close match found. Generating a fresh bundle for best fit."


def generate_bundle_cached(epic: Epic) -> tuple[GeneratedBundle, dict]:
    raw = _cache_input(epic)
    norm = _normalize(raw)
    h = _hash(norm)

    # 1) exact hit
    cached = get_cached_by_hash(h)
    if cached:
        meta = {
            "cache_hit": "hash",
            "policy_version": POLICY_VERSION,
            "user_message": _user_message("hash"),
        }
        return GeneratedBundle.model_validate(cached), meta

    # 2) semantic lookup
    emb = embed_text(norm)

    # NOTE: ideally this returns (cached_json, similarity, source_id)
    # If your current implementation returns only (cached_json, sim), we handle that too.
    sim_hit = get_cached_by_similarity(emb, min_similarity=ADAPT_THRESHOLD)

    if sim_hit:
        # Robust unpacking: supports (cached_json, sim) OR (cached_json, sim, source_id)
        try:
            cached_json, sim, source_requirement_id = sim_hit  # type: ignore[misc]
        except ValueError:
            cached_json, sim = sim_hit  # type: ignore[misc]
            source_requirement_id = None

        sim = float(sim)
        # Explicit policy guardrails (cache_policy_v1)
        if sim < ADAPT_THRESHOLD:
            sim_hit = None
        # 2a) semantic reuse
        if sim >= REUSE_THRESHOLD:
            meta = {
                "cache_hit": "semantic_reuse",
                "similarity": sim,
                "source_requirement_id": source_requirement_id,
                "policy_version": POLICY_VERSION,
                "user_message": _user_message("semantic_reuse", sim),
            }
            return GeneratedBundle.model_validate(cached_json), meta

        # 2b) semantic adapt (explicit band)
        if ADAPT_THRESHOLD <= sim < REUSE_THRESHOLD:
            adapted = generate_with_openai(
                epic,
                draft_bundle=cached_json,
                mode="semantic_adapt",
                similarity=sim,
            )

            store_bundle(
                raw_text=raw,
                normalized_text=norm,
                text_hash=h,
                embedding=emb,
                bundle_json=adapted.model_dump(),
                model=get_model(),
                prompt_version="v1_adapt",
                cache_hit="semantic_adapt",
                similarity=sim,
                source_requirement_id=source_requirement_id,
                policy_version=POLICY_VERSION,
            )

            meta = {
                "cache_hit": "semantic_adapt",
                "similarity": sim,
                "source_requirement_id": source_requirement_id,
                "policy_version": POLICY_VERSION,
                "user_message": _user_message("semantic_adapt", sim),
            }
            return adapted, meta
    # If similarity is in an unexpected range, fall through to miss.

    # 3) miss → generate fresh
    bundle = generate_with_openai(epic)

    # 4) store fresh
    store_bundle(
        raw_text=raw,
        normalized_text=norm,
        text_hash=h,
        embedding=emb,
        bundle_json=bundle.model_dump(),
        model=get_model(),
        prompt_version="v1",
        cache_hit="miss",
        similarity=None,
        source_requirement_id=None,
        policy_version=POLICY_VERSION,
    )

    return bundle, {
        "cache_hit": "miss",
        "policy_version": POLICY_VERSION,
        "user_message": _user_message("miss"),
    }
