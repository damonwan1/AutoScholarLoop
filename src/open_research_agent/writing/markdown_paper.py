from __future__ import annotations

from typing import Any


def build_markdown_paper(context: dict[str, Any]) -> str:
    brief = context.get("brief", {})
    ideas = context.get("ideas", {}).get("candidates", [])
    selected = context.get("selected_idea", "direction_1")
    selected_idea = next((x for x in ideas if x.get("id") == selected), ideas[0] if ideas else {})
    evidence = context.get("evidence", {})
    claims = evidence.get("claims", [])
    limitations = evidence.get("limitations", [])
    paper_format = context.get("paper_format", "ieee")
    manuscript = context.get("manuscript", {})
    if _has_manuscript_content(manuscript):
        return _build_from_manuscript(manuscript, context, claims, limitations, paper_format)
    if manuscript:
        context = dict(context)
        context["manuscript_warning"] = "The model returned an empty manuscript object; fallback draft was used."

    return _build_fallback_paper(context, brief, selected_idea, claims, limitations, paper_format)


def _build_fallback_paper(
    context: dict[str, Any],
    brief: dict[str, Any],
    selected_idea: dict[str, Any],
    claims: list[dict[str, Any]],
    limitations: list[str],
    paper_format: str,
) -> str:
    lines = [
        f"# {selected_idea.get('title', 'AUTO Research Draft')}",
        "",
        f"Format target: {paper_format}",
        "",
        "## Abstract",
        "",
        f"This draft studies {brief.get('problem', context.get('seed'))}. "
        "It proposes an auditable AUTO Research workflow that connects idea generation, "
        "novelty checks, exploration, evidence synthesis, paper writing, review, and revision.",
        "",
        "## Introduction",
        "",
        "Automated research systems need more than fluent paper writing. They need a traceable "
        "process that preserves why directions were selected, what evidence was collected, and "
        "which claims are supported.",
        "",
        "## Related Work",
        "",
        "This section is intentionally conservative in v0.1. Provided references are treated as "
        "source material, while external literature search is scheduled for a later adapter.",
        "",
        "## Method",
        "",
        "The method represents research as a sequence of typed stages. Each stage consumes the "
        "workspace state and writes artifacts before the next stage can proceed.",
        "",
        "## Experiments And Exploration",
        "",
        "The current implementation runs an offline architecture probe. Future versions will attach "
        "sandboxed shell, notebook, and remote GPU execution backends.",
        "",
        "## Results And Evidence",
        "",
    ]
    if claims:
        for claim in claims:
            lines.append(f"- Claim: {claim.get('claim')}")
            lines.append(f"  Support: {claim.get('support')}")
            lines.append(f"  Status: {claim.get('status')}")
    else:
        lines.append("- No supported claims were produced.")

    lines.extend(["", "## Limitations", ""])
    for limitation in limitations or ["Real novelty checking and experiment execution are not implemented in v0.1."]:
        lines.append(f"- {limitation}")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "The project establishes a reusable foundation for AUTO Research. Its main contribution "
            "at this stage is the workflow contract and artifact discipline needed for later stronger agents.",
            "",
            "## Reproducibility Note",
            "",
            "All stage artifacts are stored in the run workspace manifest.",
        ]
    )
    if context.get("manuscript_warning"):
        lines.extend(["", "## Generation Note", "", context["manuscript_warning"]])
    return "\n".join(lines)


