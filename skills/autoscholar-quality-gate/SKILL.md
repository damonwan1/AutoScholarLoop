---
name: autoscholar-quality-gate
description: Audit AutoScholarLoop S04 release readiness. Use when checking novelty, citations, reproducibility, claim support, compile status, and final release packaging for an AutoScholarLoop workspace.
---

# AutoScholar Quality Gate

Use this skill to decide whether a run can be released as a submission
candidate, routed back for revision, pivoted, or killed. S04 is a gate, not a
writing stage: it should protect the user from unsupported paper claims.

## Inputs

Read in this order:

1. `paper/final_draft.md` or `paper/draft.md`
2. `03_writing/claim_evidence_table.md`
3. `02_execution/CLAIMS_FROM_RESULTS.md`
4. `02_execution/EXPERIMENT_AUDIT.md`
5. `04_quality/CITATION_AUDIT.json` if present
6. `paper/main.tex`
7. `04_quality/compile_report.md`
8. `manifest.json`

If an input is missing, record the missing artifact and downgrade release
readiness.

## Workflow

### Phase 1: Claim Audit

For every claim in the draft:

- identify the exact sentence or section;
- link it to claim-evidence table entry;
- classify support: supported, partial, unsupported, hypothesis;
- identify missing evidence;
- decide: keep, weaken, move to limitations, or remove.

High-risk phrases that require evidence:

- "outperforms";
- "significantly improves";
- "state-of-the-art";
- "novel";
- "first";
- "robust";
- "generalizes";
- "reduces hallucination";
- "improves reliability".

### Phase 2: Citation Audit

Check:

- references cited in the draft exist in the workspace or bibliography;
- cited papers are not used to support unrelated claims;
- local placeholder references are labeled provisional;
- missing BibTeX or citation metadata is listed as a fix.

Do not invent citations. If no real bibliography exists, mark citation status as
`needs_real_bibtex_loop`.

### Phase 3: Reproducibility Audit

Check:

- code files exist;
- commands are recorded;
- configs are saved;
- result files are present when empirical claims exist;
- random seeds or deterministic settings are documented when relevant;
- environment assumptions are written down.

If only dry-run or smoke-run artifacts exist, empirical performance claims must
fail or be downgraded.

### Phase 4: Format And Compile Audit

Check:

- `paper/main.tex` exists;
- selected paper format is recorded;
- compile report exists;
- PDF status is explicit: compiled, failed, or skipped;
- missing class files or LaTeX engines are listed without blocking Markdown
  release unless PDF is required.

### Phase 5: Decide Route

Use these decisions:

- `submission_candidate`: claims, citations, and reproducibility are acceptable
  for a draft package.
- `return_to_writing`: prose overclaims available evidence or structure is weak.
- `return_to_execution`: empirical claims need real result files or baselines.
- `return_to_decision`: selected idea cannot support a coherent paper.
- `kill`: severe integrity problem or no viable route.

Route to the earliest stage that can fix the root cause.

## Outputs

Required:

- `04_quality/novelty_audit.md`
- `04_quality/citation_audit.md`
- `04_quality/reproducibility_audit.md`
- `04_quality/claim_audit.md`
- `04_quality/final_gate.md`
- `04_quality/CITATION_AUDIT.md`
- `04_quality/CITATION_AUDIT.json`
- `04_quality/compile_report.md`
- `release/README.md`

Recommended `final_gate.md` structure:

```markdown
# Final Gate

- decision:
- return_to:
- unsupported_claims:
- citation_status:
- reproducibility_status:
- compile_status:

## Required Fixes
## Release Notes
```

## Quality Gate Criteria

Accept as `submission_candidate` only when:

- no unsupported major claim remains;
- citation status is pass or clearly provisional for a non-submission demo;
- reproducibility artifacts match the claims being made;
- final draft and LaTeX exist;
- release notes disclose AI assistance and remaining limitations.

Otherwise route back with concrete required fixes.

## Rules

- A smoke test does not support benchmark or performance claims.
- Missing evidence should route back to S02 or downgrade the claim.
- A draft can be released as an audit package even when PDF compilation fails,
  if the compile failure is documented.
- Do not silently pass unsupported claims because the prose sounds plausible.
- The release package must state remaining limitations clearly.
