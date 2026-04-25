from __future__ import annotations

import json
import os
import shutil
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from open_research_agent.core.pipeline import build_default_pipeline
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.writing.paper_formats import FORMATS

try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, PlainTextResponse
except ImportError as exc:  # pragma: no cover - import guard for optional web extra
    raise RuntimeError("Install web dependencies with `pip install .[web]`.") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOCAL_DIR = PROJECT_ROOT / ".local"
CONFIG_PATH = LOCAL_DIR / "web_config.json"
RUN_ROOT = PROJECT_ROOT / "runs" / "web"
STAGE_ORDER = [
    ("S00_field_archive", "S00 Field Archive", "00_field_context"),
    ("S01_professor_decision_loop", "S01 Professor Decision", "01_decision"),
    ("S02_execution_review_loop", "S02 PhD Execution", "02_execution"),
    ("S03_writing_review_loop", "S03 Writing Review", "03_writing"),
    ("S04_quality_gate", "S04 Quality Gate", "04_quality"),
    ("release", "Release", "release"),
]
PREVIEW_FILES = [
    ("Field Map", "00_field_context/field_map.md"),
    ("Idea Report", "01_decision/IDEA_REPORT.md"),
    ("Generated Code", "02_execution/GENERATED_CODE.md"),
    ("Execution Analysis", "02_execution/RESULTS_ANALYSIS.md"),
    ("Paper Plan", "03_writing/PAPER_PLAN.md"),
    ("Claim Evidence", "03_writing/claim_evidence_table.md"),
    ("Final Gate", "04_quality/final_gate.md"),
    ("LaTeX Main", "paper/main.tex"),
    ("Compile Report", "04_quality/compile_report.md"),
    ("Final Draft", "paper/final_draft.md"),
    ("Revision Required", "release/REVISION_REQUIRED.md"),
    ("Run Error", "logs/web_error.txt"),
    ("Traceback", "logs/web_traceback.txt"),
]
DOWNLOAD_FILES = [
    ("LaTeX source", "paper/main.tex"),
    ("Compiled PDF", "paper/main.pdf"),
    ("Final draft", "paper/final_draft.md"),
    ("Manifest", "manifest.json"),
    ("Revision required", "release/REVISION_REQUIRED.md"),
]


@dataclass
class JobRecord:
    id: str
    workspace: Path
    status: str = "queued"
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None


jobs: Dict[str, JobRecord] = {}
jobs_lock = threading.Lock()

