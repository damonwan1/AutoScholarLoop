from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_WS_RE = re.compile(r"\s+")
_NON_KEY_RE = re.compile(r"[^a-z0-9]+")
_YEAR_RE = re.compile(r"(19|20)\d{2}")
_CITE_RE = re.compile(r"\[@([A-Za-z0-9:_-]+)\]")


@dataclass
class BibliographyEntry:
    key: str
    title: str
    authors: str = ""
    venue: str = ""
    year: str = ""
    abstract: str = ""
    citations: int = 0
    url: str = ""
    doi: str = ""
    language: str = "en"
    entry_type: str = "article"
    source: str = "unknown"
    source_id: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_whitespace(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def detect_language(*values: str) -> str:
    text = " ".join(value for value in values if value)
    if any("\u4e00" <= char <= "\u9fff" for char in text):
        return "zh"
    return "en"


def normalize_authors(authors: str) -> str:
    text = normalize_whitespace(authors)
    if not text:
        return ""
    text = text.replace(";", ",")
    pieces = [piece.strip() for piece in text.split(",") if piece.strip()]
    return " and ".join(pieces) if pieces else text


def make_cite_key(title: str, authors: str = "", year: str = "") -> str:
    author_seed = normalize_whitespace(authors).split(",")[0].split(" and ")[0].strip().lower()
    author_seed = _NON_KEY_RE.sub("", author_seed) or "ref"
    title_words = [word for word in _NON_KEY_RE.sub(" ", title.lower()).split() if word]
    title_seed = "".join(title_words[:3]) or "entry"
    year_seed = year if year and year.isdigit() else "nd"
    return f"{author_seed}{year_seed}{title_seed}"[:48]


def ensure_unique_keys(entries: list[BibliographyEntry]) -> list[BibliographyEntry]:
    seen: dict[str, int] = {}
    normalized: list[BibliographyEntry] = []
    for entry in entries:
        base = entry.key or make_cite_key(entry.title, entry.authors, entry.year)
        count = seen.get(base, 0)
        seen[base] = count + 1
        key = base if count == 0 else f"{base}{count + 1}"
        normalized.append(BibliographyEntry(**{**entry.to_dict(), "key": key}))
    return normalized


def normalize_entry(data: dict[str, Any]) -> BibliographyEntry:
    title = normalize_whitespace(str(data.get("title") or "Untitled reference"))
    authors = normalize_authors(str(data.get("authors") or ""))
    year_match = _YEAR_RE.search(str(data.get("year") or ""))
    year = year_match.group(0) if year_match else ""
    venue = normalize_whitespace(str(data.get("venue") or ""))
    abstract = normalize_whitespace(str(data.get("abstract") or ""))
    url = normalize_whitespace(str(data.get("url") or ""))
    doi = normalize_whitespace(str(data.get("doi") or ""))
    source = normalize_whitespace(str(data.get("source") or "unknown"))
    source_id = normalize_whitespace(str(data.get("source_id") or ""))
    note = normalize_whitespace(str(data.get("note") or ""))
    language = normalize_whitespace(str(data.get("language") or "")) or detect_language(title, authors, venue, note)
    entry_type = normalize_whitespace(str(data.get("entry_type") or "article")).lower()
    try:
        citations = int(data.get("citations") or 0)
    except (TypeError, ValueError):
        citations = 0
    key = normalize_whitespace(str(data.get("key") or "")) or make_cite_key(title, authors, year)
    return BibliographyEntry(
        key=key,
        title=title,
        authors=authors,
        venue=venue,
        year=year,
        abstract=abstract,
        citations=citations,
        url=url,
        doi=doi,
        language=language,
        entry_type=entry_type,
        source=source,
        source_id=source_id,
        note=note,
    )


def parse_reference_hint(reference: str) -> BibliographyEntry:
    ref = normalize_whitespace(reference)
    path = Path(ref)
    if path.exists():
        title = path.stem.replace("_", " ").replace("-", " ")
        return normalize_entry(
            {
                "title": title,
                "url": str(path),
                "source": "local_file",
                "entry_type": "misc",
                "note": f"Local reference file: {path.name}",
            }
        )
    parsed = urlparse(ref)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        host = parsed.netloc.lower()
        title = parsed.path.rsplit("/", 1)[-1] or host
        return normalize_entry(
            {
                "title": title.replace("-", " ").replace("_", " "),
                "url": ref,
                "source": host,
                "entry_type": "misc",
                "note": f"Reference URL from {host}",
            }
        )
    return normalize_entry(
        {
            "title": ref,
            "source": "user_reference",
            "entry_type": "misc",
            "note": "User-provided free-form reference hint.",
        }
    )


def dedupe_entries(entries: list[BibliographyEntry]) -> list[BibliographyEntry]:
    deduped: dict[tuple[str, str, str], BibliographyEntry] = {}
    for entry in entries:
        normalized = normalize_entry(entry.to_dict())
        identity = (
            normalized.title.casefold(),
            normalized.year,
            (normalized.doi or normalized.url).casefold(),
        )
        current = deduped.get(identity)
        if current is None:
            deduped[identity] = normalized
            continue
        richer = normalized if _entry_score(normalized) > _entry_score(current) else current
        deduped[identity] = richer
    return ensure_unique_keys(list(deduped.values()))


def _entry_score(entry: BibliographyEntry) -> int:
    return sum(
        int(bool(value))
        for value in [entry.authors, entry.venue, entry.year, entry.abstract, entry.url, entry.doi]
    )


def bibliography_to_bibtex(entries: list[BibliographyEntry]) -> str:
    blocks = []
    for entry in entries:
        fields = [
            ("title", entry.title),
            ("author", entry.authors),
            ("journal", entry.venue if entry.entry_type == "article" else ""),
            ("booktitle", entry.venue if entry.entry_type in {"inproceedings", "conference"} else ""),
            ("year", entry.year),
            ("doi", entry.doi),
            ("url", entry.url),
            ("abstract", entry.abstract),
            ("language", entry.language),
            ("note", entry.note),
        ]
        body = ",\n".join(
            f"  {name} = {{{_escape_bibtex(value)}}}"
            for name, value in fields
            if value
        )
        blocks.append(f"@{entry.entry_type}{{{entry.key},\n{body}\n}}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def bibliography_to_markdown(entries: list[BibliographyEntry]) -> str:
    lines = ["# Reference Inventory", ""]
    for entry in entries:
        lines.extend(
            [
                f"## {entry.key}",
                f"- Title: {entry.title}",
                f"- Authors: {entry.authors or 'unknown'}",
                f"- Venue: {entry.venue or 'unknown'}",
                f"- Year: {entry.year or 'unknown'}",
                f"- Language: {entry.language}",
                f"- Source: {entry.source}",
                f"- DOI: {entry.doi or 'n/a'}",
                f"- URL: {entry.url or 'n/a'}",
                "",
            ]
        )
    return "\n".join(lines)


def bibliography_to_json(entries: list[BibliographyEntry]) -> str:
    return json.dumps([entry.to_dict() for entry in entries], indent=2, ensure_ascii=False)


def extract_cite_keys(text: str) -> list[str]:
    return _CITE_RE.findall(text or "")


def render_citation(entry: BibliographyEntry) -> str:
    parts = [entry.authors, f'"{entry.title}"']
    if entry.venue:
        parts.append(entry.venue)
    if entry.year:
        parts.append(entry.year)
    if entry.doi:
        parts.append(f"DOI: {entry.doi}")
    elif entry.url:
        parts.append(entry.url)
    return ", ".join(part for part in parts if part)


def _escape_bibtex(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
