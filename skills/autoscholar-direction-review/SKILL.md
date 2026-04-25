---
name: autoscholar-direction-review
description: Support AutoScholarLoop S01 direction generation and review. Use when producing, repairing, or auditing `IDEA_REPORT.md`, `idea_pool.md`, `chosen_direction.md`, and `executor_brief.md` from S00 field archive artifacts.
---

# AutoScholar Direction Review

Use this skill to run the S01 professor decision stage. S01 should create
candidate directions, attack them, rank them, and select one executable
direction without overstating novelty.

## Inputs

Read in this order:

1. `00_field_context/field_map.md`
2. `00_field_context/paper_cards.md`
3. `00_field_context/method_map.md`
4. `00_field_context/dataset_baseline_map.md`
5. `00_field_context/evidence_bank.md`
6. `inputs/seed.json`

If S00 artifacts are incomplete, continue but mark the decision as provisional.

## Workflow

### Phase 1: Extract Decision Constraints

Identify:

- problem anchor;
- target users or domain;
- available evidence;
- required datasets or baselines;
- likely nearest prior work;
- compute or implementation constraints;
- venue expectations if present.

These constraints should appear in the idea report so S02 knows what must be
validated.

### Phase 2: Generate Candidate Directions

Generate 3-5 candidates unless the caller requests a different number.

Each candidate should include:

- id;
- title;
- hypothesis;
- proposed mechanism;
- minimum viable experiment;
- expected evidence if successful;
- novelty risk;
- feasibility risk;
- data and baseline requirements;
- likely reviewer objection.

Keep candidates testable. Avoid directions that only sound good as prose but
cannot be checked in S02.

### Phase 3: Critique And Prune

For each candidate, ask:

- Does S00 evidence suggest a real gap?
- What closest work might already cover this?
- Can S02 implement a meaningful check in the available workspace?
- What claim would be unsupported even if the experiment runs?
- Is the idea too broad for a single paper?

Eliminate or downgrade weak candidates. Record the reason.

### Phase 4: Rank And Select

Rank candidates using:

- novelty plausibility;
- feasibility;
- evidence availability;
- expected paper clarity;
- risk of unsupported claims;
- implementation cost.

Select one direction only if it can be handed to S02 with a minimum experiment.
If no candidate is executable, route back to S00 or request user data.

### Phase 5: Write Executor Brief

The executor brief should be concrete enough for code generation:

- selected idea;
- frozen core claim;
- required baseline scan;
- minimum experiment;
- expected result file shape;
- failure cases that should downgrade the claim.

## Outputs

Required:

- `01_decision/idea_pool.md`
- `01_decision/IDEA_REPORT.md`
- `01_decision/chosen_direction.md`
- `01_decision/executor_brief.md`

Recommended `IDEA_REPORT.md` structure:

```markdown
# Research Idea Report

## Decision Constraints
## Candidate Ideas
## Critique And Eliminations
## Ranked Shortlist
## Selected Direction
## Minimum Experiment
## Risks For S02
```

Recommended candidate table:

```markdown
| ID | Hypothesis | Minimum Experiment | Novelty Risk | Feasibility | Decision |
|---|---|---|---|---|---|
```

## Quality Gate

S01 is acceptable when:

- at least one candidate has a testable minimum experiment;
- the selected direction has an executor brief;
- novelty is described as provisional unless externally verified;
- eliminated ideas have reasons;
- risks are specific enough for S02 to act on.

Route back to S00 when:

- no closest-work context exists;
- dataset or baseline requirements are totally unknown;
- the selected idea cannot be converted into an experiment.

## Rules

- Do not treat local heuristic novelty as scientific novelty.
- Prefer one dominant claim over many weak claims.
- Do not select ideas whose only evidence would be rhetorical.
- Record reviewer objections before S02 begins.
- Keep the executor brief implementation-oriented, not essay-like.
