"""
Domain Events — RabbitMQ Event Schema Definitions

Defines the domain event types used by the HireMind workflow and
provides helper classes for event creation and routing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    CandidateUploaded = "CandidateUploaded"
    ResumeParsed = "ResumeParsed"
    CandidateMatched = "CandidateMatched"
    InterviewScheduled = "InterviewScheduled"
    InterviewCompleted = "InterviewCompleted"
    FeedbackSubmitted = "FeedbackSubmitted"
    CandidateRejected = "CandidateRejected"
    CandidateHired = "CandidateHired"
    # Phase 1: Candidate AI Ecosystem
    CareerAssessmentCompleted = "CareerAssessmentCompleted"
    CVGenerated = "CVGenerated"
    # Phase 2: Advanced Interview Intelligence
    CodingChallengeCompleted = "CodingChallengeCompleted"
    BehavioralAssessmentCompleted = "BehavioralAssessmentCompleted"
    # Phase 3: Recruiting Automation
    OutreachSent = "OutreachSent"
    WorkflowStepCompleted = "WorkflowStepCompleted"
    # Phase 4: Agentic Intelligence
    DebateConsensusReached = "DebateConsensusReached"
    ReflectionFlagged = "ReflectionFlagged"
    # Phase 5: Market Intelligence
    MarketSnapshotUpdated = "MarketSnapshotUpdated"

    @property
    def routing_key(self) -> str:
        import re

        name = self.value
        segments = re.sub(r"(?<!^)(?=[A-Z])", ".", name).lower().split(".")
        return "event." + ".".join(segments)


EVENT_SCHEMAS: dict[EventType, dict[str, Any]] = {
    EventType.CandidateUploaded: {
        "aggregate_id": "workflow_id or candidate_id",
        "payload": {
            "job_id": "str",
            "filename": "str",
            "source": "str",
            "uploaded_at": "ISO8601 timestamp",
        },
    },
    EventType.ResumeParsed: {
        "aggregate_id": "workflow_id or candidate_id",
        "payload": {
            "resume_text": "str",
            "skills": "list[str]",
            "seniority": "str",
            "domain": "str",
            "summary": "str",
        },
    },
    EventType.CandidateMatched: {
        "aggregate_id": "workflow_id or job_id",
        "payload": {
            "candidate_id": "str",
            "job_id": "str",
            "match_score": "float",
            "matched_skills": "list[str]",
            "missing_skills": "list[str]",
            "recommendation": "str",
        },
    },
    EventType.InterviewScheduled: {
        "aggregate_id": "interview_id",
        "payload": {
            "candidate_id": "str",
            "interview_id": "str",
            "scheduled_at": "ISO8601 timestamp",
            "interviewer": "str",
            "location": "str",
        },
    },
    EventType.InterviewCompleted: {
        "aggregate_id": "interview_id",
        "payload": {
            "candidate_id": "str",
            "interview_id": "str",
            "summary": "str",
            "score": "float",
            "feedback": "str",
        },
    },
    EventType.FeedbackSubmitted: {
        "aggregate_id": "application_id",
        "payload": {
            "candidate_id": "str",
            "job_id": "str",
            "recruiter_id": "str",
            "feedback_text": "str",
            "hired": "bool",
            "rejection_reason": "str",
        },
    },
    EventType.CandidateRejected: {
        "aggregate_id": "workflow_id or candidate_id",
        "payload": {
            "candidate_id": "str",
            "job_id": "str",
            "reason": "str",
        },
    },
    EventType.CandidateHired: {
        "aggregate_id": "workflow_id or candidate_id",
        "payload": {
            "candidate_id": "str",
            "job_id": "str",
            "offer_details": "dict[str, Any]",
        },
    },
}


@dataclass
class DomainEvent:
    event_type: EventType
    aggregate_id: str
    payload: dict[str, Any]
    workflow_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        return cls(
            event_type=EventType(data["event_type"]),
            aggregate_id=data.get("aggregate_id", ""),
            payload=data.get("payload", {}),
            workflow_id=data.get("workflow_id", ""),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )

    @property
    def routing_key(self) -> str:
        return self.event_type.routing_key


def get_event_schema(event_type: EventType) -> dict[str, Any]:
    return EVENT_SCHEMAS.get(event_type, {})
