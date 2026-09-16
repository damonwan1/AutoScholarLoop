---
name: autoscholarloop
description: Automate literature-driven AI research loops from recent top-conference paper folders to idea generation, implementation planning, coding iteration, experiment refinement, and conference-style paper drafting. Use when Codex needs to act as an AI researcher with role separation across decision makers, executors, and writers, especially for a subfield that already has 5-15 recent papers collected locally.
---

# AutoScholarLoop

Run a staged research loop around one narrow field folder that already contains recent papers.

## Non-Negotiable Constraints

- Use real multi-agent delegation for the decision phase when sub-agents are available. Do not collapse professor-style deliberation into one uninterrupted single-agent pass.
- Do not generate the final `3-5` candidate ideas immediately after reading papers. First run explicit inter-agent deliberation and record it.
- Let the decision group proxy the user by default. Do not stop to ask the user to choose among ideas or revisions unless external access, missing credentials, or destructive actions make that unavoidable.
- After the decision group selects a primary direction, move directly into executor handoff and execution planning. Do not ask the user whether to proceed unless a real external blocker exists.
- After executors start, enforce multi-agent execution plus multi-agent professor review. Do not treat one implementation pass plus one summary as sufficient.
- Define and satisfy minimum discussion rounds at key stages before accepting outputs.
- Keep a written deliberation record in markdown so later execution rounds can trace why a direction was chosen.
- Every major step must emit a markdown checkpoint artifact with explicit `stage` and `round` labels. Do not keep progress only in chat.
- Use resumable checkpointing. At every step update `00_field_context/checkpoint_state.md` and `00_field_context/progress_index.md` so the loop can restart from the latest completed checkpoint.
- Enforce filename tags for intermediate artifacts: `S{stage}_R{round}_{artifact}.md` where `stage` is two digits and `round` is two digits.
- Make the decision-maker group structurally diverse. Do not make all professor agents purely cooperative, but also do not force every professor into maximal confrontation.
- Include one frontier-sensitive professor whose job is to search for the newest overlapping work and kill ideas that are already done or too close to current papers.

## Workflow

1. Inspect the field folder and count papers.
2. Read the field index first, then sample the most relevant PDFs or notes.
3. Run a decision-maker deliberation phase with multiple agents.
4. Create role-separated outputs:
   - `01_decision/`: professor-style idea generation, debate, shortlist, and chosen direction
   - `02_execution/`: baseline search, implementation plan, experiment logs, iteration feedback
   - `03_writing/`: paper outline, draft sections, rebuttal-style reviewer comments
5. Move only one shortlisted idea into execution at a time.
6. Iterate until the decision group marks the project as `submission_candidate`.

## Operating Rules

- Keep one subfield per loop. Do not mix time-series forecasting and video generation in the same loop.
- Treat recent top-conference papers as the primary evidence base.
- Require explicit novelty claims against named baselines and adjacent papers.
- Reject ideas that are only recombinations without a defensible mechanism or evaluation edge.
- Prefer ideas that can be implemented on top of a strong public baseline.
- Keep every stage auditable in markdown files. Do not hide decisions in chat only.
- If any required checkpoint file is missing for the current step, create it immediately before proceeding.

## Stage and Checkpoint Contract

- Stage map:
  - `S00`: field context and paper mapping
  - `S01`: decision-maker deliberation and idea selection
  - `S02`: executor implementation and professor review loop
  - `S03`: writer drafting and reviewer-style refinement
- Every stage must include round-based intermediate artifacts. Minimum required:
  - `S00_R01_field_map.md` plus updates to `progress_index.md`
  - `S01_RXX_deliberation.md` for each decision round
  - `S01_R10_idea_pool.md` or later when idea pool is finalized
  - `S01_RYY_executor_brief.md` for handoff
  - `S02_RXX_execution.md` for each executor round
  - `S02_RXX_review_memo.md` for each professor review memo
  - `S03_RXX_draft_update.md` for each writing round
- Do not overwrite prior rounds. Append new rounds as new files.
- Keep canonical summary files (`deliberation_log.md`, `idea_pool.md`, `chosen_direction.md`, `executor_brief.md`, `round_XX.md`, `review_memo_XX.md`, `draft.md`) but always mirror them with stage-tagged checkpoint files.
- After each write, add one line to `00_field_context/progress_index.md` including timestamp, stage, round, and file path.

## Minimum Deliberation Rounds

These are floor values, not targets.

### Decision phase

- Use at least `3` decision-maker agents with differentiated viewpoints when possible.
- Ensure mixed interaction by design. The professor group should contain both overlapping viewpoints and conflicting priors, and should not converge too early.
- Run at least `10` rounds of inter-agent discussion before finalizing the first candidate set.
- Require these sub-stages inside those rounds:
  - rounds `1-3`: summarize papers, identify claims, challenge novelty assumptions
  - rounds `4-6`: propose directions, attack weaknesses, compare against nearest prior work
  - rounds `7-8`: refine the strongest directions and remove weak ones
  - rounds `9-10`: converge on `3-5` ideas and rank them
- Do not open execution before this minimum is met.
- Require at least one explicit rejection or major downgrade in rounds `4-10` if novelty or feasibility is weak.
- Require a novelty re-check against the newest available literature before an idea survives to the final `3-5`.

### Post-execution decision review

- After each execution round, require at least `3` rounds of decision-maker review before issuing a revision memo or killing the idea.

