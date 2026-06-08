"""
Behavioral Interview Agent — Phase 2: Advanced Interview Intelligence

STAR-method assessment for leadership, communication, problem-solving,
and culture fit dimensions.
"""
from __future__ import annotations

import re
from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


# Behavioral question bank by dimension
BEHAVIORAL_QUESTIONS = {
    "leadership": [
        "Tell me about a time you led a team through a difficult project.",
        "Describe a situation where you had to make a tough decision without all the information.",
        "How have you mentored or developed team members?",
    ],
    "communication": [
        "Describe a time you had to explain a complex technical concept to a non-technical stakeholder.",
        "Tell me about a conflict you resolved with a colleague.",
        "How do you handle disagreements during code reviews?",
    ],
    "problem_solving": [
        "Walk me through the most challenging bug you've ever debugged.",
        "Describe a time you had to learn a new technology quickly to solve a problem.",
        "Tell me about a project where you had to make architectural trade-offs.",
    ],
    "culture_fit": [
        "What kind of work environment helps you do your best work?",
        "How do you handle feedback that you disagree with?",
        "Describe your ideal team and working style.",
    ],
}

# Signal keywords for scoring each dimension
DIMENSION_SIGNALS = {
    "leadership": {
        "positive": ["led", "managed", "coordinated", "delegated", "mentored", "inspired", "vision", "strategy", "guided", "empowered"],
        "negative": ["followed", "was told", "didn't lead"],
    },
    "communication": {
        "positive": ["explained", "presented", "documented", "communicated", "clarified", "summarized", "aligned", "negotiated", "facilitated"],
        "negative": ["confused", "misunderstood", "unclear"],
    },
    "problem_solving": {
        "positive": ["analyzed", "debugged", "investigated", "solved", "optimized", "refactored", "root cause", "hypothesis", "systematic", "traced"],
        "negative": ["gave up", "couldn't figure out"],
    },
    "culture_fit": {
        "positive": ["collaboration", "team", "feedback", "learn", "adapt", "flexible", "growth", "iterate", "inclusive", "open"],
        "negative": ["alone", "don't like feedback", "rigid"],
    },
}


class BehavioralInterviewAgent(BaseAgent):
    """Conducts STAR-method behavioral assessments."""

    def __init__(self) -> None:
        super().__init__(name="behavioral_interview")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "generate_questions":
            result = self.generate_questions(payload)
        elif task == "evaluate_answer":
            result = self.evaluate_answer(payload)
        elif task == "full_assessment":
            result = self.full_assessment(payload)
        else:
            raise ValueError(f"BehavioralInterviewAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    def generate_questions(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate behavioral questions for specified dimensions."""
        dimensions = payload.get("dimensions", list(BEHAVIORAL_QUESTIONS.keys()))
        count_per = payload.get("count_per_dimension", 1)

        questions = []
        for dim in dimensions:
            dim_qs = BEHAVIORAL_QUESTIONS.get(dim, [])
            for q in dim_qs[:count_per]:
                questions.append({"dimension": dim, "question": q})

        return {"questions": questions, "total": len(questions)}

    def evaluate_answer(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single behavioral answer using STAR analysis."""
        answer = payload.get("answer", "")
        dimension = payload.get("dimension", "leadership")

        star = self._detect_star(answer)
        signal_score = self._score_signals(answer, dimension)
        depth_score = self._score_depth(answer)

        # Composite scoring
        star_weight = sum(1 for v in star.values() if v) / 4.0
        overall = (star_weight * 40) + (signal_score * 35) + (depth_score * 25)

        feedback = []
        if not star["situation"]:
            feedback.append("Missing situation context — describe the specific scenario.")
        if not star["task"]:
            feedback.append("Missing task description — what was your responsibility?")
        if not star["action"]:
            feedback.append("Missing action details — what did YOU specifically do?")
        if not star["result"]:
            feedback.append("Missing result — what was the measurable outcome?")

        return {
            "dimension": dimension,
            "overall_score": round(overall, 1),
            "star_analysis": star,
            "signal_score": round(signal_score * 100, 1),
            "depth_score": round(depth_score * 100, 1),
            "feedback": feedback,
        }

    def full_assessment(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run full behavioral assessment across all dimensions."""
        answers = payload.get("answers", {})  # dimension -> answer text
        results = {}
        total_score = 0

        for dimension in ["leadership", "communication", "problem_solving", "culture_fit"]:
            answer = answers.get(dimension, "")
            if answer:
                eval_result = self.evaluate_answer({"answer": answer, "dimension": dimension})
                results[dimension] = eval_result
                total_score += eval_result["overall_score"]
            else:
                results[dimension] = {"overall_score": 0, "feedback": ["No answer provided."]}

        dimensions_with_answers = sum(1 for d in results.values() if d["overall_score"] > 0)
        avg_score = total_score / max(1, dimensions_with_answers)

        return {
            "dimension_results": results,
            "average_score": round(avg_score, 1),
            "recommendation": "Strong Hire" if avg_score >= 75 else "Hire" if avg_score >= 55 else "Needs Evaluation" if avg_score >= 35 else "Pass",
            "strongest_dimension": max(results, key=lambda d: results[d]["overall_score"]) if results else None,
            "weakest_dimension": min(results, key=lambda d: results[d]["overall_score"]) if results else None,
        }

    def _detect_star(self, text: str) -> dict[str, bool]:
        """Detect STAR (Situation, Task, Action, Result) components."""
        lower = text.lower()
        return {
            "situation": bool(re.search(r"\b(situation|context|background|scenario|when|at|during)\b", lower)),
            "task": bool(re.search(r"\b(task|responsible|goal|objective|needed to|had to|assigned)\b", lower)),
            "action": bool(re.search(r"\b(i (did|built|led|created|implemented|designed|developed|wrote|organized|coordinated))\b", lower)),
            "result": bool(re.search(r"\b(result|outcome|impact|improved|reduced|increased|achieved|delivered|success)\b", lower)),
        }

    def _score_signals(self, text: str, dimension: str) -> float:
        """Score answer based on positive/negative signal keywords."""
        signals = DIMENSION_SIGNALS.get(dimension, {"positive": [], "negative": []})
        lower = text.lower()

        pos_hits = sum(1 for kw in signals["positive"] if kw in lower)
        neg_hits = sum(1 for kw in signals["negative"] if kw in lower)

        return min(1.0, max(0.0, (pos_hits * 0.15) - (neg_hits * 0.2)))

    def _score_depth(self, text: str) -> float:
        """Score answer depth based on length and specificity."""
        words = text.split()
        if len(words) < 20:
            return 0.2
        if len(words) < 50:
            return 0.4
        if len(words) < 100:
            return 0.7
        return min(1.0, 0.7 + (len(words) - 100) * 0.003)


behavioral_interview_agent = BehavioralInterviewAgent()
