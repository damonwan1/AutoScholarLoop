from __future__ import annotations

from open_research_agent.adapters.execution import build_execution_backend
from open_research_agent.adapters.literature import build_literature_provider
from open_research_agent.core.loop_state import LoopPolicy
from open_research_agent.core.providers import build_provider
from open_research_agent.core.research_loop import ResearchGroupLoopPipeline
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.stages.drafting import DraftingStage
from open_research_agent.stages.execution import ExecutionStage
from open_research_agent.stages.ideation import IdeationStage
from open_research_agent.stages.intake import IntakeStage
from open_research_agent.stages.novelty import NoveltyStage
from open_research_agent.stages.planning import PlanningStage
from open_research_agent.stages.release import ReleaseStage
from open_research_agent.stages.review import ReviewStage
from open_research_agent.stages.revision import RevisionStage
from open_research_agent.stages.synthesis import SynthesisStage


class ResearchPipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(
        self,
        *,
        workspace: ResearchWorkspace,
        seed: str,
        references: list[str],
        num_ideas: int = 3,
    ) -> PipelineContext:
        context = PipelineContext(seed=seed, references=references, num_ideas=num_ideas)
        workspace.write_input("seed", {"seed": seed, "references": references, "num_ideas": num_ideas})
        for stage in self.stages:
            result = stage.run(workspace, context)
            workspace.record_stage(result.stage, result.status, result.artifacts)
            context.update(result.updates)
        return context


def build_default_pipeline(
    provider_name: str = "local",
    model: str = "local-researcher",
    base_url: str | None = None,
    literature: str = "local",
    execution_backend: str = "dry-run",
    shell_command: list[str] | None = None,
    review_ensemble: int = 1,
    compile_pdf: bool = False,
    loop_mode: str = "standard",
    max_big_loops: int | None = None,
    decision_rounds: int | None = None,
    execution_rounds: int | None = None,
    writing_rounds: int | None = None,
    paper_format: str = "ieee",
) -> ResearchGroupLoopPipeline:
    provider = build_provider(provider_name, model=model, base_url=base_url)
    literature_provider = build_literature_provider(literature)
    executor = build_execution_backend(execution_backend, commands=shell_command)
    services = {
        "literature": literature_provider,
        "executor": executor,
        "review_ensemble": review_ensemble,
        "compile_pdf": compile_pdf,
        "paper_format": paper_format,
    }
    policy = LoopPolicy.from_mode(loop_mode)
    if max_big_loops is not None:
        policy.max_big_loops = max_big_loops
    if decision_rounds is not None:
        policy.decision_rounds = decision_rounds
    if execution_rounds is not None:
        policy.execution_rounds = execution_rounds
    if writing_rounds is not None:
        policy.writing_rounds = writing_rounds
    return ResearchGroupLoopPipeline(
        provider=provider,
        services=services,
        policy=policy,
    )
