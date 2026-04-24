from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.writing.latex_paper import compile_latex, write_latex_from_markdown
from open_research_agent.writing.markdown_paper import build_markdown_paper


class DraftingStage(Stage):
    name = "drafting"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        paper = build_markdown_paper(context)
        paper_path = workspace.write_markdown("paper", "draft.md", paper)
        outputs = [paper_path]
        tex_path = write_latex_from_markdown(
            workspace.root / "paper" / "draft.md",
            workspace.root / "paper" / "draft.tex",
        )
        outputs.append(str(tex_path))
        compile_result = None
        if self.services.get("compile_pdf"):
            compile_result = compile_latex(tex_path)
        meta_path = workspace.write_artifact(
            Artifact(
                self.name,
                "draft_metadata",
                {
                    "formats": ["markdown", "latex"],
                    "markdown": paper_path,
                    "latex": str(tex_path),
                    "compile_result": compile_result,
                },
            )
        )
        outputs.append(meta_path)
        return StageResult.ok(self.name, outputs, draft_path=paper_path, latex_path=str(tex_path))
