from __future__ import annotations

import json
import os
import shutil
import threading
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
    from fastapi.responses import PlainTextResponse
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
    ("Execution Analysis", "02_execution/RESULTS_ANALYSIS.md"),
    ("Paper Plan", "03_writing/PAPER_PLAN.md"),
    ("Claim Evidence", "03_writing/claim_evidence_table.md"),
    ("Final Gate", "04_quality/final_gate.md"),
    ("Final Draft", "paper/final_draft.md"),
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
    if config.get("api_key"):
        os.environ["OPENAI_API_KEY"] = config["api_key"]
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
    target = (record.workspace / path).resolve()
    root = record.workspace.resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=400, detail="Path is outside workspace.")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return target.read_text(encoding="utf-8", errors="replace")


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
        pipeline.run(
            workspace=ResearchWorkspace.create(record.workspace),
            seed=seed,
            references=references,
            num_ideas=num_ideas,
        )
        record.status = "completed"
    except Exception as exc:  # pragma: no cover - surfaced through API
        record.status = "failed"
        record.error = str(exc)
        (record.workspace / "logs").mkdir(parents=True, exist_ok=True)
        (record.workspace / "logs" / "web_error.txt").write_text(str(exc), encoding="utf-8")
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
    progress = int((completed_count / len(stages)) * 100)
    previews = []
    for title, relpath in PREVIEW_FILES:
        path = record.workspace / relpath
        if path.exists():
            previews.append({"title": title, "path": relpath})
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
        "manifest": manifest,
    }


def _get_job(job_id: str) -> JobRecord:
    with jobs_lock:
        record = jobs.get(job_id)
    if record is None:
        workspace = RUN_ROOT / job_id
        if not workspace.exists():
            raise HTTPException(status_code=404, detail="Run not found.")
        record = JobRecord(id=job_id, workspace=workspace, status="completed")
    return record


def _read_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"provider": "local", "model": "local-researcher", "base_url": None, "api_key": None}
    return _read_json(CONFIG_PATH, default={})


def _public_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": config.get("provider", "local"),
        "model": config.get("model", "local-researcher"),
        "base_url": config.get("base_url"),
        "has_api_key": bool(config.get("api_key")),
    }


def _read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
