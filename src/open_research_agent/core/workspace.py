from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from open_research_agent.core.artifacts import Artifact, utc_now


class ResearchWorkspace:
    def __init__(self, root: Path):
        self.root = root
        self.manifest_path = root / "manifest.json"

    @classmethod
    def create(cls, root: Path) -> "ResearchWorkspace":
        root.mkdir(parents=True, exist_ok=True)
        for child in [
            "inputs",
            "artifacts",
            "logs",
            "paper",
            "reviews",
            "release",
            "source_papers",
            "00_field_context",
            "01_decision",
            "02_execution",
            "03_writing",
            "04_quality",
        ]:
            (root / child).mkdir(exist_ok=True)
        ws = cls(root)
        if not ws.manifest_path.exists():
            ws._write_json(
                ws.manifest_path,
                {
                    "schema": "autoscholarloop.workspace.v1",
                    "created_at": utc_now(),
                    "stages": [],
                    "artifacts": [],
                },
            )
        return ws

    def write_input(self, name: str, data: dict[str, Any]) -> str:
        path = self.root / "inputs" / f"{name}.json"
        self._write_json(path, data)
        return str(path)

    def write_artifact(self, artifact: Artifact) -> str:
        safe_stage = artifact.stage.replace(" ", "_")
        idx = len(self.manifest().get("artifacts", [])) + 1
        path = self.root / "artifacts" / f"{idx:03d}_{safe_stage}_{artifact.kind}.json"
        self._write_json(path, artifact.__dict__)
        self.record_artifact(str(path), artifact)
        return str(path)

    def write_markdown(self, folder: str, filename: str, text: str) -> str:
        path = self.root / folder / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return str(path)

    def write_text(self, folder: str, filename: str, text: str) -> str:
        path = self.root / folder / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return str(path)

    def manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def record_stage(self, stage: str, status: str, artifacts: list[str]) -> None:
        manifest = self.manifest()
        manifest["stages"].append(
            {
                "stage": stage,
                "status": status,
                "artifacts": artifacts,
                "finished_at": utc_now(),
            }
        )
        self._write_json(self.manifest_path, manifest)

    def record_artifact(self, path: str, artifact: Artifact) -> None:
        manifest = self.manifest()
        manifest["artifacts"].append(
            {
                "path": path,
                "stage": artifact.stage,
                "kind": artifact.kind,
                "created_at": artifact.created_at,
            }
        )
        self._write_json(self.manifest_path, manifest)

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
