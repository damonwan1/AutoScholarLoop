# AutoScholarLoop

[English](README.md) | [中文](README_CN.md)

**AutoScholarLoop** is an open-source AUTO Research framework for building
auditable, multi-agent research loops. It helps users turn an initial research
direction, recent papers, reference notes, and optional code into a staged
research process that can generate ideas, run execution loops, draft papers,
review claims, and package submission candidates.

The project is developed for research automation scenarios at AI Group, CAS CNIC
(Computer Network Information Center, Chinese Academy of Sciences).


AI Group
![图片1](./img/img1.png)


## Description

AutoScholarLoop simulates a small research group rather than a single chatbot.
The system separates research work into role-based stages:

1. `S00` Field Archive Group builds the field map, paper cards, method map,
   dataset/baseline map, and evidence bank.
2. `S01` Professor Decision Group runs multi-round idea generation, critique,
   novelty probing, ranking, and direction selection.
3. `S02` PhD Execution Group plans baselines, implementation, experiments,
   failure analysis, and professor review memos.
4. `S03` Writing Group turns evidence into a manuscript plan, claim-evidence
   table, draft, figures, and review-driven revisions.
5. `S04` Quality Control Group audits novelty, citations, reproducibility,
   unsupported claims, and final release readiness.

The core design is a nested loop:

```text
S00 evidence preparation
  -> S01 professor decision loop
  -> S02 execution-review loop
  -> S03 writing-review loop
  -> S04 quality gate
  -> submission_candidate / revise / pivot / kill
```

Every stage writes Markdown checkpoints and structured artifacts so users can
inspect how an idea was created, why it was selected, what evidence supports
the paper, and where quality gates passed or failed.

## Features

- Multi-stage AUTO Research loop with explicit checkpoints.
- Deterministic local provider for offline demos and tests. It is not a real
  model-backed research run.
- OpenAI-compatible provider adapter for real model APIs.
- Local, Semantic Scholar, and OpenAlex literature adapters.
- Dry-run and local shell execution backends. The Web console defaults to local
  shell execution: model-generated code is written under `code/` and then run
  on the current machine.
- Format-aware paper writing for `acm`, `ieee`, `springer_lncs`, and
  `chinese_thesis`.
- Markdown and LaTeX manuscript export.
- Optional PDF compilation if `--compile-pdf` is enabled and a LaTeX toolchain
  plus required venue class files are installed.
- Vue Web console for first-run model configuration, paper upload, live loop
  progress, and checkpoint preview.
- CLI and Web API use the same underlying research pipeline.
![图片2](./img/img2.png)

## Installation

```powershell
cd AutoScholarLoop
pip install -e ".[api,web,dev]"
```

For the Web frontend:

```powershell
cd web
npm install
```

The frontend currently uses Vite 2 for compatibility with older Node
environments. Node 18+ is recommended for future frontend upgrades.

## CLI Quick Start

```powershell
autoscholarloop run `
  --seed "I want to study retrieval-augmented agents for scientific writing." `
  --loop-mode fast `
  --paper-format ieee `
  --workspace runs/demo
```

Useful options:

```powershell
autoscholarloop run `
  --seed "your research idea" `
  --reference "paper title, URL, local path, or note" `
  --num-ideas 5 `
  --loop-mode standard `
  --paper-format acm `
  --literature semanticscholar `
  --execution-backend dry-run `
  --review-ensemble 5 `
  --compile-pdf `
  --workspace runs/demo
```

The legacy command alias `new-ai-scientist` is kept for compatibility.

By default, `local` provider mode is a deterministic demo. For real research
runs, configure an OpenAI-compatible model provider and API key. The system
always writes `paper/main.tex`; PDF generation is attempted only when explicitly
enabled and when the local LaTeX environment supports the selected format.
The compiler prefers `latexmk`, then falls back to `xelatex` or `pdflatex`
with multi-pass compilation.

If your network environment injects a system proxy that breaks `httpx`
connections, set:

```powershell
$env:AUTOSCHOLARLOOP_HTTP_TRUST_ENV='0'
```

Example for DeepSeek-compatible APIs:

```powershell
$env:OPENAI_API_KEY='your_api_key'
$env:AUTOSCHOLARLOOP_HTTP_TRUST_ENV='0'
autoscholarloop run `
  --seed "your research idea" `
  --provider openai-compatible `
  --model deepseek-chat `
  --base-url https://api.deepseek.com/v1 `
  --workspace runs/deepseek_demo
