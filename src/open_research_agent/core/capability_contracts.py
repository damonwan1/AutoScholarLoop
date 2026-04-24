from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityContract:
    key: str
    responsibility: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    quality_gates: tuple[str, ...]
    fallback_route: str


STAGE_CAPABILITIES: dict[str, tuple[CapabilityContract, ...]] = {
    "S00": (
        CapabilityContract(
            key="brief_normalizer",
            responsibility="Turn the user seed into a bounded research brief with problem, scope, constraints, non-goals, and target venue assumptions.",
            inputs=("user seed", "target venue", "constraints", "uploaded notes"),
            outputs=("research_brief.md", "normalized problem statement", "constraint ledger"),
            quality_gates=("one narrow subfield", "explicit non-goals", "known target output"),
            fallback_route="S00:data_repair",
        ),
        CapabilityContract(
            key="field_cartographer",
            responsibility="Map local papers and retrieved metadata into paper cards, method families, datasets, baselines, and evidence gaps.",
            inputs=("source_papers/", "reference metadata", "user references"),
            outputs=("paper_cards.md", "method_map.md", "dataset_baseline_map.md", "landscape_gaps.md"),
            quality_gates=("local material checked first", "papers grouped by approach", "gaps tied to evidence"),
            fallback_route="S00:repair_or_narrow_scope",
        ),
        CapabilityContract(
            key="recent_work_indexer",
            responsibility="Collect structured recent-work records and mark coverage limits for novelty-sensitive decisions.",
            inputs=("search queries", "paper titles", "paper IDs", "literature API records"),
            outputs=("recent_work_records.json", "closest_work_candidates.md", "source_coverage_note.md"),
            quality_gates=("deduplicated records", "recency window marked", "missing sources explicit"),
            fallback_route="S00:provisional_evidence",
        ),
    ),
    "S01": (
        CapabilityContract(
            key="direction_workshop",
            responsibility="Run a professor-style landscape-to-direction workshop with generation, attack, filtering, review, and refinement.",
            inputs=("field_map.md", "paper_cards.md", "method_map.md", "research_brief.md"),
            outputs=("IDEA_REPORT.md", "ranked_directions.md", "eliminated_directions.md"),
            quality_gates=("directions grounded in landscape gaps", "weak directions eliminated", "pilot need marked"),
            fallback_route="S01:rerun_with_adjusted_scope",
        ),
        CapabilityContract(
            key="hypothesis_factory",
            responsibility="Generate concrete research hypotheses with minimum viable tests, risk, effort, and reviewer objections.",
            inputs=("landscape summary", "known gaps", "constraints", "do-not-repeat list"),
            outputs=("raw_direction_pool", "filtered_direction_pool", "top_candidate_set"),
            quality_gates=("not trivial transfer", "compute feasible", "reviewer relevance test passed"),
            fallback_route="S01:downgrade_merge_or_eliminate",
        ),
        CapabilityContract(
            key="frontier_overlap_probe",
            responsibility="Break a candidate into core claims and compare each against recent and closest prior work.",
            inputs=("candidate direction", "core technical claims", "literature hits"),
            outputs=("novelty_report.md", "closest_prior_work_table.md", "proceed_caution_abandon"),
            quality_gates=("3-5 claims checked", "recent work checked", "delta explicit"),
            fallback_route="S01:kill_pivot_or_reframe",
        ),
        CapabilityContract(
            key="senior_critique_panel",
            responsibility="Stress-test idea quality, top-venue sufficiency, and experimental defensibility.",
            inputs=("top direction", "novelty report", "pilot signal if available"),
            outputs=("critical_review.md", "minimum_fix_list.md", "experiment_requirements.md"),
            quality_gates=("actionable objections", "claims matrix", "minimum evidence package"),
            fallback_route="S01:refine_or_restart",
        ),
    ),
    "S02": (
        CapabilityContract(
            key="method_freezer",
            responsibility="Freeze the problem anchor and convert the selected direction into a claim-driven experiment roadmap.",
            inputs=("executor_brief.md", "review concerns", "chosen direction"),
            outputs=("FINAL_PROPOSAL.md", "EXPERIMENT_PLAN.md", "EXPERIMENT_TRACKER.md"),
            quality_gates=("primary claims limited", "strong baselines prioritized", "must-run experiments identified"),
            fallback_route="S01:no_executable_plan",
        ),
        CapabilityContract(
            key="implementation_bridge",
            responsibility="Turn the experiment roadmap into runnable code, sanity checks, deployment hooks, and initial result capture.",
            inputs=("EXPERIMENT_PLAN.md", "base repo", "method proposal"),
            outputs=("experiment scripts", "sanity result", "initial result logs"),
            quality_gates=("configurable runs", "fixed seeds", "parseable results", "sanity first"),
            fallback_route="S02:debug_or_reduce_scope",
        ),
        CapabilityContract(
            key="run_orchestrator",
            responsibility="Launch, monitor, retry, and record experiments under compute and timeout budgets.",
            inputs=("run commands", "compute budget", "tracker milestones"),
            outputs=("run logs", "status table", "failure records"),
            quality_gates=("timeouts enforced", "stderr preserved", "partial results collected"),
            fallback_route="S02:retry_reschedule_or_block",
        ),
        CapabilityContract(
            key="evidence_interpreter",
            responsibility="Convert result files into supported, partial, or unsupported claims and audit experiment integrity.",
            inputs=("result JSON/CSV", "logs", "intended claims", "baseline comparisons"),
            outputs=("RESULTS_ANALYSIS.md", "CLAIMS_FROM_RESULTS.md", "EXPERIMENT_AUDIT.md"),
            quality_gates=("delta vs baseline computed", "missing evidence listed", "integrity affects confidence"),
            fallback_route="S02:add_experiment_revise_pivot_or_kill",
        ),
    ),
    "S03": (
        CapabilityContract(
            key="paper_architect",
            responsibility="Create a section-by-section paper plan from claims, evidence, venue assumptions, and figure needs.",
            inputs=("CLAIMS_FROM_RESULTS.md", "review conclusions", "experiment results"),
            outputs=("PAPER_PLAN.md", "claims_evidence_matrix.md", "figure_plan.md"),
            quality_gates=("one coherent story", "front-loaded contribution", "venue budget tracked"),
            fallback_route="S02:missing_evidence_or_S01_unclear_story",
        ),
        CapabilityContract(
            key="evidence_writer",
            responsibility="Draft manuscript sections from the plan and evidence while keeping citation and claim discipline.",
            inputs=("PAPER_PLAN.md", "narrative report", "figures", "bibliography"),
            outputs=("paper/main.tex", "paper/sections/*.tex", "references.bib"),
            quality_gates=("no placeholders", "claims mapped to evidence", "venue citation style consistent"),
            fallback_route="S03:revise_or_weaken_claim",
        ),
        CapabilityContract(
            key="figure_storyboarder",
            responsibility="Register or generate figure specifications that directly support the paper's claim sequence.",
            inputs=("figure plan", "result tables", "analysis outputs"),
            outputs=("figures/*", "figures/latex_includes.tex", "figure_readability_report.md"),
            quality_gates=("figures answer claims", "captions match data", "visuals readable"),
            fallback_route="S02:analysis_needed_or_S03:rewrite_figure_spec",
        ),
        CapabilityContract(
            key="manuscript_review_loop",
            responsibility="Run independent reviewer-style critique and visible paper-improvement rounds.",
            inputs=("draft paper", "claim table", "review log"),
            outputs=("AUTO_REVIEW.md", "PAPER_IMPROVEMENT_LOG.md", "revision_plan.md"),
            quality_gates=("critical weaknesses addressed", "review threshold met", "fixes visible in files"),
            fallback_route="S03:edit_or_S02:collect_more_evidence",
        ),
    ),
    "S04": (
        CapabilityContract(
            key="reference_integrity_auditor",
            responsibility="Verify citation existence, metadata consistency, and whether cited context supports the manuscript claim.",
            inputs=("paper tex files", "references.bib", "cite contexts"),
            outputs=("CITATION_AUDIT.md", "CITATION_AUDIT.json"),
            quality_gates=("cite keys resolved", "metadata canonical", "context supports claim"),
            fallback_route="S03:fix_replace_or_remove_reference",
        ),
        CapabilityContract(
            key="submission_builder",
            responsibility="Compile the manuscript, diagnose build errors, and record output readiness checks.",
            inputs=("paper/main.tex", "sections", "references.bib", "figures"),
            outputs=("paper/main.pdf", "compile.log", "page_count.md"),
            quality_gates=("PDF exists", "no unresolved references", "page budget checked"),
            fallback_route="S03:fix_compile_errors",
        ),
        CapabilityContract(
            key="external_package_sync",
            responsibility="Optionally synchronize a clean local release with an external writing or collaboration target.",
            inputs=("paper directory", "release package", "sync config"),
            outputs=("sync_report.md", "remote_state_note.md"),
            quality_gates=("local release clean", "remote overwrite explicit"),
            fallback_route="S04:skip_sync_keep_local_release",
        ),
    ),
}


def contracts_for(stage: str) -> tuple[CapabilityContract, ...]:
    return STAGE_CAPABILITIES.get(stage, ())


def contracts_markdown(stage: str) -> str:
    contracts = contracts_for(stage)
    if not contracts:
        return ""
    lines = [f"## Capability Contracts For {stage}", ""]
    for contract in contracts:
        lines.append(f"### {contract.key}")
        lines.append(f"- Responsibility: {contract.responsibility}")
        lines.append("- Inputs: " + ", ".join(contract.inputs))
        lines.append("- Outputs: " + ", ".join(contract.outputs))
        lines.append("- Quality gates: " + ", ".join(contract.quality_gates))
        lines.append(f"- Fallback route: {contract.fallback_route}")
        lines.append("")
    return "\n".join(lines)


def contracts_json(stage: str) -> list[dict[str, object]]:
    return [
        {
            "key": c.key,
            "responsibility": c.responsibility,
            "inputs": list(c.inputs),
            "outputs": list(c.outputs),
            "quality_gates": list(c.quality_gates),
            "fallback_route": c.fallback_route,
        }
        for c in contracts_for(stage)
    ]