def _build_from_manuscript(
    manuscript: dict[str, Any],
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    limitations: list[str],
    paper_format: str,
) -> str:
    title = manuscript.get("title") or "AUTO Research Draft"
    supported_claims = [claim for claim in claims if _is_supported_claim(claim)]
    unsupported_claims = [claim for claim in claims if not _is_supported_claim(claim)]
    if unsupported_claims:
        results_text = (
            "No validated experimental result is available yet. The quality gate requires another "
            "execution loop before any efficiency, accuracy, dataset, or superiority claim can be stated as a result."
        )
    elif supported_claims:
        results_text = _clean_text(manuscript.get("results")) or _section_fallback("results", context)
    else:
        results_text = "No claim-evidence table was produced for this draft."
    section_text = {
        "abstract": _clean_text(manuscript.get("abstract")) or _section_fallback("abstract", context),
        "introduction": _clean_text(manuscript.get("introduction")) or _section_fallback("introduction", context),
        "related_work": _clean_text(manuscript.get("related_work")) or _section_fallback("related_work", context),
        "method": _clean_text(manuscript.get("method")) or _section_fallback("method", context),
        "experiments": _clean_text(manuscript.get("experiments")) or _section_fallback("experiments", context),
        "conclusion": _clean_text(manuscript.get("conclusion")) or _section_fallback("conclusion", context),
    }
    if unsupported_claims:
        section_text.update(_unsupported_claim_section_overrides(context, unsupported_claims))
        results_text = _unsupported_claim_results_text()
    elif _has_result_evidence(context):
        result_overrides = _result_section_overrides(context)
        section_text.update(result_overrides)
        results_text = result_overrides["results"]
    discussion_text = _discussion_section(context) if _has_result_evidence(context) else ""
    threats_text = _threats_section(context) if _has_result_evidence(context) else ""
    problem_text = _problem_formulation_section(context) if _has_result_evidence(context) else ""
    benchmark_text = _benchmark_section(context) if _has_result_evidence(context) else ""
    implementation_text = _implementation_section(context) if _has_result_evidence(context) else ""
    diagnostic_text = _diagnostic_section(context) if _has_result_evidence(context) else ""
    ablation_text = _ablation_section(context) if _has_result_evidence(context) else ""
    references_text = _references_section(context)
    lines = [
        f"# {title}",
        "",
        f"Format target: {paper_format}",
        "",
        "## Abstract",
        "",
        section_text["abstract"],
        "",
        "## Introduction",
        "",
        section_text["introduction"],
        "",
        "## Related Work",
        "",
        section_text["related_work"],
        "",
    ]
    if problem_text:
        lines.extend(["## Problem Formulation", "", problem_text, ""])
    lines.extend(
        [
        "## Method",
        "",
        section_text["method"],
        "",
        ]
    )
    if benchmark_text:
        lines.extend(["## Benchmark Construction", "", benchmark_text, ""])
    if implementation_text:
        lines.extend(["## Implementation Details", "", implementation_text, ""])
    lines.extend(
        [
        "## Experiments",
        "",
        section_text["experiments"],
        "",
        "## Results",
        "",
        results_text,
        "",
    ]
    )
    if ablation_text:
        lines.extend(["## Ablation Study", "", ablation_text, ""])
    if discussion_text:
        lines.extend(["## Discussion", "", discussion_text, ""])
    if diagnostic_text:
        lines.extend(["## Diagnostic Analysis", "", diagnostic_text, ""])
    if threats_text:
        lines.extend(["## Threats to Validity", "", threats_text, ""])
    lines.extend(
        [
        "## Claim-Evidence Status",
        "",
        ]
    )
    if claims:
        for claim in claims:
            lines.append(f"- Claim: {_claim_text(claim)}")
            lines.append(f"  Support: {_claim_support(claim)}")
            lines.append(f"  Status: {_claim_status(claim)}")
    else:
        lines.append("- No supported claims were produced.")

    merged_limitations = limitations or manuscript.get("limitations") or []
    lines.extend(["", "## Limitations", ""])
    for limitation in merged_limitations:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            section_text["conclusion"],
            "",
            "## Reproducibility Note",
            "",
            "All generated code, checkpoints, LaTeX files, and quality reports are stored in the run workspace.",
        ]
    )
    if references_text:
        lines.extend(["", "## References", "", references_text])
    return "\n".join(lines)


def _is_supported_claim(claim: dict[str, Any]) -> bool:
    status = str(claim.get("status", "")).lower()
    support = str(claim.get("support") or claim.get("evidence") or "").strip().lower()
    if not support or support in {"none", "null", "n/a", "no evidence", "hypothesis"}:
        return False
    weak_markers = (
        "unsupported",
        "hypothesis",
        "future",
        "planned",
        "missing",
        "unknown",
        "partial",
        "provisional",
        "aspirational",
        "untested",
    )
    support_weak_markers = (
        "no experimental result",
        "no result",
        "not executed",
        "not implemented",
        "not evaluated",
        "has not been",
        "synthetic data only",
        "future work",
        "hypothesis",
    )
    return not any(marker in status for marker in weak_markers) and not any(
        marker in support for marker in support_weak_markers
    )


