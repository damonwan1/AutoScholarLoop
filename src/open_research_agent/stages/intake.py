from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class IntakeStage(Stage):
    name = "intake"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="research_director",
            task="intake",
            context=dict(context),
            schema_hint={"problem": "str", "constraints": "list[str]", "references": "list[str]"},
        )
        path = workspace.write_artifact(Artifact(self.name, "normalized_brief", data))
        return StageResult.ok(self.name, [path], brief=data)
