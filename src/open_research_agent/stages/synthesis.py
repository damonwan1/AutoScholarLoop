from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class SynthesisStage(Stage):
    name = "synthesis"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="evidence_auditor",
            task="synthesis",
            context=dict(context),
            schema_hint={"claims": "list[claim]", "limitations": "list[str]"},
        )
        path = workspace.write_artifact(Artifact(self.name, "evidence_map", data))
        return StageResult.ok(self.name, [path], evidence=data)
