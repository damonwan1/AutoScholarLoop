# Design Notes

## Why A Stage Graph

The research process should be inspectable and resumable. A stage graph makes
each decision explicit and lets future versions swap in stronger components.

## Why Not A Fixed Template Contract

Fixed files such as a single `experiment.py` are easy to start with but become
limiting for broader AUTO Research. This project supports template packs, but the
core engine only depends on artifacts and stage interfaces.

## Planned Template Types

- code experiment template;
- literature-only survey template;
- benchmark replication template;
- theorem/proof template;
- system-building template;
- paper-improvement template.

## Compatibility Direction

The project should be easy to drive from:

- CLI;
- Python API;
- Codex skill;
- ClaudeCode instruction pack;
- notebook;
- later web UI.
