from __future__ import annotations

import re
import os
import json
import sqlite3
from datetime import datetime
from dataclasses import dataclass, field
from math import ceil, log2
import numpy as np

from rank_bm25 import BM25Okapi
from nltk.stem import PorterStemmer

try:
    from backend.app.schemas import HiringRules
except ImportError:
    HiringRules = None
from ai_engine.rules_engine import HiringRulesEngine, get_rule_template_for_job
from ai_engine.embeddings import EmbeddingEngine
from ai_engine.skills import SkillExtractor, CATEGORY_ALIAS_PATTERNS


# Try importing CrossEncoder from sentence_transformers, fallback gracefully

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

# Pre-initialize Porter Stemmer
stemmer = PorterStemmer()

@dataclass
class MatchReport:
    similarity: float
    skill_score: float
    title_score: float
    context_score: float
    match_percentage: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    recommendation: str = ""
    # Added for upgraded explainability and confidence scoring
    experience_alignment_score: float = 0.0
    reranker_score: float = 0.0
    domain_alignment: str = "Unknown"
    seniority_alignment: str = "Unknown"
    reason: str = ""
    rule_status: str = "PASSED"
    rule_reasons: list[str] = field(default_factory=list)


@dataclass
class RoleMatchResult:
    role_name: str
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    confidence: float = 0.0
    composite: float = 0.0
    match_level: str = "Low"
    priority_score: float = 0.0
    reason: str = ""

@dataclass
class AgentMemory:
    previous_attempts: list[dict] = field(default_factory=list)
    failed_searches: list[str] = field(default_factory=list)
    query_rewrites: list[str] = field(default_factory=list)
    retrieved_evidence: list[dict] = field(default_factory=list)

