import sys
import time
import json
import uuid
from pathlib import Path
import traceback

from dotenv import load_dotenv
load_dotenv()

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ai_engine.agents.base import AgentMessage
from ai_engine.agents.career_coach_agent import career_coach_agent
from ai_engine.agents.candidate_copilot_agent import candidate_copilot_agent
from ai_engine.agents.coding_interview_agent import coding_interview_agent
from ai_engine.agents.behavioral_interview_agent import behavioral_interview_agent
from ai_engine.agents.debate_agent import debate_agent
from ai_engine.services.cv_builder_service import cv_builder_service
from backend.app.services.memory_service import memory_service
from ai_engine.agents.message_bus import agent_message_bus
from ai_engine.services.analytics_service import analytics_service

results = []

def run_test(name, func):
    print(f"Running {name}...")
    start = time.time()
    try:
        inputs, outputs = func()
        duration = time.time() - start
        results.append({
            "name": name,
            "status": "PASS",
            "duration": duration,
            "inputs": inputs,
            "outputs": outputs
        })
    except Exception as e:
        duration = time.time() - start
        results.append({
            "name": name,
            "status": "FAIL",
            "duration": duration,
            "inputs": None,
            "outputs": traceback.format_exc()
        })

# 1. Candidate Career Coach
def test_career_coach():
    payload = {
        "candidate_skills": ["python", "flask", "sql"],
        "target_role": "Senior Backend Engineer",
        "candidate_text": "I am a developer with 4 years of python experience."
    }
    
    msg_gap = AgentMessage("user", "coach", "skill_gap_analysis", payload)
    res_gap = career_coach_agent.run(msg_gap)
    
    msg_roadmap = AgentMessage("user", "coach", "career_roadmap", payload)
    res_roadmap = career_coach_agent.run(msg_roadmap)
    
    return payload, {"gap_analysis": res_gap.result, "roadmap": res_roadmap.result}

# 2. Candidate Copilot
def test_candidate_copilot():
    questions = [
        "Review my CV for a backend role.",
        "How should I prepare for a system design interview?",
        "What are the best skills to learn right now?",
        "How can I improve my experience section?",
        "Give me a mock interview question for Python."
    ]
    answers = []
    for q in questions:
        msg = AgentMessage("user", "candidate_copilot", "chat", {"message": q, "session_id": "test_session"})
        res = candidate_copilot_agent.run(msg)
        answers.append({"question": q, "answer": res.result.get("answer") if res.result else res.payload})
        
    return {"questions": questions}, {"answers": answers}