def _claim_text(claim: dict[str, Any]) -> str:
    return _clean_text(claim.get("claim") or claim.get("statement") or claim.get("id") or "Unspecified claim")


def _claim_support(claim: dict[str, Any]) -> str:
    return _clean_text(claim.get("support") or claim.get("evidence") or "No evidence provided")


def _claim_status(claim: dict[str, Any]) -> str:
    return _clean_text(claim.get("status") or "unknown")


def _has_manuscript_content(manuscript: Any) -> bool:
    if not isinstance(manuscript, dict):
        return False
    text_fields = (
        "title",
        "abstract",
        "introduction",
        "related_work",
        "method",
        "experiments",
        "results",
        "conclusion",
    )
    if any(_clean_text(manuscript.get(field)) for field in text_fields):
        return True
    limitations = manuscript.get("limitations")
    return isinstance(limitations, list) and any(_clean_text(item) for item in limitations)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _section_fallback(section: str, context: dict[str, Any]) -> str:
    seed = _clean_text(context.get("seed")) or "the requested research direction"
    selected = _clean_text(context.get("selected_idea")) or "the selected direction"
    fallbacks = {
        "abstract": (
            f"This draft studies {seed}. It records the current AutoScholarLoop artifacts and "
            "keeps claims constrained to the evidence available in this run."
        ),
        "introduction": (
            f"The run starts from {seed} and converts it into auditable research decisions, "
            "execution artifacts, evidence checks, and a manuscript draft."
        ),
        "related_work": (
            "Related work should be expanded from verified uploaded references and literature cards. "
            "This fallback text is used because the model did not provide a populated section."
        ),
        "method": (
            f"The selected direction is {selected}. The workflow uses field mapping, idea selection, "
            "execution review, evidence synthesis, writing review, and a final quality gate."
        ),
        "experiments": (
            "The current run records generated code, execution logs, and claim-evidence artifacts. "
            "Real benchmark claims require completed result files and fair baselines."
        ),
        "results": "No validated result text was supplied by the model for this section.",
        "conclusion": (
            "The draft is a recoverable research artifact rather than a final paper. The next loop "
            "should strengthen evidence, citations, and experimental support."
        ),
    }
    return fallbacks[section]


def _unsupported_claim_section_overrides(
    context: dict[str, Any],
    unsupported_claims: list[dict[str, Any]],
) -> dict[str, str]:
    seed = _clean_text(context.get("seed")) or "the requested research direction"
    issue_count = len(unsupported_claims)
    return {
        "abstract": (
            f"This manuscript studies {seed}. The current run produced a research plan, method description, "
            f"and execution scaffold, but the quality gate found {issue_count} claim(s) without sufficient "
            "experimental or citation evidence. Therefore, the paper reports no performance numbers and treats "
            "the proposed method as an unvalidated research artifact pending another execution loop."
        ),
        "introduction": (
            f"The target problem is {seed}. This draft defines the task, candidate method, evidence requirements, "
            "and reproducibility artifacts. It intentionally avoids accuracy, efficiency, dataset, or superiority "
            "claims until the execution stage produces auditable result files and baseline comparisons."
        ),
        "experiments": (
            "The current workspace contains generated experiment scaffolds, configuration files, and run commands. "
            "These artifacts are not sufficient evidence by themselves. A submission-ready version must run the "
            "planned experiments on a documented dataset, preserve logs and result tables, and compare against "
            "clearly specified baselines."
        ),
        "conclusion": (
            "This draft is a truthful intermediate manuscript rather than a submission-ready empirical paper. "
            "The next required step is to return to execution, run the proposed method and baselines, audit the "
            "result files, and then regenerate the manuscript with only evidence-supported claims."
        ),
    }


def _unsupported_claim_results_text() -> str:
    return (
        "No validated experimental result is available yet. The quality gate requires another "
        "execution loop before any efficiency, accuracy, dataset, or superiority claim can be stated as a result."
    )


def _has_result_evidence(context: dict[str, Any]) -> bool:
    return context.get("result_evidence", {}).get("status") == "ok"


