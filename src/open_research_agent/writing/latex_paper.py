from __future__ import annotations

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


def compile_latex(tex_path: Path, timeout: int = 60) -> dict[str, str | int | bool]:
    if shutil.which("pdflatex") is None:
        return {"compiled": False, "return_code": 127, "message": "pdflatex not found"}
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path.name],
        cwd=str(tex_path.parent),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    pdf_path = tex_path.with_suffix(".pdf")
    return {
        "compiled": pdf_path.exists(),
        "return_code": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "pdf": str(pdf_path) if pdf_path.exists() else "",
    }


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
