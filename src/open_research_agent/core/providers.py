from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    @abstractmethod
    def complete_json(
        self,
        *,
        role: str,
        task: str,
        context: dict[str, Any],
        schema_hint: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError


class LocalHeuristicProvider(ModelProvider):
    """Deterministic provider for offline development and tests."""

    def complete_json(
        self,
        *,
        role: str,
        task: str,
        context: dict[str, Any],
        schema_hint: dict[str, Any],
    ) -> dict[str, Any]:
        seed = context.get("seed", "unspecified research seed")
        if task == "intake":
            return {
                "problem": seed,
                "constraints": ["avoid unsupported claims", "keep references auditable"],
                "references": context.get("references", []),
                "target_output": "conference-style research paper",
            }
        if task == "ideation":
            requested = max(1, int(context.get("num_ideas", 2)))
            base_candidates = [
                {
                    "id": "direction_1",
                    "title": "Evidence-Grounded Research Agent Loops",
                    "hypothesis": f"Structured evidence checks can improve AUTO Research reliability for: {seed}",
                    "novelty_claim": "Combines direction generation with claim-level audit gates.",
                    "feasibility": "high",
                    "risks": ["may need strong literature retrieval", "evaluation can be subjective"],
                },
                {
                    "id": "direction_2",
                    "title": "Reviewer-Guided Paper Iteration",
                    "hypothesis": "A standing reviewer panel can reduce hallucinated contributions.",
                    "novelty_claim": "Treats review comments as executable revision tasks.",
                    "feasibility": "medium",
                    "risks": ["reviewer bias", "requires robust task tracking"],
                },
                {
                    "id": "direction_3",
                    "title": "Citation-Aware Claim Expansion",
                    "hypothesis": "Research ideas become safer when every new claim is paired with a required evidence source.",
                    "novelty_claim": "Makes claim expansion conditional on source availability.",
                    "feasibility": "medium",
                    "risks": ["retrieval coverage", "overly conservative writing"],
                },
            ]
            return {
                "candidates": base_candidates[:requested],
                "self_critique": "The first direction is broader and easier to evaluate with artifact checks.",
            }
        if task == "novelty":
            return {
                "selected_id": "direction_1",
                "decision": "proceed",
                "closest_known_work": context.get("references", []),
                "rationale": "No exact duplicate was found in provided references; requires external literature check in v0.3.",
            }
        if task == "planning":
            return {
                "objective": "Build and evaluate an evidence-grounded AUTO Research loop.",
                "work_packages": [
                    "define artifact schema",
                    "generate candidate directions",
                    "audit claims against produced artifacts",
                    "draft and review a paper",
                ],
                "success_metrics": ["artifact coverage", "claim support ratio", "review issue closure"],
            }
        if task == "execution":
            return {
                "runs": [
                    {
                        "name": "architecture_probe",
                        "status": "completed",
                        "observation": "Stage artifacts create a traceable path from seed to draft.",
                    }
                ],
                "open_issues": ["real experiment execution backend is deferred"],
            }
        if task == "code_generation":
            return {
                "files": [
                    {
                        "path": "code/methods/proposed_method.py",
                        "content": (
                            "class ProposedMethod:\n"
                            "    def __init__(self, config):\n"
                            "        self.config = config\n\n"
                            "    def fit(self, train_data):\n"
                            "        return self\n\n"
                            "    def predict(self, batch):\n"
                            "        return [0 for _ in batch]\n\n"
                            "    def cost_estimate(self):\n"
                            "        return {'compute_cost': 0.0, 'latency': 0.0}\n"
                        ),
                    }
                ],
                "commands": [
                    "python code/experiments/run_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
                ],
                "notes": "Local fallback code only; real provider should replace with domain-specific implementation.",
            }
        if task == "synthesis":
            return {
                "claims": [
                    {
                        "claim": "A stage graph improves auditability of automated research workflows.",
                        "support": "workspace manifest and stage artifacts",
                        "status": "supported_by_design_artifact",
                    }
                ],
                "limitations": ["offline provider does not validate scientific novelty"],
            }
        if task == "paper_draft":
            return {
                "title": "Evidence-Grounded AUTO Research Loops",
                "abstract": (
                    "This paper draft describes a staged AUTO Research workflow. "
                    "Empirical claims remain provisional until backed by executed experiments."
                ),
                "introduction": "The research problem is converted into auditable decisions, execution artifacts, and writing checkpoints.",
                "related_work": "Related work should be populated from verified literature cards and citation audits.",
                "method": "The method consists of field archiving, professor decision loops, executor-review loops, evidence-driven writing, and quality gates.",
                "experiments": "The current demo run generates experiment code scaffolds but does not execute a real benchmark.",
                "results": "No performance claim is accepted without result files and claim-evidence support.",
                "limitations": ["Local demo mode is not a substitute for real experiments."],
                "conclusion": "The workflow is a foundation for controlled, auditable research automation.",
            }
        if task == "review":
            return {
                "summary": "The draft proposes a modular AUTO Research framework.",
                "strengths": ["clear lifecycle", "auditable artifacts"],
                "weaknesses": ["needs real literature search", "needs execution sandbox"],
                "scores": {"originality": 3, "soundness": 2, "clarity": 3, "significance": 3},
                "recommendation": "revise",
                "required_revisions": ["mark deferred components clearly", "avoid overclaiming empirical results"],
            }
        if task == "revision":
            return {
                "revision_plan": ["tighten claims", "separate implemented and planned features"],
                "accepted": True,
            }
        return {"note": f"local response for {role}/{task}", "schema_hint": schema_hint}


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, model: str, base_url: str | None = None):
        try:
            import httpx
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install with `pip install .[api]` to use API providers.") from exc
        self.model = model
        trust_env = os.getenv("AUTOSCHOLARLOOP_HTTP_TRUST_ENV", "1").lower() not in {"0", "false", "no"}
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            http_client=httpx.Client(trust_env=trust_env),
        )

    def complete_json(
        self,
        *,
        role: str,
        task: str,
        context: dict[str, Any],
        schema_hint: dict[str, Any],
    ) -> dict[str, Any]:
        prompt = {
            "role": role,
            "task": task,
            "context": context,
            "schema_hint": schema_hint,
            "instruction": (
                "Return valid JSON only. Do not include markdown fences. "
                "Never invent experimental numbers, citations, datasets, or completed baselines. "
                "If result files or backend logs do not support a claim, mark the claim as unsupported or hypothesis. "
                "For code_generation, create runnable local Python code plus commands that can execute on the current machine. "
                "For paper_draft, write only evidence-grounded results and move unsupported claims to limitations or future work."
            ),
        }
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a rigorous AUTO Research agent. You operate like a research group, "
                        "but every manuscript claim must be backed by explicit evidence artifacts. "
                        "Fabricated metrics are a critical failure."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content or "{}"
        return _safe_json_loads(content, task=task, role=role, schema_hint=schema_hint)


