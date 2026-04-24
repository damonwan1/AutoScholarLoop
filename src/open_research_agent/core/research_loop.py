from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.checkpoints import write_canonical, write_checkpoint
from open_research_agent.core.loop_state import LoopPolicy
from open_research_agent.core.capability_contracts import contracts_json, contracts_markdown
from open_research_agent.core.stage import PipelineContext
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.writing.latex_paper import compile_latex, write_latex_from_markdown
from open_research_agent.writing.markdown_paper import build_markdown_paper
from open_research_agent.writing.paper_formats import get_paper_format, write_format_profile


class ResearchGroupLoopPipeline:
    """Nested-loop AUTO Research pipeline organized as a small research group."""

    def __init__(self, provider, services: dict[str, Any], policy: LoopPolicy):
        self.provider = provider
        self.services = services
        self.policy = policy

    def run(
        self,
        *,
        workspace: ResearchWorkspace,
        seed: str,
        references: list[str],
        num_ideas: int = 5,
    ) -> PipelineContext:
        context = PipelineContext(
            seed=seed,
            references=references,
            num_ideas=num_ideas,
            paper_format=self.services.get("paper_format", "ieee"),
            capability_contracts={stage: contracts_json(stage) for stage in ["S00", "S01", "S02", "S03", "S04"]},
            research_state="initialized",
            big_loop_iteration=1,
        )
        workspace.write_input(
            "seed",
            {
                "seed": seed,
                "references": references,
                "num_ideas": num_ideas,
                "loop_policy": self.policy.__dict__,
                "paper_format": context["paper_format"],
            },
        )
        self._s00_field_archive(workspace, context)
        next_stage = "S01"
        for big_loop in range(1, self.policy.max_big_loops + 1):
            context["big_loop_iteration"] = big_loop
            if next_stage == "S01":
                self._s01_decision_loop(workspace, context)
                self._s02_execution_review_loop(workspace, context)
                self._s03_writing_review_loop(workspace, context)
            elif next_stage == "S02":
                self._s02_execution_review_loop(workspace, context)
                self._s03_writing_review_loop(workspace, context)
            elif next_stage == "S03":
                self._s03_writing_review_loop(workspace, context)
            self._s04_quality_gate(workspace, context)
            if context.get("research_state") == "submission_candidate":
                break
            next_stage = context.get("quality_gate", {}).get("return_to") or "S01"
        self._release(workspace, context)
        return context

    def _record(self, workspace: ResearchWorkspace, result: StageResult) -> None:
        workspace.record_stage(result.stage, result.status, result.artifacts)

    def _s00_field_archive(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        brief = self.provider.complete_json(
            role="field_archive_group",
            task="intake",
            context=dict(context),
            schema_hint={"problem": "str", "references": "list[str]"},
        )
        query = context["seed"]
        literature_hits = self.services["literature"].search(query, limit=8)
        context["field_brief"] = brief
        context["literature_hits"] = [record.__dict__ for record in literature_hits]

        field_map = (
            f"# Field Map\n\n"
            f"{contracts_markdown('S00')}\n"
            f"## User Direction\n\n{context['seed']}\n\n"
            f"## Target Output\n\n{brief.get('target_output', 'conference-style paper')}\n\n"
            f"## Constraints\n\n"
            + "\n".join(f"- {item}" for item in brief.get("constraints", []))
            + "\n"
        )
        paper_cards = "# Paper Cards\n\n" + "\n\n".join(
            f"## {paper['title']}\n- Authors: {paper.get('authors', '')}\n"
            f"- Venue: {paper.get('venue', '')} {paper.get('year', '')}\n"
            f"- Abstract: {paper.get('abstract', '')}"
            for paper in context["literature_hits"]
        )
        method_map = "# Method Map\n\n- Extracted methods will be refined by the professor group.\n"
        dataset_map = "# Dataset And Baseline Map\n\n- Baselines are unknown until S02 baseline scan.\n"
        evidence_bank = (
            "# Evidence Bank\n\n"
            "- User seed recorded.\n"
            "- Literature hits recorded.\n"
            "- No experimental evidence yet.\n"
        )
        paths = [
            write_canonical(workspace, "00_field_context", "capability_contracts.md", contracts_markdown("S00")),
            write_canonical(workspace, "00_field_context", "field_map.md", field_map),
            write_canonical(workspace, "00_field_context", "paper_cards.md", paper_cards),
            write_canonical(workspace, "00_field_context", "method_map.md", method_map),
            write_canonical(workspace, "00_field_context", "dataset_baseline_map.md", dataset_map),
            write_canonical(workspace, "00_field_context", "evidence_bank.md", evidence_bank),
            write_checkpoint(
                workspace,
                folder="00_field_context",
                stage="S00",
                round_id=1,
                artifact="field_map",
                title="S00 Field Archive",
                body=field_map,
                state="field_mapped",
                next_action="start professor decision loop",
            ),
        ]
        artifact_path = workspace.write_artifact(
            Artifact(
                "S00_field_archive",
                "field_context",
                {"context": dict(context), "capability_contracts": contracts_json("S00")},
            )
        )
        paths.append(artifact_path)
        self._record(workspace, StageResult.ok("S00_field_archive", paths, research_state="field_mapped"))
        context["research_state"] = "field_mapped"

    def _s01_decision_loop(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        deliberation_log = ["# Professor Deliberation Log\n", contracts_markdown("S01")]
        idea_pool = None
        paths = []
        for round_id in range(1, self.policy.decision_rounds + 1):
            if round_id <= 3:
                focus = "understand field evidence and challenge assumptions"
            elif round_id <= 6:
                focus = "generate ideas and attack weaknesses"
            elif round_id <= 8:
                focus = "refine strong ideas and remove weak ones"
            elif round_id < self.policy.decision_rounds:
                focus = "rank 3-5 candidates and check closest prior work"
            else:
                focus = "select one direction for execution"
            response = self.provider.complete_json(
                role="professor_decision_group",
                task="ideation",
                context=dict(context, decision_round=round_id, focus=focus),
                schema_hint={"candidates": "list[idea]", "self_critique": "str"},
            )
            idea_pool = response
            body = contracts_markdown("S01") + "\n" + _decision_round_markdown(round_id, focus, response)
            deliberation_log.append(body)
            paths.append(
                write_checkpoint(
                    workspace,
                    folder="01_decision",
                    stage="S01",
                    round_id=round_id,
                    artifact="deliberation",
                    title=f"S01 Professor Decision Round {round_id}",
                    body=body,
                    state="ideas_ready" if round_id < self.policy.decision_rounds else "direction_selected",
                    next_action="continue decision loop"
                    if round_id < self.policy.decision_rounds
                    else "handoff to PhD execution group",
                )
            )
        novelty = self.provider.complete_json(
            role="frontier_scout",
            task="novelty",
            context=dict(context, ideas=idea_pool),
            schema_hint={"selected_id": "str", "decision": "proceed|pivot|kill"},
        )
        context["ideas"] = idea_pool or {}
        context["novelty"] = novelty
        context["selected_idea"] = novelty.get("selected_id", "direction_1")
        write_canonical(workspace, "01_decision", "deliberation_log.md", "\n".join(deliberation_log))
        write_canonical(workspace, "01_decision", "capability_contracts.md", contracts_markdown("S01"))
        write_canonical(workspace, "01_decision", "IDEA_REPORT.md", _idea_report_markdown(context))
        write_canonical(workspace, "01_decision", "idea_pool.md", _idea_pool_markdown(context["ideas"]))
        write_canonical(workspace, "01_decision", "chosen_direction.md", _chosen_direction_markdown(context))
        write_canonical(workspace, "01_decision", "executor_brief.md", _executor_brief_markdown(context))
        paths.append(
            workspace.write_artifact(
                Artifact(
                    "S01_professor_decision_loop",
                    "decision",
                    {"context": dict(context), "capability_contracts": contracts_json("S01")},
                )
            )
        )
        self._record(workspace, StageResult.ok("S01_professor_decision_loop", paths, research_state="direction_selected"))
        context["research_state"] = "direction_selected"

    def _s02_execution_review_loop(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        paths = []
        execution_history = []
        for round_id in range(1, self.policy.execution_rounds + 1):
            if round_id == 1:
                focus = "baseline scan"
            elif round_id == 2:
                focus = "baseline reproduction"
            elif round_id == 3:
                focus = "method implementation"
            elif round_id == 4:
                focus = "debug and main experiment"
            else:
                focus = "ablation, analysis, and professor feedback"
            plan = self.provider.complete_json(
                role="phd_execution_group",
                task="planning",
                context=dict(context, execution_round=round_id, focus=focus),
                schema_hint={"objective": "str", "work_packages": "list[str]"},
            )
            code_generation = self.provider.complete_json(
                role="phd_code_agent",
                task="code_generation",
                context=dict(context, execution_round=round_id, focus=focus, plan=plan),
                schema_hint={
                    "files": "list[{path:str, content:str}]",
                    "commands": "list[str]",
                    "notes": "str",
                },
            )
            code_paths = _write_experiment_scaffold(workspace, context, execution_history, code_generation)
            plan["commands"] = code_generation.get("commands") or plan.get("commands", [])
            backend = self.services["executor"].execute(workspace.root, plan)
            execution = self.provider.complete_json(
                role="phd_execution_group",
                task="execution",
                context=dict(context, plan=plan, backend=backend, execution_round=round_id),
                schema_hint={"runs": "list[run]", "open_issues": "list[str]"},
            )
            execution["backend_result"] = backend
            review = {
                "decision": "promote_to_writing"
                if round_id == self.policy.execution_rounds
                else "continue",
                "next_action": "enter writing loop"
                if round_id == self.policy.execution_rounds
                else "continue execution-review loop",
                "professor_notes": execution.get("open_issues", []),
            }
            execution_history.append({"round": round_id, "plan": plan, "execution": execution, "review": review})
            paths.append(
                write_checkpoint(
                    workspace,
                    folder="02_execution",
                    stage="S02",
                    round_id=round_id,
                    artifact="execution",
                    title=f"S02 Execution Round {round_id}",
                    body=contracts_markdown("S02") + "\n" + _execution_round_markdown(round_id, focus, plan, execution),
                    state="execution_under_review",
                    next_action="professor review memo",
                )
            )
            paths.append(
                write_checkpoint(
                    workspace,
                    folder="02_execution",
                    stage="S02",
                    round_id=round_id,
                    artifact="review_memo",
                    title=f"S02 Professor Review Memo {round_id}",
                    body=_review_memo_markdown(review),
                    state="writing_ready" if review["decision"] == "promote_to_writing" else "execution_under_review",
                    next_action=review["next_action"],
                )
            )
        context["execution_history"] = execution_history
        context["execution"] = {"runs": execution_history, "status": "writing_ready"}
        context["code_artifacts"] = sorted(
            str(path) for path in (workspace.root / "code").rglob("*") if path.is_file()
        )
        analysis = _results_analysis_markdown(execution_history)
        claims = _claims_from_results_markdown(execution_history)
        audit = _experiment_audit_markdown(execution_history)
        write_canonical(workspace, "02_execution", "capability_contracts.md", contracts_markdown("S02"))
        write_canonical(workspace, "02_execution", "baseline_scan.md", _baseline_scan_markdown(execution_history))
        write_canonical(workspace, "02_execution", "RESULTS_ANALYSIS.md", analysis)
        write_canonical(workspace, "02_execution", "CLAIMS_FROM_RESULTS.md", claims)
        write_canonical(workspace, "02_execution", "EXPERIMENT_AUDIT.md", audit)
        write_canonical(workspace, "02_execution", "GENERATED_CODE.md", _generated_code_markdown(context["code_artifacts"]))
        paths.extend(context["code_artifacts"])
        paths.append(
            workspace.write_artifact(
                Artifact(
                    "S02_execution_review_loop",
                    "execution_history",
                    {"context": dict(context), "capability_contracts": contracts_json("S02")},
                )
            )
        )
        self._record(workspace, StageResult.ok("S02_execution_review_loop", paths, research_state="writing_ready"))
        context["research_state"] = "writing_ready"

    def _s03_writing_review_loop(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        evidence = self.provider.complete_json(
            role="evidence_auditor",
            task="synthesis",
            context=dict(context),
            schema_hint={"claims": "list[claim]", "limitations": "list[str]"},
        )
        context["evidence"] = evidence
        manuscript = self.provider.complete_json(
            role="paper_writer_group",
            task="paper_draft",
            context=dict(context),
            schema_hint={
                "title": "str",
                "abstract": "str",
                "introduction": "str",
                "related_work": "str",
                "method": "str",
                "experiments": "str",
                "results": "str",
                "limitations": "list[str]",
                "conclusion": "str",
            },
        )
        context["manuscript"] = manuscript
        paper_format = get_paper_format(context.get("paper_format", "ieee"))
        paper = build_markdown_paper(context)
        draft_path = workspace.write_markdown("03_writing", "draft.md", paper)
        workspace.write_markdown("paper", "draft.md", paper)
        write_format_profile(workspace.root / "paper" / "format_profile.json", paper_format)
        write_canonical(workspace, "03_writing", "format_profile.md", paper_format.to_markdown())
        paths = [draft_path, str(workspace.root / "paper" / "format_profile.json")]
        for round_id in range(1, self.policy.writing_rounds + 1):
            if round_id == 1:
                focus = "paper outline and narrative"
            elif round_id == 2:
                focus = "complete first draft"
            elif round_id == 3:
                focus = "claim-evidence table"
            elif round_id == 4:
                focus = "reviewer-style critique"
            else:
                focus = "revision to submission candidate"
            review = self.provider.complete_json(
                role="writing_review_group",
                task="review",
                context=dict(context, writing_round=round_id, focus=focus),
                schema_hint={"weaknesses": "list[str]", "required_revisions": "list[str]"},
            )
            body = contracts_markdown("S03") + "\n" + _writing_round_markdown(round_id, focus, evidence, review)
            paths.append(
                write_checkpoint(
                    workspace,
                    folder="03_writing",
                    stage="S03",
                    round_id=round_id,
                    artifact="draft_update",
                    title=f"S03 Writing Review Round {round_id}",
                    body=body,
                    state="draft_under_review"
                    if round_id < self.policy.writing_rounds
                    else "quality_audit",
                    next_action="continue writing-review loop"
                    if round_id < self.policy.writing_rounds
                    else "quality control gate",
                )
            )
        claim_table = _claim_evidence_table(evidence)
        write_canonical(workspace, "03_writing", "capability_contracts.md", contracts_markdown("S03"))
        write_canonical(workspace, "03_writing", "claim_evidence_table.md", claim_table)
        write_canonical(workspace, "03_writing", "PAPER_PLAN.md", _paper_plan_markdown(context))
        write_canonical(workspace, "03_writing", "paper_outline.md", _paper_outline_markdown(context))
        write_canonical(workspace, "03_writing", "figure_plan.md", _figure_plan_markdown(context))
        write_canonical(workspace, "03_writing", "AUTO_REVIEW.md", "See S03_RXX_draft_update.md files for reviewer-style critique.\n")
        write_canonical(workspace, "03_writing", "PAPER_IMPROVEMENT_LOG.md", "Writing-review loop completed inside S03 checkpoints.\n")
        write_canonical(workspace, "03_writing", "review_log.md", "See S03_RXX_draft_update.md files.\n")
        context["draft_path"] = str(workspace.root / "paper" / "draft.md")
        tex_path = write_latex_from_markdown(
            Path(context["draft_path"]),
            workspace.root / "paper" / "main.tex",
            paper_format_key=paper_format.key,
        )
        context["latex_path"] = str(tex_path)
        if self.services.get("compile_pdf"):
            context["compile_result"] = compile_latex(tex_path)
        paths.append(
            workspace.write_artifact(
                Artifact(
                    "S03_writing_review_loop",
                    "draft",
                    {"context": dict(context), "capability_contracts": contracts_json("S03")},
                )
            )
        )
        self._record(workspace, StageResult.ok("S03_writing_review_loop", paths, research_state="quality_audit"))
        context["research_state"] = "quality_audit"

    def _s04_quality_gate(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        evidence = context.get("evidence", {})
        unsupported = [
            item for item in evidence.get("claims", []) if _is_unsupported_claim(item)
        ]
        claims = evidence.get("claims", [])
        missing_evidence = not claims or bool(unsupported)
        gate = {
            "decision": "submission_candidate" if not missing_evidence else "return_to_execution",
            "return_to": None if not missing_evidence else "S02",
            "unsupported_claims": unsupported,
            "checks": {
                "novelty": "pass_with_local_evidence",
                "citation": "needs_real_bibtex_loop" if not context.get("literature_hits") else "pass",
                "reproducibility": "pass_for_recorded_artifacts",
                "claim_evidence": "pass" if not missing_evidence else "fail",
            },
        }
        context["quality_gate"] = gate
        paths = []
        write_canonical(workspace, "04_quality", "capability_contracts.md", contracts_markdown("S04"))
        for artifact, title, body in [
            ("novelty_audit", "Novelty Audit", _quality_section(gate, "novelty")),
            ("citation_audit", "Citation Audit", _quality_section(gate, "citation")),
            ("reproducibility_audit", "Reproducibility Audit", _quality_section(gate, "reproducibility")),
            ("claim_audit", "Claim Audit", _quality_section(gate, "claim_evidence")),
            ("final_gate", "Final Gate", _final_gate_markdown(gate)),
        ]:
            paths.append(
                write_checkpoint(
                    workspace,
                    folder="04_quality",
                    stage="S04",
                    round_id=1,
                    artifact=artifact,
                    title=f"S04 {title}",
                    body=contracts_markdown("S04") + "\n" + body,
                    state=gate["decision"],
                    next_action="release package" if gate["decision"] == "submission_candidate" else "route back",
                )
            )
            write_canonical(workspace, "04_quality", f"{artifact}.md", body)
        write_canonical(workspace, "04_quality", "CITATION_AUDIT.md", _citation_audit_markdown(gate))
        write_canonical(workspace, "04_quality", "CITATION_AUDIT.json", _citation_audit_json(gate))
        write_canonical(workspace, "04_quality", "compile_report.md", _compile_report_markdown(context))
        write_canonical(workspace, "04_quality", "overleaf_sync.md", _overleaf_sync_markdown())
        final_draft = Path(context["draft_path"]).read_text(encoding="utf-8")
        final_draft += "\n\n## Quality Gate\n\n" + _final_gate_markdown(gate)
        context["final_draft_path"] = workspace.write_markdown("paper", "final_draft.md", final_draft)
        paths.append(
            workspace.write_artifact(
                Artifact(
                    "S04_quality_gate",
                    "quality_gate",
                    {"gate": gate, "capability_contracts": contracts_json("S04")},
                )
            )
        )
        self._record(workspace, StageResult.ok("S04_quality_gate", paths, research_state=gate["decision"]))
        context["research_state"] = gate["decision"]

    def _release(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        package = {
            "state": context.get("research_state"),
            "final_draft": context.get("final_draft_path"),
            "manifest": str(workspace.manifest_path),
            "checkpoint_state": str(workspace.root / "00_field_context" / "checkpoint_state.md"),
            "progress_index": str(workspace.root / "00_field_context" / "progress_index.md"),
        }
        release_md = (
            "# Release Package\n\n"
            f"- State: {package['state']}\n"
            f"- Final draft: {package['final_draft']}\n"
            f"- Manifest: {package['manifest']}\n"
            f"- Checkpoint state: {package['checkpoint_state']}\n"
            f"- Progress index: {package['progress_index']}\n"
        )
        release_path = workspace.write_markdown("release", "README.md", release_md)
        artifact_path = workspace.write_artifact(Artifact("release", "release_package", package))
        self._record(workspace, StageResult.ok("release", [release_path, artifact_path], release=package))


def _decision_round_markdown(round_id: int, focus: str, response: dict[str, Any]) -> str:
    lines = [f"## Focus\n\n{focus}\n", "## Candidate Discussion\n"]
    for idea in response.get("candidates", []):
        lines.append(f"### {idea.get('id')}: {idea.get('title')}")
        lines.append(f"- Hypothesis: {idea.get('hypothesis')}")
        lines.append(f"- Novelty claim: {idea.get('novelty_claim')}")
        lines.append(f"- Feasibility: {idea.get('feasibility')}")
        lines.append(f"- Risks: {', '.join(idea.get('risks', []))}")
    lines.append(f"\n## Self Critique\n\n{response.get('self_critique', '')}\n")
    return "\n".join(lines)


def _idea_pool_markdown(ideas: dict[str, Any]) -> str:
    return _decision_round_markdown(0, "final idea pool", ideas)


def _idea_report_markdown(context: dict[str, Any]) -> str:
    ideas = context.get("ideas", {}).get("candidates", [])
    lines = [
        "# Research Idea Report",
        "",
        f"**Direction**: {context.get('seed')}",
        f"**Selected**: {context.get('selected_idea')}",
        "",
        "## Recommended Ideas",
        "",
    ]
    for index, idea in enumerate(ideas, start=1):
        lines.extend(
            [
                f"### Idea {index}: {idea.get('title')}",
                f"- Hypothesis: {idea.get('hypothesis')}",
                "- Minimum experiment: defined in executor_brief.md and S02 experiment plan.",
                "- Expected outcome: positive or negative empirical signal tied to claim evidence.",
                f"- Novelty: provisional; closest work tracked by novelty report.",
                f"- Feasibility: {idea.get('feasibility')}",
                f"- Risk: {', '.join(idea.get('risks', []))}",
                "- Pilot result: pending S02 execution loop.",
                "- Reviewer's likely objection: insufficient novelty or incomplete baseline unless S02 validates it.",
                "",
            ]
        )
    lines.extend(
        [
            "## Eliminated Ideas",
            "",
            "Eliminations are recorded in S01 deliberation checkpoints when novelty, feasibility, or impact gates fail.",
            "",
            "## Suggested Execution Order",
            "",
            "1. Baseline scan.",
            "2. Baseline reproduction.",
            "3. Method implementation.",
            "4. Main experiment.",
            "5. Ablation and claim-support gate.",
        ]
    )
    return "\n".join(lines)


def _chosen_direction_markdown(context: dict[str, Any]) -> str:
    return (
        "# Chosen Direction\n\n"
        f"- selected_id: {context.get('selected_idea')}\n"
        f"- novelty decision: {context.get('novelty', {}).get('decision')}\n"
        f"- rationale: {context.get('novelty', {}).get('rationale')}\n"
    )


def _executor_brief_markdown(context: dict[str, Any]) -> str:
    return (
        "# Executor Brief\n\n"
        f"Selected direction: {context.get('selected_idea')}\n\n"
        "Tasks:\n"
        "- scan baseline and datasets\n"
        "- reproduce baseline where possible\n"
        "- implement proposed method\n"
        "- run main result and ablations\n"
        "- report failures honestly\n"
    )


def _execution_round_markdown(round_id: int, focus: str, plan: dict[str, Any], execution: dict[str, Any]) -> str:
    return (
        f"## Round Focus\n\n{focus}\n\n"
        f"## Plan\n\n{plan}\n\n"
        f"## Execution Report\n\n{execution}\n\n"
        "## Required Fields\n\n"
        "- execution_report: included above\n"
        "- result_summary: see backend_result and runs\n"
        "- failure_analysis: see open_issues\n"
    )


def _review_memo_markdown(review: dict[str, Any]) -> str:
    return (
        "# Professor Review Memo\n\n"
        f"- decision: {review.get('decision')}\n"
        f"- next_action: {review.get('next_action')}\n"
        f"- notes: {review.get('professor_notes')}\n"
    )


def _baseline_scan_markdown(history: list[dict[str, Any]]) -> str:
    first = history[0] if history else {}
    return "# Baseline Scan\n\n" + str(first.get("plan", {})) + "\n"


def _results_analysis_markdown(history: list[dict[str, Any]]) -> str:
    lines = [
        "# Results Analysis",
        "",
        "## Raw Data Table",
        "",
        "| Round | Focus | Backend | Status | Key Observation |",
        "|---|---|---|---|---|",
    ]
    for item in history:
        execution = item.get("execution", {})
        backend = execution.get("backend_result", {})
        observation = ""
        runs = execution.get("runs", [])
        if runs:
            observation = runs[0].get("observation", "")
        lines.append(
            f"| {item.get('round')} | {item.get('plan', {}).get('objective', '')} | "
            f"{backend.get('backend', '')} | {backend.get('status', '')} | {observation} |"
        )
    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            "1. The current run records execution artifacts and backend status for each executor round.",
            "2. Quantitative comparisons require real result JSON/CSV from a shell or remote execution backend.",
            "",
            "## Suggested Next Experiments",
            "",
            "- Attach a baseline repository and run shell-backed sanity experiments.",
            "- Add ablation result files for the claim-support gate.",
        ]
    )
    return "\n".join(lines)


def _claims_from_results_markdown(history: list[dict[str, Any]]) -> str:
    return (
        "# Claims From Results\n\n"
        "| Claim | Verdict | Support | Missing Evidence | Next Action |\n"
        "|---|---|---|---|---|\n"
        "| Stage artifacts improve auditability | partial | Workspace manifest and checkpoints | Real user study or ablation | Keep as design claim until measured |\n"
        "\n"
        "## Route\n\n"
        "- claim_supported: partial\n"
        "- confidence: medium for design evidence, low for empirical performance claims\n"
    )


def _experiment_audit_markdown(history: list[dict[str, Any]]) -> str:
    return (
        "# Experiment Audit\n\n"
        "- integrity_status: provisional\n"
        "- seeds_checked: not applicable for dry-run backend\n"
        "- metric_correctness: requires real result parser\n"
        "- baseline_fairness: pending baseline reproduction\n"
        "- action: downgrade empirical claims until shell-backed experiments are available\n"
    )


def _write_experiment_scaffold(
    workspace: ResearchWorkspace,
    context: dict[str, Any],
    history: list[dict[str, Any]],
    code_generation: dict[str, Any] | None = None,
) -> list[str]:
    code_root = workspace.root / "code"
    experiments = code_root / "experiments"
    methods = code_root / "methods"
    experiments.mkdir(parents=True, exist_ok=True)
    methods.mkdir(parents=True, exist_ok=True)
    selected = context.get("selected_idea", "direction_1")
    seed = context.get("seed", "")
    config = {
        "research_seed": seed,
        "selected_idea": selected,
        "backend": "dry-run-compatible",
        "datasets": ["replace_with_real_dataset"],
        "baselines": ["replace_with_real_baseline"],
        "metrics": ["accuracy", "compute_cost", "latency"],
        "note": "Generated scaffold. Replace placeholders before making empirical claims.",
    }
    files = {
        code_root / "README.md": (
            "# Generated Experiment Workspace\n\n"
            "This folder is produced by S02 PhD Execution. It is a runnable scaffold, "
            "not evidence by itself. Empirical claims require real datasets, baselines, "
            "and result files.\n\n"
            "## Files\n\n"
            "- `experiments/run_experiment.py`: CLI entrypoint for a sanity experiment.\n"
            "- `methods/proposed_method.py`: placeholder method module.\n"
            "- `experiments/config.json`: experiment configuration.\n"
            "- `experiments/results_schema.json`: expected result schema.\n"
        ),
        experiments / "config.json": json.dumps(config, indent=2, ensure_ascii=False),
        experiments / "results_schema.json": json.dumps(
            {
                "required": ["run_id", "dataset", "method", "baseline", "metrics", "claim_support"],
                "metrics": {"accuracy": "float", "compute_cost": "float", "latency": "float"},
            },
            indent=2,
        ),
        methods / "proposed_method.py": _proposed_method_py(),
        experiments / "run_experiment.py": _run_experiment_py(),
    }
    for item in (code_generation or {}).get("files", []):
        rel = str(item.get("path", "")).replace("\\", "/").lstrip("/")
        if not rel or ".." in Path(rel).parts:
            continue
        path = workspace.root / rel
        if path.suffix not in {".py", ".json", ".yaml", ".yml", ".md", ".txt", ".sh", ".ps1"}:
            continue
        files[path] = str(item.get("content", ""))
    commands = (code_generation or {}).get("commands") or [
        "python code/experiments/run_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
    ]
    files[code_root / "run_commands.json"] = json.dumps({"commands": commands}, indent=2, ensure_ascii=False)
    paths = []
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        paths.append(str(path))
    return paths


def _proposed_method_py() -> str:
    return '''"""Generated placeholder method module.

Replace this scaffold with the actual proposed method before treating any
result as scientific evidence.
"""


class ProposedMethod:
    def __init__(self, config):
        self.config = config

    def fit(self, train_data):
        return self

    def predict(self, batch):
        # Placeholder: preserve input cardinality for smoke tests.
        return [0 for _ in batch]

    def cost_estimate(self):
        return {"compute_cost": 0.0, "latency": 0.0}
'''


def _run_experiment_py() -> str:
    return '''"""Run a generated sanity experiment.

This script intentionally writes a low-confidence placeholder result unless
connected to real datasets and baselines.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from methods.proposed_method import ProposedMethod


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output", default="result.json")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    method = ProposedMethod(config)
    predictions = method.predict([{"sample": 1}, {"sample": 2}])
    result = {
        "run_id": "generated_sanity_run",
        "dataset": config.get("datasets", ["placeholder"])[0],
        "method": "proposed_method_scaffold",
        "baseline": config.get("baselines", ["placeholder"])[0],
        "metrics": {
            "accuracy": None,
            "compute_cost": method.cost_estimate()["compute_cost"],
            "latency": method.cost_estimate()["latency"],
        },
        "num_predictions": len(predictions),
        "claim_support": "none_real_dataset_required",
    }
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
'''


def _generated_code_markdown(paths: list[str]) -> str:
    lines = [
        "# Generated Code",
        "",
        "S02 generated an experiment scaffold. These files are required execution artifacts, "
        "but they do not support empirical claims until run on real datasets against fair baselines.",
        "",
    ]
    for path in paths:
        lines.append(f"- {path}")
    return "\n".join(lines) + "\n"


def _is_unsupported_claim(claim: dict[str, Any]) -> bool:
    status = str(claim.get("status", "")).lower()
    support = claim.get("support")
    if not support or str(support).strip().lower() in {"none", "n/a", "no evidence", "null"}:
        return True
    weak_markers = ["unsupported", "hypothesis", "provisional", "partial", "pending", "planned"]
    return any(marker in status for marker in weak_markers)


def _writing_round_markdown(round_id: int, focus: str, evidence: dict[str, Any], review: dict[str, Any]) -> str:
    return (
        f"## Focus\n\n{focus}\n\n"
        f"## Evidence Snapshot\n\n{evidence}\n\n"
        f"## Reviewer-Style Feedback\n\n{review}\n"
    )


def _claim_evidence_table(evidence: dict[str, Any]) -> str:
    lines = ["# Claim Evidence Table\n"]
    for claim in evidence.get("claims", []):
        lines.append(f"## {claim.get('claim')}")
        lines.append(f"- Evidence: {claim.get('support')}")
        lines.append(f"- Status: {claim.get('status')}")
    return "\n".join(lines)


def _paper_outline_markdown(context: dict[str, Any]) -> str:
    fmt = get_paper_format(context.get("paper_format", "ieee"))
    return "# Paper Outline\n\n" + "\n".join(f"- {section}" for section in fmt.recommended_sections) + "\n"


def _paper_plan_markdown(context: dict[str, Any]) -> str:
    fmt = get_paper_format(context.get("paper_format", "ieee"))
    return (
        "# Paper Plan\n\n"
        f"## Target Format\n\n{fmt.to_markdown()}\n\n"
        "## Claims-Evidence Matrix\n\n"
        + _claim_evidence_table(context.get("evidence", {}))
        + "\n\n## Section Plan\n\n"
        + _paper_outline_markdown(context)
        + "\n\n## Venue Assumptions\n\n"
        f"- Citation style: {fmt.citation_style}\n"
        f"- Column layout: {fmt.columns} column(s)\n"
        f"- Bibliography note: {fmt.bibliography_note}\n"
    )


def _figure_plan_markdown(context: dict[str, Any]) -> str:
    fmt = get_paper_format(context.get("paper_format", "ieee"))
    return (
        "# Figure Plan\n\n"
        f"- Figure caption rule: {fmt.figure_caption}\n"
        f"- Table caption rule: {fmt.table_caption}\n"
        f"- Column layout: {fmt.columns} column(s)\n\n"
        "| ID | Type | Description | Data Source | Priority |\n"
        "|---|---|---|---|---|\n"
        "| Fig 1 | System diagram | Nested research loop and checkpoint flow | generated from architecture | HIGH |\n"
        "| Table 1 | Claim table | Claim-evidence matrix | 03_writing/claim_evidence_table.md | HIGH |\n"
        "| Fig 2 | Result plot | Main experiment result once real backend produces metrics | result JSON/CSV | MEDIUM |\n"
    )


def _quality_section(gate: dict[str, Any], key: str) -> str:
    return f"# {key} audit\n\n- status: {gate.get('checks', {}).get(key)}\n"


def _final_gate_markdown(gate: dict[str, Any]) -> str:
    return (
        "# Final Gate\n\n"
        f"- decision: {gate.get('decision')}\n"
        f"- return_to: {gate.get('return_to')}\n"
        f"- unsupported_claims: {gate.get('unsupported_claims')}\n"
    )


def _citation_audit_markdown(gate: dict[str, Any]) -> str:
    return (
        "# Citation Audit Report\n\n"
        "## Summary\n\n"
        f"- Verdict: {gate.get('checks', {}).get('citation')}\n"
        "- KEEP: provisional local references\n"
        "- FIX: real BibTeX loop pending\n"
        "- REPLACE: none detected by local provider\n"
        "- REMOVE: none detected by local provider\n"
        "\n"
        "## Priority Fixes\n\n"
        "- Run real reference integrity audit after the manuscript writer creates references.bib.\n"
    )


def _citation_audit_json(gate: dict[str, Any]) -> str:
    payload = {
        "summary": {"KEEP": 0, "FIX": 1, "REPLACE": 0, "REMOVE": 0},
        "status": gate.get("checks", {}).get("citation"),
        "entries": [],
        "note": "Local provisional audit. Real reference integrity audit requires bibliography and web verification.",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _compile_report_markdown(context: dict[str, Any]) -> str:
    fmt = get_paper_format(context.get("paper_format", "ieee"))
    result = context.get("compile_result")
    if not result:
        return (
            "# Compile Report\n\n"
            f"- target_format: {fmt.key}\n"
            f"- latex_class: {fmt.latex_documentclass}\n"
            "- status: skipped\n"
            "- reason: --compile-pdf not enabled\n"
        )
    return (
        "# Compile Report\n\n"
        f"- target_format: {fmt.key}\n"
        f"- latex_class: {fmt.latex_documentclass}\n"
        + "\n".join(f"- {key}: {value}" for key, value in result.items())
        + "\n"
    )


def _overleaf_sync_markdown() -> str:
    return (
        "# Overleaf Sync\n\n"
        "- status: skipped\n"
        "- reason: no Overleaf sync configuration was provided\n"
        "- fallback: local release package is authoritative\n"
    )