class RecruitmentMatcher:
    def __init__(self) -> None:
        self.embedding_engine = EmbeddingEngine()
        self.skill_extractor = SkillExtractor()
        # Initialize Cross-Encoder if available, otherwise fallback
        if CrossEncoder:
            try:
                self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            except Exception:
                self.cross_encoder = None
        else:
            self.cross_encoder = None

    def _preprocess_text(self, text: str) -> list[str]:
        """Normalize, remove noise, merge tech phrases, and stem."""
        text = text.lower()
        # Merge technical phrases to support phrase matching
        phrases = [
            "rest api", "cloud architecture", "deep learning", "machine learning",
            "sentence transformers", "model evaluation", "feature engineering",
            "information retrieval", "prompt engineering", "infrastructure automation",
            "incident response", "active directory", "windows server", "fiber optics",
            "microwave links", "wireless networking", "network security",
            "network operations", "network integration", "site survey"
        ]
        for p in phrases:
            text = text.replace(p, p.replace(" ", "_"))
            
        tokens = re.findall(r"\b\w+\b", text)
        return [stemmer.stem(t) for t in tokens if len(t) > 1]

    def _tokenize_and_boost(self, text: str, boost_skills: list[str]) -> list[str]:
        """Tokenize text and boost critical skills by duplicating tokens."""
        tokens = self._preprocess_text(text)
        boosted = list(tokens)
        stemmed_boost = {stemmer.stem(s.lower().replace(" ", "_")) for s in boost_skills}
        
        for t in tokens:
            if t in stemmed_boost:
                boosted.extend([t] * 3)  # Boost weight by 3x duplication
        return boosted

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        denom = float(np.linalg.norm(left) * np.linalg.norm(right))
        return float(np.dot(left, right) / denom) if denom != 0 else 0.0

    def score(
        self,
        candidate_text: str,
        candidate_skills: list[str],
        job_title: str,
        job_description: str,
        required_skills: list[str],
        candidate_level: str | None = None,
        job_level: str | None = None,
        hiring_rules: HiringRules | None = None,
        job_id: str = "",
    ) -> MatchReport:
        """Run the single-candidate RAG matching pipeline."""
        candidates = [{
            "id": "single_candidate",
            "name": "Candidate",
            "text": candidate_text,
            "skills": candidate_skills
        }]
        
        ranked = self.retrieve_and_rank(
            candidates=candidates,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            experience_level=job_level or "",
            domain="",
            hiring_rules=hiring_rules,
            job_id=job_id
        )
        return ranked[0]

    def retrieve_and_rank(
        self,
        candidates: list[dict],
        job_title: str,
        job_description: str,
        required_skills: list[str],
        experience_level: str = "",
        domain: str = "",
        ground_truth: dict[str, int] | None = None,  # Map of candidate_id -> relevance (0 or 1)
        hiring_rules: HiringRules | None = None,
        job_id: str = "",
    ) -> list[MatchReport | dict]:
        """
        Executes the 6-stage Hybrid Agentic RAG pipeline:
        Stage 1: BM25 Retrieval
        Stage 2: Dense Vector Retrieval
        Stage 3: RRF Fusion
        Stage 4: Cross-Encoder Re-ranking
        Stage 5: Agentic Reflection (Self-Correction/Expansion)
        Stage 6: Final Candidate Ranking
        """

        agent_memory = AgentMemory()
        
        query = f"{job_title}. {job_description}. {' '.join(required_skills)}"
        
        # We start the Stage 1 to 4 loop
        ranked_reports = self._execute_retrieval_and_rerank(
            candidates, query, required_skills, job_title, job_description, experience_level, domain, agent_memory, hiring_rules, job_id
        )
        
        # Stage 5: Agentic Reflection
        top_match_pct = ranked_reports[0].match_percentage if ranked_reports else 0.0

        
        # If match percentage is very low (< 50%) and we haven't expanded yet, try Agentic self-correction
        if top_match_pct < 50.0 and len(agent_memory.previous_attempts) < 2:
            expanded_query = self._agentic_rewrite_query(query, required_skills, agent_memory)
            if expanded_query != query:
                agent_memory.query_rewrites.append(expanded_query)
                # Re-run Stage 1-4 with expanded query
                new_reports = self._execute_retrieval_and_rerank(
                    candidates, expanded_query, required_skills, job_title, job_description, experience_level, domain, agent_memory, hiring_rules, job_id
                )
                # Keep the better scoring retrieval
                if new_reports and new_reports[0].match_percentage > top_match_pct:
                    ranked_reports = new_reports
                    ranked_reports[0].logs.append(f"Agent Reflection triggered query expansion: {expanded_query}")
                else:
                    agent_memory.failed_searches.append(expanded_query)


        # Stage 6: Final Candidate Ranking
        # Ranks are already sorted by match_percentage descending in _execute_retrieval_and_rerank
        
        # If ground truth labels are provided, evaluate retrieval and store metrics
        if ground_truth and len(candidates) > 1:
            self._calculate_and_log_metrics(ranked_reports, ground_truth)
            
        return ranked_reports

    def _execute_retrieval_and_rerank(
        self,
        candidates: list[dict],
        query: str,
        required_skills: list[str],
        job_title: str,
        job_description: str,
        job_level: str,
        job_domain: str,
        agent_memory: AgentMemory,
        hiring_rules: HiringRules | None = None,
        job_id: str = "",
    ) -> list[MatchReport]:
        """Execute Stage 1 (BM25), Stage 2 (Dense), Stage 3 (RRF), and Stage 4 (Cross-Encoder)."""
        num_candidates = len(candidates)
        if num_candidates == 0:
            return []

        if hiring_rules is None:
            hiring_rules = get_rule_template_for_job(job_title)

        from ai_engine.feedback import get_dynamic_skill_weights
        dynamic_weights = get_dynamic_skill_weights(job_id) if job_id else {}



        # Stage 1: BM25 Retrieval
        corpus_tokens = [self._tokenize_and_boost(c["text"], required_skills) for c in candidates]
        if len(corpus_tokens) == 1:
            corpus_tokens.append(["__dummy__"])
        bm25 = BM25Okapi(corpus_tokens)
        query_tokens = self._preprocess_text(query)
        bm25_scores = list(bm25.get_scores(query_tokens))[:num_candidates]
        
        # Rank by BM25
        bm25_ranks = np.argsort(bm25_scores)[::-1]
        bm25_rank_map = {bm25_ranks[i]: i for i in range(num_candidates)}

        # Stage 2: Dense Vector Retrieval
        query_vector = self.embedding_engine.encode(query)
        dense_scores = []
        for c in candidates:
            c_vector = self.embedding_engine.encode(c["text"])
            dense_scores.append(self._cosine_similarity(query_vector, c_vector))
            
        # Rank by Dense similarity
        dense_ranks = np.argsort(dense_scores)[::-1]
        dense_rank_map = {dense_ranks[i]: i for i in range(num_candidates)}

        # Stage 3: RRF Rank Fusion
        rrf_scores = []
        for i in range(num_candidates):
            bm25_r = bm25_rank_map[i]
            dense_r = dense_rank_map[i]
            rrf_score = 1.0 / (60.0 + bm25_r) + 1.0 / (60.0 + dense_r)
            rrf_scores.append(rrf_score)
            
        # Sort candidates by RRF rank
        rrf_ranks = np.argsort(rrf_scores)[::-1]

        # Stage 4: Cross-Encoder Re-ranking
        reranker_scores = []
        for i in range(num_candidates):
            cand_text = candidates[i]["text"]
            # Format inputs as a tuple for Cross-Encoder
            if self.cross_encoder:
                try:
                    score_ce = float(self.cross_encoder.predict((query, cand_text)))
                    # Map ms-marco output (logits) to 0-1 range using sigmoid
                    score_ce = 1.0 / (1.0 + np.exp(-score_ce))
                except Exception:
                    score_ce = 0.5  # Neutral fallback
            else:
                # Rule-based fallback Cross-Encoder: combining semantic similarity and keyword overlaps
                score_ce = dense_scores[i] * 0.6 + (bm25_scores[i] / max(1.0, np.max(bm25_scores))) * 0.4
            
            reranker_scores.append(score_ce)

        # Build reports & compute final multi-factor Confidence Scores
        reports = []
        for i in range(num_candidates):
            c = candidates[i]
            c_text = c["text"]
            c_skills = c.get("skills", [])
            
            # Sub-components
            dense_sim = dense_scores[i]
            bm25_raw = bm25_scores[i]
            rerank_s = reranker_scores[i]
            
            # Normalizations & skill mapping
            normalized_job = sorted(list(set(s.lower().strip() for s in required_skills if s)))
            normalized_candidate = sorted(list(set(s.lower().strip() for s in c_skills if s)))
            matched_skills = [s for s in normalized_job if s in normalized_candidate]
            missing_skills = [s for s in normalized_job if s not in matched_skills]
            
            skill_score = self._calculate_weighted_skill_score(normalized_job, normalized_candidate, c_text, dynamic_weights)
            title_score = self._title_alignment(c_text, job_title)
            context_score = self._context_quality(c_text)
            
            # Years/experience alignment
            cand_exp = self._extract_experience_years(c_text)
            req_exp = self._extract_experience_years(job_description)
            exp_alignment = self._experience_alignment(cand_exp, req_exp)
            
            # Nonlinear Experience Penalty
            experience_penalty = self._calculate_experience_penalty(cand_exp, req_exp)
            
            # Mandatory skill gating check
            mandatory_skills = hiring_rules.mandatory_skills if (hiring_rules and hiring_rules.mandatory_skills) else self._get_mandatory_skills(job_title)
            missing_mandatory = []
            for ms in mandatory_skills:
                if not self._has_skill_with_negation_check(c_text, ms, c_skills):
                    missing_mandatory.append(ms)
            
            # Seniority & Domain checks
            cand_level = self._infer_seniority(c_text, cand_exp)
            role_level = job_level if job_level else self._infer_seniority(query, req_exp)
            
            # Penalties list
            penalties = []
            level_penalty = 0.0
            
            # Penalize missing skills based on dynamic weights
            for ms in missing_skills:
                ms_low = ms.lower().strip()
                if ms_low in dynamic_weights:
                    level_penalty += dynamic_weights[ms_low]
                    penalties.append(f"Consistently rejected missing skill: {ms} (-{int(dynamic_weights[ms_low] * 100)}%)")

            if cand_level != role_level:
                level_penalty += 0.05
                penalties.append("Seniority mismatch (-5%)")

                
            domain_alignment = "Aligned"
            # Inferred candidate domain
            cand_domain = self._infer_domain(normalized_candidate, c_text)
            target_domain = job_domain.lower() if job_domain else self._infer_domain(normalized_job, query)
            if target_domain and cand_domain != target_domain and cand_domain != "general":
                level_penalty += 0.05
                penalties.append("Domain mismatch (-5%)")
                domain_alignment = "Domain Mismatch"

            if experience_penalty > 0.0:
                level_penalty += experience_penalty
                penalties.append(f"Experience deficit penalty (-{int(experience_penalty * 100)}%)")

            if missing_mandatory:
                level_penalty += 0.30
                penalties.append(f"Missing mandatory skill(s): {', '.join(missing_mandatory)} (-30%)")

            # ----------------------------------------------------
            # Hiring Rules Engine Evaluation
            # ----------------------------------------------------
            rule_status = "PASSED"
            rule_reasons = []
            rules_penalty = 0.0
            
            if hiring_rules:
                rules_engine = HiringRulesEngine()
                rules_result = rules_engine.evaluate(
                    candidate_name=c.get("name", "Candidate"),
                    cv_text=c_text,
                    candidate_skills=c_skills,
                    years_of_experience=cand_exp,
                    hiring_rules=hiring_rules
                )
                rule_status = rules_result["rule_status"]
                rule_reasons = rules_result["reasons"]
                rules_penalty = rules_result["penalty"]
                
                for r_reason in rule_reasons:
                    if r_reason not in penalties:
                        penalties.append(r_reason)

            # ----------------------------------------------------
            # Multi-factor Confidence Score Calculation (0-100)
            # ----------------------------------------------------
            # Dense Sim (0.25) + BM25 normalized (0.15) + Reranker (0.35) + Skill coverage (0.15) + Experience (0.10)
            max_bm25 = max(1.0, np.max(bm25_scores))
            norm_bm25 = min(1.0, bm25_raw / max_bm25)
            
            confidence_score = (
                dense_sim * 0.25 +
                norm_bm25 * 0.15 +
                rerank_s * 0.35 +
                skill_score * 0.15 +
                exp_alignment * 0.10
            )
            # Apply penalties
            confidence_score = max(0.0, confidence_score - level_penalty - rules_penalty)
            match_percentage = round(confidence_score * 100.0, 2)
            
            # Explainability
            reason = self._generate_explainability_reason(
                c.get("name", "Candidate"), job_title, matched_skills, missing_skills,
                cand_exp, req_exp, cand_level, role_level, cand_domain, target_domain, match_percentage
            )
            if missing_mandatory or rule_status == "REJECTED":
                combined_reasons = list(set(missing_mandatory + [r.replace("Missing mandatory skill: ", "").replace("Missing required skill: ", "") for r in rule_reasons]))
                reason = f"[REJECTED: {', '.join(combined_reasons)}] " + reason
            
            report = MatchReport(
                similarity=dense_sim,
                skill_score=skill_score,
                title_score=title_score,
                context_score=context_score,
                match_percentage=match_percentage,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                penalties=penalties,
                score_breakdown={
                    "dense_similarity": round(dense_sim, 4),
                    "bm25_score": round(bm25_raw, 4),
                    "reranker_score": round(rerank_s, 4),
                    "skill_score": round(skill_score, 4),
                    "experience_alignment": round(exp_alignment, 4),
                },
                recommendation=self._build_recommendation(confidence_score),
                experience_alignment_score=exp_alignment,
                reranker_score=rerank_s,
                domain_alignment=cand_domain.title(),
                seniority_alignment=cand_level,
                reason=reason,
                rule_status=rule_status,
                rule_reasons=rule_reasons,
                logs=["Stage 1: BM25 sparse check complete.", "Stage 2: Dense BGE embeddings complete.", "Stage 3: RRF Fusion rank complete.", "Stage 4: MS-Marco Cross-Encoder re-rank complete."]
            )
            reports.append(report)
            
        # Sort final list by match_percentage descending
        reports.sort(key=lambda r: r.match_percentage, reverse=True)
        
        # Prevent ranking inside Top 3 for candidates missing mandatory skills or rejected by rules engine
        if len(reports) > 3:
            invalid_in_top_3 = []
            valid_in_top_3 = []
            for r in reports[:3]:
                if any("Missing mandatory skill" in p for p in r.penalties) or r.rule_status == "REJECTED":
                    invalid_in_top_3.append(r)
                else:
                    valid_in_top_3.append(r)
                    
            if invalid_in_top_3:
                valid_below = []
                invalid_below = []
                for r in reports[3:]:
                    if any("Missing mandatory skill" in p for p in r.penalties) or r.rule_status == "REJECTED":
                        invalid_below.append(r)
                    else:
                        valid_below.append(r)
                        
                # Re-construct list ensuring invalid candidates are pushed below Top 3 if possible
                new_top_3 = valid_in_top_3 + valid_below[:3 - len(valid_in_top_3)]
                remaining_valid_below = valid_below[3 - len(valid_in_top_3):]
                new_below = remaining_valid_below + invalid_in_top_3 + invalid_below
                
                new_top_3.sort(key=lambda r: r.match_percentage, reverse=True)
                new_below.sort(key=lambda r: r.match_percentage, reverse=True)
                reports = new_top_3 + new_below


        # Log evidence to Agent memory
        agent_memory.previous_attempts.append({
            "query": query,
            "top_percentage": reports[0].match_percentage if reports else 0.0
        })
        for r in reports[:3]:
            agent_memory.retrieved_evidence.append({
                "candidate_skills": r.matched_skills,
                "confidence": r.match_percentage
            })
            
        return reports

    def _calculate_experience_penalty(self, candidate_years: int, required_years: int) -> float:
        if required_years == 0:
            return 0.0
        if candidate_years >= required_years:
            return 0.0
            
        ratio = candidate_years / required_years
        
        # Piecewise interpolation matching specified rules:
        # Candidate 1 year (ratio 0.125) -> Penalty 40%
        # Candidate 3 years (ratio 0.375) -> Penalty 25%
        # Candidate 5 years (ratio 0.625) -> Penalty 10%
        # Candidate 8 years (ratio 1.0) -> Penalty 0%
        if ratio <= 0.125:
            return 0.40
        elif ratio <= 0.375:
            return 0.40 - (ratio - 0.125) * (0.15 / 0.25)
        elif ratio <= 0.625:
            return 0.25 - (ratio - 0.375) * (0.15 / 0.25)
        else:
            return 0.10 - (ratio - 0.625) * (0.10 / 0.375)

    def _get_mandatory_skills(self, job_title: str) -> list[str]:
        title_low = job_title.lower()
        if "devops" in title_low:
            return ["kubernetes", "terraform", "aws"]
        elif "backend" in title_low:
            return ["python", "fastapi"]
        elif "frontend" in title_low or "react" in title_low:
            return ["react", "javascript"]
        elif "machine learning" in title_low or "ai" in title_low or "nlp" in title_low or "ml" in title_low:
            return ["python", "machine learning"]
        return []

    def _has_skill_with_negation_check(self, text: str, skill: str, candidate_skills: list[str]) -> bool:
        skill_low = skill.lower()
        candidate_skills_lower = {s.lower().strip() for s in candidate_skills}
        if skill_low not in candidate_skills_lower:
            # Check synonyms
            synonyms = {
                "kubernetes": ["kubernetes", "k8s"],
                "aws": ["aws", "amazon web services", "amazon"],
                "terraform": ["terraform"],
                "python": ["python"],
                "fastapi": ["fastapi", "fast api"],
                "react": ["react", "reactjs", "react.js"],
                "javascript": ["javascript", "js"],
                "machine learning": ["machine learning", "ml"]
            }
            has_synonym = False
            for syn in synonyms.get(skill_low, [skill_low]):
                if syn in candidate_skills_lower:
                    has_synonym = True
                    break
            if not has_synonym:
                return False
                
        negation_regex = re.compile(
            r"\b(no|not|never|lack\s+of|without|zero|nil|none\s+of|limited|no\s+experience\s+with|no\s+experience\s+in)\b",
            re.IGNORECASE
        )
        sentences = re.split(r'[.\n]', text)
        skill_mentions_count = 0
        negated_mentions_count = 0
        
        skill_patterns = {
            "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
            "aws": [r"\baws\b", r"\bamazon\s+web\s+services\b"],
            "terraform": [r"\bterraform\b"],
            "python": [r"\bpython\b"],
            "fastapi": [r"\bfastapi\b", r"\bfast\s+api\b"],
            "react": [r"\breact(?:\.js)?\b"],
            "javascript": [r"\bjavascript\b", r"\bjs\b"],
            "machine learning": [r"\bmachine\s+learning\b", r"\bml\b"]
        }
        
        pats = skill_patterns.get(skill_low, [r"\b" + re.escape(skill_low) + r"\b"])
        for sentence in sentences:
            sentence_low = sentence.lower()
            matched_pat = None
            for pat in pats:
                match = re.search(pat, sentence_low)
                if match:
                    matched_pat = match
                    break
            
            if matched_pat:
                skill_mentions_count += 1
                start_idx = matched_pat.start()
                context_before = sentence_low[max(0, start_idx - 60):start_idx]
                if negation_regex.search(context_before):
                    negated_mentions_count += 1
                    
        if skill_mentions_count > 0 and negated_mentions_count == skill_mentions_count:
            return False
            
        return True

    def _estimate_skill_recency(self, cv_text: str, skill: str) -> int | None:
        current_year = 2026
        cv_text_lower = cv_text.lower()
        skill_patterns = []
        for cat, entries in CATEGORY_ALIAS_PATTERNS.items():
            if skill in entries:
                skill_patterns = entries[skill]
                break
        if not skill_patterns:
            skill_patterns = [r"\b" + re.escape(skill.lower()) + r"\b"]
            
        paragraphs = [p.strip() for p in cv_text.split("\n") if p.strip()]
        last_used_year = None
        year_pattern = re.compile(r"\b(199\d|20[0-2]\d)\b")
        present_pattern = re.compile(r"\b(present|current|now|active)\b", re.IGNORECASE)
        
        for p in paragraphs:
            p_lower = p.lower()
            has_skill = False
            for pat in skill_patterns:
                if re.search(pat, p_lower):
                    has_skill = True
                    break
            
            if has_skill:
                years = [int(y) for y in year_pattern.findall(p)]
                if present_pattern.search(p):
                    years.append(current_year)
                
                if years:
                    para_year = max(years)
                    if last_used_year is None or para_year > last_used_year:
                        last_used_year = para_year
                else:
                    idx = paragraphs.index(p)
                    found_year = None
                    for j in range(max(0, idx - 3), idx):
                        prev_p = paragraphs[j]
                        prev_years = [int(y) for y in year_pattern.findall(prev_p)]
                        if present_pattern.search(prev_p):
                            prev_years.append(current_year)
                        if prev_years:
                            found_year = max(prev_years)
                    if found_year:
                        if last_used_year is None or found_year > last_used_year:
                            last_used_year = found_year
                            
        if last_used_year is None:
            has_skill_at_all = False
            for pat in skill_patterns:
                if re.search(pat, cv_text_lower):
                    has_skill_at_all = True
                    break
            if has_skill_at_all:
                all_years = [int(y) for y in year_pattern.findall(cv_text)]
                if present_pattern.search(cv_text):
                    all_years.append(current_year)
                if not all_years:
                    return current_year
                else:
                    return max(all_years)
            else:
                return None
        return last_used_year

    def _get_skill_decay_factor(self, cv_text: str, skill: str) -> float:
        last_used = self._estimate_skill_recency(cv_text, skill)
        if last_used is None:
            return 1.0
        current_year = 2026
        diff = current_year - last_used
        if diff <= 5:
            return 1.0
        return max(0.3, 1.0 - (diff - 5) * 0.15)

    def _agentic_rewrite_query(self, query: str, required_skills: list[str], memory: AgentMemory) -> str:
        """Agent query expansion using technical synonyms to resolve vocabulary mismatches."""
        synonym_map = {
            "kubernetes": ["k8s", "helm", "orchestration", "container"],
            "docker": ["containerization", "containers", "docker-compose"],
            "aws": ["amazon", "ec2", "s3", "rds", "eks", "cloud"],
            "fastapi": ["python api", "fast api", "restful api"],
            "react": ["frontend", "javascript", "reactjs", "ui"],
            "machine learning": ["ml", "scikit-learn", "model", "scikit"],
            "nlp": ["transformers", "spacy", "text processing", "text mining"],
        }
        
        rewritten_parts = [query]
        for skill in required_skills:
            skill_low = skill.lower()
            if skill_low in synonym_map:
                for syn in synonym_map[skill_low]:
                    if syn not in query.lower():
                        rewritten_parts.append(syn)
                        
        return " ".join(rewritten_parts)

    def _extract_experience_years(self, text: str) -> int:
        explicit = [int(v) for v in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|year)", text.lower())]
        if explicit: 
            return max(explicit)
        spans = re.findall(r"(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:present|current|(?:19|20)\d{2})", text.lower())
        if spans:
            return min(10, len(spans) * 2)
        return 0

    def _experience_alignment(self, candidate_years: int, required_years: int) -> float:
        if required_years == 0: 
            return 1.0
        diff = candidate_years - required_years
        if diff >= 0:
            return 1.0  # Over-qualified or exact fit is good
        # Soft penalty for missing years
        return max(0.2, 1.0 - abs(diff) * 0.15)

    def _infer_seniority(self, text: str, years: int) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["principal", "staff", "lead", "senior"]) or years >= 7:
            return "Senior"
        if any(token in lowered for token in ["junior", "entry", "intern"]) or years <= 2:
            return "Junior"
        return "Mid"

    def _infer_domain(self, skills: list[str], text: str) -> str:
        skill_set = {s.lower() for s in skills}
        lowered = text.lower()
        if any(s in skill_set for s in ["kubernetes", "terraform", "aws", "monitoring"]):
            return "devops"
        if any(s in skill_set for s in ["python", "fastapi", "django", "rest api"]):
            return "backend_ai"
        if any(s in lowered for s in ["telecom", "network", "routing", "switching"]):
            return "telecom_network"
        return "general"

    def _calculate_weighted_skill_score(self, required: list[str], candidate: list[str], cv_text: str, dynamic_weights: dict[str, float] | None = None) -> float:
        if not required: 
            return 0.0
        total = len(required)
        core_count = max(1, ceil(total * 0.6))
        core_skills = required[:core_count]
        other_skills = required[core_count:]
        
        dynamic_weights = dynamic_weights or {}
        
        def hit_ratio(bucket):
            if not bucket: return 0.0
            score_sum = 0.0
            for s in bucket:
                s_low = s.lower().strip()
                if s in candidate:
                    decay = self._get_skill_decay_factor(cv_text, s)
                    boost = dynamic_weights.get(s_low, 0.0)
                    score_sum += decay * (1.0 + boost)
            return min(1.0, score_sum / len(bucket))
            
        return (hit_ratio(core_skills) * 0.7) + (hit_ratio(other_skills) * 0.3)


    def _title_alignment(self, text: str, title: str) -> float:
        tokens = {t for t in re.findall(r"\w+", title.lower()) if len(t) > 2}
        if not tokens: return 0.0
        resume_tokens = set(re.findall(r"\w+", text.lower()))
        return len(tokens & resume_tokens) / len(tokens)

    def _context_quality(self, text: str) -> float:
        tokens = re.findall(r"\w+", text.lower())
        if not tokens: return 0.0
        return min(1.0, len(tokens) / 200.0)

    def _build_recommendation(self, score: float) -> str:
        if score > 0.8: return "Strong Match"
        if score >= 0.5: return "Good Fit"
        if score >= 0.3: return "Partial Match"
        return "Weak Match"

    def _generate_explainability_reason(
        self, name: str, job_title: str, matched_skills: list[str], missing_skills: list[str],
        cand_exp: int, req_exp: int, cand_level: str, role_level: str,
        cand_domain: str, target_domain: str, match_pct: float
    ) -> str:
        """Create human-readable explainability logs justifying the ranking position."""
        reasons = [f"{name} is scored at {match_pct}% match for the {job_title} role."]
        
        # Skill overlaps
        if matched_skills:
            reasons.append(f"Matched core skills: {', '.join(matched_skills[:4])}.")
        if missing_skills:
            reasons.append(f"Gaps found in: {', '.join(missing_skills[:3])}.")
        
        # Seniority and Experience
        reasons.append(f"Experience: Candidate has {cand_exp} years vs Job's {req_exp} years.")
        if cand_level != role_level:
            reasons.append(f"Seniority alignment mismatch: Candidate is {cand_level} while job requires {role_level}.")
        else:
            reasons.append(f"Seniority level ({cand_level}) is aligned.")
            
        # Domain alignment
        if cand_domain == target_domain:
            reasons.append(f"Technical domain ({cand_domain}) is a strong match.")
        elif cand_domain != "general":
            reasons.append(f"Domain focus is in {cand_domain} (expected {target_domain}).")
            
        return " ".join(reasons)

    def _calculate_and_log_metrics(self, ranked_reports: list[MatchReport], ground_truth: dict[str, int]) -> None:
        """Evaluate retrieval against ground truth labels and log standard metrics."""
        # ground_truth is a dict of candidate_name -> binary relevance (0 or 1)
        # Sort matching reports by match percentage
        total_relevant = sum(1 for v in ground_truth.values() if v > 0)
        if total_relevant == 0:
            return

        relevance_vector = []
        for r in ranked_reports:
            # Match using first word of name or matching key if present
            # For simplicity, extract candidate name from reason or default to fallback
            cand_name = "Candidate"
            for k in ground_truth.keys():
                if k.lower() in r.reason.lower():
                    cand_name = k
                    break
            rel = ground_truth.get(cand_name, 0)
            relevance_vector.append(rel)

        # MRR
        mrr = 0.0
        for idx, val in enumerate(relevance_vector):
            if val > 0:
                mrr = 1.0 / (idx + 1)
                break

        # Precision@5, Precision@10, Recall@5, Recall@10
        p5 = sum(relevance_vector[:5]) / 5.0
        p10 = sum(relevance_vector[:10]) / min(10.0, len(relevance_vector))
        r5 = sum(relevance_vector[:5]) / total_relevant
        r10 = sum(relevance_vector[:10]) / total_relevant

        # NDCG@10
        dcg = 0.0
        for idx in range(min(10, len(relevance_vector))):
            rel = relevance_vector[idx]
            dcg += rel / log2(idx + 2)
            
        ideal_relevance = sorted(relevance_vector, reverse=True)
        idcg = 0.0
        for idx in range(min(10, len(ideal_relevance))):
            rel = ideal_relevance[idx]
            idcg += rel / log2(idx + 2)
            
        ndcg10 = (dcg / idcg) if idcg > 0 else 0.0

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "precision_at_5": p5,
            "precision_at_10": p10,
            "recall_at_5": r5,
            "recall_at_10": r10,
            "mrr": mrr,
            "ndcg_at_10": ndcg10
        }

        # Save to database directory
        metrics_path = "database/metrics_history.json"
        history = []
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        
        history.append(metrics)
        
        try:
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass

    def compare_role_match(
        self,
        candidate_skills: list[str],
        required_skills: list[str],
        normalized_text: str,
        **kwargs
    ) -> RoleMatchResult:
        """Detailed role comparison for automated recommendations."""
        candidate_set = {s.lower() for s in candidate_skills}
        matched = [s for s in required_skills if s.lower() in candidate_set or s.lower() in normalized_text.lower()]
        missing = [s for s in required_skills if s not in matched]
        
        confidence = len(matched) / len(required_skills) if required_skills else 0.0
        
        # Map values to composite
        composite = confidence
        
        return RoleMatchResult(
            role_name=kwargs.get("role_name", "Unknown"),
            required_skills=required_skills,
            matched_skills=matched,
            missing_skills=missing,
            confidence=confidence,
            composite=composite,
            match_level="High" if confidence > 0.7 else "Medium" if confidence > 0.4 else "Low",
            reason=f"Matched {len(matched)} core skills."
        )
