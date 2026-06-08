"""
Coding Interview Agent — Phase 2: Advanced Interview Intelligence

Generates coding challenges, evaluates submitted code via static analysis,
estimates complexity, and produces detailed feedback.
"""
from __future__ import annotations

import ast
import json
import uuid
import re
from typing import Any
from datetime import datetime, timezone

from ai_engine.agents.base import AgentMessage, BaseAgent

# Curated problem bank organized by difficulty and domain
PROBLEM_BANK = {
    "easy": [
        {"id": "two_sum", "title": "Two Sum", "description": "Given an array of integers and a target, return indices of two numbers that add up to the target.", "expected_complexity": "O(n)", "tags": ["arrays", "hash_map"]},
        {"id": "reverse_string", "title": "Reverse String", "description": "Write a function that reverses a string in-place.", "expected_complexity": "O(n)", "tags": ["strings"]},
        {"id": "valid_parentheses", "title": "Valid Parentheses", "description": "Given a string containing '(', ')', '{', '}', '[', ']', determine if the input string is valid.", "expected_complexity": "O(n)", "tags": ["stack"]},
    ],
    "medium": [
        {"id": "lru_cache", "title": "LRU Cache", "description": "Design a data structure that follows the constraints of a Least Recently Used cache.", "expected_complexity": "O(1)", "tags": ["design", "hash_map", "linked_list"]},
        {"id": "merge_intervals", "title": "Merge Intervals", "description": "Given an array of intervals, merge all overlapping intervals.", "expected_complexity": "O(n log n)", "tags": ["arrays", "sorting"]},
        {"id": "binary_search_rotated", "title": "Search in Rotated Sorted Array", "description": "Search for a target value in a rotated sorted array.", "expected_complexity": "O(log n)", "tags": ["binary_search"]},
    ],
    "hard": [
        {"id": "median_two_sorted", "title": "Median of Two Sorted Arrays", "description": "Find the median of two sorted arrays with O(log(m+n)) complexity.", "expected_complexity": "O(log(min(m,n)))", "tags": ["binary_search", "divide_and_conquer"]},
        {"id": "word_ladder", "title": "Word Ladder", "description": "Find the shortest transformation sequence from beginWord to endWord.", "expected_complexity": "O(M^2 * N)", "tags": ["bfs", "graph"]},
    ],
}


class CodingInterviewAgent(BaseAgent):
    """Generates and evaluates coding challenges."""

    def __init__(self) -> None:
        super().__init__(name="coding_interview")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "generate_challenge":
            result = self.generate_challenge(payload)
        elif task == "evaluate_submission":
            result = self.evaluate_submission(payload)
        else:
            raise ValueError(f"CodingInterviewAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    def generate_challenge(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Select a coding problem based on difficulty and tags."""
        difficulty = payload.get("difficulty", "medium")
        tags = set(payload.get("tags", []))

        problems = PROBLEM_BANK.get(difficulty, PROBLEM_BANK["medium"])

        if tags:
            matched = [p for p in problems if tags & set(p["tags"])]
            problem = matched[0] if matched else problems[0]
        else:
            problem = problems[0]

        return {
            "challenge_id": str(uuid.uuid4()),
            "problem": problem,
            "difficulty": difficulty,
            "time_limit_minutes": {"easy": 15, "medium": 30, "hard": 45}.get(difficulty, 30),
        }

    def evaluate_submission(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate submitted Python code using AST analysis."""
        code = payload.get("code", "")
        problem_id = payload.get("problem_id", "")

        analysis = self._analyze_code(code)
        complexity = self._estimate_complexity(code)
        style_score = self._score_style(code)

        # Compute overall score
        correctness = 70 if analysis["has_function"] and not analysis["syntax_errors"] else 30
        efficiency = 80 if "O(n)" in complexity.get("estimated", "") or "O(1)" in complexity.get("estimated", "") else 50
        overall = (correctness * 0.5) + (efficiency * 0.3) + (style_score * 0.2)

        feedback = []
        if analysis["syntax_errors"]:
            feedback.append(f"Syntax error detected: {analysis['syntax_errors']}")
        if not analysis["has_function"]:
            feedback.append("No function definition found. Wrap your solution in a function.")
        if analysis["uses_recursion"]:
            feedback.append("Recursive approach detected. Consider iterative alternatives for large inputs.")
        if style_score < 60:
            feedback.append("Consider adding docstrings and meaningful variable names.")

        return {
            "overall_score": round(overall, 1),
            "correctness_score": correctness,
            "efficiency_score": efficiency,
            "style_score": round(style_score, 1),
            "complexity_analysis": complexity,
            "code_analysis": analysis,
            "feedback": feedback,
        }

    def _analyze_code(self, code: str) -> dict[str, Any]:
        """Parse code AST for structural analysis."""
        result = {
            "has_function": False,
            "function_count": 0,
            "has_class": False,
            "uses_recursion": False,
            "line_count": len(code.strip().split("\n")),
            "syntax_errors": None,
        }

        try:
            tree = ast.parse(code)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            result["has_function"] = len(functions) > 0
            result["function_count"] = len(functions)
            result["has_class"] = any(isinstance(n, ast.ClassDef) for n in ast.walk(tree))

            # Check for recursion (function calling itself)
            for func in functions:
                for node in ast.walk(func):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id == func.name:
                            result["uses_recursion"] = True
        except SyntaxError as e:
            result["syntax_errors"] = str(e)

        return result

    def _estimate_complexity(self, code: str) -> dict[str, Any]:
        """Heuristic-based complexity estimation."""
        loop_count = len(re.findall(r"\bfor\b|\bwhile\b", code))
        nested_loops = len(re.findall(r"for.*:\s*\n\s+for|while.*:\s*\n\s+while", code))

        if nested_loops > 0:
            estimated = "O(n^2) or higher"
        elif loop_count == 1:
            estimated = "O(n)"
        elif loop_count == 0:
            estimated = "O(1)"
        else:
            estimated = f"O(n) — {loop_count} sequential loops"

        has_sort = bool(re.search(r"\.sort\(|sorted\(", code))
        if has_sort:
            estimated = "O(n log n) — sorting detected"

        return {
            "estimated": estimated,
            "loop_count": loop_count,
            "nested_loops": nested_loops,
            "uses_sorting": has_sort,
        }

    def _score_style(self, code: str) -> float:
        """Score code style quality."""
        score = 50.0
        if '"""' in code or "'''" in code:
            score += 15  # docstrings
        if re.search(r"#\s+\w", code):
            score += 10  # comments
        lines = code.split("\n")
        if all(len(line) <= 100 for line in lines):
            score += 10  # line length
        if not re.search(r"[a-z]\d{3,}", code):
            score += 15  # no cryptic variable names
        return min(100.0, score)


coding_interview_agent = CodingInterviewAgent()
