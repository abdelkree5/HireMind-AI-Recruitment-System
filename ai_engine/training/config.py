from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"

BASE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ترتيب الأوزان في التقييم النهائي
WEIGHTS = {
    "semantic": 0.55,
    "skill": 0.25,
    "title": 0.10,
    "context": 0.10,
}

# datasets ممكن تتغير مع الوقت، فبنحط قائمة بدائل
DATASET_CANDIDATES = [
    {
        "name": "cnamuangtoun/resume-job-description-fit",
        "split": "train",
        "kind": "resume",
    },
    {
        "name": "cnamuangtoun/resume-job-description-fit",
        "split": "train",
        "kind": "job",
    },
    {
        "name": "datasetmaster/resumes",
        "split": "train",
        "kind": "resume",
    },
    {
        "name": "rohankrishna99/job-descriptions-dataset-mini",
        "split": "train",
        "kind": "job",
    },
]

RAW_RESUME_FILE = RAW_DIR / "resumes.jsonl"
RAW_JOB_FILE = RAW_DIR / "jobs.jsonl"
PAIR_ALL_FILE = PROCESSED_DIR / "pairs_all.jsonl"
PAIR_TRAIN_FILE = PROCESSED_DIR / "pairs_train.jsonl"
PAIR_VAL_FILE = PROCESSED_DIR / "pairs_val.jsonl"

EVAL_JSON_REPORT = REPORTS_DIR / "evaluation_report.json"
EVAL_CSV_REPORT = REPORTS_DIR / "evaluation_report.csv"
CV_JSON_REPORT = REPORTS_DIR / "cross_validation_report.json"
CV_CSV_REPORT = REPORTS_DIR / "cross_validation_report.csv"
RERANK_JSON_REPORT = REPORTS_DIR / "rerank_report.json"
RERANK_CSV_REPORT = REPORTS_DIR / "rerank_report.csv"

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_TOP_K = 5
RERANK_HYBRID_ALPHA = 0.8
