"""
MCP Integration — Phase 7: AI Platform Capabilities

Exposes HireMind tools as Model Context Protocol (MCP) compatible endpoints.
Enables external AI systems to discover and invoke HireMind capabilities.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP-compatible tool server for HireMind.
    Implements the core discovery and invocation protocol so that
    external LLM clients (Claude, GPT, etc.) can call HireMind tools.
    """

    def __init__(self) -> None:
        self.name = "hiremind-mcp"
        self.version = "1.0.0"

    def get_server_info(self) -> dict[str, Any]:
        """Return MCP server metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False,
            },
        }

    def list_tools(self) -> dict[str, Any]:
        """List all available tools in MCP format."""
        from ai_engine.tools.registry import tool_registry

        all_tools = tool_registry.list_tools(role="admin")
        mcp_tools = []

        for tool in all_tools:
            mcp_tools.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        k: {"type": v if v in ("string", "number", "boolean", "array") else "string"}
                        for k, v in tool.get("input_schema", {}).items()
                    },
                },
            })

        return {"tools": mcp_tools}

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke a tool via MCP protocol."""
        from ai_engine.tools.registry import tool_registry

        try:
            result = tool_registry.execute_tool(
                tool_name, arguments,
                caller_agent="mcp_external",
                caller_role="admin",
            )
            return {
                "content": [
                    {"type": "text", "text": json.dumps(result.get("result", result), ensure_ascii=False)}
                ],
                "isError": False,
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": str(e)}],
                "isError": True,
            }


mcp_server = MCPServer()
