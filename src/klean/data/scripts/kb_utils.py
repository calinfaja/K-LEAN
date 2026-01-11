#!/usr/bin/env python3
"""
K-LEAN Knowledge Base Utilities
===============================
Shared utilities for the knowledge database system.
Cross-platform support for Windows, Linux, and macOS using TCP sockets.

This module is self-contained and does NOT depend on the klean package,
so it can be run with system Python outside the pipx venv.
"""

import getpass
import hashlib
import json
import os
import socket
import sys
import tempfile
from pathlib import Path

# =============================================================================
# Platform Utilities (copied from klean.platform to be self-contained)
# =============================================================================

DEFAULT_KB_PORT = 14000

# Windows process constants (for is_process_running)
_WIN_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_WIN_STILL_ACTIVE = 259


def get_runtime_dir() -> Path:
    """Get the K-LEAN runtime directory for temporary files like sockets and PIDs.

    Returns:
        Linux/macOS: /tmp/klean-{username}
        Windows: %TEMP%/klean-{username}

    The directory is created if it doesn't exist.
    """
    username = getpass.getuser()
    runtime_dir = Path(tempfile.gettempdir()) / f"klean-{username}"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def get_project_hash(project_path: Path) -> str:
    """Generate a short hash for a project path.

    Args:
        project_path: Path to the project root.

    Returns:
        8-character hex hash of the project path.
    """
    path_str = str(project_path.resolve())
    return hashlib.md5(path_str.encode()).hexdigest()[:8]


def get_kb_port_file(project_path: Path) -> Path:
    """Get the path to the knowledge server port file for a project.

    Args:
        project_path: Path to the project root.

    Returns:
        Path to the .port file in runtime directory.
    """
    project_hash = get_project_hash(project_path)
    return get_runtime_dir() / f"kb-{project_hash}.port"


def get_kb_pid_file(project_path: Path) -> Path:
    """Get the path to the knowledge server PID file for a project.

    Args:
        project_path: Path to the project root.

    Returns:
        Path to the .pid file in runtime directory.
    """
    project_hash = get_project_hash(project_path)
    return get_runtime_dir() / f"kb-{project_hash}.pid"


def find_project_root(start_path: Path | None = None) -> Path | None:
    """Find the project root by looking for markers.

    Searches upward from start_path (or cwd) for:
    1. CLAUDE_PROJECT_DIR environment variable
    2. .knowledge-db directory
    3. .serena directory
    4. .claude directory
    5. .git directory

    Args:
        start_path: Starting directory (defaults to cwd).

    Returns:
        Project root path, or None if not found.
    """
    # Check environment variable first
    if env_dir := os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(env_dir)

    current = Path(start_path or Path.cwd()).resolve()
    markers = [".knowledge-db", ".serena", ".claude", ".git"]

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    return None


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running.

    Cross-platform: Uses os.kill on Unix, ctypes on Windows.

    Args:
        pid: Process ID to check.

    Returns:
        True if process exists and is running, False otherwise.
    """
    if sys.platform == "win32":
        # Windows: Use ctypes to call OpenProcess
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(_WIN_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle == 0:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return exit_code.value == _WIN_STILL_ACTIVE
            return False
        finally:
            kernel32.CloseHandle(handle)
    else:
        # Unix: os.kill with signal 0 checks existence without killing
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError, PermissionError):
            # PermissionError means process exists but we can't signal it
            # For our purposes (checking if server is running), this is fine
            return False


def read_pid_file(pid_file: Path) -> int | None:
    """Read a PID from a file.

    Args:
        pid_file: Path to the PID file.

    Returns:
        PID as integer, or None if file doesn't exist or is invalid.
    """
    try:
        if pid_file.exists():
            content = pid_file.read_text().strip()
            return int(content)
    except (ValueError, OSError):
        pass
    return None


def get_kb_port() -> int:
    """Get the knowledge server base port from environment or default.

    Returns:
        Port number from KLEAN_KB_PORT env var, or DEFAULT_KB_PORT (14000).
    """
    return int(os.environ.get("KLEAN_KB_PORT", str(DEFAULT_KB_PORT)))


def write_pid_file(pid_file: Path, pid: int) -> None:
    """Write a PID to a file.

    Args:
        pid_file: Path to the PID file.
        pid: Process ID to write.
    """
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(pid))


def kill_process_tree(pid: int, timeout: float = 5.0) -> bool:
    """Kill a process and all its children.

    Uses graceful termination first, then force kill after timeout.
    Cross-platform: works on Windows, Linux, and macOS.

    Args:
        pid: Process ID to kill.
        timeout: Seconds to wait for graceful termination.

    Returns:
        True if process was killed, False if it didn't exist.
    """
    import signal

    if not is_process_running(pid):
        return False

    try:
        if sys.platform == "win32":
            # Windows: use taskkill to kill process tree
            import subprocess

            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                timeout=timeout,
            )
        else:
            # Unix: send SIGTERM, wait, then SIGKILL if needed
            os.kill(pid, signal.SIGTERM)
            # Wait for process to terminate
            import time

            start = time.time()
            while time.time() - start < timeout:
                if not is_process_running(pid):
                    return True
                time.sleep(0.1)
            # Force kill if still running
            if is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
        return True
    except (OSError, ProcessLookupError, PermissionError):
        return False


def cleanup_stale_files(project_path: Path) -> None:
    """Remove stale PID and port files for a project.

    Checks if the PID in the file is still running, and removes
    the files if not.

    Args:
        project_path: Path to the project root.
    """
    pid_file = get_kb_pid_file(project_path)
    port_file = get_kb_port_file(project_path)

    pid = read_pid_file(pid_file)
    if pid and not is_process_running(pid):
        # Process is dead, clean up files
        try:
            pid_file.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            port_file.unlink(missing_ok=True)
        except OSError:
            pass


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "find_project_root",
    "get_kb_pid_file",
    "get_kb_port",
    "get_kb_port_file",
    "get_project_hash",
    "get_runtime_dir",
    "is_process_running",
    "read_pid_file",
    "write_pid_file",
    "kill_process_tree",
    "cleanup_stale_files",
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
# Cross-platform: Windows uses Scripts/, Unix uses bin/
_venv_bin = "Scripts" if sys.platform == "win32" else "bin"
_python_exe = "python.exe" if sys.platform == "win32" else "python"

_kb_python_env = os.environ.get("KB_PYTHON") or os.environ.get("KLEAN_KB_PYTHON")
if _kb_python_env:
    PYTHON_BIN = Path(_kb_python_env)
elif (Path.home() / ".venvs" / "knowledge-db" / _venv_bin / _python_exe).exists():
    PYTHON_BIN = Path.home() / ".venvs" / "knowledge-db" / _venv_bin / _python_exe
elif (Path.home() / ".local" / "share" / "klean" / "venv" / _venv_bin / _python_exe).exists():
    PYTHON_BIN = Path.home() / ".local" / "share" / "klean" / "venv" / _venv_bin / _python_exe
else:
    PYTHON_BIN = Path("python3" if sys.platform != "win32" else "python")  # Fallback

# Scripts directory - check environment override first
_kb_scripts_env = os.environ.get("KB_SCRIPTS_DIR") or os.environ.get("KLEAN_SCRIPTS_DIR")
if _kb_scripts_env:
    KB_SCRIPTS_DIR = Path(_kb_scripts_env)
else:
    KB_SCRIPTS_DIR = Path.home() / ".claude/scripts"

KB_DIR_NAME = ".knowledge-db"
HOST = "127.0.0.1"

# Project markers in priority order
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
