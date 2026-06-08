from __future__ import annotations
import re
from typing import Any
from backend.app.schemas import HiringRules

# Hierarchy of education levels for comparison
EDUCATION_HIERARCHY = {
    "none": 0,
    "high school": 1,
    "bachelor": 2,
    "master": 3,
    "phd": 4
}

# Hierarchy of seniority levels
SENIORITY_HIERARCHY = {
    "junior": 1,
    "mid": 2,
    "senior": 3
}

# Default templates for roles
ROLE_RULE_TEMPLATES: dict[str, dict[str, Any]] = {
    "devops engineer": {
        "mandatory_skills": ["Kubernetes", "Terraform", "AWS"],
        "preferred_skills": ["Grafana", "Prometheus", "ArgoCD"],
        "min_experience_years": 5,
        "required_seniority": "Senior",
        "language": "English"
    },
    "backend python developer": {
        "mandatory_skills": ["Python", "FastAPI"],
        "preferred_skills": ["PostgreSQL", "Docker", "Redis"],
        "min_experience_years": 3,
        "required_seniority": "Mid",
        "language": "English"
    },
    "frontend react developer": {
        "mandatory_skills": ["React", "JavaScript"],
        "preferred_skills": ["TypeScript", "Tailwind", "Redux"],
        "min_experience_years": 3,
        "required_seniority": "Mid",
        "language": "English"
    },
    "machine learning engineer": {
        "mandatory_skills": ["Python", "Machine Learning"],
        "preferred_skills": ["PyTorch", "TensorFlow", "Scikit-Learn"],
        "min_experience_years": 4,
        "required_seniority": "Mid",
        "language": "English"
    }
}

def get_rule_template_for_job(job_title: str) -> HiringRules:
    """Returns a default HiringRules configuration based on job title."""
    title_low = job_title.lower()
    for role_name, config in ROLE_RULE_TEMPLATES.items():
        if role_name in title_low:
            return HiringRules(
                mandatory_skills=config.get("mandatory_skills", []),
                preferred_skills=config.get("preferred_skills", []),
                min_experience_years=config.get("min_experience_years"),
                required_seniority=config.get("required_seniority"),
                min_education="Bachelor",
                location="Remote",
                language=config.get("language")
            )
    
    # Generic fallback rules template
    return HiringRules(
        mandatory_skills=[],
        preferred_skills=[],
        min_experience_years=0,
        required_seniority="Junior",
        min_education="none"
    )

class CandidateAttributeExtractor:
    """Utility class to extract candidate attributes from resume text via heuristics."""
    
    def __init__(self, text: str):
        self.text = text.lower()
        
    def extract_education(self) -> str:
        if any(term in self.text for term in ["phd", "ph.d", "doctorate", "doctor of philosophy"]):
            return "phd"
        if any(term in self.text for term in ["master of science", "master's", "msc", "m.sc", "master degree"]):
            return "master"
        if any(term in self.text for term in ["bachelor of science", "bachelor's", "bsc", "b.sc", "bachelor degree", "undergraduate"]):
            return "bachelor"
        if any(term in self.text for term in ["high school", "diploma", "secondary school"]):
            return "high school"
        return "bachelor" # Default fallback
        
    def extract_seniority(self) -> str:
        if any(term in self.text for term in ["principal", "staff", "lead", "senior"]):
            return "Senior"
        if any(term in self.text for term in ["junior", "entry", "intern"]):
            return "Junior"
        return "Mid"
        
    def extract_languages(self) -> list[str]:
        languages = []
        if "english" in self.text:
            languages.append("english")
        if "german" in self.text:
            languages.append("german")
        if "french" in self.text:
            languages.append("french")
        if "arabic" in self.text:
            languages.append("arabic")
        return languages

    def check_language_level(self, language: str) -> str:
        # Check for CEFR levels near language mentions
        pattern = r"\b" + re.escape(language.lower()) + r"\b.*?([a-c][1-2])"
        match = re.search(pattern, self.text)
        if match:
            return match.group(1).upper()
        if "fluent" in self.text or "native" in self.text:
            return "C1"
        return "B2"
        
    def extract_location(self) -> str:
        if "remote" in self.text:
            return "Remote"
        locations = ["egypt", "cairo", "alexandria", "giza", "usa", "us", "uk", "germany", "berlin"]
        for loc in locations:
            if loc in self.text:
                return loc.title()
        return "Remote"
        
    def extract_work_authorization(self) -> str:
        if any(term in self.text for term in ["work authorization", "authorized to work", "citizen", "permanent resident"]):
            return "Authorized"
        if any(term in self.text for term in ["sponsorship required", "visa required"]):
            return "Requires Sponsorship"
        return "Authorized"
        
    def extract_salary_expectations(self) -> int | None:
        # Look for patterns like "$100,000", "120k", etc.
        matches = re.findall(r"\$?(\d{2,3}),?000\b", self.text)
        if matches:
            return int(matches[0])
        k_matches = re.findall(r"\b(\d{2,3})k\b", self.text)
        if k_matches:
            return int(k_matches[0]) * 1000
        return None

    def extract_industry(self) -> str:
        industries = {
            "finance": ["finance", "fintech", "banking", "trading"],
            "healthcare": ["healthcare", "medical", "pharma", "biotech"],
            "telecom": ["telecom", "telecommunications", "networking", "isp"],
            "retail": ["retail", "ecommerce", "e-commerce", "sales"],
            "automotive": ["automotive", "car", "self-driving"]
        }
        for ind, keywords in industries.items():
            if any(kw in self.text for kw in keywords):
                return ind.title()
        return "General"


