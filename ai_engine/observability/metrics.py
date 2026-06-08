"""
Platform Metrics — Retrieval Quality, Ranking Quality, Decision Quality

Provides metric computation functions for evaluating agent pipeline
performance without requiring external LLM API keys.
"""
from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# Retrieval Quality Metrics
# ---------------------------------------------------------------------------

def precision_at_k(relevant_ids: set[str], retrieved_ids: list[str], k: int) -> float:
    """Precision@K: fraction of top-K retrieved that are relevant."""
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r in relevant_ids)
    return round(hits / k, 4)


def recall_at_k(relevant_ids: set[str], retrieved_ids: list[str], k: int) -> float:
    """Recall@K: fraction of all relevant items found in top-K."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for r in top_k if r in relevant_ids)
    return round(hits / len(relevant_ids), 4)


def ndcg_at_k(relevant_ids: set[str], retrieved_ids: list[str], k: int) -> float:
    """NDCG@K: Normalized Discounted Cumulative Gain at position K."""
    top_k = retrieved_ids[:k]
    dcg = sum(
        (1.0 / math.log2(i + 2)) for i, r in enumerate(top_k) if r in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    if idcg == 0:
        return 0.0
    return round(dcg / idcg, 4)


def mean_reciprocal_rank(relevant_ids: set[str], retrieved_ids: list[str]) -> float:
    """MRR: reciprocal of the rank of the first relevant item."""
    for i, r in enumerate(retrieved_ids):
        if r in relevant_ids:
            return round(1.0 / (i + 1), 4)
    return 0.0


# ---------------------------------------------------------------------------
# Ranking Quality Metrics
# ---------------------------------------------------------------------------

def spearman_correlation(ranks_a: list[int], ranks_b: list[int]) -> float:
    """
    Spearman rank correlation between AI ranking and recruiter ranking.
    Returns a value in [-1, 1] where 1 = perfect agreement.
    """
    n = len(ranks_a)
    if n < 2:
        return 0.0
    d_sq_sum = sum((a - b) ** 2 for a, b in zip(ranks_a, ranks_b))
    return round(1 - (6 * d_sq_sum) / (n * (n**2 - 1)), 4)


# ---------------------------------------------------------------------------
# Decision Quality Metrics
# ---------------------------------------------------------------------------

def compute_decision_metrics(feedback_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Computes FP rate, FN rate, accuracy, and recruiter-AI agreement
    from a list of recruiter_feedback records.
    """
    total = len(feedback_rows)
    if total == 0:
        return {
            "total": 0,
            "accuracy": 0.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
            "agreement_rate": 0.0,
            "hired_rate": 0.0,
        }

    true_positive = 0   # AI high score + recruiter accepted
    false_positive = 0  # AI high score + recruiter rejected
    true_negative = 0   # AI low score + recruiter rejected
    false_negative = 0  # AI low score + recruiter accepted
    hired = 0

    for r in feedback_rows:
        ai_score = float(r.get("ai_score", 0))
        is_accepted = int(r.get("is_accepted", 0))
        is_hired = int(r.get("is_hired", 0))
        ai_recommends = 1 if ai_score >= 70.0 else 0

        if ai_recommends == 1 and is_accepted == 1:
            true_positive += 1
        elif ai_recommends == 1 and is_accepted == 0:
            false_positive += 1
        elif ai_recommends == 0 and is_accepted == 0:
            true_negative += 1
        elif ai_recommends == 0 and is_accepted == 1:
            false_negative += 1

        if is_hired:
            hired += 1

    accuracy = (true_positive + true_negative) / total
    fp_rate = false_positive / max(1, false_positive + true_negative)
    fn_rate = false_negative / max(1, false_negative + true_positive)
    agreement = (true_positive + true_negative) / total

    return {
        "total": total,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "accuracy": round(accuracy, 4),
        "false_positive_rate": round(fp_rate, 4),
        "false_negative_rate": round(fn_rate, 4),
        "agreement_rate": round(agreement, 4),
        "hired_rate": round(hired / total, 4),
    }


# ---------------------------------------------------------------------------
# Latency Metrics
# ---------------------------------------------------------------------------

def compute_latency_stats(latencies_ms: list[float]) -> dict[str, float]:
    """Compute p50, p95, p99, and mean latency from a list of ms values."""
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "count": 0}
    sorted_lat = sorted(latencies_ms)
    n = len(sorted_lat)

    def percentile(p: float) -> float:
        idx = int(math.ceil(p / 100.0 * n)) - 1
        return round(sorted_lat[max(0, min(idx, n - 1))], 2)

    return {
        "p50": percentile(50),
        "p95": percentile(95),
        "p99": percentile(99),
        "mean": round(sum(sorted_lat) / n, 2),
        "count": n,
    }


def get_agent_latency_stats() -> dict[str, dict[str, float]]:
    """Query per-agent latency stats from the agent_traces table."""
    try:
        from database.connection import get_connection
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT agent_name, latency_ms FROM agent_traces WHERE status = 'completed'"
            ).fetchall()

        agent_latencies: dict[str, list[float]] = {}
        for r in rows:
            agent_latencies.setdefault(r["agent_name"], []).append(float(r["latency_ms"]))

        return {
            agent: compute_latency_stats(lats)
            for agent, lats in agent_latencies.items()
        }
    except Exception:
        return {}


def get_error_rates() -> dict[str, float]:
    """Compute per-agent error rate from agent_traces."""
    try:
        from database.connection import get_connection
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT agent_name, status FROM agent_traces"
            ).fetchall()

        totals: dict[str, int] = {}
        failures: dict[str, int] = {}
        for r in rows:
            agent = r["agent_name"]
            totals[agent] = totals.get(agent, 0) + 1
            if r["status"] == "failed":
                failures[agent] = failures.get(agent, 0) + 1

        return {
            agent: round(failures.get(agent, 0) / total, 4)
            for agent, total in totals.items()
        }
    except Exception:
        return {}


def get_full_platform_metrics() -> dict[str, Any]:
    """Aggregate all platform observability metrics."""
    from database.connection import get_connection

    try:
        with get_connection() as conn:
            feedback_rows = [
                dict(r) for r in conn.execute("SELECT * FROM recruiter_feedback").fetchall()
            ]
    except Exception:
        feedback_rows = []

    return {
        "decision_quality": compute_decision_metrics(feedback_rows),
        "latency_per_agent": get_agent_latency_stats(),
        "error_rates": get_error_rates(),
    }
