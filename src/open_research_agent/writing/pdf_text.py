from __future__ import annotations

from pathlib import Path


def load_pdf_text(path: str | Path, max_pages: int | None = None) -> str:
    pdf_path = Path(path)
    try:
        import pymupdf4llm

        if max_pages is None:
            return pymupdf4llm.to_markdown(str(pdf_path))
        return pymupdf4llm.to_markdown(str(pdf_path), pages=list(range(max_pages)))
    except Exception:
        pass
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pages = reader.pages if max_pages is None else reader.pages[:max_pages]
        return "\n".join(page.extract_text() or "" for page in pages)
    except Exception as exc:
        raise RuntimeError(f"Unable to extract text from PDF: {pdf_path}") from exc
