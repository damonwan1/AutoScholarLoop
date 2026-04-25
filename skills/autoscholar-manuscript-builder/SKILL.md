---
name: autoscholar-manuscript-builder
description: Build AutoScholarLoop S03 manuscripts from evidence, execution reports, and claim tables. Use when drafting, repairing, or auditing `PAPER_PLAN.md`, `claim_evidence_table.md`, `figure_plan.md`, Markdown drafts, or LaTeX manuscripts in an AutoScholarLoop workspace.
---

# AutoScholar Manuscript Builder

Use this skill to turn verified workspace evidence into a manuscript. S03 should
write from evidence, not aspiration. It can produce a full draft, but every
claim should either be supported, narrowed, or labeled as a limitation.

## Inputs

Read in this order:

1. `01_decision/chosen_direction.md`
2. `01_decision/executor_brief.md`
3. `02_execution/RESULTS_ANALYSIS.md`
4. `02_execution/CLAIMS_FROM_RESULTS.md`
5. `02_execution/EXPERIMENT_AUDIT.md`
6. `00_field_context/paper_cards.md`
7. `paper/format_profile.json` or selected paper format

If S02 only produced scaffold or smoke evidence, write a design/system paper
draft or mark empirical claims as future work. Do not invent benchmark results.

## Workflow

### Phase 1: Build The Claim-Evidence Map

Before prose, create a table:

```markdown
| Claim ID | Claim | Evidence | Evidence Level | Status | Where Used |
|---|---|---|---|---|---|
```

Evidence levels:

- `real_result`
- `smoke_result`
- `design_artifact`
- `literature_context`
- `hypothesis`
- `missing`

Only `real_result` can support performance or benchmark claims. `design_artifact`
can support architecture, workflow, or auditability claims.

### Phase 2: Decide The Paper Story

Choose one dominant narrative:

- method paper: new algorithm or system component;
- system paper: workflow, architecture, and audit trail;
- empirical paper: real benchmark result;
- position/demo paper: early-stage tool with limitations.

The chosen story must match available evidence. If real experiments are absent,
do not structure the paper as a benchmark paper.

### Phase 3: Write The Paper Plan

`PAPER_PLAN.md` should include:

- target format;
- title candidates;
- one-paragraph thesis;
- section outline;
- claim-evidence mapping;
- figure/table plan;
- limitations and missing evidence;
- required S02 follow-ups before submission.

### Phase 4: Draft Sections

Draft each section with evidence constraints:

- Abstract: state only supported contributions.
- Introduction: motivate the problem and summarize the narrow contribution.
- Related Work: use paper cards and avoid unverifiable citation claims.
- Method/System: describe what was actually implemented or designed.
- Experiments: report real results if present; otherwise describe scaffold and
  required future evaluation.
- Results: do not fabricate numbers.
- Limitations: explicitly list missing baselines, datasets, citations, or user
  studies.
- Conclusion: restate supported claims only.

### Phase 5: Format-Aware Output

Respect the selected `paper_format`:

- `ieee`: concise two-column style, numeric citations, compact related work.
- `acm`: clear contribution bullets, artifact/system framing when applicable.
- `springer_lncs`: single-column proceedings structure.
- `chinese_thesis`: chapter-style organization and thesis-level exposition.

Generated LaTeX is a draft. Venue templates still need human verification.

### Phase 6: Review And Revise

Use reviewer-style checks:

- Is the main claim actually supported?
- Are there unsupported words such as "outperforms", "significantly", "novel",
  or "state-of-the-art" without evidence?
- Does each figure/table have a data source?
- Are limitations visible enough?
- Can S04 audit the draft without guessing?

## Outputs

Required:

- `03_writing/PAPER_PLAN.md`
- `03_writing/claim_evidence_table.md`
- `03_writing/figure_plan.md`
- `paper/draft.md`
- `paper/main.tex`

Recommended:

- `03_writing/AUTO_REVIEW.md`
- `03_writing/PAPER_IMPROVEMENT_LOG.md`
- `03_writing/review_log.md`

Recommended `claim_evidence_table.md` entry:

```markdown
## C1: [claim]
- Evidence:
- Evidence level:
- Status: supported | partial | unsupported | hypothesis
- Used in sections:
- Required fix:
```

## Quality Gate

S03 is acceptable when:

- every major claim appears in the claim-evidence table;
- unsupported claims are downgraded or moved to limitations;
- paper plan matches the target format;
- figure/table plans name data sources;
- the draft can be audited by S04 without hidden assumptions.

Route back to S02 when the paper needs empirical support that does not exist.
Route back to S01 when the selected direction cannot support a coherent paper.

## Rules

- Evidence first, prose second.
- Do not fabricate results, citations, or implementation details.
- Do not use generated experiment scaffolds as empirical evidence.
- Write limitations as part of the paper, not as private notes.
- Keep contribution claims narrow enough to survive S04.
