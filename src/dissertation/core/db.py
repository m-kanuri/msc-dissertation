from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Run:\n"
            "  export DATABASE_URL='postgresql+psycopg://user@localhost:5432/disserdb'\n"
            "Then retry."
        )

    _engine = create_engine(url, pool_pre_ping=True)
    return _engine
