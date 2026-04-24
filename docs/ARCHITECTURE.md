# Architecture

## Goal

Build a full AUTO Research system that behaves like a small research group and
can accept:

- a short research idea;
- notes or hypothesis sketches;
- local reference papers or bibliographic metadata;
- optional baseline code.

The system expands the input into research directions, checks novelty, plans and
executes exploration, writes a paper, reviews it, improves it, and leaves a
complete audit trail. The core control model is a nested loop:

```text
non-loop preparation -> local loops -> research big loop -> quality gate routing
```

## High-Level Pipeline

```text
Research Seed
  -> S00 Field Archive
  -> S01 Professor Decision Loop
  -> S02 PhD Execution-Review Loop
  -> S03 Writing-Review Loop
  -> S04 Quality Control Gate
  -> Release Package or Route Back
```

## Main Difference From Existing AI-Scientist-Style Repos

This project does not center the codebase around one monolithic launcher and a
fixed template folder contract. Instead it uses:

- `Stage` objects with explicit input/output artifact schemas;
- a `ResearchWorkspace` that persists state independent of execution backend;
- provider adapters for model APIs;
- execution adapters for shell, notebook, remote GPU, or human-in-the-loop runs;
- writing adapters for Markdown, LaTeX, Docx, or Overleaf later;
- skill manifests so Codex and ClaudeCode can perform stage-specific actions.

The workflow remains complete, but the architecture is composable.

## Core Concepts

### ResearchWorkspace

A run directory containing:

```text
manifest.json
inputs/
artifacts/
logs/
paper/
reviews/
release/
```

Every stage writes timestamped artifacts and updates the manifest.

### Stage Graph

Each stage implements:

- `name`
- `run(context) -> StageResult`
- declared dependencies
- artifact outputs

The default graph is linear for v0.1, but the model supports branching and
iteration.

### Provider Adapter

LLM calls go through `ModelProvider`. The initial implementation includes:

- `LocalHeuristicProvider`: offline deterministic responses for smoke tests;
- `OpenAICompatibleProvider`: configurable base URL for OpenAI, DeepSeek,
  OpenRouter, and compatible gateways.

Anthropic, Gemini, Bedrock, and Vertex can be added without changing stages.

### Literature Adapter

Novelty and citation stages depend on `LiteratureProvider`.

Planned adapters:

- Semantic Scholar;
- OpenAlex;
- arXiv;
- local PDF/metadata index;
- web search connector.

### Execution Adapter

Exploration is not hard-coded to one experiment script. It is abstracted as
`ExecutionBackend`.

Planned modes:

- `dry_run`: turns a plan into auditable pseudo-results;
- `shell`: runs configured commands in a sandboxed workspace;
- `codex_skill`: emits tasks for a coding agent;
- `remote_gpu`: dispatches jobs to GPU providers.

### Paper Builder

The writing stage first creates a claim/evidence map, then drafts sections.
This prevents the system from claiming results that were not produced.

## Research Group Stages

### S00 Field Archive Group

Mostly non-loop. It builds:

- `field_map.md`
- `paper_cards.md`
- `method_map.md`
- `dataset_baseline_map.md`
- `evidence_bank.md`
- `capability_contracts.md`

It only loops for data repair when materials are missing, scattered, or unreadable.
Its native capabilities are `brief_normalizer`, `field_cartographer`, and
`recent_work_indexer`.

### S01 Professor Decision Group

Mandatory local loop. It creates, attacks, refines, checks, and selects ideas.

Default rounds:

- fast: 3
- standard: 10
- strict: 12

Outputs include `deliberation_log.md`, `idea_pool.md`, `chosen_direction.md`, and
`executor_brief.md`. It also writes `IDEA_REPORT.md` through
`direction_workshop`, `hypothesis_factory`, `frontier_overlap_probe`, and
`senior_critique_panel`.

### S02 PhD Execution Group

Strongest loop. It scans baselines, reproduces, implements, runs experiments,
analyzes failures, and receives professor review memos.

Each round writes:

- `S02_RXX_execution.md`
- `S02_RXX_review_memo.md`

It also writes `RESULTS_ANALYSIS.md`, `CLAIMS_FROM_RESULTS.md`, and
`EXPERIMENT_AUDIT.md` through `method_freezer`, `implementation_bridge`,
`run_orchestrator`, and `evidence_interpreter`.

### S03 Writing Group

Medium loop. It writes from evidence, not from aspiration. The required audit
artifact is `claim_evidence_table.md`.

It also writes `PAPER_PLAN.md`, `figure_plan.md`, `AUTO_REVIEW.md`, and
`PAPER_IMPROVEMENT_LOG.md` through `paper_architect`, `evidence_writer`,
`figure_storyboarder`, and `manuscript_review_loop`.

### S04 Quality Control Group

Gate, not a long loop. It checks:

- novelty;
- citation integrity;
- reproducibility;
- claim-evidence alignment;
- final gate decision.

It can route the project back to S01, S02, or S03.
It writes `CITATION_AUDIT.md`, `CITATION_AUDIT.json`, `compile_report.md`, and
`overleaf_sync.md` through `reference_integrity_auditor`,
`submission_builder`, and `external_package_sync`.

## Agent Roles

The default graph maps stages to role prompts:

- `field_archive_group`: builds evidence context;
- `professor_decision_group`: creates and kills ideas;
- `frontier_scout`: checks overlap with newest work;
- `phd_execution_group`: handles baseline, code, experiments, and failure reports;
- `writing_review_group`: drafts and critiques evidence-grounded writing;
- `quality_control_group`: audits novelty, citations, reproducibility, and claims.

## State Machine

```text
initialized
field_mapped
ideas_ready
direction_selected
execution_started
execution_under_review
writing_ready
draft_under_review
quality_audit
submission_candidate
pivot_required
killed
```

Stage decisions use:

```text
continue
revise
add_evidence
pivot
kill
promote
submit_candidate
```

## Safety And Originality

- The system must not copy text from input papers.
- Literature summaries are evidence, not generated paper text.
- Every final claim must cite an artifact, a reference, or be marked hypothesis.
- Code execution is opt-in and routed through an execution backend.
- Model output is parsed into project-owned schemas before use.

## v0.1 Scope

Implemented now:

- nested research-group loop;
- local provider;
- workspace artifact persistence;
- markdown checkpoint and progress index;
- complete offline pipeline;
- Markdown paper output;
- design docs and version roadmap.

Deferred:

- real literature API calls;
- real shell/GPU experiment runner;
- LaTeX compilation;
- PDF ingestion;
- external coding-agent skill execution.
