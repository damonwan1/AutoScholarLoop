from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from open_research_agent.core.artifacts import StageResult
from open_research_agent.core.providers import ModelProvider
from open_research_agent.core.workspace import ResearchWorkspace


class PipelineContext(dict):
    pass


class Stage(ABC):
    name: str

    def __init__(self, provider: ModelProvider, **services: Any):
        self.provider = provider
        self.services = services

    @abstractmethod
    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        raise NotImplementedError
