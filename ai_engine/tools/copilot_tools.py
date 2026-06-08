from __future__ import annotations
import json
from ai_engine.tools.registry import tool_registry

def search_candidates(query: str, limit: int = 5) -> dict:
    """Candidate Search Tool: Queries the PostgreSQL database for job applications."""
    from database.connection import get_connection
    query_lower = query.lower()
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, candidate_name, candidate_headline, candidate_skills, match_score 
                FROM job_applications 
                WHERE lower(candidate_skills) LIKE ? 
                   OR lower(candidate_headline) LIKE ? 
                ORDER BY match_score DESC LIMIT ?
                """,
                (f"%{query_lower}%", f"%{query_lower}%", limit)
            ).fetchall()
        
        candidates = [dict(r) for r in rows]
        return {"candidates": candidates, "count": len(candidates)}
    except Exception as e:
        return {"error": str(e)}

def skill_graph_expand(skill_name: str) -> dict:
    """Skill Graph Tool: Expands a skill to find synonyms and parent/child relationships."""
    from ai_engine.skill_graph import skill_graph
    try:
        expanded = skill_graph.expand_skill(skill_name)
        return {"original": skill_name, "expanded_skills": expanded}
    except Exception as e:
        return {"error": str(e)}

def recruiter_memory_retrieve(query: str, recruiter_id: str = "default") -> dict:
    """Recruiter Memory Tool: Retrieves relevant historical preferences for a recruiter."""
    from backend.app.services.memory_service import memory_service
    try:
        prefs = memory_service.get_relevant_preferences(recruiter_id, query, top_k=3)
        return {"preferences": prefs}
    except Exception as e:
        return {"error": str(e)}

def job_analysis(title: str, description: str) -> dict:
    """Job Analysis Tool: Parses job description and generates templates."""
    from ai_engine.agents.job_analysis_agent import job_analysis_agent
    try:
        res = job_analysis_agent.analyze_job({
            "title": title, "description": description
        })
        return res
    except Exception as e:
        return {"error": str(e)}

def interview_question_generate(candidate_name: str, skills: list, job_title: str) -> dict:
    """Interview Question Tool: Generates technical interview questions based on candidate profile."""
    from ai_engine.interview import InterviewEngine
    engine = InterviewEngine()
    # Dummy history to trigger generation
    history = [{"answer": "I have experience with " + ", ".join(skills)}]
    try:
        q = engine.generate_next_question(history, job_title)
        return {"questions": [q]}
    except Exception as e:
        return {"error": str(e)}

def candidate_summary(cv_text: str) -> dict:
    """Candidate Summary Tool: Summarizes a CV's key strengths and weaknesses."""
    from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent
    agent = CVAnalysisAgent()
    try:
        # We can just extract insight
        res = agent.analyze_cv(text=cv_text)
        return {
            "headline": res.get("inferred_headline"),
            "seniority": res.get("level"),
            "skills": res.get("skills"),
            "primary_domain": res.get("primary_domain"),
            "years_of_experience": res.get("years_of_experience")
        }
    except Exception as e:
        return {"error": str(e)}

def register_copilot_tools():
    """Register all copilot tools into the global registry."""
    tool_registry.register_tool(
        name="search_candidates",
        description="Search for candidates in the database matching a specific query.",
        handler=search_candidates,
        required_role="recruiter",
        input_schema={"query": "str", "limit": "int"},
        tags=["copilot", "search"]
    )
    tool_registry.register_tool(
        name="skill_graph_expand",
        description="Expand a skill to find synonyms and related technical concepts.",
        handler=skill_graph_expand,
        required_role="recruiter",
        input_schema={"skill_name": "str"},
        tags=["copilot", "skill_graph"]
    )
    tool_registry.register_tool(
        name="recruiter_memory_retrieve",
        description="Retrieve historical preferences for a recruiter based on a query.",
        handler=recruiter_memory_retrieve,
        required_role="recruiter",
        input_schema={"query": "str", "recruiter_id": "str"},
        tags=["copilot", "memory"]
    )
    tool_registry.register_tool(
        name="job_analysis",
        description="Analyze a job title and description to extract required skills and seniority.",
        handler=job_analysis,
        required_role="recruiter",
        input_schema={"title": "str", "description": "str"},
        tags=["copilot", "job"]
    )
    tool_registry.register_tool(
        name="interview_question_generate",
        description="Generate an interview question for a candidate based on their skills.",
        handler=interview_question_generate,
        required_role="recruiter",
        input_schema={"candidate_name": "str", "skills": "list", "job_title": "str"},
        tags=["copilot", "interview"]
    )
    tool_registry.register_tool(
        name="candidate_summary",
        description="Summarize a candidate's CV text into key insights.",
        handler=candidate_summary,
        required_role="recruiter",
        input_schema={"cv_text": "str"},
        tags=["copilot", "cv"]
    )
