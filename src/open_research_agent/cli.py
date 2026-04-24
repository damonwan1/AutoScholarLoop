from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from open_research_agent.core.pipeline import build_default_pipeline
from open_research_agent.core.workspace import ResearchWorkspace
from open_research_agent.writing.paper_formats import FORMATS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AutoScholarLoop research pipeline.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the full AUTO Research workflow.")
    run.add_argument("--seed", required=True, help="User research idea or notes.")
    run.add_argument("--workspace", required=True, help="Output workspace directory.")
    run.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Reference paper title, URL, note, or local path. Can be repeated.",
    )
    run.add_argument(
        "--provider",
        default="local",
        choices=["local", "openai-compatible"],
        help="Model provider to use.",
    )
    run.add_argument("--model", default="local-researcher", help="Model name.")
    run.add_argument("--base-url", default=None, help="OpenAI-compatible base URL.")
    run.add_argument("--num-ideas", type=int, default=3, help="Number of candidate ideas to request.")
    run.add_argument(
        "--loop-mode",
        default="standard",
        choices=["fast", "standard", "strict"],
        help="Nested-loop depth. standard runs S01=10, S02=5, S03=5 rounds.",
    )
    run.add_argument(
        "--max-big-loops",
        type=int,
        default=None,
        help="Override the number of global Research Big Loop attempts.",
    )
    run.add_argument("--decision-rounds", type=int, default=None, help="Override S01 professor decision rounds.")
    run.add_argument("--execution-rounds", type=int, default=None, help="Override S02 PhD execution rounds.")
    run.add_argument("--writing-rounds", type=int, default=None, help="Override S03 writing-review rounds.")
    run.add_argument(
        "--literature",
        default="local",
        choices=["local", "semanticscholar", "openalex"],
        help="Literature search backend for novelty and citation support.",
    )
    run.add_argument(
        "--execution-backend",
        default="dry-run",
        choices=["dry-run", "shell"],
        help="Execution backend for exploration runs.",
    )
    run.add_argument(
        "--shell-command",
        action="append",
        default=[],
        help="Shell command to run when --execution-backend shell is selected. Can be repeated.",
    )
    run.add_argument(
        "--review-ensemble",
        type=int,
        default=1,
        help="Number of reviewer samples to aggregate.",
    )
    run.add_argument(
        "--compile-pdf",
        action="store_true",
        help="Also export LaTeX and attempt pdflatex compilation.",
    )
    run.add_argument(
        "--paper-format",
        default="ieee",
        choices=sorted(FORMATS),
        help="Target manuscript format for writing and LaTeX export.",
    )
    batch = sub.add_parser("batch", help="Run multiple seeds as independent workspaces.")
    batch.add_argument("--seed-file", required=True, help="Text file with one research seed per line.")
    batch.add_argument("--workspace-root", required=True, help="Root folder for batch runs.")
    batch.add_argument("--parallel", type=int, default=1, help="Number of parallel workers.")
    batch.add_argument("--provider", default="local", choices=["local", "openai-compatible"])
    batch.add_argument("--model", default="local-researcher")
    batch.add_argument("--base-url", default=None)
    batch.add_argument("--literature", default="local", choices=["local", "semanticscholar", "openalex"])
    batch.add_argument("--execution-backend", default="dry-run", choices=["dry-run", "shell"])
    batch.add_argument("--review-ensemble", type=int, default=1)
    batch.add_argument("--loop-mode", default="standard", choices=["fast", "standard", "strict"])
    batch.add_argument("--max-big-loops", type=int, default=None)
    batch.add_argument("--decision-rounds", type=int, default=None)
    batch.add_argument("--execution-rounds", type=int, default=None)
    batch.add_argument("--writing-rounds", type=int, default=None)
    batch.add_argument("--paper-format", default="ieee", choices=sorted(FORMATS))
    web = sub.add_parser("web", help="Start the local Web API for the Vue console.")
    web.add_argument("--host", default="127.0.0.1", help="API host.")
    web.add_argument("--port", type=int, default=8000, help="API port.")
    web.add_argument("--reload", action="store_true", help="Enable uvicorn reload.")
    return parser


def run_command(args: argparse.Namespace) -> None:
    workspace = ResearchWorkspace.create(Path(args.workspace))
    pipeline = build_default_pipeline(
        provider_name=args.provider,
        model=args.model,
        base_url=args.base_url,
        literature=args.literature,
        execution_backend=args.execution_backend,
        shell_command=args.shell_command,
        review_ensemble=args.review_ensemble,
        compile_pdf=args.compile_pdf,
        loop_mode=args.loop_mode,
        max_big_loops=args.max_big_loops,
        decision_rounds=args.decision_rounds,
        execution_rounds=args.execution_rounds,
        writing_rounds=args.writing_rounds,
        paper_format=args.paper_format,
    )
    final_state = pipeline.run(
        workspace=workspace,
        seed=args.seed,
        references=args.reference,
        num_ideas=args.num_ideas,
    )
    print(f"Run completed: {workspace.root}")
    print(f"Final draft: {final_state.get('final_draft_path', 'not generated')}")


def _run_one_batch(item: tuple[int, str, dict]) -> str:
    index, seed, options = item
    workspace = ResearchWorkspace.create(Path(options["workspace_root"]) / f"run_{index:03d}")
    pipeline = build_default_pipeline(
        provider_name=options["provider"],
        model=options["model"],
        base_url=options["base_url"],
        literature=options["literature"],
        execution_backend=options["execution_backend"],
        review_ensemble=options["review_ensemble"],
        loop_mode=options["loop_mode"],
        max_big_loops=options["max_big_loops"],
        decision_rounds=options["decision_rounds"],
        execution_rounds=options["execution_rounds"],
        writing_rounds=options["writing_rounds"],
        paper_format=options["paper_format"],
    )
    state = pipeline.run(workspace=workspace, seed=seed, references=[], num_ideas=options["num_ideas"])
    return str(state.get("final_draft_path", workspace.root))


def batch_command(args: argparse.Namespace) -> None:
    seed_path = Path(args.seed_file)
    seeds = [line.strip() for line in seed_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    options = {
        "workspace_root": args.workspace_root,
        "provider": args.provider,
        "model": args.model,
        "base_url": args.base_url,
        "literature": args.literature,
        "execution_backend": args.execution_backend,
        "review_ensemble": args.review_ensemble,
        "loop_mode": args.loop_mode,
        "max_big_loops": args.max_big_loops,
        "decision_rounds": args.decision_rounds,
        "execution_rounds": args.execution_rounds,
        "writing_rounds": args.writing_rounds,
        "paper_format": args.paper_format,
        "num_ideas": 3,
    }
    items = [(index, seed, options) for index, seed in enumerate(seeds, start=1)]
    if args.parallel > 1:
        with ProcessPoolExecutor(max_workers=args.parallel) as pool:
            outputs = list(pool.map(_run_one_batch, items))
    else:
        outputs = [_run_one_batch(item) for item in items]
    for output in outputs:
        print(f"Final draft: {output}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        run_command(args)
    elif args.command == "batch":
        batch_command(args)
    elif args.command == "web":
        import uvicorn

        uvicorn.run(
            "open_research_agent.web.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )


if __name__ == "__main__":
    main()