def build_provider(name: str, model: str, base_url: str | None = None) -> ModelProvider:
    if name == "local":
        return LocalHeuristicProvider()
    if name == "openai-compatible":
        return OpenAICompatibleProvider(model=model, base_url=base_url)
    raise ValueError(f"Unsupported provider: {name}")


def _safe_json_loads(content: str, *, task: str, role: str, schema_hint: dict[str, Any]) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            loaded = json.loads(candidate)
            return loaded if isinstance(loaded, dict) else {"items": loaded}
        except json.JSONDecodeError:
            continue
    return _fallback_response(task=task, role=role, schema_hint=schema_hint, raw=content)


def _fallback_response(*, task: str, role: str, schema_hint: dict[str, Any], raw: str) -> dict[str, Any]:
    note = (
        f"Model response for {role}/{task} was not valid JSON. "
        "AutoScholarLoop converted this step into a recoverable checkpoint."
    )
    if task == "planning":
        return {
            "objective": "Recover from malformed model planning output and continue with a minimal local experiment.",
            "work_packages": ["run local sanity experiment", "record failure details", "return to professor review"],
            "success_metrics": ["command completion", "parseable result file"],
            "parser_warning": note,
        }
    if task == "code_generation":
        return {
            "files": [],
            "commands": [
                "python code/experiments/run_experiment.py --config code/experiments/config.json --output code/experiments/result.json"
            ],
            "notes": note,
            "parser_warning": note,
        }
    if task == "execution":
        return {
            "runs": [{"name": "recovered_execution", "status": "failed", "observation": note}],
            "open_issues": [note, "Repeat S02 with stricter code-generation prompt or inspect generated commands."],
            "parser_warning": note,
        }
    if task == "synthesis":
        return {
            "claims": [
                {
                    "claim": "The current run produced only partial execution evidence.",
                    "support": "execution logs and parser recovery note",
                    "status": "unsupported",
                }
            ],
            "limitations": [note],
        }
    if task == "paper_draft":
        return {
            "title": "Recovered AutoScholarLoop Draft",
            "abstract": "The run produced partial artifacts but did not produce enough valid evidence for a scientific claim.",
            "introduction": "This draft is a recovery artifact generated after malformed model output.",
            "related_work": "Related work must be regenerated after the execution loop is repaired.",
            "method": "The proposed method is not yet validated.",
            "experiments": "Execution did not complete reliably.",
            "results": "No validated result is available.",
            "limitations": [note],
            "conclusion": "Return to S02 for another execution loop.",
        }
    return {"note": note, "schema_hint": schema_hint, "raw_preview": raw[:1000]}
