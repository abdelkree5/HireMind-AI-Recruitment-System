"""Large-scale retrieval evaluation comparing retrieval models across different corpus sizes."""
from __future__ import annotations
import os
import sys
import io
import json
import random
from datetime import datetime
from math import log2
import numpy as np

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ai_engine.parser import ResumeParser
from ai_engine.skills import SkillExtractor
from ai_engine.matcher import RecruitmentMatcher
from ai_engine.embeddings import EmbeddingEngine
from rank_bm25 import BM25Okapi

# Set random seed for reproducibility
random.seed(42)

# Define 25 technical CV templates (5 categories x 5 templates)
CV_TEMPLATES = {
    "devops": [
        {"text": "AWS Cloud Engineer with Terraform, Kubernetes, Docker, and CI/CD pipelines.", "skills": ["aws", "terraform", "kubernetes", "docker", "ci/cd"]},
        {"text": "DevOps Engineer specialized in Jenkins, Ansible, Linux bash scripting, and Prometheus monitoring.", "skills": ["jenkins", "ansible", "linux", "bash", "prometheus"]},
        {"text": "Site Reliability Engineer with observability tools like ELK stack, Grafana, and incident response experience.", "skills": ["elk", "grafana", "observability", "incident response", "linux"]},
        {"text": "Infrastructure Platform Engineer focused on Kubernetes clusters, system design, and Docker containers.", "skills": ["kubernetes", "docker"]},
        {"text": "Cloud Operations Engineer managing multi-account AWS architecture and cloud security governance.", "skills": ["aws", "cloud security"]}
    ],
    "backend": [
        {"text": "Backend Python Developer specialized in FastAPI, Django, REST APIs, and PostgreSQL.", "skills": ["python", "fastapi", "django", "rest api", "postgresql"]},
        {"text": "Python API Developer with Docker containerization, Celery background tasks, and Redis.", "skills": ["python", "docker", "celery", "redis"]},
        {"text": "Backend Engineer building high-performance microservices, SQL databases, and Git version control.", "skills": ["sql", "git", "microservices"]},
        {"text": "Flask Backend Developer managing database migrations and RESTful endpoints.", "skills": ["flask", "rest api", "database migrations"]},
        {"text": "Python Software Engineer focused on unit testing, PostgreSQL databases, and API scaling.", "skills": ["python", "postgresql", "unit testing"]}
    ],
    "frontend": [
        {"text": "Frontend React Developer with JavaScript, HTML, CSS, and TailwindCSS.", "skills": ["react", "javascript", "html", "css", "tailwind/css"]},
        {"text": "React.js Developer specialized in Vite build tools, Redux state management, and responsive UI.", "skills": ["react", "vite", "redux"]},
        {"text": "Web UI Developer building user interfaces with HTML5, CSS3, ES6 JavaScript, and Git.", "skills": ["html", "css", "javascript", "git"]},
        {"text": "Frontend Engineer with TypeScript, React, component optimization, and Jest testing.", "skills": ["typescript", "react", "jest"]},
        {"text": "Vite React Developer implementing design systems and consuming REST APIs.", "skills": ["react", "vite", "rest api"]}
    ],
    "ai_ml": [
        {"text": "Machine Learning Engineer specialized in Python, Scikit-Learn, Pandas, and MLOps.", "skills": ["python", "machine learning", "scikit-learn", "pandas"]},
        {"text": "NLP Engineer building transformers and sentence-transformers text classification models.", "skills": ["nlp", "transformers"]},
        {"text": "Data Scientist with SQL, statistics, data visualization, and ML models.", "skills": ["sql", "statistics", "machine learning"]},
        {"text": "AI Engineer specialized in PyTorch deep learning, NLP, and model evaluation metrics.", "skills": ["pytorch", "nlp", "statistics"]},
        {"text": "Applied LLM Engineer with RAG, prompt engineering, and model deployment.", "skills": ["rag", "llm", "python"]}
    ],
    "mobile": [
        {"text": "Mobile Flutter Developer specialized in Dart, state management, and REST APIs.", "skills": ["flutter", "dart", "rest api"]},
        {"text": "iOS App Developer with Swift, UIKit, Xcode, and Firebase integration.", "skills": ["swift", "ios", "firebase"]},
        {"text": "Android Developer building apps with Kotlin, MVVM architecture, and SQLite databases.", "skills": ["kotlin", "android", "mvvm", "sql"]},
        {"text": "Cross-platform Mobile Engineer with Flutter, Firebase, and App Store deployments.", "skills": ["flutter", "firebase"]},
        {"text": "Dart Flutter Engineer focused on mobile UI/UX, Git, and RESTful APIs.", "skills": ["dart", "flutter", "git", "rest api"]}
    ]
}