app = FastAPI(title="AutoScholarLoop Web API", version="0.2.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "formats": sorted(FORMATS)}


@app.get("/api/config")
def get_config():
    config = _read_config()
    return _public_config(config)


@app.post("/api/config")
def save_config(payload: Dict[str, Any]):
    provider = payload.get("provider", "local")
    if provider not in {"local", "openai-compatible"}:
        raise HTTPException(status_code=400, detail="Unsupported provider.")
    config = {
        "provider": provider,
        "model": payload.get("model") or "local-researcher",
        "base_url": payload.get("base_url") or None,
        "api_key": payload.get("api_key") or _read_config().get("api_key"),
        "http_trust_env": bool(payload.get("http_trust_env", True)),
    }
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    if config.get("api_key"):
        os.environ["OPENAI_API_KEY"] = config["api_key"]
    return _public_config(config)


@app.post("/api/runs")
async def create_run(
    seed: str = Form(...),
    target_venue: str = Form(""),
    paper_format: str = Form("ieee"),
    loop_mode: str = Form("fast"),
    decision_rounds: int = Form(0),
    execution_rounds: int = Form(0),
    writing_rounds: int = Form(0),
    max_big_loops: int = Form(0),
    num_ideas: int = Form(3),
    literature: str = Form("local"),
    execution_backend: str = Form("dry-run"),
    compile_pdf: bool = Form(False),
    demo_mode: bool = Form(False),
    provider: str = Form(""),
    model: str = Form(""),
    base_url: str = Form(""),
    api_key: str = Form(""),
    http_trust_env: bool = Form(True),
    files: Optional[List[UploadFile]] = File(default=None),
):
    if paper_format not in FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported paper format.")
    if loop_mode not in {"fast", "standard", "strict"}:
        raise HTTPException(status_code=400, detail="Unsupported loop mode.")
    config = _read_config()
    if provider:
        config["provider"] = provider
    if model:
        config["model"] = model
    if base_url:
        config["base_url"] = base_url
    if api_key:
        config["api_key"] = api_key
    config["http_trust_env"] = http_trust_env
    if config.get("api_key"):
        os.environ["OPENAI_API_KEY"] = config["api_key"]
    os.environ["AUTOSCHOLARLOOP_HTTP_TRUST_ENV"] = "1" if config.get("http_trust_env", True) else "0"
    if config.get("provider", "local") == "local" and not demo_mode:
        raise HTTPException(
            status_code=400,
            detail=(
                "No model API is configured. Select demo mode to run the local deterministic "
                "provider, or configure an OpenAI-compatible API key for a real research run."
            ),
        )

    job_id = uuid.uuid4().hex[:12]
    workspace = RUN_ROOT / job_id
    ws = ResearchWorkspace.create(workspace)
    references = []
    for upload in files or []:
        if not upload.filename:
            continue
        target = workspace / "source_papers" / Path(upload.filename).name
        with target.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        references.append(str(target))

    enriched_seed = seed.strip()
    if target_venue.strip():
        enriched_seed += f"\n\nTarget venue or journal: {target_venue.strip()}"
    record = JobRecord(id=job_id, workspace=workspace)
    with jobs_lock:
        jobs[job_id] = record

    thread = threading.Thread(
        target=_run_job,
        args=(
            record,
            enriched_seed,
            references,
            config,
            paper_format,
            loop_mode,
            num_ideas,
            literature,
            execution_backend,
            compile_pdf,
            decision_rounds or None,
            execution_rounds or None,
            writing_rounds or None,
            max_big_loops or None,
        ),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id, "workspace": str(workspace), "status_url": f"/api/runs/{job_id}"}


@app.get("/api/runs/{job_id}")
def get_run(job_id: str):
    record = _get_job(job_id)
    return _status_payload(record)


@app.get("/api/runs/{job_id}/artifact", response_class=PlainTextResponse)
def get_artifact(job_id: str, path: str) -> str:
    record = _get_job(job_id)
    target = _resolve_workspace_path(record.workspace, path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return target.read_text(encoding="utf-8", errors="replace")


@app.get("/api/runs/{job_id}/download")
def download_artifact(job_id: str, path: str):
    record = _get_job(job_id)
    target = _resolve_workspace_path(record.workspace, path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return FileResponse(target, filename=target.name)


def _run_job(
    record: JobRecord,
    seed: str,
    references: List[str],
    config: Dict[str, Any],
    paper_format: str,
    loop_mode: str,
    num_ideas: int,
    literature: str,
    execution_backend: str,
    compile_pdf: bool,
    decision_rounds: Optional[int],
    execution_rounds: Optional[int],
    writing_rounds: Optional[int],
    max_big_loops: Optional[int],
) -> None:
    record.status = "running"
    try:
        os.environ["AUTOSCHOLARLOOP_HTTP_TRUST_ENV"] = "1" if config.get("http_trust_env", True) else "0"
        pipeline = build_default_pipeline(
            provider_name=config.get("provider", "local"),
            model=config.get("model", "local-researcher"),
            base_url=config.get("base_url"),
            literature=literature,
            execution_backend=execution_backend,
            compile_pdf=compile_pdf,
            loop_mode=loop_mode,
            max_big_loops=max_big_loops,
            decision_rounds=decision_rounds,
            execution_rounds=execution_rounds,
            writing_rounds=writing_rounds,
            paper_format=paper_format,
        )
        context = pipeline.run(
            workspace=ResearchWorkspace.create(record.workspace),
            seed=seed,
            references=references,
            num_ideas=num_ideas,
        )
        record.status = "completed" if context.get("research_state") == "submission_candidate" else "needs_revision"
    except Exception as exc:  # pragma: no cover - surfaced through API
        record.status = "failed"
        record.error = str(exc)
        (record.workspace / "logs").mkdir(parents=True, exist_ok=True)
        (record.workspace / "logs" / "web_error.txt").write_text(str(exc), encoding="utf-8")
        (record.workspace / "logs" / "web_traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        record.finished_at = datetime.now(timezone.utc).isoformat()


def _status_payload(record: JobRecord) -> Dict[str, Any]:
    manifest = _read_json(record.workspace / "manifest.json", default={"stages": [], "artifacts": []})
    done_stage_names = {stage.get("stage") for stage in manifest.get("stages", [])}
    stages = []
    for index, (key, label, folder) in enumerate(STAGE_ORDER, start=1):
        completed = key in done_stage_names
        stages.append(
            {
                "key": key,
                "label": label,
                "folder": folder,
                "status": "completed" if completed else "pending",
                "index": index,
            }
        )
    completed_count = sum(1 for stage in stages if stage["status"] == "completed")
    if record.status == "running" and completed_count < len(stages):
        stages[completed_count]["status"] = "active"
    elif record.status == "failed":
        failed_stage = _read_current_stage(record.workspace)
        for stage in stages:
            if failed_stage and stage["key"].startswith(failed_stage):
                stage["status"] = "failed"
    elif record.status == "needs_revision":
        return_to = _read_return_to(record.workspace)
        for stage in stages:
            if return_to and stage["key"].startswith(return_to):
                stage["status"] = "needs_revision"
    progress = int((completed_count / len(stages)) * 100)
    previews = []
    for title, relpath in PREVIEW_FILES:
        path = record.workspace / relpath
        if path.exists():
            previews.append({"title": title, "path": relpath})
    for event in _run_events(record.workspace):
        if event.get("path") and not any(item["path"] == event["path"] for item in previews):
            previews.append({"title": event.get("title") or event["message"], "path": event["path"]})
    downloads = []
    for title, relpath in DOWNLOAD_FILES:
        path = record.workspace / relpath
        if path.exists():
            downloads.append({"title": title, "path": relpath, "size": path.stat().st_size})
    return {
        "job_id": record.id,
        "status": record.status,
        "error": record.error,
        "workspace": str(record.workspace),
        "created_at": record.created_at,
        "finished_at": record.finished_at,
        "progress": 100 if record.status == "completed" else progress,
        "stages": stages,
        "previews": previews,
        "downloads": downloads,
        "logs": _run_events(record.workspace),
        "current_action": _current_action(record.workspace, record.status),
        "manifest": manifest,
    }


def _get_job(job_id: str) -> JobRecord:
    with jobs_lock:
        record = jobs.get(job_id)
    if record is None:
        workspace = RUN_ROOT / job_id
        if not workspace.exists():
            raise HTTPException(status_code=404, detail="Run not found.")
        record = JobRecord(id=job_id, workspace=workspace, status=_infer_terminal_status(workspace))
    return record


def _resolve_workspace_path(workspace: Path, path: str) -> Path:
    target = (workspace / path).resolve()
    root = workspace.resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=400, detail="Path is outside workspace.")
    return target


def _run_events(workspace: Path, limit: int = 80) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    progress = workspace / "00_field_context" / "progress_index.md"
    if progress.exists():
        for line in progress.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("- "):
                continue
            parts = [part.strip() for part in line[2:].split("|")]
            if len(parts) >= 4:
                title = _checkpoint_title(parts[1], parts[2], Path(parts[3]).name)
                events.append(
                    {
                        "time": parts[0],
                        "stage": parts[1],
                        "round": parts[2],
                        "message": title,
                        "title": title,
                        "detail": Path(parts[3]).name,
                        "status": "completed",
                        "path": _relative_or_empty(workspace, parts[3]),
                    }
                )
    shell_dir = workspace / "logs" / "shell_runs"
    if shell_dir.exists():
        for log_path in sorted(shell_dir.glob("run_*.json")):
            data = _read_json(log_path, default={})
            return_code = data.get("return_code")
            summary = data.get("summary") or _shell_summary(data)
            events.append(
                {
                    "time": datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "stage": "S02",
                    "round": "shell",
                    "message": summary,
                    "title": "Local experiment command",
                    "detail": f"{data.get('command', 'shell command')} -> rc={return_code}",
                    "status": "completed" if return_code == 0 else "failed",
                    "path": _relative_or_empty(workspace, str(log_path)),
                }
            )
    return events[-limit:]


def _current_action(workspace: Path, status: str) -> str:
    if status == "failed":
        error_path = workspace / "logs" / "web_error.txt"
        error = error_path.read_text(encoding="utf-8", errors="replace").strip() if error_path.exists() else ""
        stage = _read_current_stage(workspace) or "current stage"
        return f"{stage} failed. Reason: {error or 'unknown error'}"
    if status == "needs_revision":
        return_to = _read_return_to(workspace) or "the failed stage"
        return f"Quality gate did not pass. Return to {return_to} for another loop."
    state_path = workspace / "00_field_context" / "checkpoint_state.md"
    if not state_path.exists():
        return "Preparing workspace and reading inputs."
    lines = state_path.read_text(encoding="utf-8", errors="replace").splitlines()
    state = [
        line.replace("- ", "")
        for line in lines
        if line.startswith("- state:") or line.startswith("- current_stage:") or line.startswith("- next_action:")
    ]
    return " | ".join(state[-3:]) or "Running research loop."


def _read_return_to(workspace: Path) -> str:
    gate_path = workspace / "04_quality" / "final_gate.md"
    if not gate_path.exists():
        return ""
    for line in gate_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("- return_to:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_current_stage(workspace: Path) -> str:
    state_path = workspace / "00_field_context" / "checkpoint_state.md"
    if not state_path.exists():
        return ""
    for line in state_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("- current_stage:"):
            return line.split(":", 1)[1].strip()
    return ""


def _checkpoint_title(stage: str, round_id: str, filename: str) -> str:
    label = {
        "S00": "Field archive updated",
        "S01": "Professor group discussed and refined ideas",
        "S02": "PhD execution round recorded",
        "S03": "Writing/review draft checkpoint saved",
        "S04": "Quality audit checkpoint saved",
    }.get(stage, "Research checkpoint saved")
    if "review_memo" in filename:
        label = "Professor review memo saved"
    if "final_gate" in filename:
        label = "Final quality gate completed"
    return f"{label} ({stage} {round_id})"


def _shell_summary(data: dict[str, Any]) -> str:
    command = str(data.get("command", "shell command")).lower()
    rc = data.get("return_code")
    output = str(data.get("stderr") or data.get("stdout") or "").strip().splitlines()
    reason = output[-1] if output else "non-zero exit code"
    if "baseline" in command:
        action = "Baseline reproduction/check"
    elif "experiment" in command or "train" in command:
        action = "Experiment execution"
    elif "mkdir" in command:
        action = "Workspace preparation"
    else:
        action = "Local command"
    return f"{action} completed successfully." if rc == 0 else f"{action} failed: {reason[:220]}"


def _infer_terminal_status(workspace: Path) -> str:
    if (workspace / "release" / "REVISION_REQUIRED.md").exists():
        return "needs_revision"
    if (workspace / "logs" / "web_error.txt").exists():
        return "failed"
    return "completed"


def _relative_or_empty(workspace: Path, path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(workspace.resolve())).replace("\\", "/")
    except Exception:
        return ""


def _read_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {
            "provider": "local",
            "model": "local-researcher",
            "base_url": None,
            "api_key": None,
            "http_trust_env": True,
        }
    return _read_json(CONFIG_PATH, default={})


def _public_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": config.get("provider", "local"),
        "model": config.get("model", "local-researcher"),
        "base_url": config.get("base_url"),
        "has_api_key": bool(config.get("api_key")),
        "http_trust_env": bool(config.get("http_trust_env", True)),
    }


def _read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