class HiringRulesEngine:
    """Rules Engine to evaluate candidate details and resume texts against custom or template hiring rules."""
    
    def evaluate(
        self,
        candidate_name: str,
        cv_text: str,
        candidate_skills: list[str],
        years_of_experience: int,
        hiring_rules: HiringRules | None = None
    ) -> dict[str, Any]:
        """
        Evaluates candidate attributes against the configured hiring rules.
        Returns:
            {
                "rule_status": "PASSED" | "REJECTED",
                "reasons": list[str],
                "penalty": float
            }
        """
        if not hiring_rules:
            # Default fallback pass
            return {"rule_status": "PASSED", "reasons": [], "penalty": 0.0}

        rejection_reasons = []
        applied_penalty = 0.0
        extractor = CandidateAttributeExtractor(cv_text)

        # 1. Mandatory Skills Check
        if hiring_rules.mandatory_skills:
            candidate_skills_lower = {s.lower().strip() for s in candidate_skills}
            for skill in hiring_rules.mandatory_skills:
                skill_low = skill.lower().strip()
                if skill_low not in candidate_skills_lower:
                    rejection_reasons.append(f"Missing mandatory skill: {skill}")
                    applied_penalty += 0.30

        # 2. Preferred Skills Check (Informational, small penalty if missing)
        if hiring_rules.preferred_skills:
            candidate_skills_lower = {s.lower().strip() for s in candidate_skills}
            missing_preferred = [s for s in hiring_rules.preferred_skills if s.lower().strip() not in candidate_skills_lower]
            if missing_preferred:
                penalty_val = min(0.15, len(missing_preferred) * 0.02)
                applied_penalty += penalty_val
                # Not a hard reject reason, but logged in penalties

        # 3. Experience Requirements
        if hiring_rules.min_experience_years is not None and hiring_rules.min_experience_years > 0:
            if years_of_experience < hiring_rules.min_experience_years:
                rejection_reasons.append(f"Experience below minimum requirement: {years_of_experience} yrs vs required {hiring_rules.min_experience_years} yrs")
                applied_penalty += 0.20

        # 4. Seniority Requirements
        if hiring_rules.required_seniority:
            cand_seniority = extractor.extract_seniority().lower()
            req_seniority = hiring_rules.required_seniority.lower()
            cand_val = SENIORITY_HIERARCHY.get(cand_seniority, 2)
            req_val = SENIORITY_HIERARCHY.get(req_seniority, 2)
            if cand_val < req_val:
                rejection_reasons.append(f"Seniority mismatch: Candidate is {cand_seniority.title()} but job requires {hiring_rules.required_seniority.title()}")
                applied_penalty += 0.05

        # 5. Education Requirements
        if hiring_rules.min_education:
            cand_edu = extractor.extract_education().lower()
            req_edu = hiring_rules.min_education.lower()
            cand_val = EDUCATION_HIERARCHY.get(cand_edu, 2)
            req_val = EDUCATION_HIERARCHY.get(req_edu, 2)
            if cand_val < req_val:
                rejection_reasons.append(f"Education requirement not met: Candidate has {cand_edu.title()} but job requires {hiring_rules.min_education.title()}")
                applied_penalty += 0.10

        # 6. Location Requirements
        if hiring_rules.location:
            cand_loc = extractor.extract_location().lower()
            req_loc = hiring_rules.location.lower()
            if req_loc != "remote" and req_loc not in cand_loc and "remote" not in cand_loc:
                # Not a strict rejection, but applies location penalty
                applied_penalty += 0.10

        # 7. Language Requirements
        if hiring_rules.language:
            req_lang = hiring_rules.language.lower()
            languages = extractor.extract_languages()
            if req_lang not in languages:
                rejection_reasons.append(f"Missing required language capability: {hiring_rules.language}")
                applied_penalty += 0.15

        # 8. Salary Requirements
        if hiring_rules.max_salary is not None:
            cand_salary = extractor.extract_salary_expectations()
            if cand_salary and cand_salary > hiring_rules.max_salary:
                rejection_reasons.append(f"Salary expectations ({cand_salary}) exceed max budget ({hiring_rules.max_salary})")
                applied_penalty += 0.10

        # 9. Employment Type Requirements
        if hiring_rules.employment_type:
            cand_text_low = cv_text.lower()
            req_type = hiring_rules.employment_type.lower()
            # If the candidate explicitly mentions looking for something else (e.g. looking for freelance when full-time required)
            if req_type == "full-time" and "part-time" in cand_text_low and "full-time" not in cand_text_low:
                rejection_reasons.append("Employment type mismatch: Candidate seeks Part-time, required Full-time")
                applied_penalty += 0.05

        # 10. Work Authorization Requirements
        if hiring_rules.work_authorization:
            cand_auth = extractor.extract_work_authorization()
            req_auth = hiring_rules.work_authorization
            if req_auth == "Authorized" and cand_auth == "Requires Sponsorship":
                rejection_reasons.append("Work authorization required; sponsorship not provided")
                applied_penalty += 0.20

        # 11. Industry-Specific Requirements
        if hiring_rules.industry:
            cand_industry = extractor.extract_industry().lower()
            req_industry = hiring_rules.industry.lower()
            if req_industry != "general" and cand_industry != "general" and req_industry != cand_industry:
                applied_penalty += 0.05

        status = "REJECTED" if rejection_reasons else "PASSED"
        
        return {
            "rule_status": status,
            "reasons": rejection_reasons,
            "penalty": applied_penalty
        }
