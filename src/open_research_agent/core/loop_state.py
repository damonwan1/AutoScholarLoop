from __future__ import annotations

from dataclasses import dataclass


VALID_STATES = {
    "initialized",
    "field_mapped",
    "ideas_ready",
    "direction_selected",
    "execution_started",
    "execution_under_review",
    "writing_ready",
    "draft_under_review",
    "quality_audit",
    "submission_candidate",
    "pivot_required",
    "killed",
}


@dataclass
class LoopPolicy:
    mode: str = "standard"
    decision_rounds: int = 10
    execution_rounds: int = 5
    writing_rounds: int = 5
    max_big_loops: int = 1

    @classmethod
    def from_mode(cls, mode: str) -> "LoopPolicy":
        if mode == "fast":
            return cls(mode=mode, decision_rounds=3, execution_rounds=2, writing_rounds=3, max_big_loops=1)
        if mode == "standard":
            return cls(mode=mode, decision_rounds=10, execution_rounds=5, writing_rounds=5, max_big_loops=2)
        if mode == "strict":
            return cls(mode=mode, decision_rounds=12, execution_rounds=6, writing_rounds=7, max_big_loops=3)
        raise ValueError(f"Unsupported loop mode: {mode}")
