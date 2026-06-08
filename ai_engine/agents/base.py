"""
Base agent classes, message protocol, and agent status definitions.

Every agent in HireMind inherits from BaseAgent and communicates
via structured AgentMessage objects through the AgentMessageBus.
"""
from __future__ import annotations

import uuid
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent Status
# ---------------------------------------------------------------------------

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# ---------------------------------------------------------------------------
# Agent Message (Inter-Agent Communication Protocol)
# ---------------------------------------------------------------------------

@dataclass
class AgentMessage:
    """
    Structured message passed between agents.

    Schema:
        sender_agent   : Name of the sending agent
        receiver_agent : Name of the target agent (or "broadcast")
        task_type      : Operation being requested (e.g. "analyze_cv")
        payload        : Input data for the task
        status         : Current lifecycle status of the message
        trace_id       : Unique identifier for observability tracing
        workflow_id    : Parent workflow this message belongs to
        timestamp      : UTC ISO timestamp when message was created
        retry_count    : Number of times this message has been retried
        result         : Output data after task completion (populated by receiver)
        error          : Error message if status is "failed"
    """
    sender_agent: str
    receiver_agent: str
    task_type: str
    payload: dict[str, Any]
    status: str = "pending"           # pending | processing | completed | failed
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    workflow_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender_agent": self.sender_agent,
            "receiver_agent": self.receiver_agent,
            "task_type": self.task_type,
            "payload": self.payload,
            "status": self.status,
            "trace_id": self.trace_id,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Agent Trace Context
# ---------------------------------------------------------------------------

@dataclass
class AgentTraceContext:
    """Carries tracing information across an agent execution lifecycle."""
    trace_id: str
    workflow_id: str
    agent_name: str
    task_type: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    status: str = "running"
    input_summary: str = ""
    output_summary: str = ""
    latency_ms: float = 0.0

    def complete(self, status: str = "completed", output_summary: str = "") -> None:
        self.end_time = time.time()
        self.latency_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        self.output_summary = output_summary


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base class for all HireMind agents.

    Each concrete agent must implement `run(message)` which accepts an
    AgentMessage and returns an AgentMessage with the result populated.

    Agents communicate via the AgentMessageBus and emit traces to the
    observability layer automatically on each run.
    """

    def __init__(self, name: str, max_retries: int = 3) -> None:
        self.name = name
        self.max_retries = max_retries
        self.status = AgentStatus.IDLE
        self._bus = None  # Injected by SupervisorAgent or retrieved lazily

    @property
    def bus(self):
        if self._bus is None:
            from ai_engine.agents.message_bus import agent_message_bus
            self._bus = agent_message_bus
        return self._bus

    @abstractmethod
    def run(self, message: AgentMessage) -> AgentMessage:
        """
        Execute the agent's core task.

        Args:
            message: Incoming AgentMessage with task_type and payload.

        Returns:
            AgentMessage with status="completed" and result populated,
            or status="failed" with error populated on failure.
        """

    def execute(self, message: AgentMessage) -> AgentMessage:
        """
        Safe wrapper around run() that handles retries, status updates,
        tracing, and error handling.
        """
        from ai_engine.observability.tracer import agent_tracer

        self.status = AgentStatus.RUNNING
        trace_ctx = AgentTraceContext(
            trace_id=message.trace_id,
            workflow_id=message.workflow_id,
            agent_name=self.name,
            task_type=message.task_type,
            input_summary=str(list(message.payload.keys()))[:200],
        )

        for attempt in range(self.max_retries):
            try:
                message.status = "processing"
                result_msg = self.run(message)
                result_msg.status = "completed"
                self.status = AgentStatus.COMPLETED

                trace_ctx.complete(
                    status="completed",
                    output_summary=str(list((result_msg.result or {}).keys()))[:200],
                )
                agent_tracer.record(trace_ctx)

                # Publish result to bus for audit trail
                self.bus.publish(result_msg)
                return result_msg

            except Exception as exc:
                message.retry_count += 1
                self.status = AgentStatus.RETRYING
                logger.warning(
                    f"[{self.name}] attempt {attempt + 1}/{self.max_retries} failed: {exc}"
                )
                if attempt + 1 == self.max_retries:
                    message.status = "failed"
                    message.error = str(exc)
                    self.status = AgentStatus.FAILED

                    trace_ctx.complete(status="failed", output_summary=str(exc)[:200])
                    agent_tracer.record(trace_ctx)
                    self.bus.publish(message)
                    return message

        return message

    def send_to(
        self,
        receiver: str,
        task_type: str,
        payload: dict[str, Any],
        workflow_id: str = "",
        trace_id: str = "",
    ) -> AgentMessage:
        """Create and publish a message to another agent."""
        msg = AgentMessage(
            sender_agent=self.name,
            receiver_agent=receiver,
            task_type=task_type,
            payload=payload,
            workflow_id=workflow_id or uuid.uuid4().hex,
            trace_id=trace_id or uuid.uuid4().hex,
        )
        self.bus.publish(msg)
        return msg

    def reply(self, original: AgentMessage, result: dict[str, Any]) -> AgentMessage:
        """Create a reply message from this agent to the original sender."""
        return AgentMessage(
            sender_agent=self.name,
            receiver_agent=original.sender_agent,
            task_type=f"{original.task_type}.result",
            payload={},
            status="completed",
            trace_id=original.trace_id,
            workflow_id=original.workflow_id,
            result=result,
        )
