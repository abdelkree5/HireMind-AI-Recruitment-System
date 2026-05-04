from __future__ import annotations
import re

class CandidateReasoningEngine:
    def infer_seniority(self, text: str) -> str:
        years = self.extract_years_of_experience(text)
        lowered = text.lower()
        if any(token in lowered for token in ["principal", "staff", "lead", "senior"]) or years >= 7:
            return "Senior"
        if any(token in lowered for token in ["junior", "intern", "entry"]) or years <= 2:
            return "Junior"
        return "Mid"

    def infer_domain(self, skills: list[str], text: str) -> str:
        skill_set = {s.lower() for s in skills}
        lowered = text.lower()
        if any(s in skill_set for s in ["kubernetes", "terraform", "aws", "monitoring"]):
            return "devops"
        if any(s in skill_set for s in ["python", "fastapi", "django", "rest api"]):
            return "backend_ai"
        if any(s in lowered for s in ["telecom", "network", "routing", "switching"]):
            return "telecom_network"
        return "general"

    def extract_years_of_experience(self, text: str) -> int:
        explicit = [int(v) for v in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|year)", text.lower())]
        if explicit: return max(explicit)
        spans = re.findall(r"(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:present|current|(?:19|20)\d{2})", text.lower())
        return len(spans) * 2
