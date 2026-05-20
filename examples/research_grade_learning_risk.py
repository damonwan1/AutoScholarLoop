from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn

from open_research_agent.writing.latex_paper import compile_latex, write_latex_from_markdown
from open_research_agent.writing.paper_formats import get_paper_format, write_format_profile


WORKSPACE = Path("demo_runs/research_grade_learning_risk")
N_STUDENTS = 480
N_WEEKS = 8
N_SEEDS = 5


class TemporalAttentionRiskModel(nn.Module):
    def __init__(self, feature_dim: int):
        super().__init__()
        self.query = nn.Parameter(torch.zeros(feature_dim))
        self.classifier = nn.Linear(feature_dim, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        scores = torch.matmul(x, self.query)
        weights = torch.softmax(scores, dim=1)
        context = torch.sum(x * weights.unsqueeze(-1), dim=1)
        logits = self.classifier(context).squeeze(-1)
        return logits, weights


def generate_dataset(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    ability = rng.normal(0.0, 1.0, N_STUDENTS)
    diligence = rng.normal(0.0, 1.0, N_STUDENTS)
    difficulty = rng.normal(0.0, 0.45, N_WEEKS)
    sequences = np.zeros((N_STUDENTS, N_WEEKS, 4), dtype=np.float32)

    for student in range(N_STUDENTS):
        trend = rng.normal(0.0, 0.10)
        for week in range(N_WEEKS):
            learning = trend * week
            latent = ability[student] + learning - difficulty[week] + rng.normal(0.0, 0.35)
            accuracy = 1.0 / (1.0 + np.exp(-latent))
            score = np.clip(accuracy + rng.normal(0.0, 0.08), 0.0, 1.0)
            delay = rng.exponential(scale=max(0.08, 0.8 - 0.22 * diligence[student] - 0.15 * ability[student]))
            missing = rng.random() < (0.04 + 0.08 / (1.0 + np.exp(ability[student] + diligence[student])))
            sequences[student, week] = [score, min(delay, 2.5) / 2.5, accuracy, float(missing)]

    early = sequences[:, :4]
    final_score = sequences[:, :, 0].mean(axis=1)
    engagement = 1.0 - sequences[:, :, 3].mean(axis=1)
    risk_logit = -3.0 * final_score - 0.9 * engagement + 0.75 * sequences[:, 3:, 1].mean(axis=1) + 2.35
    risk_probability = 1.0 / (1.0 + np.exp(-risk_logit))
    labels = (risk_probability + rng.normal(0.0, 0.05, N_STUDENTS) > 0.52).astype(np.int64)
    return early.astype(np.float32), labels


def aggregate_features(x: np.ndarray) -> np.ndarray:
    mean = x.mean(axis=1)
    std = x.std(axis=1)
    last = x[:, -1, :]
    trend = x[:, -1, :] - x[:, 0, :]
    return np.concatenate([mean, std, last, trend], axis=1)


def precision_at_fraction(y_true: np.ndarray, scores: np.ndarray, fraction: float = 0.2) -> float:
    k = max(1, int(len(y_true) * fraction))
    order = np.argsort(scores)[::-1][:k]
    return float(y_true[order].mean())


def evaluate_scores(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    pred = (scores >= 0.5).astype(int)
    return {
        "auc": float(roc_auc_score(y_true, scores)),
        "f1": float(f1_score(y_true, pred)),
        "brier": float(brier_score_loss(y_true, scores)),
        "p_at_20": precision_at_fraction(y_true, scores),
    }


def train_attention(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    torch.manual_seed(seed)
    model = TemporalAttentionRiskModel(feature_dim=x_train.shape[-1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()
    xt = torch.tensor(x_train, dtype=torch.float32)
    yt = torch.tensor(y_train, dtype=torch.float32)
    for _ in range(220):
        optimizer.zero_grad()
        logits, _ = model(xt)
        loss = loss_fn(logits, yt)
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        logits, weights = model(torch.tensor(x_test, dtype=torch.float32))
        scores = torch.sigmoid(logits).numpy()
    return scores, weights.numpy()


def run_experiments() -> tuple[pd.DataFrame, dict[str, object]]:
    rows = []
    attention_weights = []
    for seed in range(N_SEEDS):
        x, y = generate_dataset(1000 + seed)
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30, stratify=y, random_state=seed)
        z_train = aggregate_features(x_train)
        z_test = aggregate_features(x_test)
        scaler = StandardScaler()
        z_train = scaler.fit_transform(z_train)
        z_test = scaler.transform(z_test)

        lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)
        lr.fit(z_train, y_train)
        lr_scores = lr.predict_proba(z_test)[:, 1]
        rows.append({"seed": seed, "model": "Logistic regression", **evaluate_scores(y_test, lr_scores)})

        gb = GradientBoostingClassifier(n_estimators=90, max_depth=2, learning_rate=0.05, random_state=seed)
        gb.fit(z_train, y_train)
        gb_scores = gb.predict_proba(z_test)[:, 1]
        rows.append({"seed": seed, "model": "Gradient boosting", **evaluate_scores(y_test, gb_scores)})

        att_scores, weights = train_attention(x_train, y_train, x_test, seed)
        rows.append({"seed": seed, "model": "Temporal attention", **evaluate_scores(y_test, att_scores)})
        attention_weights.append(weights.mean(axis=0))

    result = pd.DataFrame(rows)
    summary = result.groupby("model")[["auc", "f1", "brier", "p_at_20"]].agg(["mean", "std"])
    best = result.groupby("model")["auc"].mean().sort_values(ascending=False)
    meta = {
        "n_students": N_STUDENTS,
        "n_weeks": N_WEEKS,
        "n_seeds": N_SEEDS,
        "best_model_by_auc": best.index[0],
        "attention_weight_mean": np.vstack(attention_weights).mean(axis=0).round(4).tolist(),
        "summary": {
            model: {
                metric: {
                    "mean": float(summary.loc[model, (metric, "mean")]),
                    "std": float(summary.loc[model, (metric, "std")]),
                }
                for metric in ["auc", "f1", "brier", "p_at_20"]
            }
            for model in summary.index
        },
    }
    return result, meta


def fmt(meta: dict[str, object], model: str, metric: str) -> str:
    value = meta["summary"][model][metric]
    return f"{value['mean']:.3f} +/- {value['std']:.3f}"


def build_paper(meta: dict[str, object]) -> str:
    weights = ", ".join(f"week {idx + 1}: {value:.2f}" for idx, value in enumerate(meta["attention_weight_mean"]))
    best_model = str(meta["best_model_by_auc"])
    best_auc = fmt(meta, best_model, "auc")
    attention_auc = fmt(meta, "Temporal attention", "auc")
    if best_model == "Temporal attention":
        headline = (
            f"The temporal-attention model is the strongest model by mean AUC in this run, with AUC {attention_auc}. "
            "This supports the limited synthetic-benchmark claim that temporal weighting improves the tested baselines."
        )
        claim_status = "supported for the synthetic benchmark only."
    else:
        headline = (
            f"{best_model} is the strongest model by mean AUC in this run, with AUC {best_auc}. "
            f"Temporal attention remains competitive at AUC {attention_auc}, but this experiment does not support "
            "a superiority claim for the attention model."
        )
        claim_status = "not supported by this run; temporal attention is competitive but not best by mean AUC."
    table = "\n".join(
        [
            "| Model | AUC | F1 | Brier | P@20 |",
            "|---|---:|---:|---:|---:|",
            *[
                f"| {model} | {fmt(meta, model, 'auc')} | {fmt(meta, model, 'f1')} | "
                f"{fmt(meta, model, 'brier')} | {fmt(meta, model, 'p_at_20')} |"
                for model in ["Logistic regression", "Gradient boosting", "Temporal attention"]
            ],
        ]
    )
    return f"""# Temporal Attention for Early Student Learning-Risk Prediction from Sparse Quiz Records

Format target: ieee

## Abstract

Early warning systems for student support often require rich clickstream or demographic data that are not available in ordinary classroom settings. This paper studies a narrower question: whether the first four weekly quiz records are sufficient to flag students who are likely to need additional support. We implement a reproducible synthetic benchmark with {meta['n_students']} students, four observed quiz weeks, and five random train-test splits. We compare logistic regression, gradient boosting, and a lightweight temporal-attention classifier. The temporal-attention model obtains an AUC of {fmt(meta, 'Temporal attention', 'auc')} and P@20 of {fmt(meta, 'Temporal attention', 'p_at_20')}. The comparison is not a claim about deployment readiness because the benchmark is synthetic, but it provides a concrete, auditable experiment for evaluating the modeling pipeline.

## Introduction

Many educational early-warning systems depend on learning-management logs, prior GPA, attendance, or demographic variables. Those signals can be unavailable, sensitive, or administratively difficult to connect. Quiz records are simpler: most courses already collect scores, submission timing, and question-level correctness. The technical problem is that early quiz records are sparse and noisy. A model must make useful predictions from only a few observations while remaining interpretable enough for instructors.

This demo paper makes three limited contributions. First, it defines a minimal quiz-only risk-prediction task that uses the first four weekly quizzes to predict end-of-course risk. Second, it implements a reproducible benchmark comparing two aggregate-feature baselines against a temporal-attention model. Third, it reports claim-evidence status explicitly, distinguishing results supported by the generated experiment from limitations that require real classroom data.

## Related Work

Educational risk prediction has commonly used logistic regression, tree models, and neural sequence models. Logistic regression remains attractive because it is stable and interpretable on small cohorts. Gradient-boosted trees often improve nonlinear decision boundaries but can obscure which weekly signals matter. Recurrent and attention-based models can use temporal structure directly, but they are harder to justify without sufficient data. This paper does not claim novelty over the full educational-data-mining literature; it is a controlled scaffold for testing whether AutoScholarLoop can produce an evidence-grounded manuscript from a runnable experiment.

## Method

Each student is represented by four weekly quiz vectors. A weekly vector contains normalized score, normalized submission delay, question accuracy, and a missing-submission indicator. The baselines transform the four-week sequence into aggregate features: mean, standard deviation, last observed value, and first-to-last trend for each signal. Logistic regression is trained with balanced class weights. Gradient boosting uses shallow trees to limit overfitting.

The temporal-attention model keeps the weekly sequence structure. It learns a query vector that assigns a softmax weight to each week, forms a weighted context vector, and feeds that context into a logistic output layer. This model is deliberately small: it has only a query vector and a linear classifier, so the attention weights remain directly inspectable.

## Experimental Setup

The benchmark is synthetic because no public classroom quiz dataset is bundled with the repository. For each of five seeds, the generator samples latent student ability, diligence, weekly difficulty, score noise, submission delay, and missingness. The risk label is derived from final mean score, engagement, and later delay. Each seed uses a stratified 70/30 train-test split. Models are evaluated using AUC, F1, Brier score, and precision among the top 20 percent highest-risk predictions.

All experiment code is stored in `examples/research_grade_learning_risk.py` and the generated run workspace. The exact per-seed metrics are saved as `results/metrics_by_seed.csv`, and aggregate statistics are saved as `results/summary.json`.

## Results

{table}

{headline} The learned average attention distribution is {weights}. This indicates that later observed quizzes receive more weight than the earliest quiz, which is consistent with the task design. The result is not evidence that any model will improve outcomes in a real classroom.

## Claim-Evidence Status

- Claim: Temporal attention improves quiz-only early-risk prediction on the generated synthetic benchmark.
  Support: `results/metrics_by_seed.csv` and `results/summary.json`; mean AUC is {fmt(meta, 'Temporal attention', 'auc')}.
  Status: {claim_status}
- Claim: The model is lightweight and inspectable.
  Support: the implementation uses a learned query vector plus one linear classifier, and stores average attention weights.
  Status: supported by code inspection.
- Claim: The method is ready for classroom deployment.
  Support: no real classroom dataset, intervention study, fairness audit, or calibration review is included.
  Status: unsupported.

## Limitations

- The dataset is synthetic and cannot establish real-world effectiveness.
- Hyperparameter tuning is intentionally minimal.
- The benchmark does not include demographic fairness, instructor actionability, or longitudinal intervention outcomes.
- The attention model is small by design; stronger sequence models could outperform it on larger datasets.
- Citations are described at the level of research areas rather than verified bibliographic entries.

## Conclusion

This run is materially stronger than the earlier demo because it contains a real executable experiment, saved metrics, a generated PDF, and explicit claim-evidence boundaries. The resulting paper is still not submission-ready because it lacks real data and verified references. It is, however, a reproducible research-style artifact that the main AutoScholarLoop pipeline should aim to produce automatically.

## References

[1] Educational data mining work on early warning and student-success prediction.
[2] Learning analytics studies using course activity and assessment traces.
[3] Sequence modeling and attention mechanisms for student modeling and knowledge tracing.
"""


def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "results").mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "paper").mkdir(parents=True, exist_ok=True)
    result, meta = run_experiments()
    result.to_csv(WORKSPACE / "results" / "metrics_by_seed.csv", index=False)
    (WORKSPACE / "results" / "summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    paper = build_paper(meta)
    draft_path = WORKSPACE / "paper" / "final_draft.md"
    draft_path.write_text(paper, encoding="utf-8")
    write_format_profile(WORKSPACE / "paper" / "format_profile.json", get_paper_format("ieee"))
    tex_path = write_latex_from_markdown(draft_path, WORKSPACE / "paper" / "main.tex", paper_format_key="ieee")
    compile_result = compile_latex(tex_path)
    (WORKSPACE / "paper" / "compile_result.json").write_text(json.dumps(compile_result, indent=2), encoding="utf-8")
    print(json.dumps({"workspace": str(WORKSPACE), "pdf": compile_result.get("pdf"), "compiled": compile_result.get("compiled")}, indent=2))


if __name__ == "__main__":
    main()
