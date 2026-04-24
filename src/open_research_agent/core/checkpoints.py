from __future__ import annotations

from pathlib import Path

from open_research_agent.core.artifacts import utc_now
from open_research_agent.core.workspace import ResearchWorkspace


LOOP_DIRS = [
    "source_papers",
    "00_field_context",
    "01_decision",
    "02_execution",
    "03_writing",
    "04_quality",
]


def ensure_loop_workspace(workspace: ResearchWorkspace) -> None:
    for folder in LOOP_DIRS:
        (workspace.root / folder).mkdir(parents=True, exist_ok=True)
    progress = workspace.root / "00_field_context" / "progress_index.md"
    if not progress.exists():
        progress.write_text("# Progress Index\n\n", encoding="utf-8")
    state = workspace.root / "00_field_context" / "checkpoint_state.md"
    if not state.exists():
        state.write_text(
            "# Checkpoint State\n\n"
            "- state: initialized\n"
            "- current_stage: S00\n"
            "- current_round: 0\n"
            "- next_action: build field context\n",
            encoding="utf-8",
        )


def write_checkpoint(
    workspace: ResearchWorkspace,
    *,
    folder: str,
    stage: str,
    round_id: int,
    artifact: str,
    title: str,
    body: str,
    state: str,
    next_action: str,
) -> str:
    ensure_loop_workspace(workspace)
    filename = f"{stage}_R{round_id:02d}_{artifact}.md"
    path = workspace.root / folder / filename
    text = f"# {title}\n\nstage: {stage}\nround: {round_id:02d}\nstate: {state}\n\n{body}\n"
    path.write_text(text, encoding="utf-8")
    append_progress(workspace, stage, round_id, path)
    update_state(workspace, state=state, stage=stage, round_id=round_id, next_action=next_action)
    return str(path)


def write_canonical(workspace: ResearchWorkspace, folder: str, filename: str, body: str) -> str:
    ensure_loop_workspace(workspace)
    path = workspace.root / folder / filename
    path.write_text(body, encoding="utf-8")
    return str(path)


def append_progress(workspace: ResearchWorkspace, stage: str, round_id: int, path: Path) -> None:
    progress = workspace.root / "00_field_context" / "progress_index.md"
    with progress.open("a", encoding="utf-8") as handle:
        handle.write(f"- {utc_now()} | {stage} | R{round_id:02d} | {path}\n")


def update_state(
    workspace: ResearchWorkspace,
    *,
    state: str,
    stage: str,
    round_id: int,
    next_action: str,
) -> None:
    path = workspace.root / "00_field_context" / "checkpoint_state.md"
    path.write_text(
        "# Checkpoint State\n\n"
        f"- state: {state}\n"
        f"- current_stage: {stage}\n"
        f"- current_round: {round_id}\n"
        f"- next_action: {next_action}\n"
        f"- updated_at: {utc_now()}\n",
        encoding="utf-8",
    )
