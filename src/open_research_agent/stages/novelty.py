from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class NoveltyStage(Stage):
    name = "novelty"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="novelty_scout",
            task="novelty",
            context=dict(context),
            schema_hint={"selected_id": "str", "decision": "proceed|revise|reject"},
        )
        literature = self.services["literature"]
        query = data.get("selected_id") or context.get("seed", "")
        records = literature.search(str(query), limit=5)
        data["literature_hits"] = [record.__dict__ for record in records]
        path = workspace.write_artifact(Artifact(self.name, "novelty_decision", data))
        return StageResult.ok(self.name, [path], novelty=data, selected_idea=data.get("selected_id"))
