# توثيق API - Hire-Mind (نسخة عربية)

## معلومات عامة

- Base URL: `http://localhost:8000`
- كل الردود `application/json` ما عدا endpoint الـ stream.
- النظام RTL-friendly والرسائل بالعربي.

## 1) Health Check

### GET /health

الهدف: التأكد إن السيرفر شغال + مصدر موديل الـ embeddings.

### مثال Response

```json
{
  "status": "ok",
  "message": "[19:26:45] health: السيرفر شغال ومجهز للتحليل",
  "embedding_runtime": {
    "model_source": "artifacts",
    "artifact_path": "E:\\graduate\\Ai_resume_graduate\\ai_engine\\training\\artifacts",
    "base_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  }
}
```

## 2) تحليل CV لوظيفة واحدة

### POST /api/cv/analyze

النوع: `multipart/form-data`

### الحقول

- `file`: ملف PDF أو DOCX
- `job_title`: عنوان الوظيفة
- `job_description`: وصف الوظيفة
- `required_skills`: JSON list كنص

### مثال Request

```bash
curl -X POST http://localhost:8000/api/cv/analyze \
  -F "file=@resume.docx" \
  -F "job_title=AI Engineer" \
  -F "job_description=Build NLP matching API" \
  -F "required_skills=[\"python\",\"nlp\",\"fastapi\"]"
```

### مثال Response

```json
{
  "job_title": "AI Engineer",
  "match_percentage": 81.55,
  "ranking": null,
  "similarity": 0.6981,
  "skill_score": 1.0,
  "title_score": 1.0,
  "missing_skills": [],
  "feedback": "المرشح مناسب جدًا ومفيش فجوات واضحة في المهارات الأساسية.",
  "score_breakdown": {
    "semantic": 0.6981,
    "skill": 1.0,
    "title": 1.0
  },
  "logs": [
    "أنا دلوقتي بقرأ الـ CV",
    "بحلل النص علشان أطلع المهارات الأساسية",
    "بجهز embeddings للنصوص"
  ]
}
```

## 3) تحليل CV مع Live Logs (SSE)

### POST /api/cv/analyze/stream

النوع: `multipart/form-data`

### الحقول

- نفس `analyze`

### أحداث متوقعة

- `type=log` مع `message`
- `type=result` مع النتيجة كاملة
- `type=error` مع رسالة خطأ
- `type=done` نهاية البث

## 4) مطابقة مرشح واحد لوظيفة

### POST /api/jobs/match

النوع: `application/json`

### مثال Request

```json
{
  "job": {
    "title": "AI Engineer",
    "description": "Build NLP systems",
    "required_skills": ["python", "nlp", "fastapi"]
  },
  "candidate": {
    "name": "Ahmed",
    "headline": "AI Engineer",
    "skills": ["python", "nlp", "pytorch"],
    "summary": "Built recommendation and ranking pipelines"
  }
}
```

### مثال Response

نفس شكل `CandidateMatchResponse`.

## 5) أفضل وظائف لمرشح (بالـ profile)

### POST /api/jobs/top-matches

النوع: `application/json`

### مثال Request

```json
{
  "candidate": {
    "name": "Ahmed",
    "headline": "AI Engineer",
    "skills": ["python", "nlp", "fastapi"],
    "summary": "Built matching and ranking systems"
  },
  "jobs": [
    {
      "title": "AI Engineer",
      "description": "Build NLP systems",
      "required_skills": ["python", "nlp", "sentence-transformers"]
    },
    {
      "title": "React Developer",
      "description": "Build RTL frontend",
      "required_skills": ["react", "javascript", "css"]
    }
  ]
}
```

### مثال Response

```json
{
  "candidate_name": "Ahmed",
  "total_jobs": 2,
  "matches": [
    {
      "job_title": "AI Engineer",
      "match_percentage": 79.33,
      "ranking": 1,
      "similarity": 0.6618,
      "skill_score": 1.0,
      "title_score": 1.0,
      "missing_skills": [],
      "feedback": "المرشح مناسب جدًا ومفيش فجوات واضحة في المهارات الأساسية.",
      "score_breakdown": {
        "semantic": 0.6618,
        "skill": 1.0,
        "title": 1.0
      },
      "logs": ["..."]
    }
  ]
}
```

## 6) أفضل وظائف من CV مرفوع

### POST /api/jobs/top-matches/from-cv

النوع: `multipart/form-data`

### الحقول

- `file`: PDF أو DOCX
- `jobs`: JSON list كنص

### مثال Request

```bash
curl -X POST http://localhost:8000/api/jobs/top-matches/from-cv \
  -F "file=@resume.docx" \
  -F "jobs=[{\"title\":\"AI Engineer\",\"description\":\"Build NLP systems\",\"required_skills\":[\"python\",\"nlp\",\"sentence-transformers\"]}]"
```

### مثال Response

نفس شكل `TopMatchesResponse` (مع ranking وfeedback وmissing skills).

## 7) مقارنة مرشحين على وظيفة

### POST /api/jobs/compare-candidates

النوع: `application/json`

### مثال Request

```json
{
  "job": {
    "title": "AI Engineer",
    "description": "بناء نماذج NLP ومطابقة CVs",
    "required_skills": ["python", "nlp", "fastapi", "sentence-transformers"]
  },
  "candidates": [
    {
      "name": "Ahmed",
      "headline": "AI Engineer",
      "skills": ["python", "nlp", "fastapi", "pytorch"],
      "summary": "built ranking and ml systems"
    },
    {
      "name": "Sara",
      "headline": "Frontend Developer",
      "skills": ["react", "javascript", "css"],
      "summary": "building ui apps"
    }
  ]
}
```

### مثال Response

```json
{
  "job_title": "AI Engineer",
  "ranking": [
    {
      "job_title": "AI Engineer",
      "match_percentage": 72.26,
      "ranking": 1,
      "similarity": 0.6598,
      "skill_score": 0.75,
      "title_score": 1.0,
      "missing_skills": ["sentence-transformers"],
      "feedback": "أنصح المرشح يركز على المهارات دي: sentence-transformers.",
      "score_breakdown": {
        "semantic": 0.6598,
        "skill": 0.75,
        "title": 1.0
      },
      "logs": ["..."]
    }
  ]
}
```

## نموذج الأخطاء

- حالة 400 غالبًا في إدخال خاطئ، مثل:

```json
{
  "detail": "required_skills لازم تكون JSON list"
}
```

## ملاحظات إنتاج مهمة

- المحرك الأساسي في الإنتاج: **bi-encoder** (الموديل المتدرّب).
- fallback موجود تلقائيًا لو artifacts غير متاحة.
- score breakdown معروض دائمًا لتفسير القرار.
- Live logs بالعربي متاحة عبر stream endpoint.