```

## Web Console

Start the Python API:

```powershell
autoscholarloop web --host 127.0.0.1 --port 8000
```

Start the Vue frontend:

```powershell
cd web
npm run dev
```

The Web console supports:

- first-run large model API configuration;
- DeepSeek preset for `deepseek-chat` and `https://api.deepseek.com/v1`;
- optional system proxy bypass for environments where `httpx` fails through
  inherited proxy settings;
- research direction and target venue input;
- PDF, Markdown, text, and BibTeX upload;
- loop mode and backend selection;
- manuscript format selection;
- live S00-S04 progress visualization;
- checkpoint preview for field maps, ideas, execution reports, paper plans,
  claim evidence, final gate, and final draft.

## Generated Workspace

Each run creates an auditable workspace:

```text
run/
  source_papers/
  inputs/
  artifacts/
  logs/
  code/
  00_field_context/
  01_decision/
  02_execution/
  03_writing/
  04_quality/
  paper/
  release/
```

Important outputs include:

- `code/experiments/run_experiment.py`
- `code/methods/proposed_method.py`
- `code/experiments/result.json`
- `00_field_context/field_map.md`
- `00_field_context/paper_cards.md`
- `01_decision/IDEA_REPORT.md`
- `01_decision/chosen_direction.md`
- `02_execution/RESULTS_ANALYSIS.md`
- `02_execution/CLAIMS_FROM_RESULTS.md`
- `02_execution/EXPERIMENT_AUDIT.md`
- `03_writing/PAPER_PLAN.md`
- `03_writing/claim_evidence_table.md`
- `04_quality/CITATION_AUDIT.md`
- `04_quality/final_gate.md`
- `04_quality/compile_report.md`
- `paper/final_draft.md`
- `paper/main.tex`
- `paper/main.pdf` if local LaTeX compilation succeeds
- `release/README.md`

## Paper Formats

Supported manuscript targets:

- `acm`: ACM-style conference or journal article draft.
- `ieee`: IEEE conference or journal article draft.
- `springer_lncs`: Springer LNCS proceedings-style draft.
- `chinese_thesis`: generic Chinese thesis-style manuscript.

Official venue class files and bibliography rules still need to be checked
before real submission. The generated manuscript is a research draft and audit
package, not a guarantee of venue compliance.

## Repository Layout

```text
docs/                         Design, roadmap, workflow, and version notes
src/open_research_agent/       Python research loop package
web/                          Vue Web console
configs/                       Example pipeline configs
templates/                     Research workspace templates
examples/                      Example inputs
tests/                         Smoke tests
```

## Development

Run tests:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests -q
```

Build the Web frontend:

```powershell
cd web
npm run build
```

## Project Status

AutoScholarLoop currently provides a runnable research-loop scaffold with
auditable outputs. It is designed for iterative extension. It does not yet
guarantee true scientific novelty, correct citations, valid experiments, or
submission-ready papers without human supervision.

Use it as a research automation assistant, not as a replacement for scientific
judgment, domain expertise, peer review, or responsible authorship.

## Acknowledgements

AutoScholarLoop is inspired by and learns from several open research automation
and paper-writing projects, including:

- `AI-Scientist-main`, for demonstrating an end-to-end AI scientist workflow.
- `academic-paper-writer-main`, for paper format and manuscript-generation
  workflow ideas.
- Codex and ClaudeCode style coding-agent workflows, for skill-oriented
  automation patterns.
- Open literature infrastructure such as Semantic Scholar and OpenAlex, for
  retrieval and bibliography-oriented research workflows.

This repository is an independent implementation. Architecture, code, stage
contracts, and Web UI are written for AutoScholarLoop.

## Organization

Developed for:

**CAS CNIC**  
Computer Network Information Center, Chinese Academy of Sciences  


## License & Responsible Use

This project is licensed under **The AI Scientist Source Code License**,
a derivative of the Responsible AI License.

**Mandatory Disclosure:** By using this code, you are legally bound to clearly
and prominently disclose the use of AI in any resulting scientific manuscripts
or papers.

We recommend the following attribution in your paper's Abstract or Methods
section:

> "This manuscript was autonomously generated using AutoScholarLoop, an
> AI-assisted research-loop system inspired by The AI Scientist."

Users are responsible for verifying all claims, citations, experiments,
authorship requirements, venue policies, and disclosure obligations before
submitting any generated manuscript.
