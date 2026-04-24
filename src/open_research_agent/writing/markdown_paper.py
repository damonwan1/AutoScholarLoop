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
    if manuscript:
        return _build_from_manuscript(manuscript, context, claims, limitations, paper_format)

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
    return "\n".join(lines)


def _build_from_manuscript(
    manuscript: dict[str, Any],
    context: dict[str, Any],
    claims: list[dict[str, Any]],
    limitations: list[str],
    paper_format: str,
) -> str:
    title = manuscript.get("title") or "AUTO Research Draft"
    lines = [
        f"# {title}",
        "",
        f"Format target: {paper_format}",
        "",
        "## Abstract",
        "",
        manuscript.get("abstract", ""),
        "",
        "## Introduction",
        "",
        manuscript.get("introduction", ""),
        "",
        "## Related Work",
        "",
        manuscript.get("related_work", ""),
        "",
        "## Method",
        "",
        manuscript.get("method", ""),
        "",
        "## Experiments",
        "",
        manuscript.get("experiments", ""),
        "",
        "## Results",
        "",
        manuscript.get("results", ""),
        "",
        "## Claim-Evidence Status",
        "",
    ]
    if claims:
        for claim in claims:
            lines.append(f"- Claim: {claim.get('claim')}")
            lines.append(f"  Support: {claim.get('support')}")
            lines.append(f"  Status: {claim.get('status')}")
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
            manuscript.get("conclusion", ""),
            "",
            "## Reproducibility Note",
            "",
            "All generated code, checkpoints, LaTeX files, and quality reports are stored in the run workspace.",
        ]
    )
    return "\n".join(lines)
