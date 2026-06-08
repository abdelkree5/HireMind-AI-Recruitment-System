"""
HireMind Multi-Agent Architecture
===================================
Specialized agents for the production-grade intelligent hiring platform.

Agent Registry:
  - SupervisorAgent     : Orchestrates the full pipeline
  - CVAnalysisAgent     : Parses and analyzes resumes
  - JobAnalysisAgent    : Parses and classifies job descriptions
  - MatchingAgent       : BM25/Dense/RRF/Cross-Encoder retrieval
  - HiringRulesAgent    : Enforces business compliance rules
  - RecruiterFeedbackAgent : Collects and learns from recruiter decisions
  - InterviewAgent      : Generates and scores technical interviews
"""
from ai_engine.agents.base import AgentMessage, AgentStatus, BaseAgent

__all__ = ["AgentMessage", "AgentStatus", "BaseAgent"]
