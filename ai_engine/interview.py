from __future__ import annotations


class InterviewCoach:
    def reply(self, message: str) -> str:
        normalized = message.lower()
        if "python" in normalized or "بايثون" in normalized:
            return "احكيلي عن مشروع بايثون اشتغلت عليه والـ trade-offs اللي أخدتها."
        if "ml" in normalized or "machine learning" in normalized or "تعلم" in normalized:
            return "إزاي بتقلل الـ overfitting في النماذج اللي بتشتغل عليها؟"
        return "ممكن تديني مثال عملي على مشكلة وحلّيتها بشكل قابل للقياس؟"
