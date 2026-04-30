---
name: autoscholar-field-archive
description: Build AutoScholarLoop S00 field archive artifacts from a research seed, uploaded papers, notes, and references. Use when preparing, repairing, or auditing `field_map.md`, `paper_cards.md`, `method_map.md`, `dataset_baseline_map.md`, and `evidence_bank.md` for an AutoScholarLoop workspace.
---

# AutoScholar Field Archive

Use this skill to prepare the S00 evidence base. S00 should make later
automation safer by separating known facts, inferred context, and missing
information before ideas or paper claims are generated.

## Inputs

Read in this order when files exist:

1. `inputs/seed.json`
2. `source_papers/` uploads and user notes
3. `00_field_context/` existing archive artifacts
4. literature provider records already written into artifacts
5. any user-supplied BibTeX, Markdown, PDF text, or plain text references

Do not require every input. If a reference is unreadable, record it in a
missing-context section instead of blocking the whole run.

## Workflow

### Phase 1: Normalize The Research Brief

Extract:

- user research direction;
- target problem or application;
- target venue or manuscript type if present;
- available references;
- constraints such as language, compute, data, deadline, or required format;
- missing information that later stages should not hallucinate.

Convert vague ideas into a neutral problem statement. Do not invent technical
details that are not present in the seed or references.

### Phase 2: Build Paper Cards

For each provided or retrieved reference, create a compact card:

- title;
- authors or source;
- year and venue when known;
- one-sentence contribution;
- method family;
- dataset or evaluation setting;
- relation to the user seed;
- reliability note: user-provided, retrieved, parsed, or incomplete.

Avoid long source quotations. Summaries should be factual and short.

### Phase 3: Map Methods, Data, And Baselines

Create separate maps:

- method families already represented in references;
- datasets, tasks, metrics, and benchmarks mentioned;
- plausible baselines that S02 must check before making empirical claims;
- missing baselines or datasets that require user action.

When uncertain, write `unknown` or `requires S02 scan`.

### Phase 4: Build The Evidence Bank

Every evidence item should have:

- evidence id;
- source path or source record;
- evidence type: seed, paper card, user note, code, dataset, or generated artifact;
- what it can support;
- what it cannot support.

The evidence bank should make it clear that S00 does not yet support
performance claims.

### Phase 5: Handoff To S01

Write a short handoff note for the professor decision stage:

- strongest problem anchor;
- most relevant existing work;
- highest-risk missing context;
- constraints that candidate ideas must satisfy.

## Outputs

Required:

- `00_field_context/field_map.md`
- `00_field_context/paper_cards.md`
- `00_field_context/method_map.md`
- `00_field_context/dataset_baseline_map.md`
- `00_field_context/evidence_bank.md`

Recommended sections for `field_map.md`:

```markdown
# Field Map

## User Direction
## Normalized Problem
## Available Context
## Method Families
## Datasets And Metrics
## Closest Known Work
## Missing Context
## Handoff To S01
```

Recommended evidence item format:

```markdown
## E001: [short name]
- Source:
- Type:
- Supports:
- Does not support:
- Reliability:
```

## Quality Gate

S00 is acceptable when:

- the user seed is preserved;
- references are summarized without unsupported novelty claims;
- missing datasets, baselines, and citations are explicit;
- later stages can identify what evidence exists and what is still unknown.

Route back to S00 repair when:

- uploaded files were ignored;
- the field map contains invented papers, datasets, or metrics;
- evidence items lack source paths or source records.

## Rules

- Do not claim novelty in S00.
- Do not make performance claims in S00.
- Separate user-provided facts from model inference.
- Preserve traceability from every evidence item to an input or retrieved record.
- Prefer concise maps over long literature-review prose.
