"""
Agent Message Bus — RabbitMQ-backed Inter-Agent Communication Layer

This component replaces in-process agent communication with a production-grade
RabbitMQ architecture. It preserves audit trail persistence while introducing:
- durable queues
- topic exchanges
- routing keys
- retry queues
- dead-letter queues
- acknowledgements
- event persistence
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from ai_engine.agents.base import AgentMessage
from ai_engine.agents.events import DomainEvent, EventType

logger = logging.getLogger(__name__)

try:
    import pika
    from pika.exceptions import AMQPConnectionError
    from pika.spec import BasicProperties
except ImportError:  # pragma: no cover
    pika = None
    BasicProperties = None  # type: ignore


class InMemoryAgentMessageBus:
    """
    In-memory fallback bus for development and test environments.

    This retains the original publish/subscribe contract while preserving
    historical audit persistence.
    """

    def __init__(self) -> None:
        self._queues: dict[str, deque[AgentMessage]] = defaultdict(deque)
        self._buffer: dict[str, deque[AgentMessage]] = defaultdict(deque)

    def publish(self, message: AgentMessage) -> None:
        self._persist_message(message)
        if message.receiver_agent != "supervisor":
            self._execute_agent(message.receiver_agent, message)
        else:
            self._queues[message.receiver_agent].append(message)

    def publish_event(self, event: DomainEvent) -> None:
        self._persist_event(event)

    def subscribe(self, agent_name: str) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        buffer = self._buffer[agent_name]
        while buffer:
            messages.append(buffer.popleft())

        queue = self._queues[agent_name]
        while queue:
            messages.append(queue.popleft())
        return messages

    def wait_for_response(
        self,
        receiver_agent: str,
        trace_id: str,
        workflow_id: str,
        timeout_seconds: int = 30,
    ) -> AgentMessage | None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            messages = self.subscribe(receiver_agent)
            for msg in messages:
                if msg.trace_id == trace_id and msg.workflow_id == workflow_id:
                    return msg
                self._buffer[receiver_agent].append(msg)
            time.sleep(0.05)
        return None

    def get_conversation(self, workflow_id: str) -> list[dict[str, Any]]:
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT sender_agent, receiver_agent, task_type,
                           payload_json, status, created_at
                    FROM agent_messages
                    WHERE workflow_id = ?
                    ORDER BY created_at ASC
                    """,
                    (workflow_id,),
                ).fetchall()
            return [
                {
                    "sender_agent": r["sender_agent"],
                    "receiver_agent": r["receiver_agent"],
                    "task_type": r["task_type"],
                    "payload": json.loads(r["payload_json"] or "{}"),
                    "status": r["status"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        except Exception:
            return []

    def _persist_message(self, message: AgentMessage) -> None:
        try:
            from database.connection import get_connection
            msg_id = uuid.uuid4().hex
            created_at = datetime.now(timezone.utc).isoformat()
            payload_json = json.dumps(message.payload or {})
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_messages
                        (id, workflow_id, sender_agent, receiver_agent,
                         task_type, payload_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg_id,
                        message.workflow_id,
                        message.sender_agent,
                        message.receiver_agent,
                        message.task_type,
                        payload_json,
                        message.status,
                        created_at,
                    ),
                )
        except Exception:
            pass

    def _persist_event(self, event: DomainEvent) -> None:
        try:
            from database.connection import get_connection
            event_id = uuid.uuid4().hex
            created_at = datetime.now(timezone.utc).isoformat()
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO domain_events
                        (id, workflow_id, event_type, aggregate_id,
                         payload_json, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event.workflow_id,
                        event.event_type.value,
                        event.aggregate_id,
                        json.dumps(event.payload or {}),
                        json.dumps(event.metadata or {}),
                        created_at,
                    ),
                )
        except Exception:
            pass

    def _execute_agent(self, agent_name: str, message: AgentMessage) -> None:
        if agent_name == "cv_analysis":
            from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent
            agent = CVAnalysisAgent()
        elif agent_name == "job_analysis":
            from ai_engine.agents.job_analysis_agent import JobAnalysisAgent
            agent = JobAnalysisAgent()
        elif agent_name == "matching":
            from ai_engine.agents.matching_agent import MatchingAgent
            agent = MatchingAgent()
        elif agent_name == "hiring_rules":
            from ai_engine.agents.hiring_rules_agent import HiringRulesAgent
            agent = HiringRulesAgent()
        elif agent_name == "recruiter_feedback":
            from ai_engine.agents.recruiter_feedback_agent import RecruiterFeedbackAgent
            agent = RecruiterFeedbackAgent()
        elif agent_name == "interview":
            from ai_engine.agents.interview_agent import InterviewAgent
            agent = InterviewAgent()
        else:
            self._queues[message.receiver_agent].append(message)
            return

        result_msg = agent.execute(message)
        self._queues[result_msg.receiver_agent].append(result_msg)


class RabbitMQAgentMessageBus:
    EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "hiremind.agent.exchange")
    DLX = os.getenv("RABBITMQ_DLX", "hiremind.dlx")
    EVENT_EXCHANGE = os.getenv("RABBITMQ_EVENT_EXCHANGE", "hiremind.domain.exchange")
    QUEUE_PREFIX = os.getenv("RABBITMQ_QUEUE_PREFIX", "hiremind.agent")
    URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    MAX_RETRY_ATTEMPTS = 3

    KNOWN_AGENTS = [
        "supervisor",
        "cv_analysis",
        "job_analysis",
        "matching",
        "hiring_rules",
        "recruiter_feedback",
        "interview",
    ]

    def __init__(self) -> None:
        if pika is None:
            raise RuntimeError("pika is required for RabbitMQAgentMessageBus")

        self._local_buffer: dict[str, deque[AgentMessage]] = defaultdict(deque)
        self._worker_threads: list[threading.Thread] = []
        self._thread_local = threading.local()
        
        # Setup topology requires an initial connection
        initial_conn = self._connect()
        if initial_conn is None:
            raise RuntimeError("Unable to connect to RabbitMQ")
        self._setup_topology(initial_conn.channel())
        try:
            initial_conn.close()
        except Exception:
            pass

        self._start_agent_workers()

    def _get_thread_channel(self) -> Any:
        if not hasattr(self._thread_local, "connection") or self._thread_local.connection is None or self._thread_local.connection.is_closed:
            self._thread_local.connection = self._connect()
            if self._thread_local.connection:
                self._thread_local.channel = self._thread_local.connection.channel()
            else:
                raise RuntimeError("Failed to create thread-local RabbitMQ connection")
        return self._thread_local.channel

    def _connect(self) -> Any | None:
        try:
            parameters = pika.URLParameters(self.URL)
            return pika.BlockingConnection(parameters)
        except AMQPConnectionError as exc:
            logger.warning("RabbitMQ connection failed: %s", exc)
            return None
        except Exception as exc:
            logger.warning("RabbitMQ connection error: %s", exc)
            return None

    def _setup_topology(self, channel: Any) -> None:
        channel.exchange_declare(exchange=self.EXCHANGE, exchange_type="topic", durable=True)
        channel.exchange_declare(exchange=self.DLX, exchange_type="topic", durable=True)
        channel.exchange_declare(exchange=self.EVENT_EXCHANGE, exchange_type="topic", durable=True)

        for agent_name in self.KNOWN_AGENTS:
            self._declare_agent_queue(agent_name, channel)

    def _agent_queue_name(self, agent_name: str) -> str:
        return f"{self.QUEUE_PREFIX}.{agent_name}"

    def _retry_queue_name(self, agent_name: str) -> str:
        return f"{self._agent_queue_name(agent_name)}.retry"

    def _dlq_queue_name(self, agent_name: str) -> str:
        return f"{self._agent_queue_name(agent_name)}.dlq"

    def _routing_key(self, agent_name: str) -> str:
        return f"agent.{agent_name}"

    def _dlq_routing_key(self, agent_name: str) -> str:
        return f"dlq.agent.{agent_name}"

    def _declare_agent_queue(self, agent_name: str, channel: Any) -> None:
        queue_name = self._agent_queue_name(agent_name)
        retry_name = self._retry_queue_name(agent_name)
        dlq_name = self._dlq_queue_name(agent_name)

        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.DLX,
                "x-dead-letter-routing-key": self._dlq_routing_key(agent_name),
            },
        )
        channel.queue_bind(queue=queue_name, exchange=self.EXCHANGE, routing_key=self._routing_key(agent_name))

        channel.queue_declare(
            queue=retry_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.EXCHANGE,
                "x-dead-letter-routing-key": self._routing_key(agent_name),
            },
        )

        channel.queue_declare(
            queue=dlq_name,
            durable=True,
        )
        channel.queue_bind(queue=dlq_name, exchange=self.DLX, routing_key=self._dlq_routing_key(agent_name))

    def _decode_message(self, body: bytes) -> AgentMessage:
        data = json.loads(body.decode("utf-8") if isinstance(body, bytes) else body)
        return AgentMessage.from_dict(data)

    def _encode_message(self, message: AgentMessage) -> bytes:
        return json.dumps(message.to_dict(), default=str).encode("utf-8")

    def publish(self, message: AgentMessage) -> None:
        self._persist_message(message)
        body = self._encode_message(message)
        properties = BasicProperties(
            delivery_mode=2,
            content_type="application/json",
            correlation_id=message.trace_id,
            headers={
                "workflow_id": message.workflow_id,
                "x-retry-count": message.retry_count,
            },
        )
        self._get_thread_channel().basic_publish(
            exchange=self.EXCHANGE,
            routing_key=self._routing_key(message.receiver_agent),
            body=body,
            properties=properties,
        )

    def publish_event(self, event: DomainEvent) -> None:
        self._persist_event(event)
        body = json.dumps(event.to_dict(), default=str).encode("utf-8")
        properties = BasicProperties(
            delivery_mode=2,
            content_type="application/json",
            headers={
                "workflow_id": event.workflow_id,
                "aggregate_id": event.aggregate_id,
                "event_type": event.event_type.value,
            },
        )
        self._get_thread_channel().basic_publish(
            exchange=self.EVENT_EXCHANGE,
            routing_key=event.routing_key,
            body=body,
            properties=properties,
        )

    def subscribe(self, agent_name: str) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        while self._local_buffer[agent_name]:
            messages.append(self._local_buffer[agent_name].popleft())

        queue_name = self._agent_queue_name(agent_name)
        channel = self._get_thread_channel()
        while True:
            method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=False)
            if method_frame is None:
                break
            try:
                msg = self._decode_message(body)
                messages.append(msg)
                channel.basic_ack(method_frame.delivery_tag)
            except Exception as exc:
                logger.warning("Failed to decode RabbitMQ message: %s", exc)
                channel.basic_nack(method_frame.delivery_tag, requeue=False)
        return messages

    def wait_for_response(
        self,
        receiver_agent: str,
        trace_id: str,
        workflow_id: str,
        timeout_seconds: int = 30,
    ) -> AgentMessage | None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            messages = self.subscribe(receiver_agent)
            for msg in messages:
                if msg.trace_id == trace_id and msg.workflow_id == workflow_id:
                    return msg
                self._local_buffer[receiver_agent].append(msg)
            time.sleep(0.05)
        return None

    def get_conversation(self, workflow_id: str) -> list[dict[str, Any]]:
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT sender_agent, receiver_agent, task_type,
                           payload_json, status, created_at
                    FROM agent_messages
                    WHERE workflow_id = ?
                    ORDER BY created_at ASC
                    """,
                    (workflow_id,),
                ).fetchall()
            return [
                {
                    "sender_agent": r["sender_agent"],
                    "receiver_agent": r["receiver_agent"],
                    "task_type": r["task_type"],
                    "payload": json.loads(r["payload_json"] or "{}"),
                    "status": r["status"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        except Exception:
            return []

    def get_queue_metrics(self) -> dict[str, Any]:
        metrics: dict[str, Any] = {}
        channel = self._get_thread_channel()
        for agent_name in self.KNOWN_AGENTS:
            queue_name = self._agent_queue_name(agent_name)
            retry_name = self._retry_queue_name(agent_name)
            dlq_name = self._dlq_queue_name(agent_name)
            try:
                q = channel.queue_declare(queue=queue_name, passive=True)
                metrics[queue_name] = {
                    "messages_ready": q.method.message_count,
                    "consumers": q.method.consumer_count,
                }
            except Exception:
                metrics[queue_name] = {"messages_ready": 0, "consumers": 0}
            try:
                q = channel.queue_declare(queue=retry_name, passive=True)
                metrics[retry_name] = {
                    "messages_ready": q.method.message_count,
                    "consumers": q.method.consumer_count,
                }
            except Exception:
                metrics[retry_name] = {"messages_ready": 0, "consumers": 0}
            try:
                q = channel.queue_declare(queue=dlq_name, passive=True)
                metrics[dlq_name] = {
                    "messages_ready": q.method.message_count,
                    "consumers": q.method.consumer_count,
                }
            except Exception:
                metrics[dlq_name] = {"messages_ready": 0, "consumers": 0}
        return metrics

    def _start_agent_workers(self) -> None:
        for agent_name in self.KNOWN_AGENTS:
            if agent_name == "supervisor":
                continue
            thread = threading.Thread(
                target=self._run_agent_worker,
                args=(agent_name,),
                daemon=True,
                name=f"rabbitmq-worker-{agent_name}",
            )
            thread.start()
            self._worker_threads.append(thread)

    def _run_agent_worker(self, agent_name: str) -> None:
        connection = self._connect()
        if connection is None:
            logger.warning("Unable to start worker for %s because RabbitMQ is unavailable", agent_name)
            return

        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        self._declare_agent_queue(agent_name, channel)
        queue_name = self._agent_queue_name(agent_name)

        def callback(ch: Any, method: Any, properties: Any, body: bytes) -> None:
            try:
                message = self._decode_message(body)
                message.retry_count = int(properties.headers.get("x-retry-count", 0)) if properties.headers else 0
                self._execute_agent(agent_name, message)
                ch.basic_ack(method.delivery_tag)
            except Exception as exc:
                logger.exception("Worker %s failed to process message: %s", agent_name, exc)
                self._handle_worker_failure(ch, method, properties, body, agent_name)

        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        try:
            channel.start_consuming()
        except Exception as exc:
            logger.exception("RabbitMQ worker for %s stopped unexpectedly: %s", agent_name, exc)
        finally:
            try:
                connection.close()
            except Exception:
                pass

    def _execute_agent(self, agent_name: str, message: AgentMessage) -> None:
        from ai_engine.agents.base import BaseAgent

        agent = self._get_agent(agent_name)
        agent.execute(message)

    def _get_agent(self, agent_name: str) -> Any:
        if agent_name == "cv_analysis":
            from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent

            return CVAnalysisAgent()
        if agent_name == "job_analysis":
            from ai_engine.agents.job_analysis_agent import JobAnalysisAgent

            return JobAnalysisAgent()
        if agent_name == "matching":
            from ai_engine.agents.matching_agent import MatchingAgent

            return MatchingAgent()
        if agent_name == "hiring_rules":
            from ai_engine.agents.hiring_rules_agent import HiringRulesAgent

            return HiringRulesAgent()
        if agent_name == "recruiter_feedback":
            from ai_engine.agents.recruiter_feedback_agent import RecruiterFeedbackAgent

            return RecruiterFeedbackAgent()
        if agent_name == "interview":
            from ai_engine.agents.interview_agent import InterviewAgent

            return InterviewAgent()
        if agent_name == "supervisor":
            from ai_engine.agents.supervisor_agent import SupervisorAgent

            return SupervisorAgent()
        raise ValueError(f"Unknown agent: {agent_name}")

    def _handle_worker_failure(self, ch: Any, method: Any, properties: Any, body: bytes, agent_name: str) -> None:
        retry_count = 0
        if properties is not None and properties.headers is not None:
            retry_count = int(properties.headers.get("x-retry-count", 0)) + 1
        else:
            retry_count = 1

        ch.basic_ack(method.delivery_tag)
        if retry_count > self.MAX_RETRY_ATTEMPTS:
            self._publish_to_dlq(agent_name, body, retry_count, ch)
            return

        delay_ms = min(30000, 1000 * (2 ** retry_count))
        self._publish_to_retry(agent_name, body, retry_count, delay_ms, ch)

    def _publish_to_retry(self, agent_name: str, body: bytes, retry_count: int, delay_ms: int, ch: Any) -> None:
        retry_queue = self._retry_queue_name(agent_name)
        properties = BasicProperties(
            delivery_mode=2,
            content_type="application/json",
            expiration=str(delay_ms),
            headers={"x-retry-count": retry_count},
        )
        ch.basic_publish(exchange="", routing_key=retry_queue, body=body, properties=properties)

    def _publish_to_dlq(self, agent_name: str, body: bytes, retry_count: int, ch: Any) -> None:
        dlq_queue = self._dlq_queue_name(agent_name)
        properties = BasicProperties(
            delivery_mode=2,
            content_type="application/json",
            headers={"x-retry-count": retry_count, "poison": True},
        )
        ch.basic_publish(exchange="", routing_key=dlq_queue, body=body, properties=properties)

    def _persist_message(self, message: AgentMessage) -> None:
        try:
            from database.connection import get_connection
            msg_id = uuid.uuid4().hex
            created_at = datetime.now(timezone.utc).isoformat()
            payload_json = json.dumps(message.payload or {})
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_messages
                        (id, workflow_id, sender_agent, receiver_agent,
                         task_type, payload_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg_id,
                        message.workflow_id,
                        message.sender_agent,
                        message.receiver_agent,
                        message.task_type,
                        payload_json,
                        message.status,
                        created_at,
                    ),
                )
        except Exception:
            pass

    def _persist_event(self, event: DomainEvent) -> None:
        try:
            from database.connection import get_connection
            event_id = uuid.uuid4().hex
            created_at = datetime.now(timezone.utc).isoformat()
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO domain_events
                        (id, workflow_id, event_type, aggregate_id,
                         payload_json, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event.workflow_id,
                        event.event_type.value,
                        event.aggregate_id,
                        json.dumps(event.payload or {}),
                        json.dumps(event.metadata or {}),
                        created_at,
                    ),
                )
        except Exception:
            pass


class AgentMessageBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._bus = RabbitMQAgentMessageBus()

    def publish(self, message: AgentMessage) -> None:
        with self._lock:
            self._bus.publish(message)

    def publish_event(self, event: DomainEvent) -> None:
        with self._lock:
            if hasattr(self._bus, "publish_event"):
                self._bus.publish_event(event)

    def subscribe(self, agent_name: str) -> list[AgentMessage]:
        with self._lock:
            return self._bus.subscribe(agent_name)

    def wait_for_response(
        self,
        receiver_agent: str,
        trace_id: str,
        workflow_id: str,
        timeout_seconds: int = 30,
    ) -> AgentMessage | None:
        if hasattr(self._bus, "wait_for_response"):
            return self._bus.wait_for_response(receiver_agent, trace_id, workflow_id, timeout_seconds)
        return None

    def get_conversation(self, workflow_id: str) -> list[dict[str, Any]]:
        return self._bus.get_conversation(workflow_id)

    def get_queue_metrics(self) -> dict[str, Any]:
        if hasattr(self._bus, "get_queue_metrics"):
            return self._bus.get_queue_metrics()
        return {}


# Singleton instance
agent_message_bus = AgentMessageBus()
