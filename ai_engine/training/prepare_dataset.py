from __future__ import annotations

import json
import random
from pathlib import Path

from ai_engine.training.config import PAIR_ALL_FILE, PAIR_TRAIN_FILE, PAIR_VAL_FILE, RAW_JOB_FILE, RAW_RESUME_FILE
from ai_engine.training.text_cleaning import compact_text, normalize_text

RANDOM_SEED = 42
VAL_RATIO = 0.15
MAX_RESUMES = 2500


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _extract_skills(record: dict) -> set[str]:
    skills = record.get("skills")
    if isinstance(skills, list):
        return {normalize_text(str(item)) for item in skills if str(item).strip()}
    return set()


def _build_positive_score(resume: dict, job: dict) -> float:
    resume_text = normalize_text(resume.get("text", ""))
    job_text = normalize_text(f"{job.get('title', '')} {job.get('description', '')}")

    # approximation بسيطة لجودة الزوج قبل التدريب الفعلي
    overlap = len(set(resume_text.split()) & set(job_text.split()))
    base = min(1.0, overlap / 25.0)

    resume_skills = _extract_skills(resume)
    job_skills = _extract_skills(job)
    skill_ratio = 0.0 if not job_skills else len(resume_skills & job_skills) / len(job_skills)
    return min(1.0, 0.65 * base + 0.35 * skill_ratio)


def _score_with_cache(resume_tokens: set[str], resume_skills: set[str], job_tokens: set[str], job_skills: set[str]) -> float:
    overlap = len(resume_tokens & job_tokens)
    base = min(1.0, overlap / 25.0)
    skill_ratio = 0.0 if not job_skills else len(resume_skills & job_skills) / len(job_skills)
    return min(1.0, 0.65 * base + 0.35 * skill_ratio)


def prepare() -> None:
    random.seed(RANDOM_SEED)

    resumes = _read_jsonl(RAW_RESUME_FILE)
    jobs = _read_jsonl(RAW_JOB_FILE)
    if not resumes or not jobs:
        raise SystemExit("الداتا الخام ناقصة. شغل download_datasets.py أو وفر ملفات raw محلية.")

    pairs: list[dict] = []
    sample_jobs = jobs if len(jobs) < 500 else random.sample(jobs, 500)

    # هنا بنحدد سقف للـ resumes عشان الزمن يفضل عملي في التشغيل المحلي
    if len(resumes) > MAX_RESUMES:
        resumes = random.sample(resumes, MAX_RESUMES)

    # cache للوظائف لتجنب إعادة التطبيع كل مرة
    job_cache: list[dict] = []
    for job in sample_jobs:
        job_text = compact_text(f"{job.get('title', '')}. {job.get('description', '')}")
        job_cache.append(
            {
                "job": job,
                "text": job_text,
                "tokens": set(normalize_text(job_text).split()),
                "skills": _extract_skills(job),
            }
        )

    for index, resume in enumerate(resumes, start=1):
        resume_text = compact_text(resume.get("text", ""))
        if not resume_text:
            continue

        resume_tokens = set(normalize_text(resume_text).split())
        resume_skills = _extract_skills(resume)

        scored_jobs: list[tuple[float, dict]] = []
        for item in job_cache:
            score = _score_with_cache(resume_tokens, resume_skills, item["tokens"], item["skills"])
            scored_jobs.append((score, item))

        scored_jobs.sort(key=lambda pair: pair[0], reverse=True)
        positive_score, positive_item = scored_jobs[0]
        positive_text = positive_item["text"]

        pairs.append(
            {
                "resume_text": resume_text,
                "job_text": positive_text,
                "label": max(0.7, positive_score),
            }
        )

        # hard negative: من أعلى مرشحين بس أقل score من الإيجابي
        hard_pool = [entry for entry in scored_jobs[1:8] if entry[0] < positive_score]
        if hard_pool:
            negative_score, negative_item = random.choice(hard_pool)
        else:
            negative_score, negative_item = random.choice(scored_jobs[max(1, len(scored_jobs) // 2):])
        negative_text = negative_item["text"]

        pairs.append(
            {
                "resume_text": resume_text,
                "job_text": negative_text,
                "label": min(0.35, negative_score),
            }
        )

        if index % 250 == 0:
            print(f"[INFO] processed resumes: {index}/{len(resumes)}")

    random.shuffle(pairs)

    PAIR_ALL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PAIR_ALL_FILE.open("w", encoding="utf-8") as all_file:
        for row in pairs:
            all_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    split_index = int(len(pairs) * (1.0 - VAL_RATIO))
    train_rows = pairs[:split_index]
    val_rows = pairs[split_index:]

    PAIR_TRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PAIR_TRAIN_FILE.open("w", encoding="utf-8") as train_file:
        for row in train_rows:
            train_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    with PAIR_VAL_FILE.open("w", encoding="utf-8") as val_file:
        for row in val_rows:
            val_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[DONE] train pairs: {len(train_rows)} -> {PAIR_TRAIN_FILE}")
    print(f"[DONE] val pairs: {len(val_rows)} -> {PAIR_VAL_FILE}")
    print(f"[DONE] all pairs: {len(pairs)} -> {PAIR_ALL_FILE}")


if __name__ == "__main__":
    prepare()
