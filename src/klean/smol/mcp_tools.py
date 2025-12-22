"""MCP server integration for SmolKLN.

Uses smolagents' native MCP support via ToolCollection.from_mcp()
to integrate with MCP servers like Serena, filesystem, etc.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json


def load_mcp_config() -> Dict[str, Any]:
    """Load MCP config from Claude settings.

    Searches for MCP server configuration in common locations.

    Returns:
        Dict of MCP server configurations
    """
    config_paths = [
        Path.home() / ".claude.json",
        Path.home() / ".claude" / "claude_desktop_config.json",
        Path.home() / ".claude" / "settings.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                if "mcpServers" in data:
                    return data["mcpServers"]
            except (json.JSONDecodeError, KeyError):
                continue

    return {}


def get_mcp_server_config(server_name: str) -> Optional[Dict]:
    """Get config for a specific MCP server.

    Args:
        server_name: Name of the MCP server (e.g., "serena", "filesystem")

    Returns:
        Server configuration dict or None if not found
    """
    config = load_mcp_config()
    return config.get(server_name)


# Pre-configured MCP servers that can be used without user config
BUILTIN_MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-filesystem", "."],
        "env": {}
    },
    "git": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-server-git"],
        "env": {}
    }
}


def get_mcp_tools(
    servers: List[str] = None,
    include_builtin: bool = False
) -> List:
    """Load tools from MCP servers.

    Uses smolagents ToolCollection.from_mcp() to connect to MCP servers
    and load their tools.

    Args:
        servers: List of server names to load from user config.
                 Default: ["serena"] if configured.
        include_builtin: Whether to include builtin servers (filesystem, git)

    Returns:
        List of tools from MCP servers.
    """
    try:
        from smolagents import ToolCollection
    except ImportError:
        return []

    servers = servers or []
    tools = []

    # If no servers specified, try serena by default
    if not servers:
        if get_mcp_server_config("serena"):
            servers = ["serena"]

    # Load from user-configured servers
    for server in servers:
        config = get_mcp_server_config(server)
        if config:
            try:
                collection = ToolCollection.from_mcp(config)
                tools.extend(collection.tools)
            except Exception as e:
                # Log but don't fail
                print(f"Warning: Failed to load MCP server {server}: {e}")

    # Load builtin servers if requested
    if include_builtin:
        for name, config in BUILTIN_MCP_SERVERS.items():
            if name not in servers:  # Don't duplicate
                try:
                    collection = ToolCollection.from_mcp(config)
                    tools.extend(collection.tools)
                except Exception as e:
                    print(f"Warning: Failed to load builtin MCP server {name}: {e}")

    return tools


def list_available_mcp_servers() -> Dict[str, str]:
    """List available MCP servers.

    Returns:
        Dict of server name -> status ("configured", "builtin", "unavailable")
    """
    result = {}

    # Check user-configured servers
    user_config = load_mcp_config()
    for name in user_config:
        result[name] = "configured"

    # Add builtin servers
    for name in BUILTIN_MCP_SERVERS:
        if name not in result:
            result[name] = "builtin"

    return result


def test_mcp_connection(server_name: str) -> Dict[str, Any]:
    """Test connection to an MCP server.

    Args:
        server_name: Name of the server to test

    Returns:
        Dict with status and tool count or error message
    """
    config = get_mcp_server_config(server_name)
    if not config:
        config = BUILTIN_MCP_SERVERS.get(server_name)

    if not config:
        return {"success": False, "error": f"Server {server_name} not found"}

    try:
        from smolagents import ToolCollection
        collection = ToolCollection.from_mcp(config)
        return {
            "success": True,
            "server": server_name,
            "tools": len(collection.tools),
            "tool_names": [t.name for t in collection.tools]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
