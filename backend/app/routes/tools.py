"""
MCP Tool Registry API Routes — Phase 8

Endpoints:
  GET  /api/tools                   — List accessible tools for caller role
  GET  /api/tools/{name}            — Get tool metadata
  POST /api/tools/{name}/execute    — Execute a tool via registry
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from backend.app.services.auth_service import effective_role, require_current_user, require_role

router = APIRouter(dependencies=[Depends(require_current_user)])


@router.get("", dependencies=[Depends(require_role("candidate", "recruiter", "admin"))])
def list_tools(user = Depends(require_current_user)) -> list[dict[str, Any]]:
    """List all tools accessible by the given role."""
    try:
        from ai_engine.tools.registry import tool_registry
        return tool_registry.list_tools(role=effective_role(getattr(user, "role", "candidate")))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{tool_name}", dependencies=[Depends(require_role("candidate", "recruiter", "admin"))])
def get_tool_info(tool_name: str) -> dict[str, Any]:
    """Get metadata for a specific tool."""
    try:
        from ai_engine.tools.registry import tool_registry
        info = tool_registry.get_tool_info(tool_name)
        if not info:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
        return info
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{tool_name}/execute", dependencies=[Depends(require_role("candidate", "recruiter", "admin"))])
def execute_tool(tool_name: str, payload: dict[str, Any], user = Depends(require_current_user)) -> dict[str, Any]:
    """
    Execute a registered tool.

    Body:
        params: dict       — Tool input parameters
        caller_agent: str  — Calling agent name (default: "api")
    """
    params = payload.get("params", {})
    caller_agent = payload.get("caller_agent", f"api:{getattr(user, 'email', 'unknown')}")

    try:
        from ai_engine.tools.registry import tool_registry
        result = tool_registry.execute_tool(
            name=tool_name,
            params=params,
            caller_agent=caller_agent,
            caller_role=getattr(user, "role", "any"),
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
