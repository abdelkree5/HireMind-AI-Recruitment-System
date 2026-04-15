from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import KFold

from ai_engine.training.config import BASE_MODEL, CV_CSV_REPORT, CV_JSON_REPORT, PAIR_ALL_FILE

N_SPLITS = 3
EPOCHS_PER_FOLD = 1
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
RANDOM_STATE = 42
MAX_PAIRS_FOR_CV = 1800


def _load_pairs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return 0.0 if denom == 0.0 else float(np.dot(a, b) / denom)


def _metrics(true_labels: list[int], pred_labels: list[int], abs_errors: list[float]) -> dict:
    accuracy = sum(int(t == p) for t, p in zip(true_labels, pred_labels)) / max(1, len(true_labels))
    mae = float(np.mean(abs_errors)) if abs_errors else 1.0
    precision, recall, f1, _ = precision_recall_fscore_support(true_labels, pred_labels, average="binary", zero_division=0)
    cm = confusion_matrix(true_labels, pred_labels, labels=[0, 1]).tolist()
    return {
        "accuracy_at_0_5": float(accuracy),
        "similarity_mae": float(mae),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": cm,
    }


def run_cross_validation() -> None:
    from sentence_transformers import InputExample, SentenceTransformer, losses
    from torch.utils.data import DataLoader

    pairs = _load_pairs(PAIR_ALL_FILE)
    if not pairs:
        raise SystemExit("pairs_all.jsonl مش موجود. شغل prepare_dataset.py الأول.")

    if len(pairs) > MAX_PAIRS_FOR_CV:
        rng = np.random.default_rng(RANDOM_STATE)
        selected_indices = rng.choice(len(pairs), size=MAX_PAIRS_FOR_CV, replace=False)
        pairs = [pairs[int(idx)] for idx in selected_indices]
        print(f"[CV] using sampled pairs: {len(pairs)}")

    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    fold_reports: list[dict] = []

    indices = np.arange(len(pairs))
    for fold_index, (train_idx, val_idx) in enumerate(kf.split(indices), start=1):
        print(f"[CV] fold {fold_index}/{N_SPLITS} - training")

        train_examples = [
            InputExample(texts=[pairs[i]["resume_text"], pairs[i]["job_text"]], label=float(pairs[i]["label"]))
            for i in train_idx
        ]

        model = SentenceTransformer(BASE_MODEL)
        dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)
        train_loss = losses.CosineSimilarityLoss(model)
        model.fit(
            train_objectives=[(dataloader, train_loss)],
            epochs=EPOCHS_PER_FOLD,
            warmup_steps=max(10, len(dataloader) // 10),
            optimizer_params={"lr": LEARNING_RATE},
            show_progress_bar=False,
        )

        print(f"[CV] fold {fold_index}/{N_SPLITS} - evaluating")
        true_labels: list[int] = []
        pred_labels: list[int] = []
        abs_errors: list[float] = []

        val_rows = [pairs[i] for i in val_idx]
        resume_vecs = model.encode([row["resume_text"] for row in val_rows], normalize_embeddings=True, convert_to_numpy=True, batch_size=64)
        job_vecs = model.encode([row["job_text"] for row in val_rows], normalize_embeddings=True, convert_to_numpy=True, batch_size=64)

        for row, rv, jv in zip(val_rows, resume_vecs, job_vecs):
            sim = _cosine(np.asarray(rv), np.asarray(jv))
            y_true = 1 if float(row["label"]) >= 0.5 else 0
            y_pred = 1 if sim >= 0.5 else 0
            true_labels.append(y_true)
            pred_labels.append(y_pred)
            abs_errors.append(abs(float(row["label"]) - sim))

        fold_metrics = _metrics(true_labels, pred_labels, abs_errors)
        fold_metrics["fold"] = fold_index
        fold_reports.append(fold_metrics)
        print(
            f"[CV] fold {fold_index} done | accuracy={fold_metrics['accuracy_at_0_5']:.4f} "
            f"f1={fold_metrics['f1']:.4f} mae={fold_metrics['similarity_mae']:.4f}"
        )

    summary = {
        "accuracy_at_0_5_mean": float(np.mean([item["accuracy_at_0_5"] for item in fold_reports])),
        "accuracy_at_0_5_std": float(np.std([item["accuracy_at_0_5"] for item in fold_reports])),
        "f1_mean": float(np.mean([item["f1"] for item in fold_reports])),
        "f1_std": float(np.std([item["f1"] for item in fold_reports])),
        "similarity_mae_mean": float(np.mean([item["similarity_mae"] for item in fold_reports])),
        "similarity_mae_std": float(np.std([item["similarity_mae"] for item in fold_reports])),
    }

    report = {"n_splits": N_SPLITS, "folds": fold_reports, "summary": summary}
    CV_JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    CV_JSON_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    with CV_CSV_REPORT.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["fold", "accuracy_at_0_5", "similarity_mae", "precision", "recall", "f1", "tn", "fp", "fn", "tp"],
        )
        writer.writeheader()
        for fold in fold_reports:
            writer.writerow(
                {
                    "fold": fold["fold"],
                    "accuracy_at_0_5": f"{fold['accuracy_at_0_5']:.6f}",
                    "similarity_mae": f"{fold['similarity_mae']:.6f}",
                    "precision": f"{fold['precision']:.6f}",
                    "recall": f"{fold['recall']:.6f}",
                    "f1": f"{fold['f1']:.6f}",
                    "tn": fold["confusion_matrix"][0][0],
                    "fp": fold["confusion_matrix"][0][1],
                    "fn": fold["confusion_matrix"][1][0],
                    "tp": fold["confusion_matrix"][1][1],
                }
            )

    print(f"[CV] summary: {summary}")
    print(f"[CV] json report: {CV_JSON_REPORT}")
    print(f"[CV] csv report: {CV_CSV_REPORT}")


if __name__ == "__main__":
    run_cross_validation()
