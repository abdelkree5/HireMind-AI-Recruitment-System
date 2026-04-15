from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from ai_engine.training.config import ARTIFACTS_DIR, CROSS_ENCODER_MODEL, RAW_JOB_FILE, RAW_RESUME_FILE
from ai_engine.training.text_cleaning import compact_text, normalize_text

MAX_RESUMES = 120
TOPK_GRID = [5, 10, 20]
ALPHA_GRID = [0.5, 0.6, 0.7, 0.8, 0.9]
RANDOM_SEED = 42


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _extract_skills(record: dict) -> set[str]:
    skills = record.get("skills")
    if isinstance(skills, list):
        return {normalize_text(str(item)) for item in skills if str(item).strip()}
    return set()


def _score_with_cache(resume_tokens: set[str], resume_skills: set[str], job_tokens: set[str], job_skills: set[str]) -> float:
    overlap = len(resume_tokens & job_tokens)
    base = min(1.0, overlap / 25.0)
    skill_ratio = 0.0 if not job_skills else len(resume_skills & job_skills) / len(job_skills)
    return min(1.0, 0.65 * base + 0.35 * skill_ratio)


def _minmax(values: np.ndarray) -> np.ndarray:
    low = float(np.min(values))
    high = float(np.max(values))
    if high - low < 1e-9:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def main() -> None:
    resumes = _read_jsonl(RAW_RESUME_FILE)
    jobs = _read_jsonl(RAW_JOB_FILE)
    if not resumes or not jobs:
        raise SystemExit("raw data missing")

    random.seed(RANDOM_SEED)
    if len(resumes) > MAX_RESUMES:
        resumes = random.sample(resumes, MAX_RESUMES)

    bi_model = SentenceTransformer(str(ARTIFACTS_DIR))
    ce_model = CrossEncoder(CROSS_ENCODER_MODEL)

    job_texts = [compact_text(f"{job.get('title', '')}. {job.get('description', '')}") for job in jobs]
    job_tokens = [set(normalize_text(text).split()) for text in job_texts]
    job_skills = [_extract_skills(job) for job in jobs]
    job_embs = bi_model.encode(job_texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=128)

    prepared = []
    for resume in resumes:
        text = compact_text(resume.get("text", ""))
        if not text:
            continue
        rt = set(normalize_text(text).split())
        rs = _extract_skills(resume)
        lexical = np.asarray([_score_with_cache(rt, rs, jt, js) for jt, js in zip(job_tokens, job_skills)], dtype=np.float32)
        true_idx = int(np.argmax(lexical))
        emb = bi_model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
        sims = np.dot(job_embs, emb)
        ranked = np.argsort(sims)[::-1]
        prepared.append((text, true_idx, sims, ranked))

    base_hits = [1 if int(item[3][0]) == int(item[1]) else 0 for item in prepared]
    base_acc = float(np.mean(base_hits)) if base_hits else 0.0

    best = {"top_k": None, "alpha": None, "accuracy": -1.0}

    for top_k in TOPK_GRID:
        for alpha in ALPHA_GRID:
            hits: list[int] = []
            for text, true_idx, sims, ranked in prepared:
                top_idx = ranked[:top_k]
                pairs = [(text, job_texts[int(idx)]) for idx in top_idx]
                ce = np.asarray(ce_model.predict(pairs), dtype=np.float32)
                bi = np.asarray([sims[int(idx)] for idx in top_idx], dtype=np.float32)
                hybrid = alpha * _minmax(bi) + (1.0 - alpha) * _minmax(ce)
                pred_idx = int(top_idx[int(np.argmax(hybrid))])
                hits.append(1 if pred_idx == true_idx else 0)
            acc = float(np.mean(hits)) if hits else 0.0
            if acc > best["accuracy"]:
                best = {"top_k": top_k, "alpha": alpha, "accuracy": acc}
            print(f"[TUNE] top_k={top_k} alpha={alpha:.1f} acc={acc:.4f}")

    print(f"[TUNE] base_acc={base_acc:.4f}")
    print(f"[TUNE] best={best}")


if __name__ == "__main__":
    main()
