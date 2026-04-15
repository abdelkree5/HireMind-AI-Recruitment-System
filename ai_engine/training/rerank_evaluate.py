from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import numpy as np

from ai_engine.training.config import (
    ARTIFACTS_DIR,
    CROSS_ENCODER_MODEL,
    RAW_JOB_FILE,
    RAW_RESUME_FILE,
    RERANK_HYBRID_ALPHA,
    RERANK_CSV_REPORT,
    RERANK_JSON_REPORT,
    RERANK_TOP_K,
)
from ai_engine.training.text_cleaning import compact_text, normalize_text

MAX_RESUMES_EVAL = 150
RANDOM_SEED = 42


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
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


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return 0.0 if denom == 0.0 else float(np.dot(a, b) / denom)


def _minmax(values: np.ndarray) -> np.ndarray:
    low = float(np.min(values))
    high = float(np.max(values))
    if high - low < 1e-9:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def _ranking_metrics(hits: list[int], rr_scores: list[float]) -> dict:
    return {
        "top1_accuracy": float(np.mean(hits) if hits else 0.0),
        "mrr": float(np.mean(rr_scores) if rr_scores else 0.0),
    }


def evaluate_reranking() -> None:
    from sentence_transformers import CrossEncoder, SentenceTransformer

    resumes = _read_jsonl(RAW_RESUME_FILE)
    jobs = _read_jsonl(RAW_JOB_FILE)
    if not resumes or not jobs:
        raise SystemExit("raw resumes/jobs ناقصين. شغل download_datasets.py الأول.")

    random.seed(RANDOM_SEED)
    if len(resumes) > MAX_RESUMES_EVAL:
        resumes = random.sample(resumes, MAX_RESUMES_EVAL)

    bi_model_path = str(ARTIFACTS_DIR) if ARTIFACTS_DIR.exists() else "sentence-transformers/all-MiniLM-L6-v2"
    bi_encoder = SentenceTransformer(bi_model_path)
    cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)

    job_cache: list[dict] = []
    job_texts: list[str] = []
    for job in jobs:
        text = compact_text(f"{job.get('title', '')}. {job.get('description', '')}")
        job_cache.append(
            {
                "text": text,
                "tokens": set(normalize_text(text).split()),
                "skills": _extract_skills(job),
            }
        )
        job_texts.append(text)

    job_embeddings = bi_encoder.encode(job_texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=128)

    hits_bi: list[int] = []
    hits_ce: list[int] = []
    hits_hybrid: list[int] = []
    rr_bi: list[float] = []
    rr_ce: list[float] = []
    rr_hybrid: list[float] = []

    for resume in resumes:
        resume_text = compact_text(resume.get("text", ""))
        if not resume_text:
            continue

        resume_tokens = set(normalize_text(resume_text).split())
        resume_skills = _extract_skills(resume)

        # pseudo-ground-truth: أعلى lexical+skills score
        lexical_scores = [_score_with_cache(resume_tokens, resume_skills, item["tokens"], item["skills"]) for item in job_cache]
        true_idx = int(np.argmax(lexical_scores))

        resume_emb = bi_encoder.encode([resume_text], normalize_embeddings=True, convert_to_numpy=True)[0]
        sims = np.dot(job_embeddings, resume_emb)
        bi_ranked_indices = np.argsort(sims)[::-1]
        bi_idx = int(bi_ranked_indices[0])

        top_k_indices = np.argsort(sims)[::-1][:RERANK_TOP_K]
        pairs = [(resume_text, job_texts[idx]) for idx in top_k_indices]
        ce_scores = np.asarray(cross_encoder.predict(pairs), dtype=np.float32)
        ce_best_idx = int(top_k_indices[int(np.argmax(ce_scores))])

        bi_topk_scores = np.asarray([sims[idx] for idx in top_k_indices], dtype=np.float32)
        hybrid_scores = RERANK_HYBRID_ALPHA * _minmax(bi_topk_scores) + (1.0 - RERANK_HYBRID_ALPHA) * _minmax(ce_scores)
        hybrid_best_idx = int(top_k_indices[int(np.argmax(hybrid_scores))])

        hits_bi.append(1 if bi_idx == true_idx else 0)
        hits_ce.append(1 if ce_best_idx == true_idx else 0)
        hits_hybrid.append(1 if hybrid_best_idx == true_idx else 0)

        true_rank_bi = int(np.where(bi_ranked_indices == true_idx)[0][0]) + 1
        rr_bi.append(1.0 / true_rank_bi)

        ce_order = np.argsort(ce_scores)[::-1]
        rr_ce.append(1.0 / (int(np.where(top_k_indices[ce_order] == true_idx)[0][0]) + 1) if true_idx in top_k_indices else 0.0)

        hybrid_order = np.argsort(hybrid_scores)[::-1]
        rr_hybrid.append(1.0 / (int(np.where(top_k_indices[hybrid_order] == true_idx)[0][0]) + 1) if true_idx in top_k_indices else 0.0)

        if len(hits_bi) % 25 == 0:
            print(f"[RERANK] processed resumes: {len(hits_bi)}/{len(resumes)}")

    base = _ranking_metrics(hits_bi, rr_bi)
    ce_only = _ranking_metrics(hits_ce, rr_ce)
    rerank = _ranking_metrics(hits_hybrid, rr_hybrid)

    report = {
        "top_k": RERANK_TOP_K,
        "base_bi_encoder": base,
        "cross_encoder_only": ce_only,
        "with_cross_encoder_rerank": rerank,
        "delta": {
            "top1_accuracy": rerank["top1_accuracy"] - base["top1_accuracy"],
            "mrr": rerank["mrr"] - base["mrr"],
        },
    }

    RERANK_JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    RERANK_JSON_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    with RERANK_CSV_REPORT.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["mode", "top1_accuracy", "mrr"])
        writer.writeheader()
        for mode_name, metrics in (("bi_encoder", base), ("cross_encoder_only", ce_only), ("bi_plus_cross_hybrid", rerank)):
            writer.writerow(
                {
                    "mode": mode_name,
                    "top1_accuracy": f"{metrics['top1_accuracy']:.6f}",
                    "mrr": f"{metrics['mrr']:.6f}",
                }
            )

    print(f"[RERANK] base = {base}")
    print(f"[RERANK] rerank = {rerank}")
    print(f"[RERANK] delta = {report['delta']}")
    print(f"[RERANK] json report: {RERANK_JSON_REPORT}")
    print(f"[RERANK] csv report: {RERANK_CSV_REPORT}")


if __name__ == "__main__":
    evaluate_reranking()
