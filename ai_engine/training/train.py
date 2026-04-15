from __future__ import annotations

"""تدريب/فاين تيوننج مبدئي لنموذج sentence-transformers.

الفكرة هنا إننا نستخدم بيانات CVs + job descriptions حقيقية.
لازم قبل التشغيل نجهز ملف train.jsonl فيه أزواج أو triplets مناسبة.
"""

from pathlib import Path

from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

from ai_engine.config import BASE_MODEL_NAME

DATA_FILE = Path(__file__).with_name("train.jsonl")
OUTPUT_DIR = Path(__file__).with_name("artifacts")


def load_training_examples() -> list[InputExample]:
    if not DATA_FILE.exists():
        return []

    examples: list[InputExample] = []
    for line in DATA_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        candidate_text, job_text, label = parts
        examples.append(InputExample(texts=[candidate_text, job_text], label=float(label)))
    return examples


def train() -> None:
    examples = load_training_examples()
    if not examples:
        raise SystemExit("ملف التدريب مش موجود أو فاضي. جهز train.jsonl الأول.")

    model = SentenceTransformer(BASE_MODEL_NAME)
    dataloader = DataLoader(examples, shuffle=True, batch_size=8)
    loss = losses.CosineSimilarityLoss(model)

    model.fit(
        train_objectives=[(dataloader, loss)],
        epochs=1,
        warmup_steps=10,
        output_path=str(OUTPUT_DIR),
        show_progress_bar=True,
    )


if __name__ == "__main__":
    train()
