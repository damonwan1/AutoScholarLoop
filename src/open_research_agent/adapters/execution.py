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
        fallback = _fallback_experiment_command(workspace)
        if not commands and fallback:
            commands = [fallback]
        run_dir = workspace / "logs" / "shell_runs"
        run_dir.mkdir(parents=True, exist_ok=True)
        runs = []
        for index, command in enumerate(commands, start=1):
            skip_reason = _skip_reason(command, workspace)
            if skip_reason:
                record = {
                    "name": f"shell_run_{len(runs) + 1:02d}",
                    "command": command,
                    "normalized_command": None,
                    "return_code": 0,
                    "stdout": "",
                    "stderr": "",
                    "summary": f"Skipped unsafe or non-portable generated command: {skip_reason}",
                    "skipped": True,
                }
                (run_dir / f"run_{len(runs) + 1:02d}.json").write_text(
                    json.dumps(record, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                runs.append(record)
                continue
            normalized_command = _normalize_command(command, workspace)
            runs.append(_run_command(workspace, run_dir, len(runs) + 1, normalized_command, original_command=command))
        if fallback and not (workspace / "code" / "experiments" / "result.json").exists():
            runs.append(_run_command(workspace, run_dir, len(runs) + 1, fallback, fallback=fallback))
        has_result = (workspace / "code" / "experiments" / "result.json").exists()
        status = "completed" if has_result or all(run["return_code"] == 0 for run in runs) else "failed"
        return {"backend": "shell", "status": status, "runs": runs}


def build_execution_backend(name: str, commands: list[str] | None = None) -> ExecutionBackend:
    if name == "dry-run":
        return DryRunExecutionBackend()
    if name == "shell":
        return ShellExecutionBackend(commands=commands)
    raise ValueError(f"Unsupported execution backend: {name}")


def _normalize_command(command: str, workspace: Path | None = None) -> str:
    stripped = command.strip()
    if stripped.startswith("python3 "):
        stripped = "python " + stripped[len("python3 ") :]
    if stripped.startswith("cd /workspace && "):
        stripped = stripped[len("cd /workspace && ") :]
    if stripped.startswith("cd /workspace; "):
        stripped = stripped[len("cd /workspace; ") :]
    if stripped.startswith("cd experiments && "):
        return "cd code/experiments && " + stripped[len("cd experiments && ") :]
    if stripped.startswith("cd experiments; "):
        return "cd code/experiments; " + stripped[len("cd experiments; ") :]
    if stripped.startswith("cd analysis && "):
        return "cd code/analysis && " + stripped[len("cd analysis && ") :]
    if stripped.startswith("cd analysis; "):
        return "cd code/analysis; " + stripped[len("cd analysis; ") :]
    if stripped.startswith("python experiments/"):
        return "python code/" + stripped[len("python ") :]
    if stripped.startswith("python analysis/"):
        return "python code/" + stripped[len("python ") :]
    if stripped.startswith("python ") and workspace is not None:
        parts = stripped.split()
        if len(parts) >= 2 and parts[1].endswith(".py"):
            script = parts[1].replace("\\", "/")
            if not script.startswith("code/"):
                candidates = [workspace / "code" / script, workspace / "code" / "experiments" / script]
                for candidate in candidates:
                    if candidate.exists():
                        parts[1] = str(candidate.relative_to(workspace)).replace("\\", "/")
                        return " ".join(parts)
    if stripped.startswith("python -m pip install -r requirements.txt"):
        return stripped.replace("requirements.txt", "code/requirements.txt", 1)
    if stripped.startswith("pip install -r requirements.txt"):
        return stripped.replace("requirements.txt", "code/requirements.txt", 1)
    if stripped.startswith("mkdir -p "):
        targets = [item.strip().strip('"').strip("'") for item in stripped[len("mkdir -p ") :].split() if item.strip()]
        quoted = ", ".join(repr(target) for target in targets)
        return (
            f'"{sys.executable}" -c "from pathlib import Path; '
            f'[Path(p).mkdir(parents=True, exist_ok=True) for p in [{quoted}]]"'
        )
    return command


def _skip_reason(command: str, workspace: Path | None = None) -> str | None:
    lower = command.strip().lower()
    if not lower:
        return "empty command"
    cd_target = _cd_target(command)
    if cd_target and workspace is not None and not (workspace / cd_target).exists():
        return f"generated cd target does not exist: {cd_target}"
    if "github.com/example/" in lower:
        return "placeholder GitHub repository URL"
    if lower.startswith("git clone ") and "github.com/" in lower:
        return "external repository clone is not a reliable local evidence step"
    if "source venv/bin/activate" in lower:
        return "Linux shell activation command on Windows"
    if lower.startswith("chmod "):
        return "Unix chmod command is not needed on Windows"
    if lower.startswith("./") and lower.endswith(".sh"):
        return "Unix shell script entrypoint is not portable on Windows"
    if lower.startswith("bash ") or lower.startswith("sh "):
        return "Unix shell script command is skipped in the Windows web runner"
    if ".sh" in lower:
        return "Unix shell script command is skipped in the Windows web runner"
    if "python3 -m venv" in lower or "python -m venv" in lower:
        return "generated virtualenv setup is skipped inside the managed run environment"
    missing_req = _missing_requirements_file(command, workspace)
    if missing_req:
        return f"requirements file does not exist: {missing_req}"
    heavy_packages = ("pymarl", "smac", "torchaudio", "torchvision", "cuda", "cu118")
    if "pip install" in lower and any(package in lower for package in heavy_packages):
        return "heavy or platform-specific dependency installation"
    auxiliary_scripts = (
        "baseline_scan.py",
        "run_baselines.py",
        "aggregate_results.py",
        "analyze_results.py",
        "run_mb_marl.py",
    )
    if any(script in lower for script in auxiliary_scripts) and "run_experiment.py" not in lower:
        return "auxiliary generated script is non-blocking; fallback experiment will provide local evidence"
    return None


def _cd_target(command: str) -> Path | None:
    stripped = command.strip()
    separators = ("&&", ";")
    for separator in separators:
        prefix = f"cd "
        if stripped.startswith(prefix) and separator in stripped:
            target = stripped[len(prefix) : stripped.index(separator)].strip().strip('"').strip("'")
            if target and target != "/workspace":
                return Path(target)
    return None


def _missing_requirements_file(command: str, workspace: Path | None) -> str | None:
    if workspace is None:
        return None
    parts = command.strip().split()
    if "-r" not in parts or "pip" not in command.lower():
        return None
    idx = parts.index("-r")
    if idx + 1 >= len(parts):
        return None
    req = Path(parts[idx + 1].strip('"').strip("'"))
    base = workspace
    cd_dir = _cd_target(command)
    if cd_dir:
        base = workspace / cd_dir
    if not (base / req).exists():
        return str(req)
    return None


def _is_generated_experiment_command(command: str) -> bool:
    lower = command.strip().lower()
    markers = (
        "run_experiment.py",
        "run_experiments.py",
        "run_all_baselines.sh",
        "run_experiments.sh",
    )
    return any(marker in lower for marker in markers)


def _run_command(
    workspace: Path,
    run_dir: Path,
    index: int,
    command: str,
    *,
    original_command: str | None = None,
    fallback: str | None = None,
) -> dict[str, Any]:
    _prepare_output_dirs(workspace, command)
    result = subprocess.run(
        command,
        cwd=str(workspace),
        shell=True,
        capture_output=True,
        text=True,
    )
    record = {
        "name": f"shell_run_{index:02d}",
        "command": original_command or command,
        "normalized_command": command,
        "return_code": result.returncode,
        "stdout": _tail(result.stdout),
        "stderr": _tail(result.stderr),
        "summary": _summarize_command(original_command or command, result.returncode, result.stderr or result.stdout),
    }
    if fallback:
        record["fallback"] = True
    (run_dir / f"run_{index:02d}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return record


def _prepare_output_dirs(workspace: Path, command: str) -> None:
    parts = command.split()
    cwd = workspace
    if len(parts) >= 4 and parts[0].lower() == "cd" and parts[2] in {"&&", ";"}:
        cwd = workspace / parts[1]
    for flag in ("--output", "--output_dir"):
        if flag in parts:
            idx = parts.index(flag)
            if idx + 1 < len(parts):
                target = Path(parts[idx + 1].strip('"').strip("'"))
                parent = target if flag == "--output_dir" else target.parent
                if str(parent) not in {"", "."}:
                    (cwd / parent).mkdir(parents=True, exist_ok=True)


def _fallback_experiment_command(workspace: Path) -> str | None:
    script = workspace / "code" / "experiments" / "autoscholar_fallback_experiment.py"
    if script.exists():
        return (
            "python code/experiments/autoscholar_fallback_experiment.py "
            "--config code/experiments/config.json "
            "--output code/experiments/result.json"
        )
    script = workspace / "code" / "experiments" / "run_experiment.py"
    if not script.exists():
        return None
    return (
        "python code/experiments/run_experiment.py "
        "--config code/experiments/config.json "
        "--output code/experiments/result.json"
    )


def _tail(text: str | None, limit: int = 4000) -> str:
    return (text or "")[-limit:]


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
