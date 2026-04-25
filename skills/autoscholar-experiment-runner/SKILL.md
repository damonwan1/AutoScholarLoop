---
name: autoscholar-experiment-runner
description: Implement, run, repair, or audit AutoScholarLoop S02 experiment workspaces. Use for S02 automatic execution support when creating or updating `code/experiments/run_experiment.py`, `code/methods/proposed_method.py`, `code/run_commands.json`, result artifacts, `RESULTS_ANALYSIS.md`, `CLAIMS_FROM_RESULTS.md`, and `EXPERIMENT_AUDIT.md`.
---

# AutoScholar Experiment Runner

Use this skill for S02 execution work in the automatic Python pipeline, where
model-generated code is written and executed through `dry-run` or `shell`.
The goal is to produce execution artifacts that honestly state what evidence
exists and what claims remain unsupported.

## Inputs

1. `01_decision/executor_brief.md`
2. `01_decision/chosen_direction.md`
3. `00_field_context/dataset_baseline_map.md`
4. `00_field_context/evidence_bank.md`
5. existing `code/` files and previous `02_execution/` reports

## Workflow

### Phase 1: Freeze The Execution Target

Extract and write down:

- selected idea;
- core claim S02 is allowed to test;
- minimum experiment;
- required baselines;
- required datasets or placeholder status;
- metric definitions;
- expected output files;
- known blockers.

If the executor brief is vague, implement a small sanity scaffold and mark
claim support as `scaffold_only` instead of inventing an experiment.

### Phase 2: Build Or Repair Code

Create or refine:

- `code/experiments/config.json`
- `code/experiments/results_schema.json`
- `code/experiments/run_experiment.py`
- `code/methods/proposed_method.py`
- `code/run_commands.json`

Implementation requirements:

- expose paths, seeds, dataset names, and output paths as config or CLI args;
- write machine-readable results to JSON;
- distinguish toy data, placeholder data, and real data;
- include a baseline field even when the baseline is a placeholder;
- keep imports minimal unless the workspace already has dependencies;
- fail with a clear message when required data is missing.

Do not create broad framework code that cannot be run or audited.

### Phase 3: Run The Smallest Safe Check

Prefer this order:

1. import check;
2. config load check;
3. toy/smoke run;
4. real local run, only when data and dependencies exist;
5. external/remote run, only if explicitly configured outside this skill.

Record commands in `code/run_commands.json`:

```json
{
  "commands": [
    "python code/experiments/run_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
  ]
}
```

### Phase 4: Interpret Results

Classify evidence:

- `real_result`: real dataset, fair baseline, defined metric, and result file.
- `smoke_result`: runnable sanity check only.
- `scaffold_only`: code created but not executed.
- `blocked`: missing data, credentials, dependency, hardware, or baseline.

Never let a smoke result support a broad empirical claim. A smoke result can
support only that the scaffold runs.

### Phase 5: Write S02 Reports

Update or help produce:

- `02_execution/GENERATED_CODE.md`
- `02_execution/RESULTS_ANALYSIS.md`
- `02_execution/CLAIMS_FROM_RESULTS.md`
- `02_execution/EXPERIMENT_AUDIT.md`

Recommended `CLAIMS_FROM_RESULTS.md` table:

```markdown
| Claim | Verdict | Support | Missing Evidence | Next Action |
|---|---|---|---|---|
```

Verdict values:

- `supported`: evidence is real and sufficient for the narrow claim;
- `partial`: evidence supports only a weaker claim;
- `unsupported`: no valid evidence yet;
- `blocked`: execution could not test the claim.

## Failure Handling

When execution fails:

- capture the command, return code, stdout, and stderr;
- classify the failure: missing file, import error, bad config, data missing,
  metric bug, timeout, or unknown;
- attempt a minimal fix only inside allowed workspace paths;
- if unresolved, mark `blocked` and write the exact blocker.

Do not hide failures by replacing them with successful placeholder results.

## Boundaries

- Do not modify project source directories such as `src/`, `web/`, `docs/`,
  `configs/`, or `templates/` unless explicitly asked to work on the project
  itself rather than a run workspace.
- Do not run destructive commands.
- Do not install heavy dependencies without user approval.
- Do not download datasets unless the task or user explicitly permits it.
- Do not present generated or toy data as real empirical evidence.

## Quality Gate

S02 is acceptable when:

- code artifacts exist and are listed;
- commands are reproducible;
- results, if present, match `results_schema.json`;
- claim support is honestly classified;
- missing datasets, baselines, or metrics are listed as blockers.

Route back to S01 when the selected idea cannot produce a meaningful experiment.
Route to S03 only with explicit claim limits.