def _result_section_overrides(context: dict[str, Any]) -> dict[str, str]:
    result = context.get("result_evidence", {})
    summary = result.get("summary", {})
    primary_metric = result.get("primary_metric", "auc")
    metric_name = _metric_display_name(primary_metric)
    best = result.get("best_model") or result.get("best_model_by_auc", "the best parsed model")
    best_score = _metric_pm(summary.get(best, {}), primary_metric)
    table = _result_markdown_table(summary)
    result_path = _result_display_path(result)
    return {
        "abstract": (
            f"This manuscript reports a reproducible generated benchmark for {context.get('seed', 'the target task')}. "
            f"The execution stage produced a parsed result file across {result.get('n_seeds')} seed(s). "
            f"The strongest method by mean {metric_name} is {best} ({best_score}). Claims are limited to the generated benchmark "
            "and should not be interpreted as classroom deployment evidence."
        ),
        "introduction": _result_introduction(context, best, best_score, metric_name),
        "related_work": _result_related_work(context),
        "method": _result_method(context),
        "experiments": (
            f"The experiment uses {result.get('dataset', 'a generated benchmark')} and stores the parsed result file at "
            f"`{result_path}`. Methods are compared under the same generated benchmark using {metric_name} and any "
            "secondary metrics recorded in the result JSON. The current benchmark uses multiple random seeds where "
            "available to reduce dependence on a single random draw. The generated result file records method-level "
            "aggregate statistics and is treated as the only valid source for numerical claims in this manuscript."
        ),
        "results": (
            f"{table}\n\n"
            f"The result file identifies {best} as the strongest method by mean {metric_name} for this generated benchmark. "
            "The limitations section records why this evidence does not support deployment or real-world effectiveness claims."
        ),
        "conclusion": (
            "This run produced an evidence-grounded manuscript from an executable benchmark. The next scientific step is "
            "to replace the generated benchmark with a documented real dataset, add verified references, and rerun the "
            "claim-evidence audit before treating the manuscript as submission-ready."
        ),
    }


def _result_introduction(context: dict[str, Any], best: str, best_score: str, metric_name: str = "AUC") -> str:
    seed = context.get("seed", "the target task")
    return (
        f"The target problem is {seed}. A scientifically useful AutoScholarLoop run must not stop at generating a "
        "plausible paper outline; it must produce artifacts that can be inspected, rerun, and used to accept or reject "
        "claims. In this run, the workflow constructs a generated quiz-risk benchmark, executes several baseline models, "
        "parses the resulting metrics, and then writes the manuscript from those parsed metrics rather than from model "
        "speculation.\n\n"
        "The paper is intentionally scoped as a benchmark report rather than a deployment study. The central question is "
        "whether the system can connect a research idea to executable evidence and then preserve the evidence boundary "
        "in the manuscript. The current parsed result identifies "
        f"{best} as the strongest method by mean {metric_name} ({best_score}), but this conclusion is limited to the generated benchmark. "
        "Real educational claims require a documented dataset, verified references, and external validity checks."
        "\n\n"
        "The practical motivation is early intervention. In many course settings, quiz answers, missing submissions, "
        "and delayed attempts are available before final outcomes are known. A useful warning model must therefore "
        "summarize partial traces without leaking future information, rank students consistently enough for limited "
        "advisor attention, and expose uncertainty when the available evidence is weak. The generated benchmark captures "
        "these constraints in a controlled form: the label is synthetic, but the available variables mimic common "
        "learning-management-system signals such as recent score, submission delay, and missingness.\n\n"
        "This manuscript also serves as a regression test for the paper-generation system itself. Earlier generated "
        "drafts were too short or made claims without complete evidence. The current version addresses that failure mode "
        "by expanding the manuscript only after an executable result file is available, separating benchmark claims from "
        "deployment claims, and carrying the evidence boundary through every major section."
    )


