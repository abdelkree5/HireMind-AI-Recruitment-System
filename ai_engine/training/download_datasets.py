from __future__ import annotations

import json
from pathlib import Path

from ai_engine.training.config import DATASET_CANDIDATES, RAW_DIR, RAW_JOB_FILE, RAW_RESUME_FILE


def _safe_get_text(record: dict, keys: list[str]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_resume(record: dict) -> dict | None:
    text = _safe_get_text(
        record,
        ["Resume", "resume", "resume_text", "candidate_resume", "text", "content", "Description"],
    )
    if not text:
        return None
    return {
        "id": str(record.get("id") or record.get("ID") or ""),
        "text": text,
        "title": _safe_get_text(record, ["Category", "title", "job_title", "position"]),
        "skills": _normalize_skills(record),
    }


def _extract_job(record: dict) -> dict | None:
    description_parts = [
        _safe_get_text(record, ["description", "job_description", "job_desc", "jd", "JobDescription", "text", "content"]),
        _safe_get_text(record, ["JobRequirment", "job_requirement", "requirements"]),
        _safe_get_text(record, ["RequiredQual", "required_qualification", "qualifications"]),
    ]
    description = " ".join(part for part in description_parts if part).strip()
    if not description:
        return None
    return {
        "id": str(record.get("id") or record.get("job_id") or ""),
        "title": _safe_get_text(record, ["title", "job_title", "position", "job_role", "Title"]),
        "description": description,
        "skills": _normalize_skills(record),
    }


def _normalize_skills(record: dict) -> list[str]:
    skills = record.get("skills") or record.get("required_skills") or record.get("skill_set")
    if isinstance(skills, list):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    if isinstance(skills, str) and skills.strip():
        separators = [",", "|", ";"]
        normalized = skills
        for separator in separators:
            normalized = normalized.replace(separator, ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]
    return []


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def download() -> None:
    # لو النت مش متاح أو dataset اتغير، السكربت مش هيكسر المشروع وهيسيب تعليمات واضحة
    try:
        from datasets import load_dataset
    except ModuleNotFoundError as exc:
        raise SystemExit("مكتبة datasets مش متثبتة. ثبتها الأول: pip install datasets") from exc

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    resumes: list[dict] = []
    jobs: list[dict] = []

    for candidate in DATASET_CANDIDATES:
        name = candidate["name"]
        split = candidate["split"]
        kind = candidate["kind"]

        try:
            dataset = load_dataset(name, split=split)
        except Exception as exc:
            print(f"[WARN] فشل تحميل {name}: {exc}")
            continue

        for record in dataset:
            parsed = _extract_resume(record) if kind == "resume" else _extract_job(record)
            if not parsed:
                continue
            if kind == "resume":
                resumes.append(parsed)
            else:
                jobs.append(parsed)

        print(f"[INFO] {name} اتحمل بنجاح: resumes={len(resumes)} jobs={len(jobs)}")

    if not resumes and not RAW_RESUME_FILE.exists():
        raise SystemExit(
            "مفيش resumes اتحملت. بديل: حط ملف محلي في ai_engine/training/data/raw/resumes.jsonl"
        )
    if not jobs and not RAW_JOB_FILE.exists():
        raise SystemExit(
            "مفيش job descriptions اتحملت. بديل: حط ai_engine/training/data/raw/jobs.jsonl"
        )

    if resumes:
        _write_jsonl(RAW_RESUME_FILE, resumes)
    if jobs:
        _write_jsonl(RAW_JOB_FILE, jobs)

    print(f"[DONE] raw resumes: {RAW_RESUME_FILE}")
    print(f"[DONE] raw jobs: {RAW_JOB_FILE}")


if __name__ == "__main__":
    download()
