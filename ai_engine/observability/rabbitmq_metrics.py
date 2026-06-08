"""
RabbitMQ Observability — Queue Depth, DLQ Counts, and Retry Metrics
"""
from __future__ import annotations

import os
import logging
from typing import Any

try:
    import pika
    from pika.exceptions import AMQPConnectionError
except ImportError:  # pragma: no cover
    pika = None

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
AGENT_QUEUES = [
    "hiremind.agent.supervisor",
    "hiremind.agent.cv_analysis",
    "hiremind.agent.job_analysis",
    "hiremind.agent.matching",
    "hiremind.agent.hiring_rules",
    "hiremind.agent.recruiter_feedback",
    "hiremind.agent.interview",
]
RETRY_SUFFIX = ".retry"
DLQ_SUFFIX = ".dlq"


def _connect() -> Any | None:
    if pika is None:
        return None
    try:
        return pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    except AMQPConnectionError as exc:
        logger.warning(f"RabbitMQ observability connection failed: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"RabbitMQ observability error: {exc}")
        return None


def _inspect_queue(channel: Any, queue_name: str) -> dict[str, int]:
    try:
        result = channel.queue_declare(queue=queue_name, passive=True)
        return {
            "messages_ready": result.method.message_count,
            "consumers": result.method.consumer_count,
        }
    except Exception:
        return {"messages_ready": 0, "consumers": 0}


def get_rabbitmq_queue_metrics() -> dict[str, Any]:
    """Return queue depth and consumer counts for the HireMind RabbitMQ topology."""
    connection = _connect()
    if connection is None:
        return {"error": "RabbitMQ unavailable or pika not installed"}

    try:
        channel = connection.channel()
        metrics: dict[str, Any] = {}
        for queue in AGENT_QUEUES:
            metrics[queue] = _inspect_queue(channel, queue)
            metrics[f"{queue}{RETRY_SUFFIX}"] = _inspect_queue(channel, queue + RETRY_SUFFIX)
            metrics[f"{queue}{DLQ_SUFFIX}"] = _inspect_queue(channel, queue + DLQ_SUFFIX)
        return metrics
    finally:
        try:
            connection.close()
        except Exception:
            pass
