#!/usr/bin/env python3
"""
K-LEAN Knowledge Base Utilities
===============================
Shared utilities for the knowledge database system.
Single source of truth for project detection, socket management, and configuration.
"""

import hashlib
import os
import socket
import sys
from pathlib import Path
from typing import Optional

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
SOCKET_PREFIX = os.environ.get("KLEAN_SOCKET_DIR", "/tmp") + "/kb-"

# Project markers in priority order (matches kb-root.sh)
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
# Project Root Detection
# =============================================================================
def find_project_root(start_dir: Optional[str] = None) -> Optional[Path]:
    """Find project root by walking up looking for project markers.

    Priority order (matches kb-root.sh):
    1. CLAUDE_PROJECT_DIR environment variable
    2. .knowledge-db directory
    3. .serena directory
    4. .claude directory
    5. .git directory

    Args:
        start_dir: Starting directory (defaults to cwd)

    Returns:
        Path to project root or None if not found
    """
    # Priority 1: Environment variable
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        env_path = Path(env_dir)
        if env_path.is_dir():
            return env_path

    # Priority 2-5: Walk up looking for markers
    current = Path(start_dir) if start_dir else Path.cwd()
    while current != current.parent:
        for marker in PROJECT_MARKERS:
            if (current / marker).is_dir():
                return current
        current = current.parent
    return None


# =============================================================================
# Socket Path Management
# =============================================================================
def get_socket_path(project_path: str | Path) -> str:
    """Get KB server socket path for a project.

    Uses MD5 hash of absolute project path for unique socket name.

    Args:
        project_path: Project root directory

    Returns:
        Socket path like /tmp/kb-a1b2c3d4.sock
    """
    path_str = str(Path(project_path).resolve())
    hash_val = hashlib.md5(path_str.encode()).hexdigest()[:8]
    return f"{SOCKET_PREFIX}{hash_val}.sock"


def get_pid_path(project_path: str | Path) -> str:
    """Get KB server PID file path for a project.

    Args:
        project_path: Project root directory

    Returns:
        PID file path like /tmp/kb-a1b2c3d4.pid
    """
    path_str = str(Path(project_path).resolve())
    hash_val = hashlib.md5(path_str.encode()).hexdigest()[:8]
    return f"{SOCKET_PREFIX}{hash_val}.pid"


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
    sock_path = get_socket_path(project_path)
    if not os.path.exists(sock_path):
        return False

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(sock_path)
        sock.sendall(b'{"cmd":"ping"}')
        response = sock.recv(1024).decode()
        sock.close()
        return '"pong"' in response
    except Exception:
        return False


def clean_stale_socket(project_path: str | Path) -> bool:
    """Remove stale socket file if server not responding.

    Args:
        project_path: Project root directory

    Returns:
        True if socket was cleaned up
    """
    sock_path = get_socket_path(project_path)
    if not os.path.exists(sock_path):
        return False

    if not is_server_running(project_path):
        try:
            os.unlink(sock_path)
            debug_log(f"Cleaned stale socket: {sock_path}")
            return True
        except Exception as e:
            debug_log(f"Failed to clean socket: {e}")
    return False


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