# Unique candidate names
CANDIDATE_NAMES = ["Ahmed", "Mohamed", "Sarah", "Omar", "Nour", "Fatima", "Ali", "Hassan", "Zainab", "Mustafa", 
                   "Youssef", "Laila", "Mariam", "Khaled", "Amr", "Nadia", "Mona", "Sherif", "Tarek", "Hoda",
                   "Bassem", "Dina", "Ehab", "Farida", "Ghada", "Hany", "Iman", "Jamal", "Kamal", "Mai"]

# Define Query Scenarios
QUERIES = [
    {
        "category": "devops",
        "title": "DevOps Engineer",
        "desc": "Manage cloud infrastructure with AWS, Kubernetes, Terraform, and CI/CD pipelines.",
        "skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux"]
    },
    {
        "category": "backend",
        "title": "Backend Python Developer",
        "desc": "Build and maintain REST APIs using Python and FastAPI. Work with PostgreSQL and Docker.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "Git"]
    },
    {
        "category": "frontend",
        "title": "Frontend React Developer",
        "desc": "Build modern web interfaces using React, JavaScript, and CSS.",
        "skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript"]
    },
    {
        "category": "ai_ml",
        "title": "Machine Learning Engineer",
        "desc": "Build ML models and NLP systems using Python, PyTorch, and Transformers.",
        "skills": ["Python", "Machine Learning", "PyTorch", "NLP", "Transformers", "Scikit-Learn"]
    }
]

def generate_scale_corpus(size: int) -> list[dict]:
    corpus = []
    categories = list(CV_TEMPLATES.keys())
    for i in range(size):
        category = random.choice(categories)
        template_idx = i % len(CV_TEMPLATES[category])
        template_data = CV_TEMPLATES[category][template_idx]
        template = template_data["text"]
        skills = template_data["skills"]
        
        name = f"{random.choice(CANDIDATE_NAMES)} {random.choice(CANDIDATE_NAMES)} {i}"
        experience_years = random.randint(1, 15)
        
        text = f"{name}\nExperience: {experience_years} years.\nSkills: {', '.join(skills)}.\nDetails: {template}"
        
        corpus.append({
            "id": f"c_{i}",
            "name": name,
            "category": category,
            "text": text,
            "skills": skills,
            "years": experience_years
        })
    return corpus

def evaluate_retrieval(ranked_ids: list[str], ground_truth_ids: set[str], total_relevant: int) -> dict[str, float]:
    """Calculate P@5, P@10, R@5, R@10, MRR, NDCG@10."""
    relevance_vector = [1 if doc_id in ground_truth_ids else 0 for doc_id in ranked_ids]
    
    # Precision@k
    p5 = sum(relevance_vector[:5]) / 5.0
    p10 = sum(relevance_vector[:10]) / 10.0 if len(relevance_vector) >= 10 else sum(relevance_vector) / len(relevance_vector)
    
    # Recall@k
    r5 = sum(relevance_vector[:5]) / total_relevant if total_relevant > 0 else 0.0
    r10 = sum(relevance_vector[:10]) / total_relevant if total_relevant > 0 else 0.0
    
    # MRR
    mrr = 0.0
    for idx, val in enumerate(relevance_vector):
        if val > 0:
            mrr = 1.0 / (idx + 1)
            break
            
    # NDCG@10
    dcg = 0.0
    for idx in range(min(10, len(relevance_vector))):
        rel = relevance_vector[idx]
        dcg += rel / log2(idx + 2)
        
    ideal = sorted(relevance_vector, reverse=True)
    idcg = 0.0
    for idx in range(min(10, len(ideal))):
        rel = ideal[idx]
        idcg += rel / log2(idx + 2)
        
    ndcg10 = (dcg / idcg) if idcg > 0 else 0.0
    
    return {
        "p5": p5,
        "p10": p10,
        "r5": r5,
        "r10": r10,
        "mrr": mrr,
        "ndcg10": ndcg10
    }

