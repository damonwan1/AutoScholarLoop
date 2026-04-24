from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class PlanningStage(Stage):
    name = "planning"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="experiment_planner",
            task="planning",
            context=dict(context),
            schema_hint={"objective": "str", "work_packages": "list[str]", "success_metrics": "list[str]"},
        )
        path = workspace.write_artifact(Artifact(self.name, "exploration_plan", data))
        return StageResult.ok(self.name, [path], plan=data)
