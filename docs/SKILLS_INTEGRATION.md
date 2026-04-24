# Agent Integration

The repository can expose agent-callable wrappers that operate on the same
workspace contract as the Python pipeline. These wrappers are generated from New
AI Scientist's native capability contracts; they are not direct copies of any
external skill files.

## Planned Agent Wrappers

- `nars-brief-normalizer`: normalize ideas and references.
- `nars-direction-workshop`: expand directions and run committee debate.
- `nars-frontier-probe`: search literature and kill near-duplicates.
- `nars-execution-bridge`: implement or run experiments in a sandbox.
- `nars-evidence-writer`: draft paper sections from evidence.
- `nars-review-loop`: review and create revision tasks.
- `nars-release-builder`: package final paper and artifacts.

## Wrapper Contract

Each wrapper receives:

- workspace path;
- stage name;
- artifact paths from dependencies;
- allowed tools;
- safety limits.

Each wrapper must write:

- a JSON artifact;
- a Markdown summary;
- manifest update or return data that the Python runner records.

## Codex And ClaudeCode Direction

The skills should not hide decisions in chat. They should write durable files
that the Python orchestrator can validate and resume.
