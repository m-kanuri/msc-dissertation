from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AuditLogger:
    run_folder: Path
    _start_time: float

    @classmethod
    def create(cls, run_folder: Path) -> AuditLogger:
        run_folder.mkdir(parents=True, exist_ok=True)
        return cls(run_folder=run_folder, _start_time=time.time())

    def log(self, event: str, payload: dict[str, Any]) -> None:
        record = {
            "ts": time.time(),
            "elapsed_s": round(time.time() - self._start_time, 3),
            "event": event,
            **payload,
        }
        path = self.run_folder / "audit_log.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
