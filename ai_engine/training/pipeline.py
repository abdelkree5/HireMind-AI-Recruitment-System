from __future__ import annotations


def run_pipeline() -> None:
    from ai_engine.training.download_datasets import download
    from ai_engine.training.evaluate_model import evaluate
    from ai_engine.training.prepare_dataset import prepare
    from ai_engine.training.train_sentence_model import train

    print("[STEP] 1/4 تحميل datasets")
    download()
    print("[STEP] 2/4 تجهيز dataset للتدريب")
    prepare()
    print("[STEP] 3/4 fine-tuning")
    train()
    print("[STEP] 4/4 تقييم")
    evaluate()


if __name__ == "__main__":
    run_pipeline()
