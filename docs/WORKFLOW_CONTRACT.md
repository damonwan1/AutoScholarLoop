# Workflow Contract

This file is the authoritative reference for future iterations.

## Required Stages

Every complete AUTO Research run must include:

1. Intake
2. Ideation
3. Novelty
4. Planning
5. Execution
6. Synthesis
7. Drafting
8. Review
9. Revision
10. Release

Stages may be repeated, branched, or replaced by stronger implementations, but a
release package must identify how each required stage was satisfied.

## Artifact Rules

- Every stage writes at least one JSON artifact.
- Human-readable Markdown summaries are encouraged for auditability.
- The workspace manifest records stage status, artifact paths, and timestamps.
- Later stages must reference earlier artifacts instead of relying only on chat
  history.

## Originality Rules

- Do not copy paragraph-level wording from references.
- Keep source summaries separate from generated manuscript text.
- Novelty claims must name nearest prior work once literature connectors are
  enabled.
- Unsupported claims must be marked as hypotheses or removed.

## Execution Rules

- Arbitrary code execution is disabled unless an execution backend is configured.
- Shell commands must run inside the workspace or a configured sandbox.
- Failed runs must be preserved with logs instead of silently overwritten.

## Writing Rules

The paper draft must include:

- title;
- abstract;
- introduction;
- related work;
- method or proposed approach;
- experiments or exploration protocol;
- results/evidence;
- limitations;
- conclusion;
- reproducibility note.

## Review Rules

Review output must include:

- summary;
- strengths;
- weaknesses;
- originality;
- soundness;
- clarity;
- significance;
- confidence;
- recommendation;
- required revisions.
