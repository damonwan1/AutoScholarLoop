from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class ExecutionStage(Stage):
    name = "execution"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="executor",
            task="execution",
            context=dict(context),
            schema_hint={"runs": "list[run]", "open_issues": "list[str]"},
        )
        backend_result = self.services["executor"].execute(workspace.root, context.get("plan", {}))
        data["backend_result"] = backend_result
        path = workspace.write_artifact(Artifact(self.name, "execution_report", data))
        return StageResult.ok(self.name, [path], execution=data)
