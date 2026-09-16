# Workflow Notes

## Mandatory loop

1. Build field context from recent papers.
2. Spawn multiple decision-maker agents.
3. Run at least 10 rounds of deliberation and log them.
4. Generate the idea pool only after deliberation converges.
5. Select one idea.
6. Write `executor_brief.md` as a professor-to-executor handoff.
7. Find baseline and implement.
8. Evaluate and summarize failures.
9. Run a multi-agent executor-to-professor review loop for at least 5 rounds unless the idea is killed.
10. After each execution round, professors send a written revision memo back to execution.
11. Draft paper only after evidence exists and the 5-round minimum is satisfied or an explicit exception is justified by very strong evidence.
12. Run at least 3 rounds of writer plus decision-maker review before calling the draft strong.

## Checkpointing protocol (required)

- At each step, produce a stage-and-round markdown artifact using:
  - `S00_RXX_*` for context
  - `S01_RXX_*` for decision
  - `S02_RXX_*` for execution/review
  - `S03_RXX_*` for writing
- Keep canonical files for readability, but checkpoint files are the source of resumability.
- Update both files after every completed step:
  - `00_field_context/checkpoint_state.md`
  - `00_field_context/progress_index.md`
- `checkpoint_state.md` must always include:
  - current stage
  - current round
  - last completed artifact path
  - next required artifact path
  - resume instruction
- `progress_index.md` is append-only and should log one line per completed artifact:
  - timestamp
  - stage
  - round
  - artifact path
  - short note
- If execution stops unexpectedly, resume from `checkpoint_state.md` rather than re-running prior rounds.

## Decision-agent protocol

- Minimum agent count: `3`
- Recommended roles:
  - novelty-focused professor
  - idea-growth professor
  - systems-and-feasibility professor
  - evaluation-and-reviewer professor
- Strongly recommended fourth role:
  - frontier-scout professor
- Every round should include:
  - one concrete claim
  - one criticism of another agent's claim
  - one update to the current shortlist or ranking
- The coordinator may summarize, but may not skip rounds.

## Mixed discussion rule

- Do not optimize for shallow harmony.
- Do not optimize for total confrontation either.
- At least one professor should push for ambition even if risky.
- At least one professor should help grow and refine promising ideas.
- At least one professor should try to reject ideas on novelty or evaluation weakness.
- At least one professor should try to reject ideas on implementation burden or experimental ambiguity.
- If all professors agree too quickly, force another challenge round before allowing convergence.
- If all professors only attack and no one helps refine a promising idea, force a synthesis round before allowing rejection.

## Frontier-scout protocol

- The frontier-scout professor is responsible for checking whether a candidate idea has already been done.
- Use the newest reachable sources during the run:
  - recent conference proceedings
  - OpenReview
  - arXiv
  - strong public repos when relevant
- The frontier-scout must write a short novelty verdict for each surviving idea:
  - `clear`
  - `crowded`
  - `near-duplicate`
- Any `near-duplicate` idea should be removed or fundamentally reframed before the final shortlist.
- Any `crowded` idea must state the exact differentiator and why that differentiator is still publishable.

## Default autonomy rule

- The decision group should substitute for the user's choices inside the loop.
- Do not ask the user to pick among candidate ideas, baselines, or revisions by default.
- After a primary idea is selected, do not ask the user whether execution should start; start it and record the handoff.
- Escalate only for blockers the agent cannot responsibly infer or access.

## Execution-loop protocol

- Minimum executor count when possible: `2`
- Recommended roles:
  - implementation-focused PhD
  - experiment-and-debugging PhD
- Minimum professor review count after execution starts: `5` rounds
- Every execution round should produce:
  - one `round_XX.md`
  - one `review_memo_XX.md`
- Professors should not only approve or reject; they must issue concrete next-step instructions.
- Executors should not free-run into large changes without a review memo after each round.

## Strong default heuristics

- Prefer the newest strong baseline with public training and evaluation code.
- Prefer a narrow, defensible contribution over a broad vague one.
- Force every idea to answer:
  - Why now?
  - Why this mechanism?
  - Why will it beat the baseline?
  - What ablation would prove it?
- Stop a direction early if the mechanism cannot be isolated experimentally.
- Treat insufficient deliberation as a process failure, not just a quality issue.
- Treat weak novelty filtering as a process failure, not just an idea-quality issue.

## Exit states

- `killed`: novelty weak or results unstable
- `revise`: promising but missing evidence
- `submission_candidate`: novelty, effect, and story are aligned
