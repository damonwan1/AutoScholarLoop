# AutoScholarLoop

A Codex skill for literature-driven AI research. It organizes a narrow field's recent papers into an auditable workflow for idea selection, implementation, experiments, and paper drafting. The skill works best when Codex can delegate to multiple agents.

## Install

Download this repository and place its **entire contents** in a folder named `autoscholarloop` under your personal Codex skills directory. Keep `SKILL.md`, `scripts/`, `references/`, `assets/`, and `agents/` together.

- Windows: `C:\Users\<your-name>\.codex\skills\autoscholarloop\`
- macOS/Linux: `~/.codex/skills/autoscholarloop/`

Restart Codex if the skill does not appear. Invoke it with `$autoscholarloop` or describe a literature-driven AI research loop.

## Quick start

Prepare one narrow research-field folder with approximately 5–15 recent papers, PDFs, or paper notes. From the installed skill directory, run:

```sh
python -B scripts/bootstrap_field.py --field-dir "<output-field-folder>" --paper-dir "<papers-folder>" --field-name "<field-name>" --domain "<domain>"
```

Then ask Codex: `Use $autoscholarloop on <output-field-folder>. Start with the decision phase.` The bootstrap script creates checkpoint and template files without replacing existing ones. It requires Python 3; the skill's multi-agent research workflow also depends on the agent capabilities available in your Codex environment.

## License

MIT. See [LICENSE](LICENSE).
