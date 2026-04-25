from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from open_research_agent.writing.paper_formats import PaperFormat, get_paper_format


def markdown_to_simple_latex(markdown_text: str, paper_format: PaperFormat | None = None) -> str:
    fmt = paper_format or get_paper_format("ieee")
    lines = [
        fmt.latex_documentclass,
        r"\usepackage{hyperref}",
        r"\usepackage{booktabs}",
        r"\usepackage{graphicx}",
        *fmt.latex_packages,
        r"\title{AUTO Research Paper Draft}",
        r"\author{AutoScholarLoop}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
    ]
    if fmt.key == "chinese_thesis":
        lines = [
            fmt.latex_documentclass,
            r"\usepackage{hyperref}",
            r"\usepackage{booktabs}",
            r"\usepackage{graphicx}",
            *fmt.latex_packages,
            r"\title{Automated Research Thesis Draft}",
            r"\author{AutoScholarLoop}",
            r"\date{\today}",
            r"\begin{document}",
            r"\maketitle",
        ]
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if line.startswith("# "):
            if fmt.key == "chinese_thesis":
                lines.append(r"\chapter*{" + _escape(line[2:]) + "}")
            else:
                lines.append(r"\section*{" + _escape(line[2:]) + "}")
        elif line.startswith("## "):
            if fmt.key == "chinese_thesis":
                lines.append(r"\chapter{" + _escape(line[3:]) + "}")
            else:
                lines.append(r"\section{" + _escape(line[3:]) + "}")
        elif line.startswith("### "):
            lines.append(r"\subsection{" + _escape(line[4:]) + "}")
        elif line.startswith("- "):
            lines.append(r"\noindent $\bullet$ " + _escape(line[2:]) + r"\\")
        elif not line:
            lines.append("")
        else:
            lines.append(_escape(line) + "\n")
    lines.append(r"\end{document}")
    return "\n".join(lines)


def write_latex_from_markdown(markdown_path: Path, tex_path: Path, paper_format_key: str = "ieee") -> Path:
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    text = markdown_path.read_text(encoding="utf-8")
    tex_path.write_text(markdown_to_simple_latex(text, get_paper_format(paper_format_key)), encoding="utf-8")
    return tex_path


def compile_latex(tex_path: Path, timeout: int = 120) -> dict[str, str | int | bool]:
    fmt = _read_format_key(tex_path.parent / "format_profile.json")
    engines = _candidate_engines(fmt)
    if not engines:
        return {
            "compiled": False,
            "return_code": 127,
            "message": "No LaTeX engine found. Install latexmk, xelatex, or pdflatex.",
            "pdf": "",
        }
    logs = []
    return_code = 0
    pdf_path = tex_path.with_suffix(".pdf")
    used_engine = ""
    for engine in engines:
        used_engine = engine
        commands = _compile_commands(engine, tex_path.name, needs_bibtex=(tex_path.parent / "references.bib").exists())
        engine_logs = []
        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    cwd=str(tex_path.parent),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                return {
                    "compiled": False,
                    "return_code": 124,
                    "message": f"LaTeX command timed out: {' '.join(command)}",
                    "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                    "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
                    "pdf": "",
                }
            return_code = result.returncode
            entry = {
                "engine": engine,
                "command": " ".join(command),
                "return_code": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            }
            logs.append(entry)
            engine_logs.append(entry)
        if pdf_path.exists():
            break
        # latexmk on MiKTeX commonly fails without Perl; try the direct engine next.
        if engine.startswith("latexmk"):
            continue
        if engine_logs and all(item["return_code"] != 0 for item in engine_logs):
            continue
    return {
        "compiled": pdf_path.exists(),
        "return_code": return_code,
        "engine": used_engine,
        "passes": len(logs),
        "stdout": "\n".join(item["stdout"] for item in logs)[-4000:],
        "stderr": "\n".join(item["stderr"] for item in logs)[-4000:],
        "commands": json.dumps(logs, ensure_ascii=False),
        "pdf": str(pdf_path) if pdf_path.exists() else "",
    }


def _read_format_key(profile_path: Path) -> str:
    if not profile_path.exists():
        return "ieee"
    try:
        return json.loads(profile_path.read_text(encoding="utf-8")).get("key", "ieee")
    except json.JSONDecodeError:
        return "ieee"


def _select_engine(format_key: str) -> str | None:
    engines = _candidate_engines(format_key)
    return engines[0] if engines else None


def _candidate_engines(format_key: str) -> list[str]:
    engines = []
    if shutil.which("latexmk"):
        engines.append("latexmk-xelatex" if format_key == "chinese_thesis" else "latexmk-pdflatex")
    if format_key == "chinese_thesis" and shutil.which("xelatex"):
        engines.append("xelatex")
    if shutil.which("pdflatex"):
        engines.append("pdflatex")
    if shutil.which("xelatex"):
        engines.append("xelatex")
    return engines


def _compile_commands(engine: str, tex_name: str, needs_bibtex: bool) -> list[list[str]]:
    stem = Path(tex_name).stem
    if engine == "latexmk-pdflatex":
        return [["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", tex_name]]
    if engine == "latexmk-xelatex":
        return [["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_name]]
    base = [engine, "-interaction=nonstopmode", "-halt-on-error", tex_name]
    commands = [base]
    if needs_bibtex and shutil.which("bibtex"):
        commands.append(["bibtex", stem])
    commands.extend([base, base])
    return commands


def _escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text
