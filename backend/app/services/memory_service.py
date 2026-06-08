import uuid
import logging
from datetime import datetime, timezone
from database.connection import get_connection

logger = logging.getLogger(__name__)

class RecruiterMemoryService:
    """
    Middleware service layer for Recruiter Copilot.
    Injects historical preferences and conversational context using pgvector embeddings.
    """
    @staticmethod
    def add_preference(recruiter_id: str, preference_text: str) -> bool:
        """
        Stores a recruiter preference into the pgvector memory store.
        If pgvector is not initialized, handles it gracefully.
        """
        from ai_engine.embeddings import EmbeddingEngine
        try:
            embedding_engine = EmbeddingEngine()
            embedding = embedding_engine.encode(preference_text).tolist()
            # Format list as a Postgres vector string
            embedding_str = str(embedding)
            
            created_at = datetime.now(timezone.utc).isoformat()
            
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO recruiter_memory (id, recruiter_id, preference_text, embedding, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, recruiter_id, preference_text, embedding_str, created_at)
                )
            return True
        except Exception as e:
            logger.warning("Failed to store recruiter memory (pgvector might not be installed): %s", e)
            return False

    @staticmethod
    def get_relevant_preferences(recruiter_id: str, query: str, top_k: int = 3) -> list[str]:
        """
        Retrieves the most relevant historical preferences for the recruiter using vector similarity.
        """
        from database.connection import get_database_backend
        try:
            from ai_engine.embeddings import EmbeddingEngine
            embedding_engine = EmbeddingEngine()
            query_embedding = embedding_engine.encode(query).tolist()
            query_str = str(query_embedding)
            
            with get_connection() as conn:
                backend = get_database_backend()
                if backend == "postgresql":
                    try:
                        # Use pgvector <=> operator for cosine distance.
                        # Lower distance = higher similarity.
                        rows = conn.execute(
                            """
                            SELECT preference_text 
                            FROM recruiter_memory 
                            WHERE recruiter_id = ? 
                            ORDER BY embedding <=> ?::vector 
                            LIMIT ?
                            """,
                            (recruiter_id, query_str, top_k)
                        ).fetchall()
                        return [row["preference_text"] for row in rows]
                    except Exception as e:
                        logger.warning("Postgres vector similarity search failed, falling back: %s", e)
                
                # Fallback path for SQLite or PostgreSQL when pgvector fails
                rows = conn.execute(
                    """
                    SELECT preference_text 
                    FROM recruiter_memory 
                    WHERE recruiter_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                    """,
                    (recruiter_id, top_k)
                ).fetchall()
                
                return [row["preference_text"] for row in rows]
        except Exception as e:
            logger.warning("Failed to retrieve recruiter memory: %s", e)
            return []

memory_service = RecruiterMemoryService()
