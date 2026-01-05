"""MCP server integration for SmolKLN.

Uses smolagents' native MCP support via ToolCollection.from_mcp()
to integrate with MCP servers like Serena, filesystem, etc.
"""

import json
from pathlib import Path
from typing import Any, Optional


def load_mcp_config() -> dict[str, Any]:
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


def get_mcp_server_config(server_name: str) -> Optional[dict]:
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
        "env": {},
    },
    "git": {"command": "npx", "args": ["-y", "@anthropic/mcp-server-git"], "env": {}},
}


def get_mcp_tools(servers: list[str] = None, include_builtin: bool = False) -> list:
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
                # Extract command and args from config
                command = config.get("command")
                args = config.get("args", [])
                env = config.get("env", {})

                if command:
                    # Pass command and args separately
                    collection = ToolCollection.from_mcp(command=command, args=args, env=env)
                    tools.extend(collection.tools)
            except Exception as e:
                # Log but don't fail - MCP servers are optional
                import sys

                print(f"Note: MCP server {server} not loaded: {e}", file=sys.stderr)

    # Load builtin servers if requested
    if include_builtin:
        for name, config in BUILTIN_MCP_SERVERS.items():
            if name not in servers:  # Don't duplicate
                try:
                    command = config.get("command")
                    args = config.get("args", [])
                    env = config.get("env", {})
                    if command:
                        collection = ToolCollection.from_mcp(command=command, args=args, env=env)
                        tools.extend(collection.tools)
                except Exception as e:
                    import sys

                    print(f"Note: Builtin MCP server {name} not loaded: {e}", file=sys.stderr)

    return tools


def list_available_mcp_servers() -> dict[str, str]:
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


def test_mcp_connection(server_name: str) -> dict[str, Any]:
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

        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env", {})
        if not command:
            return {"success": False, "error": "No command in config"}
        collection = ToolCollection.from_mcp(command=command, args=args, env=env)
        return {
            "success": True,
            "server": server_name,
            "tools": len(collection.tools),
            "tool_names": [t.name for t in collection.tools],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
