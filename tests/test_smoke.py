from pathlib import Path

from open_research_agent.core.pipeline import build_default_pipeline
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.writing.paper_formats import FORMATS


def test_default_pipeline_runs(tmp_path: Path) -> None:
    ws = ResearchWorkspace.create(tmp_path / "run")
    pipeline = build_default_pipeline(loop_mode="fast")
    state = pipeline.run(workspace=ws, seed="test seed", references=[])
    assert "final_draft_path" in state
    assert Path(state["final_draft_path"]).exists()
    assert ws.manifest()["stages"][-1]["stage"] == "release"
    assert (tmp_path / "run" / "00_field_context" / "progress_index.md").exists()
    assert (tmp_path / "run" / "04_quality" / "final_gate.md").exists()
    assert (tmp_path / "run" / "01_decision" / "capability_contracts.md").exists()
    assert (tmp_path / "run" / "01_decision" / "IDEA_REPORT.md").exists()
    assert (tmp_path / "run" / "02_execution" / "CLAIMS_FROM_RESULTS.md").exists()
    assert (tmp_path / "run" / "03_writing" / "PAPER_PLAN.md").exists()
    assert (tmp_path / "run" / "04_quality" / "CITATION_AUDIT.json").exists()
    assert (tmp_path / "run" / "paper" / "main.tex").exists()
    assert (tmp_path / "run" / "paper" / "format_profile.json").exists()


def test_supported_paper_formats_run(tmp_path: Path) -> None:
    for key in FORMATS:
        ws = ResearchWorkspace.create(tmp_path / key)
        pipeline = build_default_pipeline(loop_mode="fast", paper_format=key)
        state = pipeline.run(workspace=ws, seed=f"{key} test seed", references=[])
        assert Path(state["final_draft_path"]).exists()
        assert (tmp_path / key / "paper" / "main.tex").exists()
        profile = (tmp_path / key / "paper" / "format_profile.json").read_text(encoding="utf-8")
        assert f'"key": "{key}"' in profile
