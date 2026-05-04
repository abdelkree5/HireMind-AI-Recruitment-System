from __future__ import annotations

import re

class CandidateReasoningEngine:
    def infer_seniority(self, text: str) -> str:
        years = self.extract_years_of_experience(text)
        leadership = self.score_leadership(text)
        
        if years >= 7 or leadership > 0.6:
            return "Senior"
        if years >= 3 or leadership > 0.3:
            return "Mid"
        return "Junior"

    def extract_years_of_experience(self, text: str) -> int:
        explicit = [int(v) for v in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|year)", text.lower())]
        if explicit: return max(explicit)
        
        # Count date spans
        spans = re.findall(r"(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:present|current|(?:19|20)\d{2})", text.lower())
        return len(spans) * 2

    def score_leadership(self, text: str) -> float:
        keywords = ["lead", "led", "manager", "managed", "owner", "principal", "architect", "mentored"]
        hits = sum(text.lower().count(token) for token in keywords)
        return min(1.0, hits / 4.0)

    def score_project_depth(self, text: str) -> float:
        depth_terms = ["designed", "implemented", "built", "deployed", "integrated", "optimized", "production"]
        hits = sum(text.lower().count(token) for token in depth_terms)
        return min(1.0, hits / 6.0)
