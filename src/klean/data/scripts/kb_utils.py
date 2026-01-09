#!/usr/bin/env python3
"""
K-LEAN Knowledge Base Utilities
===============================
Shared utilities for the knowledge database system.
Cross-platform support for Windows, Linux, and macOS using TCP sockets.
"""

import json
import os
import socket
import sys
from pathlib import Path

# Add parent directory to path for platform imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from klean.platform import (  # noqa: F401 - re-exported for other scripts
    find_project_root,
    get_kb_pid_file,
    get_kb_port_file,
    get_project_hash,
    get_runtime_dir,
    is_process_running,
    read_pid_file,
)

# Explicitly declare re-exports
__all__ = [
    "find_project_root",
    "get_kb_pid_file",
    "get_kb_port_file",
    "get_project_hash",
    "get_runtime_dir",
    "is_process_running",
    "read_pid_file",
    "HOST",
    "KB_DIR_NAME",
    "PROJECT_MARKERS",
    "get_server_port",
    "get_pid_path",
    "is_kb_initialized",
    "is_server_running",
    "clean_stale_socket",
    "send_command",
    "search",
]

# =============================================================================
# Configuration Constants (with environment variable overrides)
# =============================================================================
# Python binary - check environment override first
_kb_python_env = os.environ.get("KB_PYTHON") or os.environ.get("KLEAN_KB_PYTHON")
if _kb_python_env:
    PYTHON_BIN = Path(_kb_python_env)
elif (Path.home() / ".venvs/knowledge-db/bin/python").exists():
    PYTHON_BIN = Path.home() / ".venvs/knowledge-db/bin/python"
elif (Path.home() / ".local/share/klean/venv/bin/python").exists():
    PYTHON_BIN = Path.home() / ".local/share/klean/venv/bin/python"
else:
    PYTHON_BIN = Path("python3")  # Fallback to system python

# Scripts directory - check environment override first
_kb_scripts_env = os.environ.get("KB_SCRIPTS_DIR") or os.environ.get("KLEAN_SCRIPTS_DIR")
if _kb_scripts_env:
    KB_SCRIPTS_DIR = Path(_kb_scripts_env)
else:
    KB_SCRIPTS_DIR = Path.home() / ".claude/scripts"

KB_DIR_NAME = ".knowledge-db"
HOST = "127.0.0.1"

# Project markers in priority order (matches platform.py)
PROJECT_MARKERS = [".knowledge-db", ".serena", ".claude", ".git"]

# V2 Schema defaults for migration
SCHEMA_V2_DEFAULTS = {
    # Existing fields with defaults
    "confidence_score": 0.7,
    "tags": [],
    "usage_count": 0,
    "last_used": None,
    "source_quality": "medium",
    # V2 enhanced fields
    "atomic_insight": "",  # One-sentence takeaway
    "key_concepts": [],  # Terms for hybrid search boost
    "quality": "medium",  # high|medium|low
    "source": "manual",  # conversation|web|file|manual
    "source_path": "",  # URL or file path
}


# =============================================================================
# Debug Logging
# =============================================================================
def debug_log(msg: str, category: str = "kb") -> None:
    """Log debug message if KLEAN_DEBUG is set."""
    if os.environ.get("KLEAN_DEBUG"):
        print(f"[{category}] {msg}", file=sys.stderr)


# =============================================================================
# Port File Management (TCP-based, cross-platform)
# =============================================================================
def get_server_port(project_path: str | Path) -> int | None:
    """Get KB server port for a project.

    Reads port from the port file in runtime directory.

    Args:
        project_path: Project root directory

    Returns:
        Port number or None if not running
    """
    port_file = get_kb_port_file(Path(project_path))
    try:
        if port_file.exists():
            return int(port_file.read_text().strip())
    except (ValueError, OSError):
        pass
    return None


def get_pid_path(project_path: str | Path) -> str:
    """Get KB server PID file path for a project.

    Args:
        project_path: Project root directory

    Returns:
        PID file path in runtime directory
    """
    return str(get_kb_pid_file(Path(project_path)))


# Legacy aliases for backward compatibility
def get_socket_path(project_path: str | Path) -> str:
    """DEPRECATED: Use get_server_port() instead.

    Returns port as string for backward compatibility.
    """
    port = get_server_port(project_path)
    return str(port) if port else ""


# =============================================================================
# Server Status
# =============================================================================
def is_kb_initialized(project_path: str | Path) -> bool:
    """Check if knowledge DB is initialized for project.

    Args:
        project_path: Project root directory

    Returns:
        True if .knowledge-db directory exists
    """
    if not project_path:
        return False
    return (Path(project_path) / KB_DIR_NAME).is_dir()


def is_server_running(project_path: str | Path, timeout: float = 0.5) -> bool:
    """Check if KB server is running and responding.

    Args:
        project_path: Project root directory
        timeout: Socket timeout in seconds

    Returns:
        True if server responds to ping
    """
    port = get_server_port(project_path)
    if not port:
        return False

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((HOST, port))
        sock.sendall(b'{"cmd":"ping"}')
        response = sock.recv(1024).decode()
        sock.close()
        return '"pong"' in response
    except Exception:
        return False


def clean_stale_socket(project_path: str | Path) -> bool:
    """Remove stale port/pid files if server not responding.

    Args:
        project_path: Project root directory

    Returns:
        True if files were cleaned up
    """
    project = Path(project_path)
    port_file = get_kb_port_file(project)
    pid_file = get_kb_pid_file(project)

    if not port_file.exists():
        return False

    if not is_server_running(project_path):
        try:
            port_file.unlink(missing_ok=True)
            pid_file.unlink(missing_ok=True)
            debug_log(f"Cleaned stale files for: {project_path}")
            return True
        except Exception as e:
            debug_log(f"Failed to clean files: {e}")
    return False


# =============================================================================
# TCP Communication
# =============================================================================
def send_command(project_path: str | Path, cmd_data: dict, timeout: float = 5.0) -> dict | None:
    """Send command to KB server for a project.

    Args:
        project_path: Project root directory
        cmd_data: Command dict to send
        timeout: Socket timeout in seconds

    Returns:
        Response dict or None if server not running
    """
    port = get_server_port(project_path)
    if not port:
        return None

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((HOST, port))
        sock.sendall(json.dumps(cmd_data).encode("utf-8"))
        response = sock.recv(65536).decode("utf-8")
        sock.close()
        return json.loads(response)
    except Exception as e:
        debug_log(f"Send command failed: {e}")
        return {"error": str(e)}


def search(project_path: str | Path, query: str, limit: int = 5) -> dict | None:
    """Perform semantic search via KB server.

    Args:
        project_path: Project root directory
        query: Search query string
        limit: Maximum results

    Returns:
        Search results dict or None if server not running
    """
    return send_command(project_path, {"cmd": "search", "query": query, "limit": limit})


# =============================================================================
# Python Interpreter
# =============================================================================
def get_python_bin() -> str:
    """Get path to knowledge DB Python interpreter.

    Returns:
        Path to venv Python if it exists, otherwise 'python3'
    """
    if PYTHON_BIN.exists():
        return str(PYTHON_BIN)
    return "python3"


# =============================================================================
# Schema Migration
# =============================================================================
def migrate_entry(entry: dict) -> dict:
    """Migrate entry to V2 schema with defaults.

    Args:
        entry: Knowledge entry dict

    Returns:
        Entry with V2 fields filled in
    """
    for field, default in SCHEMA_V2_DEFAULTS.items():
        if field not in entry:
            entry[field] = default
    return entry
