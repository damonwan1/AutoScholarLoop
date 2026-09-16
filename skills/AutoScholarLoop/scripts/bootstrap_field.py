import argparse
from pathlib import Path


FILES = {
    "00_field_context/field_map.md": """# Field Map

## Metadata
- Domain: {domain}
- Field: {field_name}
- Paper source: {paper_dir}

## Scope

## Recent paper list

## Method clusters

## Open gaps
""",
    "00_field_context/S00_R01_field_map.md": """# S00 R01 Field Map Checkpoint

## Stage
- Stage: S00
- Round: R01
- Artifact: field_map

## Metadata
- Domain: {domain}
- Field: {field_name}
- Paper source: {paper_dir}

## Notes
""",
    "00_field_context/checkpoint_state.md": """# Checkpoint State

## Current
- Stage: S00
- Round: R01
- Last completed artifact: 00_field_context/S00_R01_field_map.md
- Next required artifact: 01_decision/S01_R01_deliberation.md

## Resume
- Resume command: continue from `Next required artifact` and append to `progress_index.md` after completion.
""",
    "00_field_context/progress_index.md": """# Progress Index

| Timestamp | Stage | Round | Artifact Path | Note |
|---|---|---|---|---|
| bootstrap | S00 | R01 | 00_field_context/S00_R01_field_map.md | initial scaffold |
""",
    "01_decision/deliberation_log.md": """# Deliberation Log

## Rules
- Minimum decision-maker agents: 3
- Minimum deliberation rounds before final idea pool: 10

## Round 01

## Round 02

## Round 03

## Round 04

## Round 05

## Round 06

## Round 07

## Round 08

## Round 09

## Round 10
""",
    "01_decision/S01_R01_deliberation.md": """# S01 R01 Deliberation Checkpoint

## Stage
- Stage: S01
- Round: R01
- Artifact: deliberation

## Discussion
""",
    "01_decision/idea_pool.md": """# Idea Pool

Only finalize this file after the 10-round minimum deliberation is complete.
""",
    "01_decision/S01_R10_idea_pool.md": """# S01 R10 Idea Pool Checkpoint

## Stage
- Stage: S01
- Round: R10
- Artifact: idea_pool

## Candidate ideas
""",
    "01_decision/chosen_direction.md": """# Chosen Direction

## Current status
- Status: not_selected

## Rationale
""",
    "01_decision/executor_brief.md": """# Executor Brief

## Selected idea

## Why this idea won

## Non-goals

## First execution tasks

## Required ablations

## Risks to watch
""",
    "01_decision/S01_R11_executor_brief.md": """# S01 R11 Executor Brief Checkpoint

## Stage
- Stage: S01
- Round: R11
- Artifact: executor_brief

## Handoff
""",
    "02_execution/baseline_scan.md": """# Baseline Scan

## Candidate repos

## Chosen baseline

## Risks
""",
    "02_execution/S02_R01_execution.md": """# S02 R01 Execution Checkpoint

## Stage
- Stage: S02
- Round: R01
- Artifact: execution

## Update
""",
    "02_execution/review_memo_01.md": """# Review Memo 01

## Professor assessment

## Main concerns

## Required next changes

## Kill / continue decision
""",
    "02_execution/S02_R01_review_memo.md": """# S02 R01 Review Memo Checkpoint

## Stage
- Stage: S02
- Round: R01
- Artifact: review_memo

## Feedback
""",
    "03_writing/paper_outline.md": """# Paper Outline

## Hook

## Main claim

## Evidence needed
""",
    "03_writing/review_log.md": """# Writing Review Log

## Round 01

## Round 02

## Round 03
""",
    "03_writing/S03_R01_draft_update.md": """# S03 R01 Draft Update Checkpoint

## Stage
- Stage: S03
- Round: R01
- Artifact: draft_update

## Changes
""",
    "03_writing/draft.md": """# Draft
""",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--field-dir", required=True)
    parser.add_argument("--paper-dir", required=True)
    parser.add_argument("--field-name", required=True)
    parser.add_argument("--domain", required=True)
    args = parser.parse_args()

    field_dir = Path(args.field_dir)
    field_dir.mkdir(parents=True, exist_ok=True)
    (field_dir / "source_papers").mkdir(exist_ok=True)

    manifest = field_dir / "source_papers" / "README.md"
    if not manifest.exists():
        manifest.write_text(
            f"# Source Papers\n\nUse papers from:\n`{args.paper_dir}`\n",
            encoding="utf-8",
        )

    for rel_path, template in FILES.items():
        path = field_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                template.format(
                    domain=args.domain,
                    field_name=args.field_name,
                    paper_dir=args.paper_dir,
                ),
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
