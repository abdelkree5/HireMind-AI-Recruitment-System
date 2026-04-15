from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from ai_engine.training.config import ARTIFACTS_DIR, BASE_MODEL, PAIR_VAL_FILE


def _load_pairs(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return 0.0 if denom == 0.0 else float(np.dot(a, b) / denom)


def _evaluate(model_name_or_path: str, pairs: list[dict]) -> tuple[float, float]:
    print(f"[INFO] evaluating model: {model_name_or_path}")
    model = SentenceTransformer(model_name_or_path)
    resumes = [row["resume_text"] for row in pairs]
    jobs = [row["job_text"] for row in pairs]

    resume_vecs = model.encode(resumes, normalize_embeddings=True, convert_to_numpy=True, batch_size=64)
    job_vecs = model.encode(jobs, normalize_embeddings=True, convert_to_numpy=True, batch_size=64)

    true_labels: list[int] = []
    pred_labels: list[int] = []
    abs_errors: list[float] = []

    for row, rv, jv in zip(pairs, resume_vecs, job_vecs):
        sim = _cosine(np.asarray(rv), np.asarray(jv))

        y_true = 1 if float(row["label"]) >= 0.5 else 0
        y_pred = 1 if sim >= 0.5 else 0
        true_labels.append(y_true)
        pred_labels.append(y_pred)
        abs_errors.append(abs(float(row["label"]) - sim))

    accuracy = sum(int(t == p) for t, p in zip(true_labels, pred_labels)) / max(1, len(true_labels))
    mae = float(np.mean(abs_errors)) if abs_errors else 1.0
    return accuracy, mae


def main() -> None:
    if not PAIR_VAL_FILE.exists():
        raise SystemExit("ملف validation مش موجود. شغل prepare_dataset الأول.")

    pairs = _load_pairs(PAIR_VAL_FILE)
    if not pairs:
        raise SystemExit("validation pairs فاضية.")

    base_acc, base_mae = _evaluate(BASE_MODEL, pairs)

    if not ARTIFACTS_DIR.exists():
        raise SystemExit("artifacts مش موجودة. شغل train_sentence_model الأول.")

    tuned_acc, tuned_mae = _evaluate(str(ARTIFACTS_DIR), pairs)

    print(f"[BASE] accuracy@0.5={base_acc:.4f} | similarity_mae={base_mae:.4f}")
    print(f"[TUNED] accuracy@0.5={tuned_acc:.4f} | similarity_mae={tuned_mae:.4f}")
    print(f"[DELTA] accuracy={(tuned_acc - base_acc):+.4f} | mae={(tuned_mae - base_mae):+.4f}")


if __name__ == "__main__":
    main()