def _result_related_work(context: dict[str, Any]) -> str:
    refs = context.get("literature_hits", []) or []
    if refs:
        titles = "; ".join(_clean_text(item.get("title")) for item in refs[:4] if item.get("title"))
        return (
            "Prior learning-analytics and educational-data-mining work studies early warning, student performance "
            "prediction, and sequence modeling from course traces. The literature records retrieved for this run include: "
            f"{titles}. These records provide topical context, but the generated manuscript still requires a deeper "
            "manual citation audit before submission. The present contribution is therefore methodological at the "
            "workflow level: it demonstrates a path from executable benchmark evidence to claim-bounded writing.\n\n"
            "The retrieved records suggest three recurring concerns that shape this benchmark report. First, predictive "
            "performance alone is insufficient when warning models are used for student support; calibration and "
            "top-ranked precision matter because interventions are capacity-limited. Second, sequence information can "
            "matter when later behavior reflects recent disengagement, but simple aggregate baselines remain important "
            "because they are easier to audit. Third, externally valid educational conclusions depend on institutional "
            "context, course design, and missing-data processes, none of which can be inferred from a generated cohort. "
            "For that reason, this paper treats literature as motivation and boundary-setting rather than as proof that "
            "the synthetic benchmark transfers to classrooms."
        )
    return (
        "The relevant literature spans learning analytics, educational data mining, early warning systems, and temporal "
        "student modeling. This run did not retrieve verified external bibliographic records, so this section avoids "
        "specific citation claims. A submission-ready paper must rerun the workflow with OpenAlex or Semantic Scholar "
        "enabled, inspect retrieved records, and replace this paragraph with verified related work."
    )


def _result_method(context: dict[str, Any]) -> str:
    return (
        "The workflow evaluates a deliberately layered method family under a shared generated benchmark. The feature "
        "encoder first converts each partially observed student sequence into auditable representations. For each quiz "
        "channel, it records the prefix mean, prefix standard deviation, most recent value, and first-to-last trend. "
        "These statistics are computed for score, delay, latent-answer proxy, and missingness channels, producing a "
        "compact representation that can be inspected without a deep sequence model. A second encoder builds a temporal "
        "weighted view in which later quiz events receive larger fixed weights, reflecting the assumption that recent "
        "engagement is more actionable for intervention timing.\n\n"
        "$$\n"
        "a_i = [\\operatorname{mean}_t x_{i,t},\\ \\operatorname{std}_t x_{i,t},\\ x_{i,T},\\ x_{i,T}-x_{i,1}]\n"
        "$$\n\n"
        "The temporal representation uses fixed recency weights over the observed prefix and concatenates a first-to-last "
        "trend term. This gives a compact alternative to a learned recurrent model while still encoding the intervention "
        "assumption that late behavior should matter more than early behavior.\n\n"
        "$$\n"
        "z_i = [\\sum_{t=1}^{T} w_t x_{i,t},\\ x_{i,T}-x_{i,1}],\\quad \\sum_{t=1}^{T} w_t = 1,\\quad w_T > w_1\n"
        "$$\n\n"
        "The model suite separates feature contribution from model capacity. A prior-only classifier estimates the risk "
        "base rate and provides a trivial lower bound. Score-only logistic regression tests whether performance traces "
        "alone are sufficient. Engagement-only logistic regression uses delay and missingness channels to isolate "
        "behavioral signals. Full-feature logistic regression combines all channels while remaining interpretable. "
        "Gradient boosting and random forest use the same full-feature representation but allow nonlinear interactions. "
        "Temporal weighted logistic regression changes the representation while keeping a linear decision rule, so it "
        "tests recency weighting without adding tree-model capacity.\n\n"
        "Training uses stratified train-test splits per random seed. Linear models use class balancing to reduce collapse "
        "toward the majority class, while tree baselines use shallow or regularized configurations so that the generated "
        "benchmark remains a smoke-test-quality empirical scaffold rather than an overfit simulator contest. All models "
        "produce probability scores, enabling ranking, thresholded classification, and calibration-oriented metrics from "
        "the same predictions.\n\n"
        "$$\n"
        "\\hat{p}_i = \\sigma(\\beta_0 + \\beta^\\top \\phi_i),\\quad "
        "\\sigma(u)=\\frac{1}{1+\\exp(-u)}\n"
        "$$\n\n"
        "The execution stage writes a JSON result file with model-level means and standard deviations across random seeds. "
        "The writing stage reads that file and only permits numerical claims that can be traced to it. This design makes "
        "the manuscript more conservative than a normal language-model draft: if no result file exists, the Results "
        "section is suppressed; if a result file exists, claims are bounded to the benchmark described by that file.\n\n"
        "All models share the same target definition and the same train-test split for each seed. The aggregate feature "
        "view is deliberately transparent: it records central tendency, recent performance, variation, missingness, delay, "
        "and short-term trend. The temporal weighted view changes only the representation, assigning larger weights to "
        "later observed quiz events before fitting a linear model. This keeps the comparison focused on whether a simple "
        "recency bias is useful under the generated data process, rather than confounding representation, model capacity, "
        "and optimization procedure."
    )


