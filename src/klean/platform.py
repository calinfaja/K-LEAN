"""Cross-platform utilities for K-LEAN.

This module provides cross-platform path handling and process management
using platformdirs and psutil. It replaces the shell-specific logic from
kb-root.sh and common.sh.
"""

from __future__ import annotations

import getpass
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import platformdirs
import psutil

# =============================================================================
# Path Utilities
# =============================================================================

# Default port for knowledge server
DEFAULT_KB_PORT = 14000


def get_config_dir() -> Path:
    """Get the K-LEAN configuration directory.

    Returns:
        Linux: ~/.config/klean
        macOS: ~/Library/Application Support/klean
        Windows: %APPDATA%/klean
    """
    return Path(platformdirs.user_config_dir("klean", ensure_exists=True))


def get_cache_dir() -> Path:
    """Get the K-LEAN cache directory.

    Returns:
        Linux: ~/.cache/klean
        macOS: ~/Library/Caches/klean
        Windows: %LOCALAPPDATA%/klean/Cache
    """
    return Path(platformdirs.user_cache_dir("klean", ensure_exists=True))


def get_runtime_dir() -> Path:
    """Get the K-LEAN runtime directory for temporary files like sockets and PIDs.

    Returns:
        Linux/macOS: /tmp/klean-{username}
        Windows: %TEMP%/klean-{username}

    The directory is created if it doesn't exist.
    """
    import tempfile

    username = getpass.getuser()
    runtime_dir = Path(tempfile.gettempdir()) / f"klean-{username}"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def get_kb_port() -> int:
    """Get the knowledge server port from environment or default.

    Returns:
        Port number from KLEAN_KB_PORT env var, or DEFAULT_KB_PORT (14000).
    """
    return int(os.environ.get("KLEAN_KB_PORT", str(DEFAULT_KB_PORT)))


def get_project_hash(project_path: Path) -> str:
    """Generate a short hash for a project path.

    This is used to create unique port/file names per project.

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


def get_venv_python(venv_dir: Path) -> Path:
    """Get the Python executable path for a virtual environment.

    Args:
        venv_dir: Path to the virtual environment root.

    Returns:
        Path to python executable (Scripts/python.exe on Windows, bin/python on Unix).
    """
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def get_venv_pip(venv_dir: Path) -> Path:
    """Get the pip executable path for a virtual environment.

    Args:
        venv_dir: Path to the virtual environment root.

    Returns:
        Path to pip executable (Scripts/pip.exe on Windows, bin/pip on Unix).
    """
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "pip.exe"
    return venv_dir / "bin" / "pip"


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


# =============================================================================
# Process Utilities
# =============================================================================


def find_process(pattern: str) -> psutil.Process | None:
    """Find a process by command line pattern.

    Cross-platform replacement for `pgrep -f pattern`.

    Args:
        pattern: Substring to search for in process command line.

    Returns:
        First matching Process object, or None if not found.
    """
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline")
            if cmdline and pattern in " ".join(cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def find_all_processes(pattern: str) -> list[psutil.Process]:
    """Find all processes matching a command line pattern.

    Args:
        pattern: Substring to search for in process command line.

    Returns:
        List of matching Process objects.
    """
    matches = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline")
            if cmdline and pattern in " ".join(cmdline):
                matches.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running.

    Args:
        pid: Process ID to check.

    Returns:
        True if process exists and is running, False otherwise.
    """
    try:
        proc = psutil.Process(pid)
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def spawn_background(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict | None = None,
    log_file: Path | None = None,
) -> int:
    """Spawn a background process that survives parent exit.

    Cross-platform process spawning that works on Linux, macOS, and Windows.

    Args:
        cmd: Command and arguments as list.
        cwd: Working directory for the process.
        env: Environment variables for the process.
        log_file: File to redirect stdout/stderr to (appends).

    Returns:
        PID of the spawned process.
    """
    # Handle output redirection
    if log_file:
        log_handle = open(log_file, "a")  # noqa: SIM115 - intentionally not using context manager
        stdout = log_handle
        stderr = log_handle
    else:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL

    kwargs: dict = {
        "stdout": stdout,
        "stderr": stderr,
        "stdin": subprocess.DEVNULL,
    }

    if cwd:
        kwargs["cwd"] = str(cwd)

    if env:
        kwargs["env"] = env

    if sys.platform == "win32":
        # Windows: CREATE_NEW_PROCESS_GROUP for detached process
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        # Unix: start_new_session for process group leader
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)
    return proc.pid


def kill_process_tree(pid: int, timeout: float = 5.0) -> bool:
    """Kill a process and all its children.

    Uses graceful termination (SIGTERM) first, then force kill (SIGKILL)
    after timeout.

    Args:
        pid: Process ID to kill.
        timeout: Seconds to wait for graceful termination.

    Returns:
        True if process was killed, False if it didn't exist.
    """
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False

    # Get all children before killing parent
    children = parent.children(recursive=True)

    # Terminate parent first
    try:
        parent.terminate()
    except psutil.NoSuchProcess:
        pass

    # Terminate all children
    for child in children:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass

    # Wait for graceful termination
    gone, alive = psutil.wait_procs([parent] + children, timeout=timeout)

    # Force kill any remaining
    for proc in alive:
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass

    return True


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


def write_pid_file(pid_file: Path, pid: int) -> None:
    """Write a PID to a file.

    Args:
        pid_file: Path to the PID file.
        pid: Process ID to write.
    """
    pid_file.write_text(str(pid))


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
            port_file.unlink(missing_ok=True)
        except OSError:
            pass
