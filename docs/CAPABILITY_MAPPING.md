# Capability Mapping

This document defines AutoScholarLoop's native capability model. It was
designed after studying common research-agent workflows, but the contracts below
are project-owned and do not depend on external skill names or files.

## Mapping

| Loop Stage | Native Capabilities |
| --- | --- |
| S00 Field Archive | `brief_normalizer`, `field_cartographer`, `recent_work_indexer` |
| S01 Professor Decision | `direction_workshop`, `hypothesis_factory`, `frontier_overlap_probe`, `senior_critique_panel` |
| S02 PhD Execution | `method_freezer`, `implementation_bridge`, `run_orchestrator`, `evidence_interpreter` |
| S03 Writing Review | `paper_architect`, `evidence_writer`, `figure_storyboarder`, `manuscript_review_loop` |
| S04 Quality Gate | `reference_integrity_auditor`, `submission_builder`, `external_package_sync` |

## Format-Aware Writing

The writing group is format-aware through the project-owned format registry:

`src/open_research_agent/writing/paper_formats.py`

Supported targets:

- `acm`
- `ieee`
- `springer_lncs`
- `chinese_thesis`

Each format defines:

- document class target;
- citation style;
- column layout;
- abstract and caption conventions;
- recommended section structure;
- final-output caveats.

## Enforcement Rules

- Each stage checkpoint must include its active native capability contracts.
- Each contract specifies inputs, outputs, quality gates, and fallback routing.
- Stage decisions route through quality gates, not only free-form model text.
- Missing external capability is allowed only if the artifact explicitly marks
  the result as provisional.

## Code Location

The machine-readable contract lives in:

`src/open_research_agent/core/capability_contracts.py`
