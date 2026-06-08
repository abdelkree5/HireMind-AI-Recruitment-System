"""
Plugin Manager — Phase 7: AI Platform Capabilities

Dynamic plugin loading, lifecycle management, and discovery.
Plugins are loaded from ai_engine/plugins/installed/ directory.
"""
from __future__ import annotations

import json
import os
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "installed")


class PluginManager:
    """Manages the lifecycle of HireMind plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, dict] = {}

    def discover_plugins(self) -> dict[str, Any]:
        """Discover plugins from the installed directory."""
        if not os.path.isdir(PLUGINS_DIR):
            os.makedirs(PLUGINS_DIR, exist_ok=True)

        discovered = []
        for entry in os.listdir(PLUGINS_DIR):
            manifest_path = os.path.join(PLUGINS_DIR, entry, "plugin.json")
            if os.path.isfile(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    discovered.append({
                        "name": manifest.get("name", entry),
                        "version": manifest.get("version", "0.0.0"),
                        "description": manifest.get("description", ""),
                        "tools": manifest.get("tools", []),
                        "status": "discovered",
                    })
                except Exception as e:
                    logger.warning("Failed to load plugin manifest %s: %s", entry, e)

        return {"plugins": discovered, "total": len(discovered)}

    def install_plugin(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a plugin in the database."""
        name = payload.get("name", "")
        version = payload.get("version", "1.0.0")
        manifest = payload.get("manifest", {})

        if not name:
            return {"error": "Plugin name is required."}

        plugin_id = str(uuid.uuid4())
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO installed_plugins (id, name, version, manifest_json, is_active, installed_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (plugin_id, name, version, json.dumps(manifest), 1,
                     datetime.now(timezone.utc).isoformat()),
                )
        except Exception as e:
            return {"error": str(e)}

        self._plugins[name] = {"id": plugin_id, "version": version, "manifest": manifest}
        return {"plugin_id": plugin_id, "name": name, "status": "installed"}

    def list_installed(self) -> dict[str, Any]:
        """List all installed plugins from database."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, name, version, is_active, installed_at FROM installed_plugins ORDER BY installed_at DESC"
                ).fetchall()
            return {
                "plugins": [
                    {"id": r["id"], "name": r["name"], "version": r["version"],
                     "active": bool(r["is_active"]), "installed_at": r["installed_at"]}
                    for r in rows
                ]
            }
        except Exception:
            return {"plugins": []}

    def register_plugin_tools(self, plugin_name: str) -> dict[str, Any]:
        """Register a plugin's tools into the MCP Tool Registry."""
        from ai_engine.tools.registry import tool_registry

        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return {"error": f"Plugin '{plugin_name}' not found in memory."}

        tools = plugin.get("manifest", {}).get("tools", [])
        registered = 0
        for tool_def in tools:
            try:
                tool_registry.register_tool(
                    name=f"plugin.{plugin_name}.{tool_def['name']}",
                    description=tool_def.get("description", ""),
                    handler=lambda params, td=tool_def: {"plugin": plugin_name, "tool": td["name"], "params": params},
                    input_schema=tool_def.get("input_schema", {}),
                    tags=["plugin", plugin_name],
                )
                registered += 1
            except Exception as e:
                logger.warning("Failed to register plugin tool %s: %s", tool_def.get("name"), e)

        return {"plugin": plugin_name, "tools_registered": registered}


plugin_manager = PluginManager()
