from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from dissertation.core.db import get_engine
from dissertation.core.db_models import ArtifactRow, RequirementRow


def get_cached_by_hash(text_hash: str) -> dict | None:
    engine = get_engine()
    with Session(engine) as s:
        req = s.scalar(select(RequirementRow).where(RequirementRow.text_hash == text_hash))
        if not req:
            return None

        art = s.scalar(select(ArtifactRow).where(ArtifactRow.requirement_id == req.id))
        if not art:
            return None

        return art.content_json


def get_cached_by_similarity(
    embedding: Sequence[float],
    *,
    min_similarity: float = 0.60,
) -> tuple[dict, float, int] | None:
    engine = get_engine()
    with Session(engine) as s:
        dist_expr = RequirementRow.embedding.cosine_distance(list(embedding))  # type: ignore[attr-defined]

        stmt = (
            select(ArtifactRow.content_json, dist_expr.label("dist"), RequirementRow.id)
            .join(RequirementRow, RequirementRow.id == ArtifactRow.requirement_id)
            .where(RequirementRow.embedding.is_not(None))
            .where(ArtifactRow.output_type == "bundle")
            .order_by("dist")
            .limit(1)
        )

        row = s.execute(stmt).first()
        if not row:
            return None

        bundle_json, dist, req_id = row
        similarity = 1.0 - float(dist)

        if similarity < min_similarity:
            return None

        return bundle_json, similarity, int(req_id)



def store_bundle(
    *,
    raw_text: str,
    normalized_text: str,
    text_hash: str,
    embedding,
    bundle_json: dict,
    model: str,
    prompt_version: str,
    cache_hit: str | None = None,
    similarity: float | None = None,
    source_requirement_id: int | None = None,
    policy_version: str | None = None,
) -> None:
    cache_metadata = {
        "cache_hit": cache_hit,
        "similarity": similarity,
        "source_requirement_id": source_requirement_id,
        "policy_version": policy_version,
        "prompt_version": prompt_version,
        "model": model,
    }
    cache_metadata = {k: v for k, v in cache_metadata.items() if v is not None}

    engine = get_engine()
    with Session(engine) as s:
        existing_req = s.scalar(select(RequirementRow).where(RequirementRow.text_hash == text_hash))
        if existing_req:
            existing_art = s.scalar(
                select(ArtifactRow).where(ArtifactRow.requirement_id == existing_req.id)
            )
            if not existing_art:
                s.add(
                    ArtifactRow(
                        requirement_id=existing_req.id,
                        output_type="bundle",
                        content_json=bundle_json,
                        model=model,
                        prompt_version=prompt_version,
                        metadata_json=cache_metadata,
                    )
                )
                s.commit()
            return

        req = RequirementRow(
            raw_text=raw_text,
            normalized_text=normalized_text,
            text_hash=text_hash,
            embedding=embedding,
        )
        s.add(req)
        s.flush()

        art = ArtifactRow(
            requirement_id=req.id,
            output_type="bundle",
            content_json=bundle_json,
            model=model,
            prompt_version=prompt_version,
            metadata_json=cache_metadata,
        )
        s.add(art)
        s.commit()

