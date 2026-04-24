from __future__ import annotations

import json
from pathlib import Path

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class ReleaseStage(Stage):
    name = "release"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        package = {
            "final_draft": context.get("final_draft_path"),
            "manifest": str(workspace.manifest_path),
            "reproducibility_note": "This v0.1 run used the configured provider and recorded all stage artifacts.",
        }
        path = workspace.write_artifact(Artifact(self.name, "release_package", package))
        summary = workspace.root / "release" / "README.md"
        summary.write_text(
            "# Release Package\n\n"
            f"- Final draft: {package['final_draft']}\n"
            f"- Manifest: {package['manifest']}\n",
            encoding="utf-8",
        )
        return StageResult.ok(self.name, [path, str(summary)], release=package)
