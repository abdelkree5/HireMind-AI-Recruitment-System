from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SessionService:
    """
    Manages multi-turn conversation state (short-term memory).
    Maintains chat history per session_id using an in-memory cache.
    In production, this could be backed by Redis or PostgreSQL.
    """
    def __init__(self):
        # Maps session_id -> list of message dicts
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def append_message(self, session_id: str, role: str, content: str, tools_used: List[str] = None):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        msg = {
            "role": role,
            "content": content
        }
        if tools_used is not None:
            msg["tools_used"] = tools_used
            
        self._sessions[session_id].append(msg)
        logger.debug(f"[SessionService] Appended {role} message to session {session_id}")

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_service = SessionService()