def _problem_formulation_section(context: dict[str, Any]) -> str:
    seed = context.get("seed", "the target task")
    return (
        f"We formulate {seed} as a supervised early-warning problem over partially observed student traces. "
        "For each student, the input consists of quiz-level observations available before the prediction time: answer "
        "accuracy, recent score summaries, missing quiz indicators, and submission-delay features. The output is a binary "
        "risk label representing whether the student belongs to a high-risk outcome group in the generated cohort.\n\n"
        "$$\n"
        "\\mathcal{D}=\\{(X_i,y_i)\\}_{i=1}^{n},\\quad X_i=[x_{i,1},\\ldots,x_{i,T}],\\quad y_i\\in\\{0,1\\}\n"
        "$$\n\n"
        "The scientific constraint is chronological: features must be computed only from observations that would have "
        "been visible at the time an instructor could intervene. The benchmark therefore avoids using final-course "
        "outcomes or later quiz behavior as predictors. This distinction matters because leakage can make a generated "
        "paper look stronger while producing a model that is unusable in practice. The workflow records this constraint "
        "explicitly so that later real-data experiments can check it against course calendars and platform logs.\n\n"
        "The operational objective is ranking rather than only classification. Instructors usually cannot contact every "
        "student flagged by a model, so the top-risk slice is important. AUC evaluates global ranking; F1 evaluates a "
        "thresholded classifier; Brier score captures calibration; and precision at the top-risk slice measures whether "
        "the highest-priority recommendations are concentrated among true risk cases in the benchmark.\n\n"
        "$$\n"
        "\\operatorname{Brier}=\\frac{1}{m}\\sum_{i=1}^{m}(\\hat{p}_i-y_i)^2,\\quad "
        "P@k=\\frac{1}{k}\\sum_{i\\in \\operatorname{TopK}(\\hat{p},k)} y_i\n"
        "$$"
    )


def _benchmark_section(context: dict[str, Any]) -> str:
    result = context.get("result_evidence", {})
    return (
        f"The current run uses `{result.get('dataset', 'a generated benchmark')}` with "
        f"{result.get('n_seeds', 'multiple')} random seed(s). The cohort generator creates latent student ability and "
        "engagement variables, then maps those latent factors into quiz accuracy, delay, and missingness patterns. This "
        "design gives the models learnable signal while preserving a clear distinction between observable features and "
        "unobserved causes.\n\n"
        "The benchmark is not presented as a substitute for a real educational dataset. Its purpose is to test whether "
        "the pipeline can execute code, preserve result files, and write a manuscript whose claims are no stronger than "
        "the evidence. Because the data-generation process is controlled, the run can be repeated quickly during system "
        "development. Because the data are synthetic, all external-validity claims are deferred until the same pipeline "
        "is rerun on a documented public or institutional dataset.\n\n"
        "Each seed produces a fresh cohort and a held-out evaluation split. The final result JSON aggregates metrics by "
        "model family, storing means and standard deviations. The paper writer reads only this structured file for "
        "numbers, which prevents a language model from inventing additional metrics or silently changing the evaluation "
        "story after execution."
    )


def _implementation_section(context: dict[str, Any]) -> str:
    result = context.get("result_evidence", {})
    path = _result_display_path(result)
    return (
        "The implementation is intentionally lightweight. It uses standard Python scientific tooling to generate the "
        "cohort, train baselines, compute metrics, and serialize a structured JSON summary. The default experiment does "
        "not require a GPU, which makes it suitable as a smoke test for the full AutoScholarLoop path from idea to PDF. "
        f"The parsed evidence file for this run is `{path}`.\n\n"
        "The writing layer applies a conservative contract. Numerical claims are allowed only when the result parser "
        "reports a valid status and finds model-level metrics. If that contract fails, the manuscript falls back to an "
        "intermediate draft that states no performance result. This behavior is important for research automation: a "
        "blank or failed experiment should produce an honest incomplete manuscript, not a polished paper with fabricated "
        "results.\n\n"
        "The PDF is produced from the generated Markdown through the project LaTeX writer. Unicode handling, stale-PDF "
        "removal, and subprocess decoding have been tightened so that a previous successful compilation cannot mask a "
        "new failure. The output therefore reflects the current manuscript rather than an old artifact left in the paper "
        "directory."
    )


