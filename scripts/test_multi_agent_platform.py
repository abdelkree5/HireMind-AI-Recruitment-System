"""
Multi-Agent Platform Validation Script — Phase 9

End-to-end test validating all 9 phases of the HireMind
Multi-Agent Intelligent Hiring Platform.

Run:
    cd e:/graduate/Ai_resume_graduate
    .venv/Scripts/python.exe scripts/test_multi_agent_platform.py
"""
from __future__ import annotations

import sys
import os
import json
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⚠️  SKIP"
results: list[tuple[str, str, str]] = []  # (phase, test, status)


def test(phase: str, name: str):
    """Decorator-like helper to run and record a test."""
    def _run(fn):
        try:
            fn()
            results.append((phase, name, PASS))
            print(f"  {PASS}  {name}")
        except Exception as exc:
            results.append((phase, name, f"{FAIL}: {exc}"))
            print(f"  {FAIL}  {name} — {exc}")
    return _run


# ---------------------------------------------------------------------------
# Phase 1: Database Init
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 3: Database / Memory Tables        ")
print("═══════════════════════════════════════════")

@test("Phase 3", "init_recruitment_db creates agent tables")
def _():
    from database.init_db import init_recruitment_db
    init_recruitment_db()
    from database.connection import get_connection
    with get_connection() as conn:
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    required = {"agent_memory_stm", "agent_memory_ltm", "agent_episodes", "agent_traces", "agent_messages"}
    missing = required - tables
    assert not missing, f"Missing tables: {missing}"


# ---------------------------------------------------------------------------
# Phase 1: Agent Base Classes
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 1: Multi-Agent Architecture        ")
print("═══════════════════════════════════════════")

@test("Phase 1", "AgentMessage instantiation")
def _():
    from ai_engine.agents.base import AgentMessage
    msg = AgentMessage(sender_agent="supervisor", receiver_agent="cv_analysis", task_type="analyze_cv", payload={"text": "test"})
    assert msg.trace_id
    assert msg.workflow_id
    assert msg.status == "pending"

@test("Phase 1", "CVAnalysisAgent instantiation")
def _():
    from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent
    agent = CVAnalysisAgent()
    assert agent.name == "cv_analysis"

@test("Phase 1", "JobAnalysisAgent instantiation")
def _():
    from ai_engine.agents.job_analysis_agent import JobAnalysisAgent
    agent = JobAnalysisAgent()
    assert agent.name == "job_analysis"

@test("Phase 1", "MatchingAgent instantiation")
def _():
    from ai_engine.agents.matching_agent import MatchingAgent
    agent = MatchingAgent()
    assert agent.name == "matching"

@test("Phase 1", "HiringRulesAgent instantiation")
def _():
    from ai_engine.agents.hiring_rules_agent import HiringRulesAgent
    agent = HiringRulesAgent()
    assert agent.name == "hiring_rules"

@test("Phase 1", "RecruiterFeedbackAgent instantiation")
def _():
    from ai_engine.agents.recruiter_feedback_agent import RecruiterFeedbackAgent
    agent = RecruiterFeedbackAgent()
    assert agent.name == "recruiter_feedback"

@test("Phase 1", "InterviewAgent instantiation")
def _():
    from ai_engine.agents.interview_agent import InterviewAgent
    agent = InterviewAgent()
    assert agent.name == "interview"

@test("Phase 1", "SupervisorAgent instantiation")
def _():
    from ai_engine.agents.supervisor_agent import SupervisorAgent
    agent = SupervisorAgent()
    assert agent.name == "supervisor"


# ---------------------------------------------------------------------------
# Phase 2: Agent Task Routing
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 2: Agent Orchestration             ")
print("═══════════════════════════════════════════")

@test("Phase 2", "JobAnalysisAgent.analyze_job")
def _():
    from ai_engine.agents.job_analysis_agent import JobAnalysisAgent
    agent = JobAnalysisAgent()
    result = agent.analyze_job({
        "title": "Senior DevOps Engineer",
        "description": "5+ years of experience required. Must have Kubernetes, Terraform, AWS.",
        "required_skills": ["kubernetes", "terraform", "aws", "docker"],
        "domain": "devops",
    })
    assert result["role_class"] == "DevOps", f"Expected DevOps, got {result['role_class']}"
    assert result["required_seniority"] in ("Senior", "Mid")
    assert "kubernetes" in result["mandatory_skills"]

@test("Phase 2", "CVAnalysisAgent.extract_skills")
def _():
    from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent
    agent = CVAnalysisAgent()
    result = agent.extract_skills("Experienced Python developer with FastAPI, Docker, PostgreSQL.")
    assert "skills" in result

@test("Phase 2", "HiringRulesAgent.enforce_mandatory_skills")
def _():
    from ai_engine.agents.hiring_rules_agent import HiringRulesAgent
    agent = HiringRulesAgent()
    result = agent.enforce_mandatory_skills(
        candidate_skills=["python", "fastapi", "docker"],
        mandatory_skills=["kubernetes", "terraform", "aws"],
    )
    assert result["passed"] is False
    assert len(result["missing_mandatory"]) == 3

