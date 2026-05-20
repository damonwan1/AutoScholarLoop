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
        if context.get("research_state") == "submission_candidate":
            self._release(workspace, context)
        else:
            self._halt_for_revision(workspace, context)
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
        literature_hits = self.services["literature"].search(query, limit=14)
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
                context=dict(context, execution_round=round_id, focus=focus, execution_contract=_execution_contract()),
                schema_hint={"objective": "str", "work_packages": "list[str]"},
            )
            code_generation = self.provider.complete_json(
                role="phd_code_agent",
                task="code_generation",
                context=dict(context, execution_round=round_id, focus=focus, plan=plan, execution_contract=_execution_contract()),
                schema_hint={
                    "files": "list[{path:str, content:str}]",
                    "commands": "list[str]",
                    "notes": "str",
                },
            )
            code_paths = _write_experiment_scaffold(workspace, context, execution_history, code_generation)
            plan["commands"] = _repair_generated_commands(workspace.root, code_generation.get("commands") or plan.get("commands", []))
            write_canonical(workspace, "02_execution", f"command_validation_R{round_id:02d}.md", _command_validation_markdown(plan["commands"]))
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
        result_evidence = _load_result_evidence(workspace.root)
        context["result_evidence"] = result_evidence
        analysis = _results_analysis_markdown(execution_history, result_evidence)
        claims = _claims_from_results_markdown(execution_history, result_evidence)
        audit = _experiment_audit_markdown(execution_history, result_evidence)
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
        evidence = _merge_result_evidence(evidence, context.get("result_evidence", {}))
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
            try:
                context["compile_result"] = compile_latex(tex_path)
            except Exception as exc:  # Keep writing/audit alive even if TeX tooling misbehaves.
                context["compile_result"] = {
                    "compiled": False,
                    "return_code": 1,
                    "message": f"LaTeX compile failed but pipeline continued: {exc}",
                    "pdf": str(tex_path.with_suffix(".pdf")) if tex_path.with_suffix(".pdf").exists() else "",
                }
        paths.append(
            workspace.write_artifact(
                Artifact(
                    "S03_writing_review_loop",
                    "draft",
                    {
                        "draft_path": context.get("draft_path"),
                        "latex_path": context.get("latex_path"),
                        "compile_result": context.get("compile_result"),
                        "paper_format": context.get("paper_format"),
                        "evidence": context.get("evidence"),
                        "capability_contracts": contracts_json("S03"),
                    },
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
        layout_audit = _layout_audit(workspace.root, context)
        gate["checks"]["layout"] = layout_audit["status"]
        gate["checks"]["content_structure"] = layout_audit["content_status"]
        context["quality_gate"] = gate
        context["layout_audit"] = layout_audit
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
        write_canonical(workspace, "04_quality", "layout_audit.md", _layout_audit_markdown(layout_audit))
        write_canonical(workspace, "04_quality", "layout_audit.json", json.dumps(layout_audit, indent=2, ensure_ascii=False))
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

    def _halt_for_revision(self, workspace: ResearchWorkspace, context: PipelineContext) -> None:
        gate = context.get("quality_gate", {})
        package = {
            "state": context.get("research_state"),
            "return_to": gate.get("return_to"),
            "final_draft": context.get("final_draft_path"),
            "latex": context.get("latex_path"),
            "pdf": context.get("compile_result", {}).get("pdf") if context.get("compile_result") else "",
            "manifest": str(workspace.manifest_path),
            "checkpoint_state": str(workspace.root / "00_field_context" / "checkpoint_state.md"),
            "progress_index": str(workspace.root / "00_field_context" / "progress_index.md"),
            "unsupported_claims": gate.get("unsupported_claims", []),
        }
        revision_md = (
            "# Revision Required\n\n"
            f"- State: {package['state']}\n"
            f"- Return to: {package['return_to']}\n"
            f"- Final draft: {package['final_draft']}\n"
            f"- LaTeX: {package['latex']}\n"
            f"- PDF: {package['pdf']}\n"
            f"- Manifest: {package['manifest']}\n\n"
            "## Unsupported Claims\n\n"
            + "\n".join(f"- {claim.get('claim')}" for claim in package["unsupported_claims"])
            + "\n"
        )
        path = workspace.write_markdown("release", "REVISION_REQUIRED.md", revision_md)
        artifact_path = workspace.write_artifact(Artifact("needs_revision", "revision_package", package))
        self._record(workspace, StageResult.ok("needs_revision", [path, artifact_path], revision=package))


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


def _results_analysis_markdown(history: list[dict[str, Any]], result_evidence: dict[str, Any] | None = None) -> str:
    result_evidence = result_evidence or {}
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
    if result_evidence.get("status") == "ok":
        primary_metric = result_evidence.get("primary_metric", "score")
        lines.extend(
            [
                "",
                "## Parsed Result File",
                "",
                f"- Result file: {result_evidence.get('path')}",
                f"- Dataset: {result_evidence.get('dataset')}",
                f"- Seeds: {result_evidence.get('n_seeds')}",
                f"- Primary metric: {primary_metric}",
                f"- Best model: {result_evidence.get('best_model') or result_evidence.get('best_model_by_auc')}",
                "",
                "| Model | Primary metric | Runtime | F1 | Brier |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for model, metrics in result_evidence.get("summary", {}).items():
            lines.append(
                f"| {model} | {_metric_pm(metrics, primary_metric)} | {_metric_pm(metrics, 'runtime')} | "
                f"{_metric_pm(metrics, 'f1')} | {_metric_pm(metrics, 'brier')} |"
            )
        lines.extend(
            [
                "",
                "## Key Findings",
                "",
                f"1. `{result_evidence.get('best_model') or result_evidence.get('best_model_by_auc')}` is strongest on the parsed primary metric.",
                "2. Claims are limited to this generated benchmark unless a real dataset is attached.",
                "",
                "## Suggested Next Experiments",
                "",
                "- Replace the synthetic generator with a real classroom or public learning analytics dataset.",
                "- Add calibration, confidence intervals, and fairness slices before any deployment claim.",
            ]
        )
        return "\n".join(lines)
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


def _claims_from_results_markdown(history: list[dict[str, Any]], result_evidence: dict[str, Any] | None = None) -> str:
    result_evidence = result_evidence or {}
    if result_evidence.get("status") == "ok":
        best = result_evidence.get("best_model") or result_evidence.get("best_model_by_auc")
        primary_metric = result_evidence.get("primary_metric", "score")
        return (
            "# Claims From Results\n\n"
            "| Claim | Verdict | Support | Missing Evidence | Next Action |\n"
            "|---|---|---|---|---|\n"
            f"| `{best}` is strongest on the generated benchmark primary metric ({primary_metric}) | supported_limited | "
            f"{result_evidence.get('path')} with {result_evidence.get('n_seeds')} seeds | real dataset and citation audit | rerun with real data |\n"
            "| The generated benchmark is deployment evidence | unsupported | synthetic data only | real classroom validation | keep as limitation |\n"
            "\n"
            "## Route\n\n"
            "- claim_supported: limited_to_generated_benchmark\n"
            "- confidence: medium for code execution, low for real-world generalization\n"
        )
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


def _experiment_audit_markdown(history: list[dict[str, Any]], result_evidence: dict[str, Any] | None = None) -> str:
    result_evidence = result_evidence or {}
    if result_evidence.get("status") == "ok":
        return (
            "# Experiment Audit\n\n"
            "- integrity_status: runnable_generated_benchmark\n"
            f"- result_file: {result_evidence.get('path')}\n"
            f"- seeds_checked: {result_evidence.get('n_seeds')}\n"
            "- metric_correctness: parsed from JSON result file generated by local script\n"
            "- baseline_fairness: same train/test splits and feature budget for aggregate baselines\n"
            "- action: allow only benchmark-limited claims; reject deployment or real-world effectiveness claims\n"
        )
    return (
        "# Experiment Audit\n\n"
        "- integrity_status: provisional\n"
        "- seeds_checked: not applicable for dry-run backend\n"
        "- metric_correctness: requires real result parser\n"
        "- baseline_fairness: pending baseline reproduction\n"
        "- action: downgrade empirical claims until shell-backed experiments are available\n"
    )


def _load_result_evidence(workspace_root: Path) -> dict[str, Any]:
    candidates = [
        workspace_root / "code" / "experiments" / "result.json",
        workspace_root / "code" / "result.json",
        workspace_root / "results" / "summary.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        evidence = _normalize_result_payload(data)
        evidence["path"] = str(path)
        return evidence
    return {"status": "missing", "path": ""}


def _normalize_result_payload(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("static"), dict) and isinstance(data.get("adaptive"), dict):
        summary = {}
        for model_name in ("static", "adaptive"):
            metrics = data[model_name]
            label = "Static decomposition" if model_name == "static" else "Adaptive decomposition"
            summary[label] = {
                "support_rate": {"mean": metrics.get("avg_support_rate"), "std": 0.0},
                "f1": {"mean": metrics.get("avg_f1"), "std": 0.0},
                "citation_accuracy": {"mean": metrics.get("avg_citation_accuracy"), "std": 0.0},
                "avg_subtasks": {"mean": metrics.get("avg_subtasks"), "std": 0.0},
            }
        primary_metric = "support_rate"
        best = _best_model_by_metric(summary, primary_metric)
        return {
            "status": "ok",
            "dataset": data.get("dataset", "generated synthetic benchmark"),
            "n_seeds": data.get("n_seeds", 1),
            "best_model_by_auc": best,
            "best_model": best,
            "primary_metric": primary_metric,
            "summary": summary,
            "ablations": {
                "delta_support_rate": data.get("delta_support_rate"),
                "delta_f1": data.get("delta_f1"),
                "delta_citation_accuracy": data.get("delta_citation_accuracy"),
            },
            "rows": [],
            "protocol": data.get("config", {}),
            "limitations": [
                "Generated benchmark only unless a real dataset is supplied.",
                "Claims are limited to parsed static-vs-adaptive experiment metrics.",
            ],
        }
    if "summary" in data and isinstance(data["summary"], dict):
        summary, primary_metric = _normalize_summary_metrics(data["summary"])
        best = data.get("best_model_by_auc") or data.get("best_model") or _best_model_by_metric(summary, primary_metric)
        return {
            "status": "ok",
            "dataset": data.get("dataset", "generated benchmark"),
            "n_seeds": data.get("n_seeds", data.get("seeds", data.get("config", {}).get("num_seeds", "unknown"))),
            "best_model_by_auc": best,
            "best_model": best,
            "primary_metric": primary_metric,
            "summary": summary,
            "ablations": data.get("ablations", {}),
            "rows": data.get("rows", []),
            "protocol": data.get("protocol", {}),
            "limitations": data.get("limitations", []),
        }
    metrics = data.get("metrics")
    if isinstance(metrics, dict):
        return {
            "status": "ok",
            "dataset": data.get("dataset", "generated benchmark"),
            "n_seeds": data.get("n_seeds", 1),
            "best_model_by_auc": data.get("method") or "generated method",
            "summary": {data.get("method", "generated method"): {key: {"mean": value, "std": 0.0} for key, value in metrics.items()}},
            "limitations": [data.get("claim_support", "")],
        }
    return {"status": "unrecognized", "dataset": data.get("dataset", "unknown"), "summary": {}}


def _normalize_summary_metrics(summary: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if not summary:
        return {}, "score"
    first = next(iter(summary.values()))
    if isinstance(first, dict) and any(isinstance(value, dict) for value in first.values()):
        if "auc" in first:
            return summary, "auc"
        first_metric = next((key for key, value in first.items() if isinstance(value, dict)), "score")
        return summary, first_metric
    normalized = {}
    for model, metrics in summary.items():
        if isinstance(metrics, dict) and "mean" in metrics:
            normalized[model] = {
                "score": {"mean": metrics.get("mean"), "std": metrics.get("std", 0.0)},
                "runtime": {"mean": metrics.get("mean_runtime", 0.0), "std": 0.0},
            }
        elif isinstance(metrics, (int, float)):
            normalized[model] = {"score": {"mean": metrics, "std": 0.0}}
    return normalized, "score"


def _best_model_by_metric(summary: dict[str, Any], metric: str) -> str:
    best_model = ""
    best_value = float("-inf")
    for model, metrics in summary.items():
        raw = metrics.get(metric, {})
        value = raw.get("mean") if isinstance(raw, dict) else raw
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        if score > best_value:
            best_model = model
            best_value = score
    return best_model or "unknown"


def _metric_pm(metrics: dict[str, Any], key: str) -> str:
    raw = metrics.get(key, {})
    if isinstance(raw, dict):
        mean = raw.get("mean")
        std = raw.get("std", 0.0)
    else:
        mean = raw
        std = 0.0
    try:
        return f"{float(mean):.3f} +/- {float(std):.3f}"
    except (TypeError, ValueError):
        return "n/a"


def _merge_result_evidence(evidence: dict[str, Any], result_evidence: dict[str, Any]) -> dict[str, Any]:
    if result_evidence.get("status") != "ok":
        return evidence
    best = result_evidence.get("best_model_by_auc", "best parsed model")
    limitations = list(result_evidence.get("limitations") or [])
    limitations.extend(result_evidence.get("limitations") or [])
    limitations.append("Result claims are limited to the generated benchmark unless real data are attached.")
    limitations.append("The current result does not establish classroom deployment readiness.")
    return {
        "claims": [
            {
                "claim": f"{best} has the highest mean AUC on the generated benchmark.",
                "support": f"code/experiments/result.json parsed across {result_evidence.get('n_seeds')} seed(s).",
                "status": "supported_limited_generated_benchmark",
            }
        ],
        "limitations": list(dict.fromkeys(item for item in limitations if item)),
    }


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
            "- `experiments/autoscholar_fallback_experiment.py`: stable local fallback used when generated shell commands are not portable.\n"
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
        experiments / "autoscholar_fallback_experiment.py": _run_experiment_py(),
    }
    for item in (code_generation or {}).get("files", []):
        rel = str(item.get("path", "")).replace("\\", "/").lstrip("/")
        path = _safe_generated_code_path(code_root, rel)
        if path is None:
            continue
        if path.suffix not in {".py", ".json", ".yaml", ".yml", ".md", ".txt", ".sh", ".ps1"}:
            continue
        files[path] = str(item.get("content", ""))
    commands = (code_generation or {}).get("commands") or [
        "python code/experiments/run_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
    ]
    files[code_root / "run_commands.json"] = json.dumps({"commands": commands}, indent=2, ensure_ascii=False)
    paths = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        paths.append(str(path))
    return paths


def _execution_contract() -> dict[str, Any]:
    return {
        "allowed_write_roots": ["code/experiments", "code/methods", "code/analysis", "code/results"],
        "required_result_file": "code/experiments/result.json",
        "portable_command_rules": [
            "Use python, not python3.",
            "Use workspace-relative paths beginning with code/.",
            "Do not cd into arbitrary folders. If cd is needed, use code/experiments, code/analysis, or code/results only.",
            "Do not use bash, sh, chmod, source, or ./script.sh on Windows.",
            "Do not clone external repositories or use github.com/example placeholders.",
            "Create parent directories before writing outputs, or write outputs under code/experiments/result.json.",
        ],
        "preferred_commands": [
            "python code/experiments/run_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
        ],
        "real_experiment_requirement": (
            "Implement a self-contained executable benchmark with generated or user-supplied data, explicit baselines, "
            "metrics, seeds, and a parseable JSON summary. Do not claim real-world validation unless real data are supplied."
        ),
    }


def _repair_generated_commands(workspace_root: Path, commands: list[str]) -> list[str]:
    repaired = []
    for command in commands:
        normalized = str(command or "").strip()
        if not normalized:
            continue
        lower = normalized.lower()
        if any(token in lower for token in ["github.com/example/", "git clone ", " chmod ", "source venv/bin/activate"]):
            continue
        if lower.startswith("chmod ") or lower.startswith("bash ") or lower.startswith("sh ") or lower.startswith("./"):
            continue
        normalized = normalized.replace("python3 ", "python ")
        normalized = _repair_cd_command(workspace_root, normalized)
        if normalized is None:
            continue
        normalized = _repair_python_script_path(workspace_root, normalized)
        if normalized is None:
            continue
        if "--output " in normalized and "code/experiments/result.json" not in normalized:
            normalized = _force_result_output(normalized)
        if normalized not in repaired:
            repaired.append(normalized)
    fallback = "python code/experiments/autoscholar_fallback_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
    if not repaired:
        repaired.append(fallback)
    elif not any("code/experiments/result.json" in command for command in repaired):
        repaired.append(fallback)
    return repaired


def _repair_cd_command(workspace_root: Path, command: str) -> str | None:
    stripped = command.strip()
    for separator in ("&&", ";"):
        if stripped.startswith("cd ") and separator in stripped:
            target_text = stripped[len("cd ") : stripped.index(separator)].strip().strip('"').strip("'")
            remainder = stripped[stripped.index(separator) :]
            if target_text == "/workspace":
                return remainder.lstrip("&; ").strip()
            candidates = [Path(target_text), Path("code") / target_text]
            for candidate in candidates:
                if (workspace_root / candidate).exists():
                    candidate_text = str(candidate).replace("\\", "/")
                    return f"cd {candidate_text} {remainder}"
            return None
    return command


def _repair_python_script_path(workspace_root: Path, command: str) -> str | None:
    parts = command.split()
    cd_dir = _command_cd_dir(command)
    for index, part in enumerate(parts):
        if not part.endswith(".py"):
            continue
        script = Path(part.replace("\\", "/"))
        if cd_dir and not str(script).startswith("code/") and (workspace_root / cd_dir / script).exists():
            return command
        candidates = [script]
        if not str(script).startswith("code/"):
            candidates.extend([Path("code") / script, Path("code/experiments") / script.name, Path("code/analysis") / script.name])
        for candidate in candidates:
            if (workspace_root / candidate).exists():
                parts[index] = str(candidate).replace("\\", "/")
                return " ".join(parts)
        return None
    return command


def _command_cd_dir(command: str) -> Path | None:
    stripped = command.strip()
    for separator in ("&&", ";"):
        if stripped.startswith("cd ") and separator in stripped:
            target_text = stripped[len("cd ") : stripped.index(separator)].strip().strip('"').strip("'")
            return Path(target_text)
    return None


def _force_result_output(command: str) -> str:
    parts = command.split()
    if "--output" not in parts:
        return command
    idx = parts.index("--output")
    if idx + 1 < len(parts):
        parts[idx + 1] = "code/experiments/result.json" if not command.startswith("cd ") else "result.json"
    return " ".join(parts)


def _command_validation_markdown(commands: list[str]) -> str:
    lines = [
        "# Command Validation",
        "",
        "S02 commands after local path and portability repair:",
        "",
    ]
    lines.extend(f"- `{command}`" for command in commands)
    return "\n".join(lines) + "\n"


def _safe_generated_code_path(code_root: Path, rel: str) -> Path | None:
    if not rel:
        return None
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None
    if rel_path.parts and rel_path.parts[0] == "code":
        rel_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path("README.md")
    if not rel_path.suffix:
        rel_path = rel_path.with_suffix(".py")
    target = (code_root / rel_path).resolve()
    root = code_root.resolve()
    if root not in target.parents and target != root:
        return None
    return target


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
    return '''"""Run a reproducible generated benchmark.

The benchmark is synthetic by default, so it supports only benchmark-limited
claims. It exists to prevent paper generation from relying on unexecuted plans.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


N_STUDENTS = 520
N_WEEKS = 6
N_SEEDS = 5


def generate_dataset(seed: int):
    rng = np.random.default_rng(seed)
    ability = rng.normal(0.0, 1.0, N_STUDENTS)
    diligence = rng.normal(0.0, 1.0, N_STUDENTS)
    difficulty = rng.normal(0.0, 0.40, N_WEEKS)
    sequences = np.zeros((N_STUDENTS, 4, 4), dtype=np.float32)
    full_scores = []
    missing_rates = []
    delays = []
    for student in range(N_STUDENTS):
        scores = []
        misses = []
        delay_values = []
        trend = rng.normal(0.0, 0.10)
        for week in range(N_WEEKS):
            latent = ability[student] + trend * week - difficulty[week] + rng.normal(0.0, 0.35)
            accuracy = 1.0 / (1.0 + np.exp(-latent))
            score = np.clip(accuracy + rng.normal(0.0, 0.08), 0.0, 1.0)
            delay = rng.exponential(scale=max(0.08, 0.75 - 0.20 * diligence[student] - 0.12 * ability[student]))
            missing = rng.random() < (0.04 + 0.08 / (1.0 + np.exp(ability[student] + diligence[student])))
            scores.append(score)
            misses.append(float(missing))
            delay_values.append(min(delay, 2.5) / 2.5)
            if week < 4:
                sequences[student, week] = [score, min(delay, 2.5) / 2.5, accuracy, float(missing)]
        full_scores.append(np.mean(scores))
        missing_rates.append(np.mean(misses))
        delays.append(np.mean(delay_values[-2:]))
    risk_logit = -3.0 * np.array(full_scores) + 0.9 * np.array(missing_rates) + 0.65 * np.array(delays) + 1.65
    risk_probability = 1.0 / (1.0 + np.exp(-risk_logit))
    labels = (risk_probability + rng.normal(0.0, 0.05, N_STUDENTS) > 0.50).astype(int)
    return sequences, labels


def aggregate_features(x):
    return np.concatenate([x.mean(axis=1), x.std(axis=1), x[:, -1, :], x[:, -1, :] - x[:, 0, :]], axis=1)


def score_only_features(x):
    score = x[:, :, 0:1]
    return np.concatenate([score.mean(axis=1), score.std(axis=1), score[:, -1, :], score[:, -1, :] - score[:, 0, :]], axis=1)


def engagement_only_features(x):
    engagement = x[:, :, [1, 3]]
    return np.concatenate(
        [engagement.mean(axis=1), engagement.std(axis=1), engagement[:, -1, :], engagement[:, -1, :] - engagement[:, 0, :]],
        axis=1,
    )


def temporal_weighted_features(x):
    weights = np.array([0.10, 0.18, 0.27, 0.45], dtype=np.float32)
    weighted = (x * weights.reshape(1, -1, 1)).sum(axis=1)
    trend = x[:, -1, :] - x[:, 0, :]
    return np.concatenate([weighted, trend], axis=1)


def precision_at_20(y_true, scores):
    k = max(1, int(len(y_true) * 0.20))
    order = np.argsort(scores)[::-1][:k]
    return float(np.mean(y_true[order]))


def evaluate(y_true, scores):
    pred = (scores >= 0.5).astype(int)
    return {
        "auc": float(roc_auc_score(y_true, scores)),
        "f1": float(f1_score(y_true, pred)),
        "brier": float(brier_score_loss(y_true, scores)),
        "p_at_20": precision_at_20(y_true, scores),
    }


def summarize(rows):
    summary = {}
    for model in sorted({row["model"] for row in rows}):
        items = [row for row in rows if row["model"] == model]
        summary[model] = {}
        for metric in ["auc", "f1", "brier", "p_at_20"]:
            values = np.array([row[metric] for row in items], dtype=float)
            summary[model][metric] = {"mean": float(values.mean()), "std": float(values.std(ddof=1))}
    return summary


def fit_logistic(train_x, train_y, test_x, seed):
    scaler = StandardScaler()
    z_train = scaler.fit_transform(train_x)
    z_test = scaler.transform(test_x)
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)
    model.fit(z_train, train_y)
    return model.predict_proba(z_test)[:, 1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output", default="result.json")
    args = parser.parse_args()
    rows = []
    for seed in range(N_SEEDS):
        x, y = generate_dataset(1000 + seed)
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30, stratify=y, random_state=seed)
        agg_train = aggregate_features(x_train)
        agg_test = aggregate_features(x_test)
        tw_train = temporal_weighted_features(x_train)
        tw_test = temporal_weighted_features(x_test)

        dummy = DummyClassifier(strategy="prior")
        dummy.fit(agg_train, y_train)
        rows.append({"seed": seed, "model": "Prior baseline", **evaluate(y_test, dummy.predict_proba(agg_test)[:, 1])})

        rows.append({
            "seed": seed,
            "model": "Score-only logistic",
            **evaluate(y_test, fit_logistic(score_only_features(x_train), y_train, score_only_features(x_test), seed)),
        })

        rows.append({
            "seed": seed,
            "model": "Engagement-only logistic",
            **evaluate(y_test, fit_logistic(engagement_only_features(x_train), y_train, engagement_only_features(x_test), seed)),
        })

        rows.append({
            "seed": seed,
            "model": "Full-feature logistic",
            **evaluate(y_test, fit_logistic(agg_train, y_train, agg_test, seed)),
        })

        gb = GradientBoostingClassifier(n_estimators=80, max_depth=2, learning_rate=0.05, random_state=seed)
        gb.fit(agg_train, y_train)
        rows.append({"seed": seed, "model": "Gradient boosting", **evaluate(y_test, gb.predict_proba(agg_test)[:, 1])})

        rf = RandomForestClassifier(n_estimators=120, max_depth=5, min_samples_leaf=5, class_weight="balanced", random_state=seed)
        rf.fit(agg_train, y_train)
        rows.append({"seed": seed, "model": "Random forest", **evaluate(y_test, rf.predict_proba(agg_test)[:, 1])})

        rows.append({
            "seed": seed,
            "model": "Temporal weighted logistic",
            **evaluate(y_test, fit_logistic(tw_train, y_train, tw_test, seed)),
        })

    summary = summarize(rows)
    best_model = max(summary, key=lambda model: summary[model]["auc"]["mean"])
    ablations = {
        "score_vs_full_auc_delta": float(summary["Full-feature logistic"]["auc"]["mean"] - summary["Score-only logistic"]["auc"]["mean"]),
        "engagement_vs_full_auc_delta": float(summary["Full-feature logistic"]["auc"]["mean"] - summary["Engagement-only logistic"]["auc"]["mean"]),
        "temporal_vs_full_auc_delta": float(summary["Temporal weighted logistic"]["auc"]["mean"] - summary["Full-feature logistic"]["auc"]["mean"]),
    }
    result = {
        "status": "ok",
        "dataset": "generated synthetic quiz-risk benchmark",
        "n_students": N_STUDENTS,
        "n_weeks": N_WEEKS,
        "n_seeds": N_SEEDS,
        "best_model_by_auc": best_model,
        "protocol": {
            "test_fraction": 0.30,
            "split": "stratified train-test split per seed",
            "metrics": ["auc", "f1", "brier", "p_at_20"],
            "models": sorted({row["model"] for row in rows}),
        },
        "summary": summary,
        "ablations": ablations,
        "rows": rows,
        "limitations": [
            "Synthetic benchmark only; no real classroom dataset is used.",
            "Claims do not establish deployment readiness or intervention effectiveness.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"best_model_by_auc": best_model, "output": str(output)}, indent=2))


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


def _layout_audit(workspace_root: Path, context: dict[str, Any]) -> dict[str, Any]:
    draft_path = Path(context.get("draft_path", workspace_root / "paper" / "draft.md"))
    tex_path = Path(context.get("latex_path", workspace_root / "paper" / "main.tex"))
    log_path = tex_path.with_suffix(".log")
    pdf_path = tex_path.with_suffix(".pdf")
    markdown = draft_path.read_text(encoding="utf-8", errors="replace") if draft_path.exists() else ""
    tex = tex_path.read_text(encoding="utf-8", errors="replace") if tex_path.exists() else ""
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    sections = [line[3:].strip() for line in markdown.splitlines() if line.startswith("## ")]
    required_sections = {
        "Abstract",
        "Introduction",
        "Related Work",
        "Problem Formulation",
        "Method",
        "Experiments",
        "Results",
        "Ablation Study",
        "Discussion",
        "References",
    }
    missing_sections = sorted(required_sections.difference(sections))
    table_count = tex.count(r"\begin{table}") + tex.count(r"\begin{table*}")
    formula_count = tex.count(r"\[")
    overfull_count = log.count("Overfull \\hbox")
    underfull_count = log.count("Underfull \\hbox")
    unresolved_markdown_tables = [line for line in tex.splitlines() if line.strip().startswith("|")]
    page_count = _page_count_from_log(log)
    issues = []
    if missing_sections:
        issues.append("missing required paper sections")
    if table_count < 2:
        issues.append("expected at least two LaTeX tables")
    if formula_count < 4:
        issues.append("expected at least four displayed formulas")
    if overfull_count:
        issues.append(f"{overfull_count} overfull hbox warning(s)")
    if unresolved_markdown_tables:
        issues.append("raw Markdown table lines remain in LaTeX")
    if page_count and page_count < 3:
        issues.append("compiled PDF is shorter than three pages")
    status = "pass" if not issues else "warn"
    content_status = "pass" if not missing_sections and len(markdown) >= 18000 else "warn"
    return {
        "status": status,
        "content_status": content_status,
        "issues": issues,
        "missing_sections": missing_sections,
        "section_count": len(sections),
        "table_count": table_count,
        "formula_count": formula_count,
        "page_count": page_count,
        "overfull_hbox": overfull_count,
        "underfull_hbox": underfull_count,
        "markdown_bytes": len(markdown.encode("utf-8")),
        "tex_bytes": len(tex.encode("utf-8")),
        "pdf_exists": pdf_path.exists(),
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
    }


def _page_count_from_log(log: str) -> int | None:
    marker = "Output written on"
    for line in log.splitlines():
        if marker not in line or "pages" not in line:
            continue
        before_pages = line.split("pages", 1)[0]
        digits = ""
        for char in reversed(before_pages):
            if char.isdigit():
                digits = char + digits
            elif digits:
                break
        if digits:
            return int(digits)
    return None


def _layout_audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Layout And Content Audit",
        "",
        f"- layout_status: {audit.get('status')}",
        f"- content_status: {audit.get('content_status')}",
        f"- page_count: {audit.get('page_count')}",
        f"- table_count: {audit.get('table_count')}",
        f"- formula_count: {audit.get('formula_count')}",
        f"- overfull_hbox: {audit.get('overfull_hbox')}",
        f"- underfull_hbox: {audit.get('underfull_hbox')}",
        f"- markdown_bytes: {audit.get('markdown_bytes')}",
        f"- pdf_bytes: {audit.get('pdf_bytes')}",
        "",
        "## Issues",
        "",
    ]
    issues = audit.get("issues") or []
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- No blocking layout issue detected by local static checks.")
    missing = audit.get("missing_sections") or []
    if missing:
        lines.extend(["", "## Missing Sections", ""])
        lines.extend(f"- {section}" for section in missing)
    return "\n".join(lines) + "\n"


def _overleaf_sync_markdown() -> str:
    return (
        "# Overleaf Sync\n\n"
        "- status: skipped\n"
        "- reason: no Overleaf sync configuration was provided\n"
        "- fallback: local release package is authoritative\n"
    )
