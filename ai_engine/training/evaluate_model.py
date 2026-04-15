from __future__ import annotations

import json
import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from ai_engine.training.config import ARTIFACTS_DIR, EVAL_CSV_REPORT, EVAL_JSON_REPORT, PAIR_VAL_FILE


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


def _collect_metrics(true_labels: list[int], pred_labels: list[int], absolute_errors: list[float]) -> dict:
    accuracy = sum(int(t == p) for t, p in zip(true_labels, pred_labels)) / max(1, len(true_labels))
    mae = float(np.mean(absolute_errors)) if absolute_errors else 1.0
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels,
        pred_labels,
        average="binary",
        zero_division=0,
    )
    cm = confusion_matrix(true_labels, pred_labels, labels=[0, 1]).tolist()
    return {
        "accuracy_at_0_5": accuracy,
        "similarity_mae": mae,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": cm,
    }


def _write_reports(metrics: dict) -> None:
    EVAL_JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    EVAL_JSON_REPORT.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    with EVAL_CSV_REPORT.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["accuracy_at_0_5", "similarity_mae", "precision", "recall", "f1", "tn", "fp", "fn", "tp"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "accuracy_at_0_5": f"{metrics['accuracy_at_0_5']:.6f}",
                "similarity_mae": f"{metrics['similarity_mae']:.6f}",
                "precision": f"{metrics['precision']:.6f}",
                "recall": f"{metrics['recall']:.6f}",
                "f1": f"{metrics['f1']:.6f}",
                "tn": metrics["confusion_matrix"][0][0],
                "fp": metrics["confusion_matrix"][0][1],
                "fn": metrics["confusion_matrix"][1][0],
                "tp": metrics["confusion_matrix"][1][1],
            }
        )


def evaluate() -> None:
    from sentence_transformers import SentenceTransformer

    pairs = _load_pairs(PAIR_VAL_FILE)
    if not pairs:
        raise SystemExit("ملف val pairs غير موجود أو فاضي.")

    model_path = ARTIFACTS_DIR if ARTIFACTS_DIR.exists() else "sentence-transformers/all-mpnet-base-v2"
    model = SentenceTransformer(str(model_path))

    true_labels: list[int] = []
    pred_labels: list[int] = []
    absolute_errors: list[float] = []

    for row in pairs:
        resume_vec = model.encode([row["resume_text"]], normalize_embeddings=True)[0]
        job_vec = model.encode([row["job_text"]], normalize_embeddings=True)[0]
        sim = _cosine(np.asarray(resume_vec), np.asarray(job_vec))

        y_true = 1 if float(row["label"]) >= 0.5 else 0
        y_pred = 1 if sim >= 0.5 else 0
        true_labels.append(y_true)
        pred_labels.append(y_pred)
        absolute_errors.append(abs(float(row["label"]) - sim))

    metrics = _collect_metrics(true_labels, pred_labels, absolute_errors)
    _write_reports(metrics)

    print(f"[METRIC] accuracy@0.5 = {metrics['accuracy_at_0_5']:.4f}")
    print(f"[METRIC] similarity_mae = {metrics['similarity_mae']:.4f}")
    print(f"[METRIC] precision = {metrics['precision']:.4f}")
    print(f"[METRIC] recall = {metrics['recall']:.4f}")
    print(f"[METRIC] f1 = {metrics['f1']:.4f}")
    print(f"[METRIC] confusion_matrix = {metrics['confusion_matrix']}")
    print(f"[REPORT] json = {EVAL_JSON_REPORT}")
    print(f"[REPORT] csv = {EVAL_CSV_REPORT}")


if __name__ == "__main__":
    evaluate()