def _ablation_section(context: dict[str, Any]) -> str:
    result = context.get("result_evidence", {})
    ablations = result.get("ablations", {}) or {}
    summary = result.get("summary", {}) or {}
    lines = [
        "The ablation study asks which information source and modeling choice is responsible for the benchmark result. "
        "Instead of reporting only the strongest model, the default experiment compares restricted feature views against "
        "the full-feature representation. This makes the generated paper less brittle: if the full model wins only by a "
        "small margin, the manuscript can state that richer features were not clearly necessary; if the restricted views "
        "fall behind, the paper can point to the missing signal source.",
        "",
        "| Ablation contrast | Mean AUC delta | Interpretation |",
        "|---|---:|---|",
    ]
    labels = {
        "score_vs_full_auc_delta": "Full-feature logistic minus score-only logistic",
        "engagement_vs_full_auc_delta": "Full-feature logistic minus engagement-only logistic",
        "temporal_vs_full_auc_delta": "Temporal weighted logistic minus full-feature logistic",
    }
    for key, label in labels.items():
        value = ablations.get(key)
        if isinstance(value, (int, float)):
            interpretation = "positive values favor the first named richer or temporal representation"
            lines.append(f"| {label} | {value:.3f} | {interpretation} |")
    if len(lines) == 4:
        lines.append("| No structured ablation deltas parsed | n/a | rerun the expanded experiment scaffold |")
    lines.extend(
        [
            "",
            "The model summary also functions as a baseline table. "
            f"It contains {len(summary)} model entries, covering trivial, restricted-feature, full-feature, nonlinear, "
            "and temporal variants when the expanded default experiment is used. A submission-oriented version should "
            "add confidence intervals, statistical tests, and feature-group ablations on a real dataset, but the current "
            "generated result is now rich enough to support a multi-paragraph experimental analysis rather than a short "
            "placeholder result."
        ]
    )
    return "\n".join(lines)


def _discussion_section(context: dict[str, Any]) -> str:
    result = context.get("result_evidence", {})
    summary = result.get("summary", {})
    best = result.get("best_model_by_auc", "the best parsed model")
    return (
        f"The parsed benchmark selects {best} by mean AUC, but the differences between models should be interpreted "
        "with caution. The benchmark is generated, the feature process is simplified, and the evaluation does not include "
        "real classroom heterogeneity, missing-data mechanisms, instructor interventions, or fairness slices. The main "
        "engineering result is that AutoScholarLoop can now propagate executed evidence into the manuscript and prevent "
        "unsupported deployment claims.\n\n"
        f"The result table contains {len(summary)} model family entries. This is enough to test claim discipline, but not "
        "enough to establish a robust educational intervention model. A stronger run should add confidence intervals from "
        "more seeds, ablations for each feature group, calibration curves, and a comparison against a real public dataset.\n\n"
        "The result should also be read in terms of model complexity. A nonlinear baseline may improve ranking when the "
        "synthetic generator contains interactions among ability, delay, and missingness. A temporal linear model may "
        "perform well when recent behavior dominates the label. However, neither pattern is a general law about student "
        "risk. The useful conclusion is narrower: the pipeline now produces a complete enough empirical scaffold for a "
        "human researcher to inspect assumptions, substitute real data, and decide which model family deserves deeper "
        "study."
    )


def _diagnostic_section(context: dict[str, Any]) -> str:
    result = context.get("result_evidence", {})
    summary = result.get("summary", {})
    best = result.get("best_model_by_auc", "the best parsed model")
    metric_lines = []
    for model, metrics in summary.items():
        metric_lines.append(
            f"{model} has AUC {_metric_pm(metrics, 'auc')}, F1 {_metric_pm(metrics, 'f1')}, "
            f"Brier {_metric_pm(metrics, 'brier')}, and P@20 {_metric_pm(metrics, 'p_at_20')}."
        )
    metric_text = " ".join(metric_lines) if metric_lines else "No model diagnostics were parsed."
    return (
        f"The diagnostic reading starts from the best-AUC model, {best}, but does not rely on AUC alone. "
        f"{metric_text} Comparing these metrics helps separate ranking quality from calibration and high-priority "
        "selection quality. A model can rank students well while still producing poorly calibrated probabilities; it can "
        "also have acceptable global AUC while failing to concentrate risk cases in the top intervention slice.\n\n"
        "For a real study, the next diagnostics should include seed-by-seed plots, calibration curves, subgroup slices, "
        "and error analysis on false positives and false negatives. The generated benchmark cannot answer whether a "
        "warning is pedagogically useful, but it can expose whether the pipeline is disciplined about evidence. The "
        "current paper therefore treats diagnostics as a checklist for the next empirical iteration rather than as final "
        "deployment validation."
    )


