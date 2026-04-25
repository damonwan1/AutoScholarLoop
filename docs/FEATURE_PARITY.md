# AI-Scientist-Main Feature Parity

This project now has feature-surface coverage for the major AI-Scientist-main
capabilities, but several implementations are intentionally adapter-based and
will need stronger backends in later versions.

| Capability | AutoScholarLoop status | Implementation |
| --- | --- | --- |
| User idea / template intake | Supported | `IntakeStage`, workspace inputs |
| Multi idea generation | Supported | `--num-ideas`, `IdeationStage` |
| Idea reflection / critique | Supported at interface level | provider returns `self_critique`; richer rounds planned |
| Novelty checking | Supported | `NoveltyStage` plus `local`, `semanticscholar`, `openalex` providers |
| Literature search | Supported | `adapters/literature.py` |
| Experiment planning | Supported | `PlanningStage` |
| Experiment execution | Supported by backend | `dry-run` and `shell` execution backends |
| Iterative result capture | Supported at artifact level | execution report and manifest ledger |
| Plot/figure handling | Partial | artifact model exists; figure registry planned |
| Paper writing | Supported | Markdown writer and LaTeX exporter |
| Citation insertion | Partial | literature backend exists; BibTeX builder planned |
| LaTeX generation | Supported | `writing/latex_paper.py` |
| PDF compilation | Supported when `pdflatex` exists | `--compile-pdf` |
| PDF text loading for review | Supported | `writing/pdf_text.py` |
| LLM paper review | Supported | `ReviewStage` |
| Review ensemble | Supported | `--review-ensemble` |
| Paper improvement loop | Supported | `RevisionStage` |
| Release packaging | Supported | `ReleaseStage` |
| Multiple model APIs | Partial | OpenAI-compatible adapter; Anthropic/Gemini dedicated adapters planned |
| Parallel evaluation | Supported | `batch --parallel N` creates independent workspaces |
| Containerization | Planned | Docker safety profile not added yet |
| Stage skills | Supported as pipeline contracts | S00-S04 repository skills under `skills/` plus runtime skill manifests |

## Important Interpretation

“Supported” here means the repository has a callable implementation and a stable
extension point. Some parts, such as real autonomous code editing and citation
quality, are not yet as strong as mature systems. They are represented by
backends so later iterations can improve capability without changing the public
workflow contract.
