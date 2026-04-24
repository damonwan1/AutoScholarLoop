from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Artifact:
    stage: str
    kind: str
    data: dict[str, Any]
    created_at: str = field(default_factory=utc_now)


@dataclass
class StageResult:
    stage: str
    status: str
    artifacts: list[str]
    updates: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, stage: str, artifacts: list[str], **updates: Any) -> "StageResult":
        return cls(stage=stage, status="ok", artifacts=artifacts, updates=updates)