def _threats_section(context: dict[str, Any]) -> str:
    return (
        "Internal validity is limited by the generated data process and by the small number of model families. Construct "
        "validity is limited because the risk label is a synthetic proxy, not an observed educational outcome. External "
        "validity is limited because the benchmark does not represent a school, course, platform, or intervention policy. "
        "Conclusion validity is limited by the default number of random seeds and by the absence of statistical tests. "
        "These threats are explicit so that the generated PDF cannot be mistaken for a finished empirical paper.\n\n"
        "There are also automation-specific threats. Literature records may be incomplete or only topically related; a "
        "citation audit is still required before submission. The generated benchmark may make one baseline look strong "
        "because its assumptions match the simulator. Finally, the manuscript structure is produced automatically, so a "
        "researcher should inspect every section for overclaiming, missing definitions, and mismatches between result "
        "files and prose before treating the PDF as a real paper draft."
    )


def _references_section(context: dict[str, Any]) -> str:
    refs = context.get("literature_hits", []) or []
    entries = []
    for index, item in enumerate(refs, start=1):
        title = _clean_text(item.get("title"))
        if not title or title.lower().startswith("provided or local reference"):
            continue
        authors = _clean_text(item.get("authors")) or "Unknown authors"
        venue = _clean_text(item.get("venue")) or "Unknown venue"
        year = _clean_text(item.get("year")) or "n.d."
        url = _clean_text(item.get("url"))
        doi = _clean_text(item.get("doi"))
        citations = item.get("citations")
        parts = [f"[{index}] {authors}. \"{title}.\" {venue}, {year}."]
        if doi:
            parts.append(f" DOI: {doi}.")
        if isinstance(citations, int) and citations > 0:
            parts.append(f" Cited by: {citations}.")
        if url and not doi:
            parts.append(f" Available: {url}")
        entries.append("".join(parts))
    if entries:
        return "\n".join(entries)
    return (
        "No verified bibliographic records were available in this run. Use `--literature openalex` or "
        "`--literature semanticscholar`, then rerun the pipeline and audit the retrieved entries before submission."
    )


def _result_markdown_table(summary: dict[str, Any]) -> str:
    metric_keys = _summary_metric_keys(summary)
    headers = ["Method"] + [_metric_display_name(key) for key in metric_keys]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---"] + ["---:"] * len(metric_keys)) + "|")
    for model, metrics in summary.items():
        values = [_metric_pm(metrics, key) for key in metric_keys]
        lines.append("| " + " | ".join([str(model)] + values) + " |")
    return "\n".join(lines)


def _summary_metric_keys(summary: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for metrics in summary.values():
        if not isinstance(metrics, dict):
            continue
        for key in metrics:
            if key not in keys and isinstance(metrics.get(key), (dict, int, float)):
                keys.append(key)
    preferred = ["auc", "score", "f1", "brier", "p_at_20", "runtime"]
    ordered = [key for key in preferred if key in keys]
    ordered.extend(key for key in keys if key not in ordered)
    return ordered[:6] or ["score"]


def _metric_display_name(key: str) -> str:
    names = {
        "auc": "AUC",
        "score": "Score",
        "f1": "F1",
        "brier": "Brier",
        "p_at_20": "P@20",
        "runtime": "Runtime",
        "mean_runtime": "Runtime",
    }
    return names.get(key, key.replace("_", " ").title())


def _metric_pm(metrics: dict[str, Any], key: str) -> str:
    raw = metrics.get(key, {}) if isinstance(metrics, dict) else {}
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


def _result_display_path(result: dict[str, Any]) -> str:
    path = _clean_text(result.get("path"))
    if not path:
        return "code/experiments/result.json"
    normalized = path.replace("\\", "/")
    marker = "code/experiments/result.json"
    if marker in normalized:
        return marker
    return normalized.rsplit("/", 1)[-1]
