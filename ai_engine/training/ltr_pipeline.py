from __future__ import annotations
import os
import pickle
import json
import numpy as np
from datetime import datetime
from typing import Any, Tuple, List
from database.connection import get_connection
from ai_engine.rules_engine import HiringRulesEngine, get_rule_template_for_job

# Define feature names in order
FEATURE_NAMES = [
    "dense_similarity_score",
    "bm25_score",
    "rrf_score",
    "cross_encoder_score",
    "skill_coverage",
    "mandatory_skill_coverage",
    "experience_match",
    "seniority_match",
    "domain_match",
    "recency_score",
    "hiring_rules_score",
    "recruiter_feedback_history"
]

class LTRPipeline:
    def __init__(self, model_dir: str = "database/models"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, "ltr_model.pkl")
        self.metadata_path = os.path.join(self.model_dir, "ltr_metadata.json")

    def extract_features_vector(
        self,
        application: dict[str, Any],
        job: dict[str, Any],
        feedback_history_rate: float = 0.5
    ) -> list[float]:
        """Extracts LTR features from database entities."""
        # Parse score breakdown
        breakdown = {}
        if isinstance(application.get("score_breakdown"), str):
            try:
                breakdown = json.loads(application["score_breakdown"])
            except Exception:
                pass
        elif isinstance(application.get("score_breakdown"), dict):
            breakdown = application["score_breakdown"]

        dense_sim = float(breakdown.get("dense_similarity", application.get("match_score", 50.0) / 100.0))
        bm25_score = float(breakdown.get("bm25_score", 0.0))
        ce_score = float(breakdown.get("reranker_score", dense_sim))
        skill_coverage = float(breakdown.get("skill_score", 0.0))
        exp_align = float(breakdown.get("experience_alignment", 1.0))

        # RRF Score approximation: 1 / (60 + dense_rank) + 1 / (60 + bm25_rank)
        rrf_score = 1.0 / 61.0 + 1.0 / 61.0  # Default middle rank

        # Mandatory skill coverage
        candidate_skills = []
        if isinstance(application.get("candidate_skills"), str):
            try:
                candidate_skills = json.loads(application["candidate_skills"])
            except Exception:
                pass
        elif isinstance(application.get("candidate_skills"), list):
            candidate_skills = application["candidate_skills"]

        candidate_skills_lower = {s.lower().strip() for s in candidate_skills}

        job_required = []
        if isinstance(job.get("required_skills"), str):
            try:
                job_required = json.loads(job["required_skills"])
            except Exception:
                pass
        elif isinstance(job.get("required_skills"), list):
            job_required = job["required_skills"]

        # Parse rules
        hiring_rules = None
        if "hiring_rules" in job and job["hiring_rules"]:
            try:
                if isinstance(job["hiring_rules"], str):
                    hiring_rules_dict = json.loads(job["hiring_rules"])
                else:
                    hiring_rules_dict = job["hiring_rules"]
                from backend.app.schemas import HiringRules
                hiring_rules = HiringRules(**hiring_rules_dict)
            except Exception:
                pass

        if not hiring_rules:
            hiring_rules = get_rule_template_for_job(job.get("title", ""))

        mandatory_skills = hiring_rules.mandatory_skills
        if mandatory_skills:
            matched_mandatory = sum(1 for s in mandatory_skills if s.lower().strip() in candidate_skills_lower)
            mandatory_coverage = matched_mandatory / len(mandatory_skills)
        else:
            mandatory_coverage = 1.0

        # Seniority Match
        job_level = job.get("experience_level", "").lower()
        cand_headline = application.get("candidate_headline", "").lower()
        cand_level = "mid"
        if any(w in cand_headline for w in ["senior", "lead", "principal", "staff"]):
            cand_level = "senior"
        elif any(w in cand_headline for w in ["junior", "entry", "intern"]):
            cand_level = "junior"

        seniority_match = 1.0 if cand_level == job_level or job_level == "" else 0.0

        # Domain Match
        job_domain = job.get("domain", "").lower()
        domain_match = 1.0
        # If candidate skills contain domain-specific keywords
        devops_kws = {"kubernetes", "terraform", "aws", "jenkins", "ci/cd"}
        if job_domain == "devops" and not (candidate_skills_lower & devops_kws):
            domain_match = 0.0

        # Recency Score
        recency_score = 1.0 # default baseline

        # Hiring Rules Score (fraction of checks passed)
        rules_engine = HiringRulesEngine()
        # Heuristically estimate years of experience from seniority
        candidate_years = 5 if cand_level == "senior" else 2 if cand_level == "mid" else 0
        rules_res = rules_engine.evaluate(
            candidate_name=application.get("candidate_name", ""),
            cv_text=application.get("feedback", "") + " " + cand_headline,
            candidate_skills=candidate_skills,
            years_of_experience=candidate_years,
            hiring_rules=hiring_rules
        )
        # Passed fraction: rules engine has 11 potential fail reasons, we subtract based on size of reasons
        reasons_count = len(rules_res.get("reasons", []))
        rules_score = max(0.0, 1.0 - reasons_count * 0.1)

        return [
            dense_sim,
            bm25_score,
            rrf_score,
            ce_score,
            skill_coverage,
            mandatory_coverage,
            exp_align,
            seniority_match,
            domain_match,
            recency_score,
            rules_score,
            feedback_history_rate
        ]

    def train(self) -> dict[str, Any]:
        """Fetches feedback from the DB, trains a LambdaMART model, and saves it."""
        with get_connection() as connection:
            feedback_rows = connection.execute(
                """
                SELECT rf.*, ja.candidate_skills, ja.candidate_headline, ja.score_breakdown, ja.feedback,
                       pj.title, pj.required_skills, pj.experience_level, pj.domain, pj.hiring_rules
                FROM recruiter_feedback rf
                JOIN job_applications ja ON rf.application_id = ja.id
                JOIN posted_jobs pj ON rf.job_id = pj.id
                """
            ).fetchall()

        if len(feedback_rows) < 5:
            return {"status": "error", "message": "Need at least 5 feedback ratings to train LTR ranker."}

        # Group data by job_id (queries)
        job_groups: dict[str, list[dict]] = {}
        for row in feedback_rows:
            j_id = row["job_id"]
            if j_id not in job_groups:
                job_groups[j_id] = []
            job_groups[j_id].append(dict(row))

        # Calculate average feedback acceptance rate
        total_decisions = len(feedback_rows)
        accepted_count = sum(1 for r in feedback_rows if r["is_accepted"] > 0)
        global_acceptance = accepted_count / total_decisions if total_decisions > 0 else 0.5

        X = []
        y = []
        groups = []

        # Decision mapping
        decision_map = {
            "REJECTED": 0,
            "ACCEPTED": 1,
            "INTERVIEWED": 2,
            "HIRED": 3
        }

        for j_id, rows in job_groups.items():
            groups.append(len(rows))
            for row in rows:
                features = self.extract_features_vector(row, row, global_acceptance)
                X.append(features)
                decision = row["recruiter_decision"].upper()
                y.append(decision_map.get(decision, 0))

        X_np = np.array(X, dtype=np.float32)
        y_np = np.array(y, dtype=np.int32)
        groups_np = np.array(groups, dtype=np.int32)

        # Train model using LightGBM LGBMRanker
        trained_with = "LightGBM LambdaMART"
        try:
            from lightgbm import LGBMRanker
            model = LGBMRanker(
                objective="lambdarank",
                metric="ndcg",
                ndcg_eval_at=[5, 10],
                n_estimators=50,
                learning_rate=0.05,
                random_state=42
            )
            model.fit(X_np, y_np, group=groups_np)
            feature_importances = model.feature_importances_.tolist()
        except ImportError:
            # Fallback to Random Forest Regressor / Gradient Boosting if LightGBM fails compile
            from sklearn.ensemble import RandomForestRegressor
            trained_with = "Sklearn RandomForestRegressor Fallback"
            model = RandomForestRegressor(n_estimators=30, random_state=42)
            model.fit(X_np, y_np)
            feature_importances = model.feature_importances_.tolist()

        # Save model pickle
        with open(self.model_path, "wb") as f:
            pickle.dump(model, f)

        # Save metadata
        metadata = {
            "trained_with": trained_with,
            "trained_at": datetime.utcnow().isoformat(),
            "samples_count": len(y),
            "groups_count": len(groups),
            "feature_importance": dict(zip(FEATURE_NAMES, feature_importances)),
            "version": f"v_{int(datetime.utcnow().timestamp())}"
        }
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

        return {"status": "success", "metadata": metadata}

    def get_metadata(self) -> dict[str, Any] | None:
        if not os.path.exists(self.metadata_path):
            return None
        try:
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def rerank_candidates(self, job: dict[str, Any], applications: list[Any]) -> list[Any]:
        """Re-ranks applications using the trained LTR model if available."""
        if not os.path.exists(self.model_path) or not applications:
            return applications

        try:
            with open(self.model_path, "rb") as f:
                model = pickle.load(f)
            metadata = self.get_metadata() or {}
            global_acceptance = metadata.get("global_acceptance", 0.5)
        except Exception:
            return applications

        X = []
        for app in applications:
            app_dict = app.model_dump() if hasattr(app, "model_dump") else dict(app)
            features = self.extract_features_vector(app_dict, job, global_acceptance)
            X.append(features)

        X_np = np.array(X, dtype=np.float32)
        try:
            # Predict ranking scores
            if hasattr(model, "predict"):
                scores = model.predict(X_np)
            else:
                scores = [app.match_score for app in applications]
        except Exception:
            return applications

        # Map score and sort
        scored_apps = list(zip(applications, scores))
        # Sort by LTR score descending
        scored_apps.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for idx, (app, score) in enumerate(scored_apps, 1):
            if hasattr(app, "match_score"):
                # We can adjust match_score slightly or keep it, but we can set candidate ranking
                app.ranking = idx
                # Store LTR score in score_breakdown if possible
                if hasattr(app, "score_breakdown") and app.score_breakdown is not None:
                    app.score_breakdown["ltr_score"] = float(score)
            reranked.append(app)

        return reranked

ltr_pipeline = LTRPipeline()
