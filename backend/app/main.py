import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.routes import auth, chat, cv, jobs, tasks, ws, feedback
from backend.app.routes import agents, observability, tools as tools_router, copilot
from backend.app.routes import candidate, interview_advanced, automation, intelligence, market, analytics
from ai_engine.embeddings import get_embedding_runtime_info, get_embedding_model
from backend.app.services.auth_service import bootstrap_auth
from ai_engine.logging_utils import build_log_message
from database.connection import ensure_database_ready, get_database_health
from database.init_db import init_recruitment_db

app = FastAPI(
    title="HireMind AI Recruiting Operating System",
    version="3.0.0",
    description="Complete AI Recruiting OS with Hybrid RAG, Multi-Agent Architecture, Career Intelligence, Interview AI, Recruiting Automation, Market Intelligence, Analytics, and Plugin Ecosystem.",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "HIREMIND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(ws.router, prefix="/ws", tags=["WebSocket"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])

# Multi-Agent Platform Routes (Phases 2, 4, 8)
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(observability.router, prefix="/api/observability", tags=["Observability"])
app.include_router(tools_router.router, prefix="/api/tools", tags=["Tools"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["Copilot"])

# AI Recruiting OS Routes
app.include_router(candidate.router, prefix="/api/candidate", tags=["Candidate AI"])
app.include_router(interview_advanced.router, prefix="/api/interview", tags=["Interview AI"])
app.include_router(automation.router, prefix="/api/automation", tags=["Automation"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Agentic Intelligence"])
app.include_router(market.router, prefix="/api/market", tags=["Market Intelligence"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])



@app.on_event("startup")
def warmup_models() -> None:
    init_recruitment_db()
    bootstrap_auth()
    get_embedding_model()
    from ai_engine.agents.message_bus import agent_message_bus
    from ai_engine.observability.rabbitmq_metrics import get_rabbitmq_queue_metrics
    get_rabbitmq_queue_metrics()



@app.get("/ready")
def readiness_check() -> dict:
    db_health = ensure_database_ready()
    return {
        "status": "ready" if db_health.get("ready") else "degraded",
        "database": db_health,
    }


@app.get("/health")
def health_check() -> dict:
    get_embedding_model()
    embedding_runtime = get_embedding_runtime_info()
    database_health = get_database_health()
    from ai_engine.observability.rabbitmq_metrics import get_rabbitmq_queue_metrics
    from ai_engine.agents.message_bus import agent_message_bus
    rabbitmq_health = get_rabbitmq_queue_metrics()
    return {
        "status": "ok" if database_health.get("ready") and "error" not in rabbitmq_health else "degraded",
        "message": build_log_message("health", "السيرفر شغال ومجهز للتحليل"),
        "embedding_runtime": embedding_runtime,
        "database": database_health,
        "rabbitmq": rabbitmq_health,
        "agents": "initialized" if agent_message_bus else "failed",
    }
