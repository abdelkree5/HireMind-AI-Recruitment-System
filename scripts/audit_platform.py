import os
import sys
import importlib
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

COMPONENTS = {
    "CareerCoachAgent": "ai_engine.agents.career_coach_agent",
    "CandidateCopilotAgent": "ai_engine.agents.candidate_copilot_agent",
    "CodingInterviewAgent": "ai_engine.agents.coding_interview_agent",
    "BehavioralInterviewAgent": "ai_engine.agents.behavioral_interview_agent",
    "VoiceInterviewAgent": "ai_engine.agents.voice_interview_agent",
    "InterviewCopilotAgent": "ai_engine.agents.interview_copilot_agent",
    "OutreachAgent": "ai_engine.agents.outreach_agent",
    "DebateAgent": "ai_engine.agents.debate_agent",
    "ReflectionAgent": "ai_engine.agents.reflection_agent",
    "EvaluationAgent": "ai_engine.agents.evaluation_agent",
    "SupervisorAgent": "ai_engine.agents.supervisor_agent",
    "MarketIntelligenceService": "ai_engine.services.market_intelligence",
    "RecommendationService": "ai_engine.services.recommendation_service",
    "ForecastingService": "ai_engine.services.forecasting_service",
    "AnalyticsService": "ai_engine.services.analytics_service",
    "CVBuilderService": "ai_engine.services.cv_builder_service",
    "WorkflowBuilderService": "ai_engine.automation.workflow_builder",
    "RecruiterMemory": "backend.app.services.memory_service",
    "SkillGraph": "ai_engine.skill_graph",
    "RabbitMQEventBus": "ai_engine.agents.message_bus",
    "HybridRAG": "ai_engine.matcher",
    "LearningToRank": "training.ltr_pipeline",
}

def check_file_and_import():
    results = []
    for name, module_path in COMPONENTS.items():
        file_path = module_path.replace(".", "/") + ".py"
        exists = os.path.exists(file_path)
        imports = False
        if exists:
            try:
                importlib.import_module(module_path)
                imports = True
            except Exception as e:
                print(f"Error importing {module_path}: {e}")
        
        results.append({
            "Component": name,
            "File Exists": exists,
            "Imports": imports
        })
    return results

def check_routes():
    try:
        from backend.app.main import app
        routes = [route.path for route in app.routes]
        return routes
    except Exception as e:
        print(f"Error checking routes: {e}")
        return []

def check_db_tables():
    from database.connection import get_connection, get_database_backend
    try:
        with get_connection() as conn:
            backend = get_database_backend()
            if backend == "sqlite":
                rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                tables = [r["name"] for r in rows]
            else:
                rows = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';").fetchall()
                tables = [r["tablename"] for r in rows]
            return tables
    except Exception as e:
        print(f"Error checking DB tables: {e}")
        return []

if __name__ == "__main__":
    print("--- COMPONENT CHECK ---")
    comp_results = check_file_and_import()
    for r in comp_results:
        print(f"{r['Component']} | Exists: {r['File Exists']} | Imports: {r['Imports']}")
    
    print("\n--- ROUTE CHECK ---")
    routes = check_routes()
    print(f"Total Routes Registered: {len(routes)}")
    # Print some to verify new ones
    new_routes = [r for r in routes if '/api/candidate' in r or '/api/interview/coding' in r or '/api/debate' in r]
    print("New Phase Routes:", new_routes)
    
    print("\n--- DATABASE TABLES ---")
    tables = check_db_tables()
    expected = [
        "recruiter_memory", "career_assessments", "generated_cvs", 
        "coding_challenges", "behavioral_assessments", "outreach_messages", 
        "workflow_definitions", "workflow_executions", "debate_sessions", 
        "agent_reflections", "market_snapshots", "analytics_cache", "installed_plugins"
    ]
    for t in expected:
        print(f"Table {t} exists: {t in tables}")
