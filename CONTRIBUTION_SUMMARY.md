# Contribution Summary

This branch contains a cleaned and runnable AutoScholarLoop variant prepared for contribution review.

## Main Improvements

- Improved Web workflow robustness for model-backed runs.
- Added stronger local execution handling for generated S02 experiment commands.
- Added result parsing for static-vs-adaptive experiment outputs, including support rate, F1, citation accuracy, and delta metrics.
- Preserved generated result artifacts outside git via `.gitignore`.
- Kept API keys, local configs, run workspaces, logs, and nested duplicate folders out of version control.

## Contribution Notes

- The project can run with OpenAI-compatible providers such as DeepSeek.
- S02 experiment results are now parsed from `code/experiments/result.json` when generated scripts produce static/adaptive benchmark outputs.
- Manuscript claims should remain evidence-grounded: unsupported claims are routed back to S02 instead of being treated as publishable results.

## Suggested Review Focus

- Review `src/open_research_agent/core/research_loop.py` for result parsing and claim-evidence integration.
- Review `src/open_research_agent/adapters/execution.py` for local shell execution behavior.
- Review `src/open_research_agent/web/server.py` for Web API run configuration and provider handling.
