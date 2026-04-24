from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from open_research_agent.writing.bibliography import detect_language, normalize_entry

@dataclass
class PaperRecord:
    title: str
    key: str = ""
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

    def to_bibliography_dict(self) -> dict[str, str | int]:
        return normalize_entry(self.__dict__).to_dict()


class LiteratureProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[PaperRecord]:
        raise NotImplementedError


class LocalLiteratureProvider(LiteratureProvider):
    def search(self, query: str, limit: int = 10) -> list[PaperRecord]:
        if not query:
            return []
        language = detect_language(query)
        return [
            PaperRecord(
                title=f"Provided or local reference related to {query}",
                authors="Local workspace",
                venue="User supplied context",
                year="unknown",
                abstract="Placeholder record used when no external literature engine is configured.",
                language=language,
                source="local",
                entry_type="misc",
                note="Placeholder record used without an external literature engine.",
            )
        ][:limit]


class SemanticScholarProvider(LiteratureProvider):
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, query: str, limit: int = 10) -> list[PaperRecord]:
        params = urlencode(
            {
                "query": query,
                "limit": limit,
                "fields": "title,authors,venue,year,abstract,citationCount,url",
            }
        )
        headers = {}
        api_key = os.getenv("S2_API_KEY")
        if api_key:
            headers["X-API-KEY"] = api_key
        req = Request(f"{self.endpoint}?{params}", headers=headers)
        with urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        time.sleep(1.0)
        records = []
        for item in payload.get("data", []):
            authors = ", ".join(a.get("name", "") for a in item.get("authors", []))
            records.append(
                PaperRecord(
                    title=item.get("title") or "",
                    authors=authors,
                    venue=item.get("venue") or "",
                    year=str(item.get("year") or ""),
                    abstract=item.get("abstract") or "",
                    citations=int(item.get("citationCount") or 0),
                    url=item.get("url") or "",
                    language=detect_language(item.get("title") or "", authors, item.get("venue") or ""),
                    source="semanticscholar",
                    source_id=item.get("paperId") or "",
                )
            )
        return records


class OpenAlexProvider(LiteratureProvider):
    endpoint = "https://api.openalex.org/works"

    def search(self, query: str, limit: int = 10) -> list[PaperRecord]:
        params = {"search": query, "per-page": limit}
        mail = os.getenv("OPENALEX_MAIL_ADDRESS")
        if mail:
            params["mailto"] = mail
        req = Request(f"{self.endpoint}?{urlencode(params)}")
        with urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        records = []
        for item in payload.get("results", []):
            authors = ", ".join(
                a.get("author", {}).get("display_name", "")
                for a in item.get("authorships", [])
            )
            source = ""
            locations = item.get("locations") or []
            if locations and locations[0].get("source"):
                source = locations[0]["source"].get("display_name", "")
            records.append(
                PaperRecord(
                    title=item.get("title") or "",
                    authors=authors,
                    venue=source,
                    year=str(item.get("publication_year") or ""),
                    abstract=item.get("abstract") or "",
                    citations=int(item.get("cited_by_count") or 0),
                    url=item.get("id") or "",
                    doi=((item.get("ids") or {}).get("doi") or ""),
                    language=detect_language(item.get("title") or "", authors, source),
                    source="openalex",
                    source_id=item.get("id") or "",
                )
            )
        return records


def build_literature_provider(name: str) -> LiteratureProvider:
    if name == "local":
        return LocalLiteratureProvider()
    if name == "semanticscholar":
        return SemanticScholarProvider()
    if name == "openalex":
        return OpenAlexProvider()
    raise ValueError(f"Unsupported literature provider: {name}")
