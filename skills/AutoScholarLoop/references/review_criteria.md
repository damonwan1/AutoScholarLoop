# Review Criteria

Use these criteria when acting as decision makers or internal reviewers.

## Idea acceptance

- Are required stage-and-round checkpoint artifacts present and ordered (no skipped required rounds)?
- Was the idea selected after the required multi-agent discussion rounds?
- Was there a healthy mix of support, refinement, and skepticism rather than only superficial consensus or only pure confrontation?
- Did a frontier-scout explicitly search the newest literature and give a novelty verdict?
- If the space is crowded, is the differentiator still precise and defensible?
- Is the problem important inside the subfield?
- Is the novelty specific rather than cosmetic?
- Is the closest prior work named explicitly?
- Is there a credible baseline repo to build on?
- Can the project reach a convincing prototype in reasonable time?

## Execution acceptance

- Does every execution round have both checkpoint artifacts:
  - `S02_RXX_execution.md`
  - `S02_RXX_review_memo.md`
- Did the decision group review the execution outcome for at least 3 rounds?
- Was execution carried out through a multi-agent executor setup rather than a single undifferentiated implementation pass, when sub-agents were available?
- Has the executor-professor loop run for at least 5 rounds unless the idea was explicitly killed?
- Are gains measured on accepted benchmarks?
- Are comparisons fair?
- Are ablations enough to support the claimed mechanism?
- Are failure cases documented instead of ignored?

## Draft acceptance

- Does each writing round emit a checkpoint artifact (`S03_RXX_draft_update.md`) and update checkpoint state?
- Did writers and decision makers review the draft for at least 3 rounds?
- Does the introduction state a concrete gap?
- Does the method section map tightly to that gap?
- Do experiments validate each claim?
- Would a skeptical reviewer still understand why this is publishable?

## Process integrity rejection conditions

- Missing `checkpoint_state.md` or `progress_index.md`
- Missing stage/round tags in intermediate files
- Rewritten history that removes prior rounds instead of appending new checkpoints
- Chat-only reasoning that was not persisted to checkpoint artifacts
