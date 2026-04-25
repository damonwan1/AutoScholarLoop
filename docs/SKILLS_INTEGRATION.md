# Skill Integration

AutoScholarLoop remains an automatic S00-S04 research pipeline. Skills are
stage contracts and optional agent-facing guides that help external coding or
review agents work on the same workspace format. They do not replace the default
end-to-end run.

## Default Automation

The main automatic flow is unchanged:

| Backend | Automatic | Role |
| --- | --- | --- |
| `dry-run` | yes | Safe offline demo that records traceable pseudo-execution. |
| `shell` | yes | Writes generated code and runs commands inside the run workspace. |

Use `shell` for the automatic code-generation and paper-writing path:

```powershell
python -m open_research_agent.cli run `
  --seed "your research idea" `
  --loop-mode fast `
  --execution-backend shell `
  --workspace runs/auto_demo
```

## Stage Skill Pack

The repository includes stage skills aligned to the automatic pipeline:

| Stage | Skill | Purpose |
| --- | --- | --- |
| S00 | `autoscholar-field-archive` | Prepare field maps, paper cards, and evidence banks. |
| S01 | `autoscholar-direction-review` | Generate, critique, rank, and select directions. |
| S02 | `autoscholar-experiment-runner` | Implement experiment scaffolds and report execution evidence. |
| S03 | `autoscholar-manuscript-builder` | Build evidence-grounded paper plans and drafts. |
| S04 | `autoscholar-quality-gate` | Audit claims, citations, reproducibility, and release readiness. |

At runtime, the Python pipeline writes `skills_manifest.md` and per-stage
`skill_support.md` files into generated workspaces. Model prompts also receive
the active stage skill metadata so the automatic path stays aligned with the
same skill contracts.

## Future Wrappers

- `autoscholar-literature-scout`: stronger external literature retrieval.
- `autoscholar-result-auditor`: result-to-claim validation once real experiments finish.
- `autoscholar-release-packager`: final artifact packaging and policy checks.

## Skill Contract

Each skill receives context through the workspace and active stage metadata:

- workspace path;
- stage name;
- artifact paths from dependencies;
- expected outputs;
- quality gate expectations.

Each skill should reinforce:

- durable Markdown artifacts;
- explicit missing evidence;
- conservative claim support;
- clear route-back decisions.

## Codex And ClaudeCode Direction

The skills should not hide decisions in chat. They should guide or produce
durable files that the Python orchestrator can validate and resume.
