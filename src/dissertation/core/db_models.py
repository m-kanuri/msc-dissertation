from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, String, DateTime, func, JSON, BigInteger
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class RequirementRow(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # 1536 dimensions for text-embedding-3-small
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArtifactRow(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    requirement_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    output_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "bundle"
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