# 3. CV Builder
def test_cv_builder():
    from database.connection import get_connection
    import datetime
    
    with get_connection() as conn:
        try:
            conn.execute("INSERT INTO users (id, email, full_name, role, password_salt, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         ("test_candidate_123", "test_candidate_123@hiremind.com", "Test Candidate", "candidate", "salt", "hash", datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))
        except Exception:
            pass

    inputs = {
        "candidate_id": "test_candidate_123",
        "linkedin_data": {},
        "github_data": {},
        "candidate_text": "Experienced Python developer working on web apps."
    }
    inputs["format_type"] = "ats_friendly"
    ats = cv_builder_service.generate_cv(inputs)
    inputs["format_type"] = "modern"
    modern = cv_builder_service.generate_cv(inputs)
    inputs["format_type"] = "recruiter_optimized"
    recruiter = cv_builder_service.generate_cv(inputs)
    
    outputs = {
        "ats_friendly": ats.get("content", ""),
        "modern": modern.get("content", ""),
        "recruiter_optimized": recruiter.get("content", "")
    }
    return inputs, outputs

# 4. Coding Interview Agent
def test_coding_agent():
    inputs = {"role": "Backend", "difficulty": "medium"}
    msg_gen = AgentMessage("user", "coding_agent", "generate_challenge", inputs)
    res_gen = coding_interview_agent.run(msg_gen)
    challenge = res_gen.result
    
    eval_inputs = {
        "problem_id": challenge.get("id", "123"),
        "code": "def solve(): return True"
    }
    msg_eval = AgentMessage("user", "coding_agent", "evaluate_submission", eval_inputs)
    res_eval = coding_interview_agent.run(msg_eval)
    
    return {"generate": inputs, "evaluate": eval_inputs}, {"challenge": challenge, "evaluation": res_eval.result}

# 5. Behavioral Interview Agent
def test_behavioral_agent():
    inputs = {"dimension": "leadership", "answer": "I led a team of 5 engineers to deliver the project ahead of schedule."}
    msg = AgentMessage("user", "behavioral_agent", "evaluate_answer", inputs)
    res = behavioral_interview_agent.run(msg)
    return inputs, res.result

# 6. Debate Agent
def test_debate_agent():
    inputs = {"candidate_id": "cand_123", "job_id": "job_456"}
    msg = AgentMessage("user", "debate", "run_debate", inputs)
    res = debate_agent.run(msg)
    return inputs, res.result

# 7. Recruiter Memory
def test_memory():
    from database.connection import get_connection
    import datetime
    with get_connection() as conn:
        try:
            conn.execute("INSERT INTO users (id, email, full_name, role, password_salt, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         ("recruiter_test_1", "recruiter_test_1@hiremind.com", "Test Recruiter", "recruiter", "salt", "hash", datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))
        except Exception:
            pass

    rec_id = "recruiter_test_1"
    pref = "I prefer candidates with strong FastAPI and Docker experience."
    memory_service.add_preference(rec_id, pref)
    
    query = "FastAPI experience"
    results = memory_service.get_relevant_preferences(rec_id, query)
    
    return {"inserted": pref, "query": query}, {"results": results}

# 8. RabbitMQ (Message Bus)
def test_rabbitmq():
    from ai_engine.agents.base import AgentMessage
    bus = agent_message_bus
    
    # Declare the queue properly using the bus topology setup to avoid channel closures
    try:
        if hasattr(bus._bus, 'KNOWN_AGENTS') and "dummy_test_agent" not in bus._bus.KNOWN_AGENTS:
            bus._bus.KNOWN_AGENTS.append("dummy_test_agent")
            ch = bus._bus._get_thread_channel()
            bus._bus._setup_topology(ch)
    except Exception:
        pass
            
    msg_id = str(uuid.uuid4())
    msg = AgentMessage(sender_agent="test_suite", receiver_agent="dummy_test_agent", task_type="ping", payload={"test_id": msg_id})
    
    bus.publish(msg)
    
    # Wait briefly
    time.sleep(0.5)
    
    consumed_msgs = bus.subscribe("dummy_test_agent")
    
    return {"published_id": msg_id}, {"consumed_messages": [m.__dict__ for m in consumed_msgs]}

# 9. Workflow Builder (Execution State Transitions)
def test_workflow():
    from database.connection import get_connection, get_database_backend
    import datetime
    
    wf_id = str(uuid.uuid4())
    exec_id = str(uuid.uuid4())
    
    with get_connection() as conn:
        backend = get_database_backend()
        if backend == "sqlite":
            conn.execute("PRAGMA foreign_keys = OFF;")
        else:
            conn.execute("SET session_replication_role = 'replica';")
            
        conn.execute("INSERT INTO workflow_definitions (id, name, trigger_event, steps_json, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                     (wf_id, "Test Workflow", "CandidateApplied", json.dumps([{"agent": "CVAnalysisAgent"}]), "system", datetime.datetime.now().isoformat()))
        conn.execute("INSERT INTO workflow_executions (id, workflow_id, status, started_at) VALUES (?, ?, ?, ?)",
                     (exec_id, wf_id, "running", datetime.datetime.now().isoformat()))
        
        conn.execute("UPDATE workflow_executions SET status = ?, completed_at = ? WHERE id = ?",
                     ("completed", datetime.datetime.now().isoformat(), exec_id))
                     
        row = conn.execute("SELECT status FROM workflow_executions WHERE id = ?", (exec_id,)).fetchone()
        
        if backend == "sqlite":
            conn.execute("PRAGMA foreign_keys = ON;")
        else:
            conn.execute("SET session_replication_role = 'origin';")
        
    return {"workflow_id": wf_id}, {"final_status": row["status"] if row else None}

# 10. Analytics
def test_analytics():
    inputs = {"job_id": "job_456"}
    metrics = analytics_service.recruiter_dashboard("job_456")
    funnel = analytics_service.candidate_funnel("job_456")
    ai_perf = analytics_service.ai_performance_dashboard()
    
    return inputs, {"recruiter_metrics": metrics, "funnel": funnel, "ai_perf": ai_perf}

def main():
    run_test("1. Candidate Career Coach", test_career_coach)
    run_test("2. Candidate Copilot", test_candidate_copilot)
    run_test("3. CV Builder", test_cv_builder)
    run_test("4. Coding Interview Agent", test_coding_agent)
    run_test("5. Behavioral Interview Agent", test_behavioral_agent)
    run_test("6. Debate Agent", test_debate_agent)
    run_test("7. Recruiter Memory", test_memory)
    run_test("8. RabbitMQ Event Bus", test_rabbitmq)
    run_test("9. Workflow Builder", test_workflow)
    run_test("10. Analytics", test_analytics)
    
    with open("real_business_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    for r in results:
        print(f"[{r['status']}] {r['name']} - {r['duration']:.2f}s")
        if r['status'] == "FAIL":
            print(f"ERROR: {r['outputs']}")

if __name__ == "__main__":
    main()
