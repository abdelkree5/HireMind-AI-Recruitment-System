# Training Pipeline (Accuracy First)

## 1) تحميل الداتا

```powershell
python -m ai_engine.training.download_datasets
```

## 2) تجهيز pairs

```powershell
python -m ai_engine.training.prepare_dataset
```

## 3) Fine-tuning

```powershell
python -m ai_engine.training.train_sentence_model
```

## 4) تقييم

```powershell
python -m ai_engine.training.evaluate_model
```

## 5) Cross-Validation متعددة splits

```powershell
python -m ai_engine.training.cross_validate
```

## 6) مقارنة القديم والجديد

```powershell
python -m ai_engine.training.compare_models
```

## 7) Re-ranking بـ Cross-Encoder

```powershell
python -m ai_engine.training.rerank_evaluate
```

## تشغيل كل المراحل معًا

```powershell
python -m ai_engine.training.pipeline
```

## ملاحظات

- لو تحميل dataset فشل، وفر ملفات محلية:
  - `ai_engine/training/data/raw/resumes.jsonl`
  - `ai_engine/training/data/raw/jobs.jsonl`
- كل سطر في JSONL عبارة عن object فيه نص واضح.


---

## 👨‍💻 Developer
**Developed by abdelkreem abdelhaleem frahat**

* **LinkedIn:** [abdelkreem abdelhaleem frahat](https://www.linkedin.com/in/abdelkreem-frahat-160g/)
* **Phone:** 01025453847
