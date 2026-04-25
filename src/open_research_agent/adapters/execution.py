from __future__ import annotations

import json
import subprocess
import sys
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
            normalized_command = _normalize_command(command)
            result = subprocess.run(
                normalized_command,
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
                "normalized_command": normalized_command,
                "return_code": result.returncode,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-4000:],
                "summary": _summarize_command(command, result.returncode, result.stderr or result.stdout),
            }
            log_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            runs.append(record)
        status = "completed" if all(run["return_code"] == 0 for run in runs) else "failed"
        return {"backend": "shell", "status": status, "runs": runs}


def build_execution_backend(name: str, commands: list[str] | None = None) -> ExecutionBackend:
    if name == "dry-run":
        return DryRunExecutionBackend()
    if name == "shell":
        return ShellExecutionBackend(commands=commands)
    raise ValueError(f"Unsupported execution backend: {name}")


def _normalize_command(command: str) -> str:
    stripped = command.strip()
    if stripped.startswith("mkdir -p "):
        targets = [item.strip().strip('"').strip("'") for item in stripped[len("mkdir -p ") :].split() if item.strip()]
        quoted = ", ".join(repr(target) for target in targets)
        return (
            f'"{sys.executable}" -c "from pathlib import Path; '
            f'[Path(p).mkdir(parents=True, exist_ok=True) for p in [{quoted}]]"'
        )
    return command


def _summarize_command(command: str, return_code: int, output: str) -> str:
    lower = command.lower()
    if "baseline" in lower:
        action = "Baseline reproduction/check"
    elif "experiment" in lower or "train" in lower:
        action = "Experiment execution"
    elif "mkdir" in lower:
        action = "Workspace preparation"
    else:
        action = "Local command"
    if return_code == 0:
        return f"{action} completed successfully."
    reason = (output or "").strip().splitlines()[-1] if output and output.strip() else "command returned a non-zero exit code"
    return f"{action} failed: {reason[:220]}"