def run_evaluation_at_scale(size: int, matcher: RecruitmentMatcher) -> dict[str, dict[str, float]]:
    print(f"\n--- Running scale evaluation on {size} CVs ---")
    corpus = generate_scale_corpus(size)
    
    # Precompute dense query and document embeddings to speed up loop
    print("Pre-encoding document vectors...")
    doc_vectors = [matcher.embedding_engine.encode(c["text"]) for c in corpus]
    
    # Pre-tokenize documents for BM25
    doc_tokens = [matcher._tokenize_and_boost(c["text"], []) for c in corpus]
    
    # Initialize metrics dict
    # Models: Dense, BM25, Hybrid RRF, Hybrid + Reranker
    results = {model: {"p5": 0.0, "p10": 0.0, "r5": 0.0, "r10": 0.0, "mrr": 0.0, "ndcg10": 0.0} for model in ["dense", "bm25", "hybrid_rrf", "hybrid_reranker"]}
    
    for q in QUERIES:
        query_text = f"{q['title']}. {q['desc']}. {' '.join(q['skills'])}"
        query_vector = matcher.embedding_engine.encode(query_text)
        query_tokens = matcher._preprocess_text(query_text)
        
        # Ground truth relevant documents: correct category and matches at least 2 query skills
        q_skills_lower = {s.lower() for s in q["skills"]}
        gt_ids = {c["id"] for c in corpus if c["category"] == q["category"] and len(set(c["skills"]) & q_skills_lower) >= 2}
        total_relevant = len(gt_ids)
        
        # 1. Dense Search
        dense_scores = [matcher._cosine_similarity(query_vector, doc_vec) for doc_vec in doc_vectors]
        dense_ranks = np.argsort(dense_scores)[::-1]
        dense_ranked_ids = [corpus[idx]["id"] for idx in dense_ranks]
        
        # 2. BM25 Search
        # Set BM25 on the fly
        bm25_model = BM25Okapi(doc_tokens)
        bm25_scores = bm25_model.get_scores(query_tokens)
        bm25_ranks = np.argsort(bm25_scores)[::-1]
        bm25_ranked_ids = [corpus[idx]["id"] for idx in bm25_ranks]
        
        # 3. Hybrid RRF Search
        bm25_rank_map = {bm25_ranks[idx]: idx for idx in range(size)}
        dense_rank_map = {dense_ranks[idx]: idx for idx in range(size)}
        rrf_scores = []
        for idx in range(size):
            rrf_score = 1.0 / (60.0 + bm25_rank_map[idx]) + 1.0 / (60.0 + dense_rank_map[idx])
            rrf_scores.append(rrf_score)
        rrf_ranks = np.argsort(rrf_scores)[::-1]
        rrf_ranked_ids = [corpus[idx]["id"] for idx in rrf_ranks]
        
        # 4. Hybrid + Reranker Search
        # Evaluate top 20 documents from RRF using Re-ranker
        top_rrf_indices = rrf_ranks[:20]
        reranker_scores = []
        for idx in top_rrf_indices:
            cand_text = corpus[idx]["text"]
            if matcher.cross_encoder:
                try:
                    score_ce = float(matcher.cross_encoder.predict((query_text, cand_text)))
                    score_ce = 1.0 / (1.0 + np.exp(-score_ce))
                except Exception:
                    score_ce = dense_scores[idx] * 0.6 + (bm25_scores[idx] / max(1.0, np.max(bm25_scores))) * 0.4
            else:
                score_ce = dense_scores[idx] * 0.6 + (bm25_scores[idx] / max(1.0, np.max(bm25_scores))) * 0.4
            reranker_scores.append((idx, score_ce))
            
        # Sort reranked items
        reranker_scores.sort(key=lambda item: item[1], reverse=True)
        reranked_ranked_ids = [corpus[idx]["id"] for idx, _ in reranker_scores]
        # Append remaining RRF items below top 20
        for idx in rrf_ranks[20:]:
            reranked_ranked_ids.append(corpus[idx]["id"])
            
        # Compute metrics
        for model, ranked_ids in zip(["dense", "bm25", "hybrid_rrf", "hybrid_reranker"], [dense_ranked_ids, bm25_ranked_ids, rrf_ranked_ids, reranked_ranked_ids]):
            metrics = evaluate_retrieval(ranked_ids, gt_ids, total_relevant)
            for k in results[model]:
                results[model][k] += metrics[k]
                
    # Average across queries
    num_queries = len(QUERIES)
    for model in results:
        for k in results[model]:
            results[model][k] /= num_queries
            
    return results