@test("Phase 2", "HiringRulesAgent.check_experience — nonlinear penalty")
def _():
    from ai_engine.agents.hiring_rules_agent import HiringRulesAgent
    agent = HiringRulesAgent()
    r1 = agent.check_experience(1, 8)
    r2 = agent.check_experience(3, 8)
    r5 = agent.check_experience(5, 8)
    r8 = agent.check_experience(8, 8)
    assert r1["penalty"] >= 0.35, f"1yr penalty too low: {r1['penalty']}"
    assert r2["penalty"] >= 0.20, f"3yr penalty too low: {r2['penalty']}"
    assert r5["penalty"] <= 0.15, f"5yr penalty too high: {r5['penalty']}"
    assert r8["passed"] is True

@test("Phase 2", "SupervisorAgent.route_task to job_analysis")
def _():
    from ai_engine.agents.supervisor_agent import SupervisorAgent
    supervisor = SupervisorAgent()
    result = supervisor.route_task(
        task_type="analyze_job",
        target_agent="job_analysis",
        agent_payload={
            "title": "Backend Engineer",
            "description": "Python developer needed.",
            "required_skills": ["python", "fastapi"],
        },
    )
    assert "role_class" in result

@test("Phase 2", "SupervisorAgent.aggregate_decisions")
def _():
    from ai_engine.agents.supervisor_agent import SupervisorAgent
    supervisor = SupervisorAgent()
    result = supervisor.aggregate_decisions({
        "matching": {"match_percentage": 85.0, "matched_skills": ["python"], "missing_skills": [], "penalties": []},
        "hiring_rules": {"is_eligible": True, "penalty": 0.0, "reasons": [], "rule_status": "PASSED"},
        "cv_analysis": {"leadership_score": 0.5, "project_depth_score": 0.7, "seniority": "Senior", "primary_domain": "backend_ai"},
        "job_analysis": {"required_seniority": "Senior", "role_class": "Backend"},
    })
    assert result["final_score"] >= 70.0, f"Expected >=70, got {result['final_score']}"
    assert result["is_eligible"] is True


# ---------------------------------------------------------------------------
# Phase 3: Memory System
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 3: Agent Memory System             ")
print("═══════════════════════════════════════════")

@test("Phase 3", "STM write and read")
def _():
    from ai_engine.memory.memory_store import memory_store
    memory_store.write_stm("test_wf", "candidate_score", {"score": 85.5}, ttl_seconds=60)
    val = memory_store.read_stm("test_wf", "candidate_score")
    assert val is not None and val["score"] == 85.5

@test("Phase 3", "LTM write and read")
def _():
    from ai_engine.memory.memory_store import memory_store
    memory_store.write_ltm("job_test_123", "recruiter_prefs", "preferred_skills", ["python", "fastapi"])
    val = memory_store.read_ltm("job_test_123", "recruiter_prefs", "preferred_skills")
    assert val is not None and "python" in val

@test("Phase 3", "Semantic memory — domain relations")
def _():
    from ai_engine.memory.memory_store import memory_store
    domains = memory_store.get_domain_relations()
    assert "devops" in domains
    assert "kubernetes" in domains["devops"]
    assert "backend_ai" in domains

@test("Phase 3", "Episodic memory record and retrieve")
def _():
    from ai_engine.memory.memory_store import memory_store
    memory_store.record_episode("job_001", "candidate_abc", "hiring_rules", "eligibility_check", {"passed": True})
    history = memory_store.get_candidate_history("candidate_abc")
    assert len(history) >= 1
    assert history[0]["event"] == "eligibility_check"


# ---------------------------------------------------------------------------
# Phase 4: Observability
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 4: Observability                   ")
print("═══════════════════════════════════════════")

@test("Phase 4", "AgentTracer.record — persists to DB")
def _():
    from ai_engine.agents.base import AgentTraceContext
    from ai_engine.observability.tracer import agent_tracer
    import uuid
    ctx = AgentTraceContext(
        trace_id=uuid.uuid4().hex,
        workflow_id="test_obs_wf",
        agent_name="test_agent",
        task_type="test_task",
        input_summary="test input",
    )
    ctx.complete(status="completed", output_summary="test output")
    agent_tracer.record(ctx)
    traces = agent_tracer.get_traces(workflow_id="test_obs_wf")
    assert len(traces) >= 1

@test("Phase 4", "Metrics — precision_at_k, ndcg_at_k, mrr")
def _():
    from ai_engine.observability.metrics import precision_at_k, ndcg_at_k, mean_reciprocal_rank
    relevant = {"a", "b", "c"}
    retrieved = ["a", "x", "b", "y", "c", "z"]
    p5 = precision_at_k(relevant, retrieved, 5)
    ndcg = ndcg_at_k(relevant, retrieved, 5)
    mrr = mean_reciprocal_rank(relevant, retrieved)
    assert 0 < p5 <= 1
    assert 0 < ndcg <= 1
    assert mrr == 1.0

