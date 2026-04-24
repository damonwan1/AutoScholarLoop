from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class IdeationStage(Stage):
    name = "ideation"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="idea_committee",
            task="ideation",
            context=dict(context),
            schema_hint={"candidates": "list[idea]", "self_critique": "str"},
        )
        md = ["# Candidate Directions", ""]
        for item in data.get("candidates", []):
            md.append(f"## {item.get('id')}: {item.get('title')}")
            md.append(f"- Hypothesis: {item.get('hypothesis')}")
            md.append(f"- Novelty claim: {item.get('novelty_claim')}")
            md.append(f"- Feasibility: {item.get('feasibility')}")
        md_path = workspace.write_markdown("artifacts", "candidate_directions.md", "\n".join(md))
        json_path = workspace.write_artifact(Artifact(self.name, "candidate_directions", data))
        return StageResult.ok(self.name, [json_path, md_path], ideas=data)