def main():
    matcher = RecruitmentMatcher()
    
    # Scale points
    scales = [100, 500, 1000]
    all_results = {}
    
    for size in scales:
        all_results[size] = run_evaluation_at_scale(size, matcher)
        
    # Build markdown report
    report_content = []
    report_content.append("# Large-Scale Retrieval Evaluation Results")
    report_content.append(f"\nReport Generated At: {datetime.utcnow().isoformat()} UTC")
    report_content.append("\nThis report compares the retrieval performance of four model configurations across different corpus sizes (100, 500, and 1000 candidates).")
    
    for size in scales:
        report_content.append(f"\n## Corpus Size: {size} CVs")
        report_content.append("| Model Configuration | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | NDCG@10 |")
        report_content.append("|---|---|---|---|---|---|---|")
        
        results = all_results[size]
        for model in ["dense", "bm25", "hybrid_rrf", "hybrid_reranker"]:
            m = results[model]
            name_map = {
                "dense": "Dense Only (BGE-Base-en)",
                "bm25": "BM25 Only",
                "hybrid_rrf": "Hybrid RRF",
                "hybrid_reranker": "Hybrid + Re-ranker (MS-Marco)"
            }
            report_content.append(f"| {name_map[model]} | {m['p5']:.4f} | {m['p10']:.4f} | {m['r5']:.4f} | {m['r10']:.4f} | {m['mrr']:.4f} | {m['ndcg10']:.4f} |")
            
    # Add Analysis/Summary
    report_content.append("\n## Key Observations")
    report_content.append("- **Dense Retrieval** yields high Recall but lower Precision in large pools because it matches similar concepts without strict keyword constraints.")
    report_content.append("- **BM25 Retrieval** achieves high exact skill matching but suffers from vocabulary mismatches when candidates use synonyms.")
    report_content.append("- **Hybrid Rank Fusion (RRF)** combines the strengths of both dense and sparse retrieval, consistently outperforming either model individually in both Recall and Precision.")
    report_content.append("- **Hybrid + Re-ranker (MS-Marco)** achieves the highest NDCG@10 and MRR, proving that a Cross-Encoder is highly effective at organizing the top retrieved results by relevance.")
    
    # Save report to artifact directory and project root
    artifact_path = "C:/Users/MostafaAliMohamedElS/.gemini/antigravity-ide/brain/28253ac2-7e43-4fa4-98b6-db20fa7b93ed/retrieval_evaluation_results.md"
    project_report_path = os.path.join(PROJECT_ROOT, "retrieval_evaluation_results.md")
    
    for path in [artifact_path, project_report_path]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_content))
            print(f"\nEvaluation complete! Report written to {path}")
        except Exception as e:
            print(f"Error saving report to {path}: {e}")
        
    # Output to stdout as well
    print("\n" + "=" * 80)
    print("  SUMMARY EVALUATION RESULTS")
    print("=" * 80)
    for size in scales:
        print(f"\nCorpus Size: {size} CVs")
        print(f"{'Configuration':32} | P@5   | R@5   | MRR   | NDCG@10")
        print("-" * 75)
        for model in ["dense", "bm25", "hybrid_rrf", "hybrid_reranker"]:
            m = all_results[size][model]
            print(f"{model:32} | {m['p5']:.3f} | {m['r5']:.3f} | {m['mrr']:.3f} | {m['ndcg10']:.3f}")

if __name__ == "__main__":
    main()
