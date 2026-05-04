from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import auth, chat, cv, jobs, tasks, ws
from ai_engine.embeddings import get_embedding_runtime_info, get_embedding_model
from backend.app.services.auth_service import bootstrap_auth
from backend.app.services.logger_service import build_log_message
from database.init_db import init_recruitment_db

app = FastAPI(title="Hire-Mind API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


@app.on_event("startup")
def warmup_models() -> None:
    init_recruitment_db()
    bootstrap_auth()
    get_embedding_model()


@app.get("/health")
def health_check() -> dict:
    get_embedding_model()
    embedding_runtime = get_embedding_runtime_info()
    return {
        "status": "ok",
        "message": build_log_message("health", "السيرفر شغال ومجهز للتحليل"),
        "embedding_runtime": embedding_runtime,
    }
