from __future__ import annotations

import json
from pathlib import Path

from sentence_transformers import InputExample

from ai_engine.training.config import ARTIFACTS_DIR, BASE_MODEL, PAIR_TRAIN_FILE

EPOCHS = 2
BATCH_SIZE = 16
LEARNING_RATE = 2e-5


def _load_examples(path: Path) -> list[InputExample]:
    if not path.exists():
        return []

    examples: list[InputExample] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        examples.append(
            InputExample(
                texts=[row["resume_text"], row["job_text"]],
                label=float(row["label"]),
            )
        )
    return examples


def train() -> None:
    from sentence_transformers import SentenceTransformer, losses
    from torch.utils.data import DataLoader

    examples = _load_examples(PAIR_TRAIN_FILE)
    if not examples:
        raise SystemExit("ملف train pairs فاضي. شغل prepare_dataset.py الأول.")

    model = SentenceTransformer(BASE_MODEL)
    dataloader = DataLoader(examples, shuffle=True, batch_size=BATCH_SIZE)
    train_loss = losses.CosineSimilarityLoss(model)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model.fit(
        train_objectives=[(dataloader, train_loss)],
        epochs=EPOCHS,
        warmup_steps=max(10, len(dataloader) // 5),
        optimizer_params={"lr": LEARNING_RATE},
        output_path=str(ARTIFACTS_DIR),
        show_progress_bar=True,
    )

    print(f"[DONE] model saved to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    train()
