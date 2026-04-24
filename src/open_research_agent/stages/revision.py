from __future__ import annotations

from pathlib import Path

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class RevisionStage(Stage):
    name = "revision"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        data = self.provider.complete_json(
            role="revision_editor",
            task="revision",
            context=dict(context),
            schema_hint={"revision_plan": "list[str]", "accepted": "bool"},
        )
        draft_path = Path(context["draft_path"])
        draft = draft_path.read_text(encoding="utf-8")
        note = "\n\n## Revision Note\n\n"
        for item in data.get("revision_plan", []):
            note += f"- {item}\n"
        final_path = workspace.write_markdown("paper", "final_draft.md", draft + note)
        artifact_path = workspace.write_artifact(Artifact(self.name, "revision_plan", data))
        return StageResult.ok(
            self.name,
            [artifact_path, final_path],
            revision=data,
            final_draft_path=final_path,
        )
