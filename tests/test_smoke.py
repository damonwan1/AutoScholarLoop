from pathlib import Path

from open_research_agent.core.pipeline import build_default_pipeline
from open_research_agent.core.providers import _safe_json_loads
from open_research_agent.core.research_loop import _is_unsupported_claim, _safe_generated_code_path
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.writing.markdown_paper import build_markdown_paper
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


def test_quality_gate_rejects_hypothesis_without_support() -> None:
    assert _is_unsupported_claim({"claim": "x", "support": None, "status": "hypothesis"})
    assert _is_unsupported_claim({"claim": "x", "support": "None", "status": "supported"})
    assert not _is_unsupported_claim(
        {"claim": "x", "support": "result table and generated artifact", "status": "supported"}
    )


def test_paper_results_are_evidence_grounded() -> None:
    paper = build_markdown_paper(
        {
            "paper_format": "ieee",
            "manuscript": {
                "title": "Draft",
                "abstract": "Abstract.",
                "introduction": "Intro.",
                "related_work": "Related.",
                "method": "Method.",
                "experiments": "Experiments.",
                "results": "Our method improves accuracy by 99%.",
                "conclusion": "Conclusion.",
            },
            "evidence": {
                "claims": [{"claim": "accuracy improves", "support": "None", "status": "unsupported"}],
                "limitations": ["No result files."],
            },
        }
    )
    assert "99%" not in paper
    assert "No validated experimental result" in paper


def test_malformed_model_json_becomes_recoverable_checkpoint() -> None:
    data = _safe_json_loads(
        '{"files": [{"path": "x.py", "content": "unterminated}',
        task="code_generation",
        role="phd_code_agent",
        schema_hint={"files": "list"},
    )
    assert data["commands"]
    assert "parser_warning" in data


def test_generated_code_paths_are_sandboxed(tmp_path: Path) -> None:
    code_root = tmp_path / "code"
    assert _safe_generated_code_path(code_root, "experiments/config") == (code_root / "experiments" / "config.py").resolve()
    assert _safe_generated_code_path(code_root, "code/methods/model.py") == (code_root / "methods" / "model.py").resolve()
    assert _safe_generated_code_path(code_root, "../escape.py") is None


def test_pipeline_survives_compile_failure(tmp_path: Path, monkeypatch) -> None:
    import open_research_agent.core.research_loop as research_loop

    def broken_compile(_tex_path):
        raise IndexError("list index out of range")

    monkeypatch.setattr(research_loop, "compile_latex", broken_compile)
    ws = ResearchWorkspace.create(tmp_path / "compile_failure")
    pipeline = build_default_pipeline(loop_mode="fast", compile_pdf=True)
    state = pipeline.run(workspace=ws, seed="compile failure smoke", references=[])
    assert state["compile_result"]["compiled"] is False
    assert (tmp_path / "compile_failure" / "04_quality" / "final_gate.md").exists()
