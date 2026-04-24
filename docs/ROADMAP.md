# Roadmap

## Version Policy

Versions describe capability milestones, not only packaging releases.

## v0.1.0 Architecture Baseline

Purpose: establish the project contract and runnable full-loop skeleton.

Deliverables:

- repository docs;
- stage graph;
- local deterministic provider;
- workspace manifest and artifacts;
- Markdown paper draft;
- smoke-testable CLI.

Exit criteria:

- a user can run the CLI with a research seed;
- the run folder contains artifacts for all core stages;
- the final draft is generated from stage outputs.

## v0.2.0 Real Model Providers

Add:

- OpenAI-compatible chat provider;
- Anthropic provider;
- Gemini provider;
- per-stage model routing;
- JSON repair and validation.

Exit criteria:

- the same pipeline can run with at least one external model API;
- prompts and schemas are separated from Python control logic.

## v0.3.0 Literature And Novelty Engine

Add:

- Semantic Scholar adapter;
- OpenAlex adapter;
- arXiv adapter;
- local PDF metadata loader;
- novelty score with closest-work table.

Exit criteria:

- each candidate idea has named closest papers and a novelty decision.

## v0.4.0 Execution Backends

Add:

- sandboxed shell execution;
- baseline project contract;
- experiment queue;
- result parser;
- retry and failure diagnosis.

Exit criteria:

- a research workspace can run configured commands and feed results back into
  the planning loop.

## v0.5.0 Paper Production

Add:

- LaTeX writer;
- BibTeX builder;
- figure/table registry;
- citation audit;
- compile/fix loop.

Exit criteria:

- the system can produce a paper PDF with checked citations and figure links.

## v0.6.0 Reviewer And Revision Loop

Add:

- multi-reviewer ensemble;
- area-chair meta-review;
- issue tracking from review comments;
- revision history and response memo.

Exit criteria:

- review findings create actionable revision tasks and measurable draft changes.

## v0.7.0 Skills Pack

Add:

- Codex skill;
- ClaudeCode instruction pack;
- stage-specific task templates;
- skill-driven execution backend.

Exit criteria:

- an external coding agent can run a stage using the same workspace contract.

## v1.0.0 Open Research Automation

Add:

- configurable multi-agent committees;
- resumable long-running jobs;
- Docker/container safety profile;
- example research templates;
- public docs and contribution guide.

Exit criteria:

- third-party users can add providers, literature engines, templates, and skills
  without changing core pipeline code.