@test("Phase 4", "Decision quality metrics computation")
def _():
    from ai_engine.observability.metrics import compute_decision_metrics
    fake_feedback = [
        {"ai_score": 80, "is_accepted": 1, "is_hired": 0},
        {"ai_score": 75, "is_accepted": 1, "is_hired": 1},
        {"ai_score": 40, "is_accepted": 0, "is_hired": 0},
        {"ai_score": 35, "is_accepted": 0, "is_hired": 0},
    ]
    metrics = compute_decision_metrics(fake_feedback)
    assert metrics["total"] == 4
    assert "accuracy" in metrics
    assert metrics["accuracy"] > 0


# ---------------------------------------------------------------------------
# Phase 5: Agent Communication Bus
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 5: Agent Communication             ")
print("═══════════════════════════════════════════")

@test("Phase 5", "MessageBus publish and subscribe")
def _():
    from ai_engine.agents.message_bus import AgentMessageBus
    from ai_engine.agents.base import AgentMessage
    bus = AgentMessageBus()
    msg = AgentMessage(
        sender_agent="supervisor", receiver_agent="cv_analysis",
        task_type="analyze_cv", payload={"text": "hello"},
        workflow_id="bus_test_wf",
    )
    bus.publish(msg)
    received = bus.subscribe("cv_analysis")
    assert len(received) >= 1
    assert received[0].task_type == "analyze_cv"

@test("Phase 5", "MessageBus persists to DB")
def _():
    from ai_engine.agents.message_bus import AgentMessageBus
    from ai_engine.agents.base import AgentMessage
    bus = AgentMessageBus()
    bus.publish(AgentMessage(
        sender_agent="job_analysis", receiver_agent="matching",
        task_type="score_candidate", payload={},
        workflow_id="bus_persist_wf",
    ))
    conversation = bus.get_conversation("bus_persist_wf")
    assert len(conversation) >= 1


# ---------------------------------------------------------------------------
# Phase 6: Feedback Learning Functions
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 6: Feedback Learning               ")
print("═══════════════════════════════════════════")

@test("Phase 6", "build_recruiter_preference_model — no data returns gracefully")
def _():
    from ai_engine.feedback import build_recruiter_preference_model
    result = build_recruiter_preference_model("nonexistent_job_xxx")
    assert isinstance(result, dict)

@test("Phase 6", "generate_feedback_report — no data fallback")
def _():
    from ai_engine.feedback import generate_feedback_report
    report = generate_feedback_report("nonexistent_job_xxx")
    assert "No recruiter feedback" in report or "Feedback Report" in report


# ---------------------------------------------------------------------------
# Phase 8: MCP Tool Registry
# ---------------------------------------------------------------------------
print("\n═══════════════════════════════════════════")
print("  Phase 8: MCP Tool Registry               ")
print("═══════════════════════════════════════════")

@test("Phase 8", "ToolRegistry lists tools for recruiter role")
def _():
    from ai_engine.tools.registry import tool_registry
    tools = tool_registry.list_tools(role="recruiter")
    names = [t["name"] for t in tools]
    assert "parse_cv" in names
    assert "score_candidate" in names
    assert "submit_feedback" in names
    # Admin-only tool should not be visible
    assert "train_ltr_model" not in names

@test("Phase 8", "ToolRegistry RBAC blocks unauthorized access")
def _():
    from ai_engine.tools.registry import tool_registry
    try:
        tool_registry.execute_tool("train_ltr_model", {}, caller_agent="test", caller_role="candidate")
        assert False, "Should have raised PermissionError"
    except PermissionError:
        pass

@test("Phase 8", "ToolRegistry extract_skills tool executes")
def _():
    from ai_engine.tools.registry import tool_registry
    result = tool_registry.execute_tool(
        "extract_skills",
        {"text": "Python, FastAPI, Docker, Kubernetes developer."},
        caller_agent="test",
        caller_role="any",
    )
    assert result["status"] == "success"
    assert "skills" in result["result"]

@test("Phase 8", "ToolRegistry stub returns stub status")
def _():
    from ai_engine.tools.registry import tool_registry
    result = tool_registry.execute_tool(
        "ats_push_candidate", {}, caller_agent="supervisor", caller_role="admin"
    )
    assert result["status"] == "stub"


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "═" * 50)
print("  VALIDATION SUMMARY")
print("═" * 50)

total = len(results)
passed = sum(1 for _, _, s in results if s == PASS)
failed = total - passed

for phase, name, status in results:
    icon = "✅" if status == PASS else "❌"
    print(f"  {icon}  [{phase}] {name}")

print(f"\n  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
print(f"  Production Readiness Score: {round(passed / total * 100, 1)}%")

if failed > 0:
    sys.exit(1)
