from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.app.services.auth_service import require_current_user, require_role
from backend.app.services.session_service import session_service
from ai_engine.agents.copilot_agent import copilot_agent
from ai_engine.agents.base import AgentMessage
from ai_engine.tools.copilot_tools import register_copilot_tools
import uuid

# Register tools
register_copilot_tools()

router = APIRouter(dependencies=[Depends(require_current_user)])

class CopilotChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class CopilotChatResponse(BaseModel):
    session_id: str
    answer: str
    reasoning_summary: str
    tools_used: List[str]
    citations: List[str]

@router.post("/chat", response_model=CopilotChatResponse, dependencies=[Depends(require_role("recruiter", "admin"))])
def chat_with_copilot(request: CopilotChatRequest) -> CopilotChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    
    # Save user message
    session_service.append_message(session_id, "user", request.message)
    
    # Trigger copilot
    msg = AgentMessage(
        "api",
        "copilot_agent",
        "chat",
        {
            "message": request.message,
            "session_id": session_id
        }
    )
    
    try:
        result_msg = copilot_agent.run(msg)
        
        answer = (result_msg.payload or {}).get("answer") or (result_msg.result or {}).get("answer", "")
        reasoning_summary = (result_msg.payload or {}).get("reasoning_summary") or (result_msg.result or {}).get("reasoning_summary", "")
        tools_used = (result_msg.payload or {}).get("tools_used") or (result_msg.result or {}).get("tools_used", [])
        citations = (result_msg.payload or {}).get("citations") or (result_msg.result or {}).get("citations", [])
        
        # Save assistant message
        session_service.append_message(session_id, "assistant", answer, tools_used)
        
        return CopilotChatResponse(
            session_id=session_id,
            answer=answer,
            reasoning_summary=reasoning_summary,
            tools_used=tools_used,
            citations=citations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
