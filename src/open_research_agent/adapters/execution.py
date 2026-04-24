from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ExecutionBackend(ABC):
    @abstractmethod
    def execute(self, workspace: Path, plan: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class DryRunExecutionBackend(ExecutionBackend):
    def execute(self, workspace: Path, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "backend": "dry_run",
            "status": "completed",
            "runs": [
                {
                    "name": "dry_run_protocol_check",
                    "command": None,
                    "return_code": 0,
                    "summary": "No command executed; plan was converted into a traceable pseudo-run.",
                }
            ],
        }


class ShellExecutionBackend(ExecutionBackend):
    def __init__(self, commands: list[str] | None = None, timeout: int = 7200):
        self.commands = commands or []
        self.timeout = timeout

    def execute(self, workspace: Path, plan: dict[str, Any]) -> dict[str, Any]:
        commands = self.commands or plan.get("commands", [])
        if not commands and (workspace / "code" / "experiments" / "run_experiment.py").exists():
            commands = [
                "python code/experiments/run_experiment.py "
                "--config code/experiments/config.json "
                "--output code/experiments/result.json"
            ]
        run_dir = workspace / "logs" / "shell_runs"
        run_dir.mkdir(parents=True, exist_ok=True)
        runs = []
        for index, command in enumerate(commands, start=1):
            result = subprocess.run(
                command,
                cwd=str(workspace),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            log_path = run_dir / f"run_{index:02d}.json"
            record = {
                "name": f"shell_run_{index:02d}",
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-4000:],
            }
            log_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            runs.append(record)
        return {"backend": "shell", "status": "completed", "runs": runs}


def build_execution_backend(name: str, commands: list[str] | None = None) -> ExecutionBackend:
    if name == "dry-run":
        return DryRunExecutionBackend()
    if name == "shell":
        return ShellExecutionBackend(commands=commands)
    raise ValueError(f"Unsupported execution backend: {name}")