### Execution-development loop

- Use real multi-agent delegation for execution when sub-agents are available.
- Require at least `5` executor-to-professor iteration rounds before treating the project as mature enough for serious paper drafting, unless the idea is explicitly killed earlier.
- Each round must include:
  - executor implementation/update report
  - professor review and criticism
  - written revision memo
  - executor response plan for the next round
- Do not jump from first implementation success to paper drafting.

### Writing review

- Before marking a draft as submission-ready, require at least `3` rounds of reviewer-style discussion between decision makers and writers.

## Role Split

### Decision Makers

Act like a small professor committee.

- Read all available paper metadata and enough paper content to compare methods.
- Debate explicitly with each other rather than silently merging conclusions.
- Attack novelty, feasibility, evaluation credibility, and baseline choice from different angles.
- Record each discussion round in `01_decision/deliberation_log.md`.
- Maintain role diversity such as:
  - novelty-maximalist professor
  - idea-growth professor
  - skeptical reviewer-style professor
  - systems-and-feasibility professor
  - frontier-scout professor
- Produce `3-5` ideas with:
  - motivation
  - core novelty
  - closest prior work
  - feasibility
  - likely failure points
- Select only one idea for execution.
- After each execution round, issue a concrete revision memo.
- Make the selection on behalf of the user unless blocked by missing external information.
- After selection, issue a direct handoff to executors in `01_decision/executor_brief.md`.
- The frontier-scout professor must explicitly check whether the idea or a near-equivalent has already appeared in the newest literature, repos, or preprints reachable during the run.
- If the frontier-scout finds near-duplicate prior work, the idea should be killed or sharply reframed rather than allowed through.
- The committee should practice `求同存异`: some professors should help refine promising ideas while others stress-test them.

Use the template in `assets/templates/idea_spec.md`.
Use the review criteria in `references/review_criteria.md`.

### Executors

Act like research PhD students.

- Find the strongest and most recent reproducible baseline.
- Treat `01_decision/executor_brief.md` as the authoritative task order from the professor committee.
- Prefer official GitHub repos; otherwise choose the cleanest community implementation and note the risk.
- Implement only the chosen idea.
- Run focused experiments before broad sweeps.
- Report back to the professor committee after every execution round.
- Expect at least 5 rounds of implementation-review iteration unless the project is killed.
- Report results in terms of:
  - what changed
  - what worked
  - what failed
  - what the decision group should do next

Use the template in `assets/templates/execution_round.md`.

### Writers

Act like conference paper authors.

- Draft from evidence, not from aspiration.
- Write only claims supported by experiments or clearly marked hypotheses.
- Follow the canonical structure:
  - `Abstract`
  - `Introduction`
  - `Related Work`
  - `Method`
  - `Experiments`
  - `Limitations`
  - `Conclusion`
- Route missing evidence back to execution instead of hand-waving.
- Expect decision makers to critique the draft in multiple rounds before acceptance.

Use the template in `assets/templates/paper_draft.md`.

## Folder Contract

Create or maintain this structure for each subfield:

```text
field/
├── source_papers/
├── 00_field_context/
├── 01_decision/
├── 02_execution/
└── 03_writing/
```

- `source_papers/`: local PDFs or links to the collected paper folder
- `00_field_context/checkpoint_state.md`: current stage, current round, next action, resume command
- `00_field_context/progress_index.md`: append-only checkpoint ledger for all intermediate artifacts
- `00_field_context/field_map.md`: scope, venues, date range, paper list, paper clusters
- `01_decision/deliberation_log.md`: round-by-round professor dialogue and convergence notes
- `01_decision/S01_RXX_deliberation.md`: per-round decision checkpoint artifacts
- `01_decision/idea_pool.md`: all generated ideas
- `01_decision/idea_XX.md`: one file per shortlisted idea
- `01_decision/chosen_direction.md`: current selected route
- `01_decision/executor_brief.md`: direct handoff from professors to executors with scope, constraints, and first tasks
- `02_execution/baseline_scan.md`: candidate repos and chosen baseline
- `02_execution/round_XX.md`: one file per implementation round
- `02_execution/review_memo_XX.md`: professor feedback after each execution round
- `02_execution/S02_RXX_execution.md`: per-round execution checkpoint artifacts
- `02_execution/S02_RXX_review_memo.md`: per-round professor memo checkpoint artifacts
- `03_writing/review_log.md`: reviewer-style critique rounds on the draft
- `03_writing/paper_outline.md`: live paper plan
- `03_writing/draft.md`: live draft
- `03_writing/S03_RXX_draft_update.md`: per-round writing checkpoint artifacts

## Quick Start

If the field folder is not scaffolded yet, run this from the directory containing this `SKILL.md` (or resolve the script path relative to this file):

```powershell
python -B scripts/bootstrap_field.py --field-dir "<field-dir>" --paper-dir "<paper-dir>" --field-name "<name>" --domain "<domain>"
```

Then:

1. Fill `00_field_context/field_map.md`.
2. Ask Codex to use `$autoscholarloop` on that field directory.
3. Start with the multi-agent decision phase only.
4. Do not finalize ideas until the minimum decision-round count is satisfied.
5. After a direction is selected, generate `executor_brief.md` and move directly into execution.
6. Do not start writing until at least one execution round exists.

## References

- Read `references/workflow_notes.md` for the end-to-end loop.
- Read `references/review_criteria.md` before accepting an idea or draft.
