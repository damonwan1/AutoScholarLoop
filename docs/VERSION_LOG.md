# Version Log

## v0.1.0-architecture-baseline

Date: 2026-04-24

This version establishes the first rewrite baseline for the new repository.

Implemented:

- full AUTO Research stage sequence;
- workspace manifest and artifact ledger;
- deterministic local model provider;
- OpenAI-compatible provider interface;
- Markdown paper draft generation;
- review and revision stages;
- release package stage;
- CLI entrypoint;
- smoke test;
- architecture, roadmap, workflow, and skills integration documents.

Known limitations:

- no real literature API calls yet;
- no real experiment execution backend yet;
- no LaTeX/PDF generation yet;
- no Codex/ClaudeCode skill package files yet;
- no typed schema validation library yet.

Next target:

- `v0.2.0`: real model provider routing, prompt templates, JSON validation and retry.

## v0.1.1 Feature-Surface Parity

Date: 2026-04-24

Added:

- feature parity matrix against AI-Scientist-main style capabilities;
- literature providers for local, Semantic Scholar, and OpenAlex;
- execution backends for dry-run and shell commands;
- LaTeX export and optional PDF compilation;
- PDF text extraction helper;
- review ensemble aggregation;
- batch CLI with optional process-level parallelism;
- CLI flags for idea count, literature backend, execution backend, shell
  commands, review ensemble, and PDF compilation.

Remaining gaps:

- richer multi-round reflection loops;
- real citation/BibTeX insertion loop;
- dedicated Anthropic/Gemini provider adapters;
- Docker/container safety profile;
- packaged Codex/ClaudeCode skills.

## v0.2.0 Nested Research Loop

Date: 2026-04-24

Changed:

- replaced the default linear stage pipeline with a research-group nested loop;
- added S00-S04 workspace layout;
- added `checkpoint_state.md` and append-only `progress_index.md`;
- added round checkpoint files such as `S01_RXX_deliberation.md`,
  `S02_RXX_execution.md`, `S02_RXX_review_memo.md`, and
  `S03_RXX_draft_update.md`;
- added `LoopPolicy` with `fast`, `standard`, and `strict` modes;
- added configurable outer Research Big Loop routing via `--max-big-loops`;
- added quality gate artifacts under `04_quality/`;
- updated README and architecture docs around the small research group model.

Current default:

- `standard`: S01=10, S02=5, S03=5.

Compatibility:

- existing provider, literature, execution, LaTeX, and batch APIs are preserved.

## v0.2.1 Native Capability Contract Alignment

Date: 2026-04-24

Added:

- machine-readable native capability contracts in `core/capability_contracts.py`;
- capability mapping document `docs/CAPABILITY_MAPPING.md`;
- per-stage `capability_contracts.md` outputs in generated workspaces;
- S01 `IDEA_REPORT.md` aligned with `direction_workshop` and `hypothesis_factory`;
- S02 `RESULTS_ANALYSIS.md`, `CLAIMS_FROM_RESULTS.md`, and
  `EXPERIMENT_AUDIT.md` aligned with `evidence_interpreter`;
- S03 `PAPER_PLAN.md`, `figure_plan.md`, `AUTO_REVIEW.md`, and
  `PAPER_IMPROVEMENT_LOG.md` aligned with native writing and review capabilities;
- S04 `CITATION_AUDIT.md`, `CITATION_AUDIT.json`, `compile_report.md`, and
  `overleaf_sync.md` aligned with native release and quality-control capabilities.

Purpose:

- make loop checkpoints enforce explicit capability inputs, outputs, gates, and
  fallbacks instead of generic stage summaries.

## v0.2.2 Format-Aware Writing Group

Date: 2026-04-24

Added:

- native paper format registry in `writing/paper_formats.py`;
- CLI option `--paper-format`;
- support for `acm`, `ieee`, `springer_lncs`, and `chinese_thesis`;
- format-specific `PAPER_PLAN.md`, `figure_plan.md`, `paper/format_profile.json`,
  and `paper/main.tex`;
- compile report now records target format and LaTeX class.

Design note:

- format profiles are project-owned structured specs, not copied template files.

## v0.2.3 Web Research Console

Date: 2026-04-24

Added:

- optional FastAPI Web API under `open_research_agent.web.server`;
- CLI command `autoscholarloop web` for launching the local API;
- Vue single-page console under `web/`;
- first-run model configuration screen for local or OpenAI-compatible providers;
- research brief form with seed, uploaded papers, target venue, loop mode,
  literature backend, execution backend, and manuscript format;
- live S00-S04 stage tracker backed by workspace manifests;
- checkpoint preview for field map, idea report, execution analysis, paper plan,
  claim evidence, final gate, and final draft.

Design note:

- the Web layer does not replace the CLI pipeline; it launches the same
  auditable workspace-producing research loop in a background worker.

## v0.2.4 Bilingual UI And Explicit Run Controls

Date: 2026-04-24

Changed:

- README remains English by default and links to `README_CN.md`;
- added complete Chinese README;
- Web console is English by default with a Chinese toggle;
- stage labels and status labels are translated in both languages;
- input controls now include hover explanations;
- Web run form exposes professor decision rounds, PhD execution rounds,
  writing-review rounds, and global big-loop count;
- Web API forwards custom loop counts to the pipeline policy;
- local deterministic provider is now treated as explicit demo mode;
- real Web runs without a configured model API are rejected unless demo mode is
  intentionally selected;
- Web form exposes PDF compilation as an explicit option.

## v0.2.5 Evidence Gate And Code Artifacts

Date: 2026-04-24

Changed:

- S03 now asks the model provider for manuscript sections instead of always
  using a fixed framework-description template;
- S02 writes a generated `code/` experiment scaffold with method, config,
  result schema, and run script artifacts;
- Web checkpoint preview includes generated code, `paper/main.tex`, and compile
  report;
- Web PDF compilation is enabled by default, while still requiring a local
  LaTeX installation;
- S04 quality gate now rejects claims with `hypothesis`, `provisional`,
  `partial`, `pending`, missing support, or `support: None`;
- unsupported empirical claims route back to S02 instead of being marked as
  `submission_candidate`.

## v0.2.6 Local Execution And LaTeX Compilation

Date: 2026-04-24

Changed:

- S02 writes code before invoking the execution backend;
- shell backend now runs generated experiment code by default when no explicit
  command is provided;
- Web defaults to local shell execution instead of dry-run;
- generated experiment scripts write `code/experiments/result.json`;
- LaTeX compilation now prefers `latexmk`, falls back to `xelatex` or
  `pdflatex`, and performs multi-pass compilation;
- compile reports include engine, pass count, command logs, and PDF path when
  generated.

## v0.2.7 Stage Skill Pack

Date: 2026-04-25

Added:

- repository skill pack for S00-S04 stage support:
  `autoscholar-field-archive`, `autoscholar-direction-review`,
  `autoscholar-experiment-runner`, `autoscholar-manuscript-builder`, and
  `autoscholar-quality-gate`;
- deeper stage skill workflows covering inputs, phase-by-phase procedures,
  outputs, quality gates, failure handling, and anti-overclaiming rules;
- stage skill registry exposed to the automatic pipeline;
- generated `skills_manifest.md` and per-stage `skill_support.md` workspace artifacts;
- smoke test coverage for stage skill registry paths and generated skill artifacts.

Design note:

- The default automatic S00-S04 pipeline remains intact. Skills are stage
  contracts that reinforce the full automatic paper-generation workflow.
