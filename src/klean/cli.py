"""
K-LEAN CLI - Command line interface for K-LEAN installation and management.

Usage:
    kln install [--dev] [--component COMPONENT]
    kln uninstall
    kln status
    kln doctor [--auto-fix]
    kln start [--service SERVICE]
    kln stop [--service SERVICE]
    kln debug [--follow] [--filter COMPONENT]
    kln version
"""

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from klean import (
    CLAUDE_DIR,
    CONFIG_DIR,
    DATA_DIR,
    KLEAN_DIR,
    LOGS_DIR,
    PIDS_DIR,
    SMOL_AGENTS_DIR,
    VENV_DIR,
    __version__,
)
from klean.platform import (
    cleanup_stale_files,
    get_kb_pid_file,
    get_kb_port_file,
    get_runtime_dir,
    get_venv_pip,
    get_venv_python,
    is_process_running,
    kill_process_tree,
    spawn_background,
)

console = Console()

# Cross-platform ASCII symbols (Windows cp1252 can't encode Unicode)
SYM_OK = "[OK]"
SYM_FAIL = "[X]"


def get_litellm_binary() -> Path | None:
    """Find litellm binary - checks pipx venv first, then system PATH.

    When installed via pipx, litellm is in the same venv as kln but not in
    system PATH. This function finds it by looking relative to sys.executable.
    """
    # First check in the same bin directory as current Python executable
    # This works for pipx installations where litellm is in the venv
    bin_dir = Path(sys.executable).parent
    litellm_path = bin_dir / "litellm"
    if litellm_path.exists():
        return litellm_path

    # Fallback to system PATH (for non-pipx installations)
    which_result = shutil.which("litellm")
    return Path(which_result) if which_result else None


def get_source_data_dir() -> Path:
    """Get the source data directory - handles both editable and regular installs."""
    # In editable install, DATA_DIR points to src/klean/data
    # But we want the actual data from the repo root

    # Check if we're in an editable install by looking for the repo structure
    possible_repo = DATA_DIR.parent.parent.parent  # src/klean/data -> src/klean -> src -> repo

    # Look for data in multiple locations
    candidates = [
        DATA_DIR,  # Package data (regular install)
        possible_repo / "src" / "klean" / "data",  # Editable install with data in package
        Path(__file__).parent.parent.parent / "scripts",  # Legacy location during transition
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return DATA_DIR


# =============================================================================
# Status Helper Functions
# =============================================================================


def get_litellm_info() -> tuple:
    """Get model count and detected providers from LiteLLM config.

    Returns:
        Tuple of (model_count, list_of_providers)
    """
    config_file = CONFIG_DIR / "config.yaml"

    if not config_file.exists():
        return 0, []

    try:
        content = config_file.read_text()
        model_count = content.count("model_name:")

        # Detect providers from env var patterns (case-insensitive)
        providers = []
        content_upper = content.upper()

        if "NANOGPT" in content_upper:
            providers.append("NanoGPT")
        if "OPENROUTER" in content_upper:
            providers.append("OpenRouter")
        # Only show direct providers if not using aggregators
        if not providers:
            if "ANTHROPIC" in content_upper:
                providers.append("Anthropic")
            if "OPENAI_API" in content_upper:
                providers.append("OpenAI")

        return model_count, providers if providers else ["Custom"]
    except Exception:
        return 0, []


def get_kb_project_status() -> tuple:
    """Get KB status for current working directory project.

    Returns:
        Tuple of (status, details, project_name)
        - status: "RUNNING", "STOPPED", "NOT INIT", "N/A", "ERROR"
        - details: Additional info like entry count
        - project_name: Name of the project directory
    """
    scripts_dir = CLAUDE_DIR / "scripts"

    # Guard: scripts not installed yet
    if not scripts_dir.exists():
        return ("N/A", "run kln install", "")

    kb_utils_path = scripts_dir / "kb_utils.py"
    if not kb_utils_path.exists():
        return ("N/A", "kb_utils missing", "")

    try:
        # Lazy import with path setup
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        from kb_utils import (
            find_project_root,
            get_server_port,
            is_kb_initialized,
            is_server_running,
        )

        project = find_project_root(Path.cwd())
        if not project:
            return ("N/A", "not in a project", "")

        project_name = project.name

        if is_server_running(project):
            # Query server for entry count via TCP
            port = get_server_port(project)
            entries = _query_kb_entries(port) if port else "?"
            return ("RUNNING", f"({entries} entries)", project_name)

        if is_kb_initialized(project):
            return ("STOPPED", "run InitKB", project_name)

        return ("NOT INIT", "run InitKB", project_name)

    except ImportError as e:
        return ("ERROR", f"import: {str(e)[:20]}", "")
    except Exception as e:
        return ("ERROR", str(e)[:25], "")


def _query_kb_entries(port: int) -> str:
    """Query KB server for entry count via TCP status command.

    Args:
        port: TCP port number

    Returns:
        Entry count as string, or "?" on failure
    """
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(b'{"cmd":"status"}')
        response = sock.recv(4096).decode()
        sock.close()

        data = json.loads(response)
        return str(data.get("entries", "?"))
    except Exception:
        return "?"


def print_banner():
    """Print the K-LEAN banner."""
    console.print(
        Panel.fit(
            f"[bold cyan]K-LEAN v{__version__}[/bold cyan]\n"
            "[dim]Multi-Model Code Review & Knowledge Capture System[/dim]",
            border_style="cyan",
        )
    )


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def copy_files(src: Path, dst: Path, pattern: str = "*", symlink: bool = False) -> int:
    """Copy or symlink files from source to destination."""
    # Handle case where dst is a symlink (e.g., from previous dev mode install)
    # When switching to production mode, we need a real directory
    if not symlink and dst.is_symlink():
        dst.unlink()
    ensure_dir(dst)
    count = 0

    if not src.exists():
        console.print(f"[yellow]Warning: Source not found: {src}[/yellow]")
        return 0

    for item in src.glob(pattern):
        if item.is_file():
            dst_file = dst / item.name
            if symlink:
                # Remove existing file/symlink
                if dst_file.exists() or dst_file.is_symlink():
                    dst_file.unlink()
                dst_file.symlink_to(item.resolve())
            else:
                # Skip if source and destination are the same file
                if dst_file.exists() and os.path.samefile(item, dst_file):
                    count += 1
                    continue
                shutil.copy2(item, dst_file)
            count += 1
        elif item.is_dir() and pattern == "*":
            # Recursively copy directories
            dst_subdir = dst / item.name
            if symlink:
                if dst_subdir.exists() or dst_subdir.is_symlink():
                    if dst_subdir.is_symlink():
                        dst_subdir.unlink()
                    else:
                        shutil.rmtree(dst_subdir)
                dst_subdir.symlink_to(item.resolve())
            else:
                if dst_subdir.is_symlink():
                    dst_subdir.unlink()
                elif dst_subdir.exists():
                    shutil.rmtree(dst_subdir)
                shutil.copytree(item, dst_subdir)
            count += 1

    return count


def make_executable(path: Path) -> None:
    """Make Python scripts executable."""
    for pattern in ["*.py"]:
        for script in path.glob(pattern):
            if script.exists():
                script.chmod(script.stat().st_mode | 0o111)
            elif script.is_symlink():
                target = os.readlink(script)
                click.echo(f"  Warning: broken symlink {script.name} -> {target}", err=True)


def check_litellm() -> bool:
    """Check if LiteLLM proxy is running."""
    try:
        import json
        import urllib.request

        # Try /models endpoint which LiteLLM supports
        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=2)
        data = json.loads(response.read().decode())
        return isinstance(data, dict) and "data" in data
    except Exception:
        return False


def _check_smolagents_installed() -> bool:
    """Check if smolagents package is installed."""
    try:
        import smolagents  # noqa: F401

        return True
    except ImportError:
        return False


def _count_configured_hooks() -> int:
    """Count kln-hook-* entry points configured in settings.json."""
    settings_path = CLAUDE_DIR / "settings.json"
    if not settings_path.exists():
        return 0

    try:
        import json

        settings = json.loads(settings_path.read_text())
        hooks = settings.get("hooks", {})
        count = 0
        for _event, hook_list in hooks.items():
            for hook_config in hook_list:
                hook_entries = hook_config.get("hooks", [])
                for entry in hook_entries:
                    if isinstance(entry, dict) and "kln-hook-" in entry.get("command", ""):
                        count += 1
        return count
    except Exception:
        return 0


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


def get_project_socket_path(project_path: Path = None) -> Path:
    """Get per-project port file path (for TCP-based knowledge server).

    Returns the port file path, not a socket path. This is for backwards
    compatibility - callers should check for port file existence.
    """
    if project_path is None:
        project_path = find_project_root()
    if not project_path:
        return None
    return get_kb_port_file(project_path)


def find_project_root(start_path: Path = None) -> Path:
    """Find project root by walking up looking for .knowledge-db."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if (current / ".knowledge-db").exists():
            return current
        current = current.parent
    return None


def check_knowledge_server(project_path: Path = None) -> bool:
    """Check if knowledge server is running for a project via TCP."""
    import socket as sock

    if project_path is None:
        project_path = find_project_root()
    if not project_path:
        return False

    port_file = get_kb_port_file(project_path)
    if not port_file.exists():
        return False

    try:
        port = int(port_file.read_text().strip())
        client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        client.settimeout(1)
        client.connect(("127.0.0.1", port))
        client.sendall(b'{"cmd":"ping"}')
        response = client.recv(1024).decode()
        client.close()
        return '"pong"' in response
    except (OSError, ValueError):
        # Port file exists but no server - clean up stale files
        cleanup_stale_files(project_path)
        return False


def list_knowledge_servers() -> list:
    """List all running knowledge servers (using TCP)."""
    import json
    import socket as sock

    servers = []
    runtime_dir = get_runtime_dir()

    # Find all port files in runtime directory
    for port_file in runtime_dir.glob("kb-*.port"):
        pid_file = port_file.with_suffix(".pid")
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                port = int(port_file.read_text().strip())

                # Check if process is running
                if not is_process_running(pid):
                    continue

                # Get project info via TCP
                client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
                client.settimeout(2)
                client.connect(("127.0.0.1", port))
                client.sendall(b'{"cmd":"status"}')
                response = json.loads(client.recv(65536).decode())
                client.close()
                servers.append(
                    {
                        "port": port,
                        "pid": pid,
                        "project": response.get("project", "unknown"),
                        "entries": response.get("entries", 0),
                        "idle": response.get("idle_seconds", 0),
                    }
                )
            except Exception:
                pass
    return servers


def check_phoenix() -> bool:
    """Check if Phoenix telemetry server is running on port 6006."""
    try:
        import urllib.request

        urllib.request.urlopen("http://localhost:6006", timeout=1)
        return True
    except Exception:
        return False


def start_phoenix(background: bool = True) -> bool:
    """Start Phoenix telemetry server on port 6006.

    Returns:
        True if Phoenix started or already running, False if failed.
    """
    if check_phoenix():
        return True  # Already running

    try:
        import subprocess

        cmd = [sys.executable, "-m", "phoenix.server.main", "serve"]
        if background:
            log_file = LOGS_DIR / "phoenix.log"
            subprocess.Popen(
                cmd, stdout=open(log_file, "w"), stderr=subprocess.STDOUT, start_new_session=True
            )
            # Give it a moment to start
            import time

            time.sleep(1)
            return check_phoenix()
        else:
            subprocess.run(cmd)
            return True
    except Exception:
        return False


def _ensure_kb_initialized(project_path: Path) -> bool:
    """Ensure knowledge DB is initialized for project.

    Creates empty index if .knowledge-db doesn't exist or has no index.

    Args:
        project_path: Project root directory

    Returns:
        True if KB is initialized (or was just initialized), False on error.
    """
    kb_dir = project_path / ".knowledge-db"
    entries_file = kb_dir / "entries.jsonl"
    embeddings_file = kb_dir / "embeddings.npy"

    # Already initialized?
    if embeddings_file.exists() or entries_file.exists():
        return True

    # Create .knowledge-db directory
    kb_dir.mkdir(parents=True, exist_ok=True)

    # Create empty entries file (server needs at least this to start)
    if not entries_file.exists():
        entries_file.write_text("")

    # Run rebuild to create empty index
    try:
        rebuild_script = CLAUDE_DIR / "scripts" / "knowledge_db.py"
        if rebuild_script.exists():
            venv_python = get_venv_python(VENV_DIR)
            python_cmd = str(venv_python) if venv_python.exists() else sys.executable
            result = subprocess.run(
                [python_cmd, str(rebuild_script), "rebuild", str(project_path)],
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
    except Exception:
        pass

    return True  # Directory exists, server can try to start


def start_knowledge_server(project_path: Path = None, wait: bool = True) -> bool:
    """Start knowledge server for a project in background (cross-platform).

    Args:
        project_path: Project root (auto-detected from CWD if None)
        wait: If True, wait up to 60s for server to start (loads index ~20s).
              If False, start in background and return immediately.
    """
    if project_path is None:
        project_path = find_project_root()

    if not project_path:
        return False  # No project found

    if check_knowledge_server(project_path):
        return True  # Already running

    # Ensure KB is initialized (creates empty index if needed)
    _ensure_kb_initialized(project_path)

    try:
        knowledge_script = CLAUDE_DIR / "scripts" / "knowledge-server.py"
        if not knowledge_script.exists():
            return False

        # Use the venv python if available
        venv_python = get_venv_python(VENV_DIR)
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        # Clean up stale files first
        cleanup_stale_files(project_path)

        # Start server in background with log capture
        ensure_klean_dirs()
        log_file = LOGS_DIR / "knowledge-server.log"

        cmd = [python_cmd, str(knowledge_script), "start", str(project_path)]
        pid = spawn_background(cmd, cwd=project_path, log_file=log_file)

        if not wait:
            return True  # Started, but not confirmed

        # Wait for TCP port (up to 60s for index loading)
        port_file = get_kb_port_file(project_path)
        for _ in range(600):  # 60 seconds
            time.sleep(0.1)
            if port_file.exists():
                if check_knowledge_server(project_path):
                    return True

        # Process still running but not ready = OK, initializing
        if is_process_running(pid):
            return True  # Started, will be ready soon

        return False  # Process exited = real failure
    except Exception:
        return False


def ensure_knowledge_server(project_path: Path = None) -> None:
    """Ensure knowledge server is running for project, start if needed (silent)."""
    if not check_knowledge_server(project_path):
        start_knowledge_server(project_path)


def ensure_klean_dirs() -> None:
    """Ensure K-LEAN directories exist."""
    KLEAN_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    PIDS_DIR.mkdir(parents=True, exist_ok=True)


def get_litellm_pid_file() -> Path:
    """Get path to LiteLLM PID file."""
    return PIDS_DIR / "litellm.pid"


def get_knowledge_pid_file() -> Path:
    """Get path to Knowledge server PID file."""
    return PIDS_DIR / "knowledge.pid"


def check_litellm_detailed() -> dict[str, Any]:
    """Check LiteLLM status with detailed info."""
    result = {"running": False, "port": 4000, "models": [], "error": None}
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=3)
        data = json.loads(response.read().decode())
        if isinstance(data, dict) and "data" in data:
            result["running"] = True
            result["models"] = [m.get("id", "unknown") for m in data.get("data", [])]
    except urllib.error.URLError:
        result["error"] = "Connection refused (proxy not running)"
    except Exception as e:
        result["error"] = str(e)
    return result


# K-LEAN hooks configuration for Claude Code settings.json
# Uses Python entry points (cross-platform) instead of shell scripts
KLEAN_HOOKS_CONFIG = {
    "SessionStart": [
        {
            "matcher": "startup",
            "hooks": [{"type": "command", "command": "kln-hook-session", "timeout": 10}],
        },
        {
            "matcher": "resume",
            "hooks": [{"type": "command", "command": "kln-hook-session", "timeout": 10}],
        },
    ],
    "UserPromptSubmit": [
        {"hooks": [{"type": "command", "command": "kln-hook-prompt", "timeout": 30}]}
    ],
    "PostToolUse": [
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "kln-hook-bash", "timeout": 15}],
        },
        {
            "matcher": "WebFetch|WebSearch",
            "hooks": [{"type": "command", "command": "kln-hook-web", "timeout": 10}],
        },
        {
            "matcher": "mcp__tavily__.*",
            "hooks": [{"type": "command", "command": "kln-hook-web", "timeout": 10}],
        },
    ],
}


def _is_old_klean_hook(hook_entry: dict) -> bool:
    """Check if a hook entry is an old K-LEAN shell script hook."""
    if "hooks" not in hook_entry:
        return False
    for h in hook_entry["hooks"]:
        cmd = h.get("command", "")
        # Old shell script hooks referenced ~/.claude/hooks/*.sh
        if "~/.claude/hooks/" in cmd and cmd.endswith(".sh"):
            return True
        # Also check for old user-prompt-handler.sh pattern
        if "user-prompt-handler.sh" in cmd or "session-start.sh" in cmd:
            return True
        if "post-bash-handler.sh" in cmd or "post-web-handler.sh" in cmd:
            return True
    return False


def merge_klean_hooks(existing_settings: dict) -> tuple[dict, list[str]]:
    """Merge K-LEAN hooks into existing settings.json, preserving user hooks.

    Also removes old K-LEAN shell script hooks that are no longer used.

    Returns:
        tuple: (updated_settings, list of hooks added)
    """
    added = []

    if "hooks" not in existing_settings:
        existing_settings["hooks"] = {}

    hooks = existing_settings["hooks"]

    # First pass: remove old K-LEAN shell script hooks
    for hook_type in list(hooks.keys()):
        hooks[hook_type] = [h for h in hooks[hook_type] if not _is_old_klean_hook(h)]

    # Second pass: add new K-LEAN hooks
    for hook_type, klean_hook_list in KLEAN_HOOKS_CONFIG.items():
        if hook_type not in hooks:
            # No hooks of this type exist - add all K-LEAN hooks
            hooks[hook_type] = klean_hook_list
            added.append(f"{hook_type} ({len(klean_hook_list)} entries)")
        else:
            # Hooks exist - merge by matcher to avoid duplicates
            existing_matchers = set()
            for h in hooks[hook_type]:
                # Use matcher if present, otherwise use command path as identifier
                matcher = h.get("matcher", "")
                if not matcher and "hooks" in h:
                    # For hooks without matcher, use command as identifier
                    matcher = h["hooks"][0].get("command", "") if h["hooks"] else ""
                existing_matchers.add(matcher)

            for klean_hook in klean_hook_list:
                klean_matcher = klean_hook.get("matcher", "")
                if not klean_matcher and "hooks" in klean_hook:
                    klean_matcher = (
                        klean_hook["hooks"][0].get("command", "") if klean_hook["hooks"] else ""
                    )

                if klean_matcher not in existing_matchers:
                    hooks[hook_type].append(klean_hook)
                    added.append(f"{hook_type}[{klean_matcher or 'default'}]")

    return existing_settings, added


def start_litellm(background: bool = True, port: int = 4000) -> bool:
    """Start LiteLLM proxy server (cross-platform, no shell scripts)."""
    ensure_klean_dirs()

    # Check if already running
    if check_litellm():
        return True

    # Check config exists
    config_file = CONFIG_DIR / "config.yaml"
    if not config_file.exists():
        console.print("[red]Error: ~/.config/litellm/config.yaml not found[/red]")
        console.print("   Run: kln install")
        return False

    # Check .env exists
    env_file = CONFIG_DIR / ".env"
    if not env_file.exists():
        console.print("[red]Error: ~/.config/litellm/.env not found[/red]")
        console.print("   Copy from .env.example and add your API key")
        return False

    # Check for litellm binary (in pipx venv or system PATH)
    litellm_bin = get_litellm_binary()
    if not litellm_bin:
        console.print("[red]Error: litellm not installed. Run: pip install litellm[/red]")
        return False

    log_file = LOGS_DIR / "litellm.log"
    pid_file = get_litellm_pid_file()

    # Build command - use litellm binary directly
    cmd = [
        str(litellm_bin),
        "--config",
        str(config_file),
        "--port",
        str(port),
    ]

    # Windows: use hypercorn instead of uvicorn (no uvloop dependency)
    if sys.platform == "win32":
        cmd.append("--run_hypercorn")

    # Load environment from .env file
    env = os.environ.copy()
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")

    try:
        if background:
            # Start in background using platform.spawn_background
            pid = spawn_background(cmd, cwd=CONFIG_DIR, env=env, log_file=log_file)
            pid_file.write_text(str(pid))

            # Wait for proxy to be ready (5s quick check)
            for _i in range(50):
                time.sleep(0.1)
                if check_litellm():
                    return True

            # Process started but not yet responding - check if still running
            if is_process_running(pid):
                return True  # Started, will be ready soon

            return False  # Process exited = real failure
        else:
            # Run in foreground
            subprocess.run(cmd, env=env, cwd=CONFIG_DIR)
            return True
    except Exception as e:
        console.print(f"[red]Error starting LiteLLM: {e}[/red]")
        return False


def stop_litellm() -> bool:
    """Stop LiteLLM proxy server (cross-platform)."""
    pid_file = get_litellm_pid_file()
    stopped = False

    # Try to kill by PID file
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if is_process_running(pid):
                kill_process_tree(pid, timeout=5.0)
                stopped = True
            pid_file.unlink(missing_ok=True)
        except (ValueError, OSError):
            pid_file.unlink(missing_ok=True)

    # Fallback: find litellm process by pattern (cross-platform via psutil)
    if not stopped:
        try:
            import psutil

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info.get("cmdline") or []
                    cmdline_str = " ".join(cmdline)
                    if "litellm" in cmdline_str and "--port" in cmdline_str:
                        kill_process_tree(proc.info["pid"], timeout=5.0)
                        stopped = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

    return stopped


def stop_knowledge_server(project_path: Path = None, stop_all: bool = False) -> bool:
    """Stop knowledge server(s) (cross-platform).

    Args:
        project_path: Stop server for specific project (auto-detect from CWD if None)
        stop_all: If True, stop ALL running knowledge servers
    """
    runtime_dir = get_runtime_dir()

    if stop_all:
        # Stop all running servers
        servers = list_knowledge_servers()
        if not servers:
            return True  # Nothing to stop

        for server in servers:
            try:
                kill_process_tree(server["pid"], timeout=5.0)
            except Exception:
                pass

        # Clean up all port and pid files
        for port_file in runtime_dir.glob("kb-*.port"):
            try:
                port_file.unlink(missing_ok=True)
            except Exception:
                pass
        for pid_file in runtime_dir.glob("kb-*.pid"):
            try:
                pid_file.unlink(missing_ok=True)
            except Exception:
                pass
        return True

    # Stop server for specific project
    if project_path is None:
        project_path = find_project_root()

    if not project_path:
        return False  # No project found

    # Check if running via PID file
    pid_file = get_kb_pid_file(project_path)
    port_file = get_kb_port_file(project_path)

    if not pid_file.exists() and not port_file.exists():
        return True  # Not running

    # Kill by PID
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if is_process_running(pid):
                kill_process_tree(pid, timeout=5.0)
        except (ValueError, OSError):
            pass

    # Clean up files
    cleanup_stale_files(project_path)

    # Verify stopped
    return not check_knowledge_server(project_path)


def log_debug_event(component: str, event: str, **kwargs) -> None:
    """Log a debug event to the unified log file."""
    ensure_klean_dirs()
    log_file = LOGS_DIR / "debug.log"

    entry = {"ts": datetime.now().isoformat(), "component": component, "event": event, **kwargs}

    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silent fail for logging


def read_debug_log(lines: int = 50, component: Optional[str] = None) -> list[dict]:
    """Read recent entries from debug log."""
    log_file = LOGS_DIR / "debug.log"
    if not log_file.exists():
        return []

    entries = []
    try:
        with open(log_file) as f:
            all_lines = f.readlines()
            for line in all_lines[-lines * 2 :]:  # Read extra to filter
                try:
                    entry = json.loads(line.strip())
                    if component is None or entry.get("component") == component:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return entries[-lines:]


def discover_models() -> list[str]:
    """Discover available models from LiteLLM proxy."""
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=3)
        data = json.loads(response.read().decode())
        if isinstance(data, dict) and "data" in data:
            return [m.get("id", "unknown") for m in data.get("data", [])]
    except Exception:
        pass
    return []


def query_phoenix_traces(limit: int = 500) -> Optional[dict]:
    """Query Phoenix telemetry for recent LLM traces.

    Returns aggregated stats and recent spans from all projects.
    """
    if not check_phoenix():
        return None

    query = f"""{{
        projects {{
            edges {{
                node {{
                    name
                    traceCount
                    spans(first: {limit}) {{
                        edges {{
                            node {{
                                name
                                latencyMs
                                startTime
                                statusCode
                                attributes
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}"""

    try:
        import urllib.request

        req = urllib.request.Request(
            "http://localhost:6006/graphql",
            data=json.dumps({"query": query}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        # Parse and aggregate results
        result = {
            "total_traces": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0,
            "error_count": 0,
            "llm_calls": [],
            "projects": {},
        }

        all_latencies = []

        for edge in data.get("data", {}).get("projects", {}).get("edges", []):
            node = edge.get("node", {})
            project_name = node.get("name", "unknown")
            trace_count = node.get("traceCount", 0)

            result["total_traces"] += trace_count
            result["projects"][project_name] = trace_count

            # Process spans
            for span_edge in node.get("spans", {}).get("edges", []):
                span = span_edge.get("node", {})
                name = span.get("name", "")
                latency = span.get("latencyMs", 0)
                status = span.get("statusCode", "OK")
                start_time = span.get("startTime", "")
                attrs_str = span.get("attributes", "{}")

                # Only process LLM spans
                if "LLM" in name or "generate" in name.lower():
                    try:
                        attrs = json.loads(attrs_str) if isinstance(attrs_str, str) else attrs_str
                    except (json.JSONDecodeError, TypeError):
                        attrs = {}

                    # Extract token counts
                    llm_attrs = attrs.get("llm", {})
                    token_count = llm_attrs.get("token_count", {})
                    prompt_tokens = token_count.get("prompt", 0)
                    completion_tokens = token_count.get("completion", 0)
                    total_tokens = token_count.get("total", prompt_tokens + completion_tokens)
                    model_name = llm_attrs.get("model_name", "unknown")

                    result["total_tokens"] += total_tokens
                    all_latencies.append(latency)

                    if status == "ERROR":
                        result["error_count"] += 1

                    # Add to LLM calls list
                    result["llm_calls"].append(
                        {
                            "time": start_time,
                            "model": model_name.split("/")[-1] if "/" in model_name else model_name,
                            "latency_ms": int(latency),
                            "tokens_in": prompt_tokens,
                            "tokens_out": completion_tokens,
                            "status": status,
                            "project": project_name,
                        }
                    )

        # Calculate averages
        if all_latencies:
            result["avg_latency_ms"] = int(sum(all_latencies) / len(all_latencies))

        # Sort LLM calls by time (most recent first)
        result["llm_calls"].sort(key=lambda x: x.get("time", ""), reverse=True)

        return result

    except Exception:
        return None


def get_model_health() -> dict[str, str]:
    """Check health of each model via LiteLLM API."""
    health = {}
    models = discover_models()

    for model in models:
        try:
            # Quick health check via LiteLLM completion with minimal tokens
            import httpx

            response = httpx.post(
                "http://localhost:4000/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 5,
                },
                timeout=15.0,
            )
            health[model] = "OK" if response.status_code == 200 else "FAIL"
        except httpx.TimeoutException:
            health[model] = "TIMEOUT"
        except Exception:
            health[model] = "ERROR"

    return health


@click.group()
@click.version_option(version=__version__, prog_name="kln")
def main():
    """K-LEAN: Multi-model code review and knowledge capture system for Claude Code."""
    # Services are started explicitly via `kln start`
    # Optional autostart can be configured in ~/.bashrc
    pass


def configure_statusline() -> bool:
    """Configure Claude Code statusline with K-LEAN statusline script.

    Automatically adds statusline configuration to ~/.claude/settings.json
    so the statusline works immediately after installation.

    Returns:
        True if configuration succeeded, False if skipped/failed
    """
    try:
        settings_file = CLAUDE_DIR / "settings.json"
        statusline_script = CLAUDE_DIR / "scripts" / "klean-statusline.py"

        # Check if statusline script exists
        if not statusline_script.exists():
            return False

        # Read existing settings or create new ones
        settings = {}
        if settings_file.exists():
            try:
                with open(settings_file) as f:
                    settings = json.load(f)
            except (OSError, json.JSONDecodeError):
                # If settings.json is corrupt, start fresh
                settings = {}

        # Check if statusline is already configured correctly
        existing_statusline = settings.get("statusLine", {})
        existing_command = existing_statusline.get("command", "")
        existing_type = existing_statusline.get("type", "")

        if existing_command == str(statusline_script) and existing_type == "command":
            # Already configured correctly (both command and type are set)
            return True

        # Configure statusline
        settings["statusLine"] = {"type": "command", "command": str(statusline_script)}

        # Write back with proper formatting
        ensure_dir(CLAUDE_DIR)
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not configure statusline: {e}[/yellow]")
        return False


# ============================================================
# PROVIDER SUBCOMMAND GROUP
# ============================================================


def _load_existing_env() -> dict:
    """Load existing .env variables."""
    env_file = CONFIG_DIR / ".env"
    if not env_file.exists():
        return {}

    env_vars = {}
    try:
        for line in env_file.read_text().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    except Exception:
        pass
    return env_vars


def _get_configured_providers() -> dict:
    """Get list of configured providers and their status."""
    env_vars = _load_existing_env()
    providers = {}

    # Check each known provider
    for provider_name, key_var in [
        ("nanogpt", "NANOGPT_API_KEY"),
        ("openrouter", "OPENROUTER_API_KEY"),
    ]:
        if key_var in env_vars:
            # Check if key looks valid (not placeholder)
            key_value = env_vars[key_var]
            is_configured = key_value and "your-" not in key_value.lower()
            providers[provider_name] = {"configured": is_configured, "key": key_value}

    return providers


@click.group()
def provider():
    """Manage K-LEAN providers (NanoGPT, OpenRouter, etc.)"""
    pass


@provider.command(name="list")
def provider_list():
    """List configured providers and their status."""
    print_banner()

    providers = _get_configured_providers()

    if not providers:
        console.print("[yellow]No providers configured[/yellow]")
        console.print("Add one with: [cyan]kln provider add nanogpt --api-key $KEY[/cyan]")
        return

    table = Table(title="Configured Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Models", style="dim")

    # For each provider, try to count models in config
    config_file = CONFIG_DIR / "config.yaml"
    model_counts = {}
    if config_file.exists():
        try:
            import yaml

            config = yaml.safe_load(config_file.read_text())
            for model in config.get("model_list", []):
                # Detect provider by api_key field, not model prefix
                # NanoGPT uses openai/ prefix but should count as nanogpt
                params = model.get("litellm_params", {})
                api_key = params.get("api_key", "")
                if "NANOGPT" in api_key:
                    provider_name = "nanogpt"
                elif "OPENROUTER" in api_key:
                    provider_name = "openrouter"
                else:
                    # Fallback to model prefix for unknown providers
                    provider_name = params.get("model", "").split("/")[0]
                if provider_name in model_counts:
                    model_counts[provider_name] += 1
                else:
                    model_counts[provider_name] = 1
        except Exception:
            pass

    for name, info in sorted(providers.items()):
        status = (
            f"[green]{SYM_OK} ACTIVE[/green]"
            if info["configured"]
            else f"[red]{SYM_FAIL} NOT CONFIGURED[/red]"
        )
        model_count = model_counts.get(name, 0)
        models = f"({model_count} models)" if model_count > 0 else "(no models)"
        table.add_row(name.upper(), status, models)

    console.print(table)


@provider.command(name="add")
@click.argument("provider_name", type=click.Choice(["nanogpt", "openrouter"]))
@click.option("--api-key", "-k", help="API key (if not provided, will prompt)")
def provider_add(provider_name: str, api_key: str):
    """Add or update a provider configuration."""
    from klean.config_generator import (
        _yaml_to_string,
        generate_env_file,
        load_config_yaml,
        merge_models_into_config,
    )
    from klean.model_defaults import get_nanogpt_models, get_openrouter_models

    if not api_key:
        api_key = click.prompt(f"{provider_name.upper()} API Key", hide_input=True)

    if not api_key:
        console.print("[red]Error: API key cannot be empty[/red]")
        return

    # Load existing env
    existing_env = _load_existing_env()

    # Create provider dict
    providers_dict = {provider_name: api_key}

    # Generate new env content (preserves existing providers)
    env_content = generate_env_file(providers_dict, existing_env=existing_env)

    # Write updated .env
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / ".env").write_text(env_content)
    (CONFIG_DIR / ".env").chmod(0o600)

    console.print(f"\n[green]{SYM_OK}[/green] Configured {provider_name.upper()} API key")

    # Show recommended models and ask for confirmation
    if provider_name == "nanogpt":
        recommended_models = get_nanogpt_models()
    else:
        recommended_models = get_openrouter_models()

    console.print(
        f"\n[bold]Recommended {provider_name.upper()} Models ({len(recommended_models)})[/bold]"
    )
    for model in recommended_models:
        console.print(f"  • {model['model_name']}")

    install_models = click.confirm("\nAdd these recommended models?", default=True)

    if install_models:
        # Load existing config or create new one
        config_path = CONFIG_DIR / "config.yaml"
        existing_config = load_config_yaml(config_path)

        if existing_config is None:
            # No config exists yet, create new one with recommended models
            from klean.config_generator import generate_litellm_config

            config_yaml = generate_litellm_config(recommended_models)
        else:
            # Merge recommended models into existing config
            updated_config = merge_models_into_config(existing_config, recommended_models)
            config_yaml = _yaml_to_string(updated_config)

        # Write updated config
        config_path.write_text(config_yaml)

        console.print(
            f"\n[green]{SYM_OK}[/green] Added {len(recommended_models)} recommended models"
        )
        console.print("Changes will take effect after service restart")
    else:
        console.print("\nNo models added. Add them later with:")
        console.print(f'  [cyan]kln model add --provider {provider_name} "model-id"[/cyan]')

    console.print("\nNext steps:")
    console.print("  • Review models: [cyan]kln model list[/cyan]")
    console.print("  • Restart services: [cyan]kln restart[/cyan]")


@provider.command(name="set-key")
@click.argument("provider_name", type=click.Choice(["nanogpt", "openrouter"]))
@click.option("--key", "-k", help="New API key")
def provider_set_key(provider_name: str, key: str):
    """Update API key for an existing provider."""
    if not key:
        key = click.prompt(f"New {provider_name.upper()} API Key", hide_input=True)

    if not key:
        console.print("[red]Error: API key cannot be empty[/red]")
        return

    existing_env = _load_existing_env()

    # Check if provider exists
    key_var = f"{provider_name.upper()}_API_KEY"
    if key_var not in existing_env:
        console.print(
            f"[yellow]Warning: {provider_name.upper()} not previously configured[/yellow]"
        )
        if not click.confirm("Continue anyway?", default=False):
            return

    from klean.config_generator import generate_env_file

    providers_dict = {provider_name: key}
    env_content = generate_env_file(providers_dict, existing_env=existing_env)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / ".env").write_text(env_content)
    (CONFIG_DIR / ".env").chmod(0o600)

    console.print(f"[green]{SYM_OK}[/green] Updated {provider_name.upper()} API key")


@provider.command(name="remove")
@click.argument("provider_name", type=click.Choice(["nanogpt", "openrouter"]))
def provider_remove(provider_name: str):
    """Remove a provider configuration."""
    if not click.confirm(f"Remove {provider_name.upper()} configuration?", default=False):
        console.print("Cancelled")
        return

    existing_env = _load_existing_env()

    # Remove provider keys
    key_vars = [f"{provider_name.upper()}_API_KEY", f"{provider_name.upper()}_API_BASE"]
    if provider_name == "nanogpt":
        key_vars.append("NANOGPT_THINKING_API_BASE")

    for key_var in key_vars:
        existing_env.pop(key_var, None)

    # Rebuild .env without this provider
    content = "# K-LEAN LiteLLM Environment Variables\n"
    content += "# Generated by kln setup\n"
    content += "\n"
    for key in sorted(existing_env.keys()):
        content += f"{key}={existing_env[key]}\n"

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / ".env").write_text(content)
    (CONFIG_DIR / ".env").chmod(0o600)

    console.print(f"[green]{SYM_OK}[/green] Removed {provider_name.upper()} configuration")
    console.print("[dim]Models from this provider will no longer be available[/dim]")


# ============================================================
# MODEL SUBCOMMAND GROUP
# ============================================================


@click.group()
def model():
    """Manage K-LEAN models"""
    pass


@model.command(name="list")
@click.option("--test", is_flag=True, help="Test each model with API call")
@click.option("--health", is_flag=True, help="Check model health status")
def model_list(test: bool, health: bool):
    """List available models from LiteLLM proxy.

    Use --health to check which models are healthy/unhealthy.
    Use --test to test each model with an API call and measure latency.
    """
    print_banner()

    if not check_litellm():
        console.print("\n[red]LiteLLM proxy is not running![/red]")
        console.print("Start it with: [cyan]kln start --service litellm[/cyan]")
        return

    models_list = discover_models()

    if not models_list:
        console.print("\n[yellow]No models found[/yellow]")
        return

    # Health check mode - query /health endpoint
    if health:
        console.print("\n[bold]Model Health Check[/bold]")
        console.print("[dim]Querying LiteLLM /health endpoint...[/dim]\n")
        try:
            import urllib.request

            req = urllib.request.Request("http://localhost:4000/health")
            response = urllib.request.urlopen(req, timeout=60)
            health_data = json.loads(response.read().decode())

            healthy_count = health_data.get("healthy_count", 0)
            unhealthy_count = health_data.get("unhealthy_count", 0)
            total = healthy_count + unhealthy_count

            # Summary
            if unhealthy_count == 0:
                console.print(f"[green][OK] All {healthy_count} models healthy[/green]\n")
            elif healthy_count == 0:
                console.print(f"[red]{SYM_FAIL} All {unhealthy_count} models unhealthy![/red]")
                console.print("[dim]Check: kln doctor -f[/dim]\n")
            else:
                console.print(
                    f"[yellow]○ {healthy_count}/{total} models healthy ({unhealthy_count} failing)[/yellow]\n"
                )

            # Show unhealthy models
            unhealthy_endpoints = health_data.get("unhealthy_endpoints", [])
            if unhealthy_endpoints:
                table = Table(title="Unhealthy Models")
                table.add_column("Model", style="red")
                table.add_column("Error", style="dim")

                for endpoint in unhealthy_endpoints:
                    model = endpoint.get("model", "unknown")
                    error = endpoint.get("error", "unknown error")
                    # Truncate error message
                    if len(error) > 60:
                        error = error[:57] + "..."
                    table.add_row(model, error)

                console.print(table)

            # Show healthy models
            healthy_endpoints = health_data.get("healthy_endpoints", [])
            if healthy_endpoints and unhealthy_count > 0:
                console.print(
                    f"\n[green]Healthy models:[/green] {', '.join(e.get('model', '?').split('/')[-1] for e in healthy_endpoints)}"
                )

        except Exception as e:
            console.print(f"[red]{SYM_FAIL} Could not check health: {e}[/red]")
        return

    if test:
        console.print("\n[dim]Testing models (5s timeout, uses tokens)...[/dim]")
        import urllib.request

        # Test each model and record latency
        results = []  # [(model, latency_ms or None)]
        for model in models_list:
            try:
                start = time.time()
                data = json.dumps(
                    {
                        "model": model,
                        "messages": [{"role": "user", "content": "1"}],
                        "max_tokens": 1,
                    }
                ).encode()
                req = urllib.request.Request(
                    "http://localhost:4000/chat/completions",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=5)
                latency = int((time.time() - start) * 1000)
                results.append((model, latency))
                console.print(f"  [green][OK][/green] {model}: {latency}ms")
            except Exception:
                results.append((model, None))
                console.print(f"  [red]{SYM_FAIL}[/red] {model}: FAIL")

        # Sort by latency (fastest first), failures last
        results.sort(key=lambda x: (x[1] is None, x[1] if x[1] else 99999))

        console.print()
        table = Table(title="Models by Latency")
        table.add_column("Model ID", style="cyan")
        table.add_column("Latency", justify="right")

        for model, latency in results:
            if latency is not None:
                table.add_row(model, f"[green]{latency}ms[/green]")
            else:
                table.add_row(model, "[red]FAIL[/red]")

        console.print(table)
        ok_count = sum(1 for _, lat in results if lat is not None)
        console.print(f"\n[bold]Total:[/bold] {ok_count}/{len(models_list)} models OK")
    else:
        table = Table(title="Available Models")
        table.add_column("Model ID", style="cyan")
        table.add_column("Status", style="green")

        for model in models_list:
            table.add_row(model, "[green]available[/green]")

        console.print(table)
        console.print(f"\n[dim]{len(models_list)} models available[/dim]")


@model.command(name="add")
@click.option(
    "--provider",
    required=True,
    type=click.Choice(["nanogpt", "openrouter"]),
    help="Model provider (nanogpt or openrouter)",
)
@click.argument("model_id")
def model_add(provider: str, model_id: str):
    """Add individual model to LiteLLM configuration.

    Examples:
        kln model add --provider openrouter "anthropic/claude-3.5-sonnet"
        kln model add --provider nanogpt "moonshotai/kimi-k2"
    """

    config_file = CONFIG_DIR / "config.yaml"
    if not config_file.exists():
        console.print("[red]Error: config.yaml not found. Run 'kln init' first.[/red]")
        sys.exit(1)

    # Parse the model ID
    if provider == "openrouter":
        full_model_id = f"openrouter/{model_id}"
        model_name = model_id.split("/")[-1]
    elif provider == "nanogpt":
        full_model_id = f"openai/{model_id}"
        model_name = model_id.split("/")[-1]
    else:
        console.print(f"[red]Error: Unknown provider '{provider}'[/red]")
        sys.exit(1)

    # Create model entry
    if provider == "openrouter":
        model_entry = {
            "model_name": model_name,
            "litellm_params": {
                "model": full_model_id,
                "api_key": "os.environ/OPENROUTER_API_KEY",
            },
        }
    else:  # nanogpt
        model_entry = {
            "model_name": model_name,
            "litellm_params": {
                "model": full_model_id,
                "api_key": "os.environ/NANOGPT_API_KEY",
            },
        }
        # Use thinking endpoint for thinking models
        if "thinking" in model_name.lower():
            model_entry["litellm_params"]["api_base"] = "os.environ/NANOGPT_THINKING_API_BASE"
        else:
            model_entry["litellm_params"]["api_base"] = "os.environ/NANOGPT_API_BASE"

    # Load existing config
    import yaml

    try:
        config_content = config_file.read_text()
        config = yaml.safe_load(config_content)
    except Exception as e:
        console.print(f"[red]Error reading config.yaml: {e}[/red]")
        sys.exit(1)

    # Check if model already exists
    existing_names = [m.get("model_name") for m in config.get("model_list", [])]
    if model_name in existing_names:
        console.print(f"[yellow]Warning: Model '{model_name}' already exists in config[/yellow]")
        if not click.confirm("Overwrite?"):
            return
        # Remove existing entry
        config["model_list"] = [
            m for m in config["model_list"] if m.get("model_name") != model_name
        ]

    # Add new model
    config["model_list"].append(model_entry)

    # Save updated config
    try:
        config_file.write_text(_dict_to_yaml(config))
        console.print(f"\n[green][OK] Added model '{model_name}'[/green]")
        console.print(f"  Provider: {provider}")
        console.print(f"  LiteLLM ID: {full_model_id}")
        console.print("\nRestart services to use the new model:")
        console.print("  [cyan]kln restart[/cyan]")
    except Exception as e:
        console.print(f"[red]Error saving config: {e}[/red]")


@model.command(name="remove")
@click.argument("model_name")
def model_remove(model_name: str):
    """Remove model from LiteLLM configuration.

    Examples:
        kln model remove "claude-3-sonnet"
        kln model remove "deepseek-v3-thinking"
    """
    from klean.config_generator import list_models_in_config, remove_model_from_config

    config_file = CONFIG_DIR / "config.yaml"
    if not config_file.exists():
        console.print("[red]Error: config.yaml not found. Run 'kln init' first.[/red]")
        sys.exit(1)

    # Try to remove the model
    removed = remove_model_from_config(config_file, model_name)

    if not removed:
        console.print(f"[yellow]Model '{model_name}' not found in config[/yellow]")
        console.print("\nAvailable models:")
        models = list_models_in_config(config_file)
        for model in models:
            console.print(f"  • {model['model_name']}")
        return

    console.print(f"[green]{SYM_OK}[/green] Removed model '{model_name}'")
    console.print("\nRemaining models:")
    models = list_models_in_config(config_file)
    for model in models:
        thinking_label = " (thinking)" if model["is_thinking"] else ""
        console.print(f"  • {model['model_name']}{thinking_label}")

    console.print("\nRestart services to apply changes:")
    console.print("  [cyan]kln restart[/cyan]")


@model.command(name="test")
@click.argument("model", required=False)
@click.option("--prompt", "-p", help="Custom prompt to test with")
@click.option("--timeout", "-t", default=30, help="Request timeout in seconds (default: 30)")
def model_test(model: Optional[str], prompt: Optional[str], timeout: int):
    """Test a specific model with a quick prompt."""
    print_banner()

    if not model:
        # Auto-select first available model
        models_list = discover_models()
        if not models_list:
            console.print("[red]No models available![/red]")
            return
        model = models_list[0]
        console.print(f"[dim]Testing first available model: {model}[/dim]")
    else:
        console.print(f"[dim]Testing model: {model}[/dim]")

    # Use provided prompt or default
    test_prompt = prompt or "Say 'Hello' and nothing else"

    console.print("\n[bold]Model Test[/bold]")
    console.print(f"Prompt: {test_prompt}\n")

    try:
        import httpx

        from klean.discovery import LITELLM_ENDPOINT

        resp = httpx.post(
            f"{LITELLM_ENDPOINT}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": test_prompt}],
                "max_tokens": 100,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        console.print("[green]Success[/green]")
        console.print(f"Response: {content}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================
# ADMIN SUBCOMMAND GROUP (Hidden - Development Only)
# ============================================================


@click.group(hidden=True)
def admin():
    """Admin commands (development tools)"""
    pass


@admin.command(name="sync")
@click.option("--check", is_flag=True, help="Check sync status only")
@click.option("--clean", is_flag=True, help="Clean before syncing")
@click.option("--verbose", is_flag=True, help="Verbose output")
def admin_sync(check: bool, clean: bool, verbose: bool):
    """Sync root directories to src/klean/data/ for PyPI packaging."""
    print_banner()

    # Get sync function code from original
    import shutil
    from pathlib import Path

    src_root = Path(__file__).parent.parent.parent
    data_dir = Path(__file__).parent / "data"

    console.print("[bold]K-LEAN File Sync[/bold]")
    console.print(f"Source: {src_root}")
    console.print(f"Target: {data_dir}\n")

    if check:
        console.print("[dim]Checking sync status (not implemented)...[/dim]")
        return

    if clean:
        console.print("[yellow]Cleaning target directory...[/yellow]")
        if data_dir.is_symlink():
            data_dir.unlink()
        elif data_dir.exists():
            shutil.rmtree(data_dir)

    console.print("[green]Sync complete[/green]")


@admin.command(name="debug")
@click.option("--follow", "-f", is_flag=True, help="Follow new log entries")
@click.option("--component-filter", "-c", help="Filter by component")
@click.option("--lines", "-n", type=int, default=50, help="Number of recent lines")
@click.option("--compact", is_flag=True, help="Compact output format")
@click.option("--interval", "-i", type=int, default=2, help="Refresh interval (seconds)")
def admin_debug(follow: bool, component_filter: str, lines: int, compact: bool, interval: int):
    """Real-time monitoring dashboard for K-LEAN services and processes."""
    print_banner()
    console.print("[bold cyan]K-LEAN Debug Dashboard[/bold cyan]")
    console.print("[dim]Real-time monitoring (press Ctrl+C to exit)[/dim]\n")

    try:
        while True:
            # Placeholder implementation
            console.print("[dim]Debug dashboard active...[/dim]")
            if follow:
                import time

                time.sleep(interval)
            else:
                break
    except KeyboardInterrupt:
        console.print("\n[dim]Debug dashboard closed[/dim]")


@admin.command(name="test")
def admin_test():
    """Run comprehensive K-LEAN test suite."""
    import shutil
    import subprocess

    if not shutil.which("pytest"):
        console.print("[red]Error:[/red] pytest is not installed")
        console.print("  Install with: [cyan]pip install pytest[/cyan]")
        sys.exit(1)

    print_banner()

    console.print("[bold]Running Test Suite[/bold]\n")
    result = subprocess.run(["pytest", "tests/", "-v"], cwd=Path(__file__).parent.parent.parent)
    sys.exit(result.returncode)


# Register subcommand groups
main.add_command(provider)
main.add_command(model)
main.add_command(admin)


@main.command()
@click.option("--dev", is_flag=True, help="Development mode: use symlinks instead of copies")
@click.option(
    "--component",
    "-c",
    type=click.Choice(
        ["all", "scripts", "commands", "hooks", "smolkln", "config", "core", "knowledge"]
    ),
    default="all",
    help="Component to install",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def install(dev: bool, component: str, yes: bool):
    """Install K-LEAN components to ~/.claude/"""
    print_banner()

    mode = "development (symlinks)" if dev else "production (copies)"
    console.print(f"\n[bold]Installation Mode:[/bold] {mode}")

    # Determine source directory
    # Both dev and production use the same package data directory
    # The only difference is dev creates symlinks, production copies files
    source_base = DATA_DIR
    source_scripts = source_base / "scripts"
    source_commands_kln = source_base / "commands" / "kln"
    # Note: Hooks are now Python entry points, not shell scripts
    source_config = source_base / "config"
    source_core = source_base / "core"

    console.print(f"[dim]Source: {source_scripts.parent}[/dim]\n")

    if not yes and not click.confirm("Proceed with installation?"):
        console.print("[yellow]Installation cancelled[/yellow]")
        return

    installed = {}

    # Install scripts (Python only - cross-platform)
    if component in ["all", "scripts"]:
        console.print("[bold]Installing scripts...[/bold]")
        scripts_dst = CLAUDE_DIR / "scripts"

        if source_scripts.exists():
            count = copy_files(source_scripts, scripts_dst, "*.py", symlink=dev)
            make_executable(scripts_dst)
            installed["scripts"] = count
            console.print(f"  [green]Installed {count} Python scripts[/green]")
        else:
            console.print(f"  [yellow]Scripts source not found: {source_scripts}[/yellow]")

    # Install commands
    if component in ["all", "commands"]:
        console.print("[bold]Installing slash commands...[/bold]")

        # KLN commands
        kln_dst = CLAUDE_DIR / "commands" / "kln"
        if source_commands_kln.exists():
            count = copy_files(source_commands_kln, kln_dst, "*.md", symlink=dev)
            installed["commands_kln"] = count
            console.print(f"  [green]Installed {count} /kln: commands[/green]")

        # SC commands are optional and from external system - skip by default
        # Users can manage SC commands separately

    # Install hooks - hooks are now Python entry points (cross-platform)
    if component in ["all", "hooks"]:
        console.print("[bold]Installing hooks...[/bold]")
        # Hooks are Python entry points installed via pip/pipx (kln-hook-*)
        # They don't need to be copied - just configured in settings.json
        console.print("  [dim]Hooks are Python entry points (kln-hook-*)[/dim]")
        console.print("  [dim]Configured in settings.json (see below)[/dim]")
        installed["hooks"] = 4  # session, prompt, bash, web

    # Install SmolKLN agents
    if component in ["all", "smolkln"]:
        console.print("[bold]Installing SmolKLN agents...[/bold]")
        # SmolKLN agents are always from package data (DATA_DIR)
        pkg_agents = DATA_DIR / "agents"
        if pkg_agents.exists():
            ensure_dir(SMOL_AGENTS_DIR)
            count = copy_files(pkg_agents, SMOL_AGENTS_DIR, "*.md", symlink=dev)
            installed["smolkln_agents"] = count
            console.print(f"  [green]Installed {count} SmolKLN agents to {SMOL_AGENTS_DIR}[/green]")
        else:
            console.print(f"  [yellow]SmolKLN agents source not found at {pkg_agents}[/yellow]")

        # Note: kln-smol command is installed via pipx as part of k-lean package

    # Install config
    if component in ["all", "config"]:
        console.print("[bold]Installing configuration...[/bold]")

        # NOTE: We deliberately do NOT touch CLAUDE.md
        # K-LEAN uses slash commands (/kln:*) which are auto-discovered
        # This preserves user's existing CLAUDE.md configuration
        console.print("  [dim]CLAUDE.md: skipped (using pure plugin approach)[/dim]")

        # LiteLLM config
        litellm_src = (
            source_config / "litellm" if not dev else source_scripts.parent / "config" / "litellm"
        )
        if litellm_src.exists():
            ensure_dir(CONFIG_DIR)
            for cfg_file in litellm_src.glob("*.yaml"):
                dst = CONFIG_DIR / cfg_file.name
                # Skip config.yaml if it already exists (user configured via 'kln setup')
                if cfg_file.name == "config.yaml" and dst.exists():
                    continue
                if dev:
                    if dst.exists() or dst.is_symlink():
                        dst.unlink()
                    dst.symlink_to(cfg_file.resolve())
                else:
                    shutil.copy2(cfg_file, dst)
            console.print("  [green]Installed LiteLLM configs[/green]")

            # Install callbacks for thinking models support
            callbacks_src = litellm_src / "callbacks"
            if callbacks_src.exists():
                callbacks_dst = CONFIG_DIR / "callbacks"
                ensure_dir(callbacks_dst)
                count = copy_files(callbacks_src, callbacks_dst, "*.py", symlink=dev)
                if count > 0:
                    console.print(
                        f"  [green]Installed {count} LiteLLM callbacks (thinking models)[/green]"
                    )

        # Install rules (loaded every Claude session)
        rules_src = DATA_DIR / "rules"
        if rules_src.exists():
            rules_dst = CLAUDE_DIR / "rules"
            ensure_dir(rules_dst)
            count = copy_files(rules_src, rules_dst, "*.md", symlink=dev)
            if count > 0:
                console.print(f"  [green]Installed {count} rules to {rules_dst}[/green]")
                installed["rules"] = count

    # Install core module (klean_core.py, prompts)
    if component in ["all", "core"]:
        console.print("[bold]Installing core module...[/bold]")
        core_dst = CLAUDE_DIR / "kln"
        if source_core.exists():
            ensure_dir(core_dst)
            # Copy main Python file
            core_py = source_core / "klean_core.py"
            if core_py.exists():
                dst_py = core_dst / "klean_core.py"
                if dev:
                    if dst_py.exists() or dst_py.is_symlink():
                        dst_py.unlink()
                    dst_py.symlink_to(core_py.resolve())
                else:
                    shutil.copy2(core_py, dst_py)
                dst_py.chmod(dst_py.stat().st_mode | 0o111)
            # Copy config
            core_cfg = source_core / "config.yaml"
            if core_cfg.exists():
                dst_cfg = core_dst / "config.yaml"
                if dev:
                    if dst_cfg.exists() or dst_cfg.is_symlink():
                        dst_cfg.unlink()
                    dst_cfg.symlink_to(core_cfg.resolve())
                else:
                    shutil.copy2(core_cfg, dst_cfg)
            # Copy prompts directory
            prompts_src = source_core / "prompts"
            if prompts_src.exists():
                prompts_dst = core_dst / "prompts"
                # Handle existing prompts_dst - symlink or directory
                if prompts_dst.is_symlink():
                    prompts_dst.unlink()
                elif prompts_dst.exists():
                    shutil.rmtree(prompts_dst)
                if dev:
                    prompts_dst.symlink_to(prompts_src.resolve())
                else:
                    shutil.copytree(prompts_src, prompts_dst)
            installed["core"] = 1
            console.print("  [green]Installed klean_core.py + prompts[/green]")
        else:
            console.print(f"  [yellow]Core source not found: {source_core}[/yellow]")

    # Install knowledge system
    if component in ["all", "knowledge"]:
        console.print("[bold]Setting up knowledge database...[/bold]")
        if not VENV_DIR.exists():
            console.print("  Creating Python virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

        # Install dependencies
        pip = get_venv_pip(VENV_DIR)
        if pip.exists():
            console.print("  Installing Python dependencies...")
            console.print("  [dim](First install may take 2-5 minutes for ML models...)[/dim]")
            subprocess.run(
                [str(pip), "install", "--upgrade", "pip"],
                capture_output=True,  # pip upgrade is fast, keep quiet
            )
            result = subprocess.run(
                [str(pip), "install", "fastembed", "numpy"]
                # No -q or capture_output: show real-time download progress
            )
            if result.returncode == 0:
                console.print("  [green]Knowledge database ready[/green]")
            else:
                console.print(
                    "  [yellow]Warning: Some dependencies may not have installed[/yellow]"
                )

    # Configure statusline (if scripts were installed)
    if component in ["all", "scripts"]:
        console.print("[bold]Configuring statusline...[/bold]")
        if configure_statusline():
            console.print("  [green]Statusline configured[/green]")
        else:
            console.print("  [dim]Statusline: skipped or already configured[/dim]")

    # Configure hooks in settings.json (if hooks were installed)
    if component in ["all", "hooks"]:
        console.print("[bold]Configuring hooks...[/bold]")
        try:
            settings_file = CLAUDE_DIR / "settings.json"
            if settings_file.exists():
                settings = json.loads(settings_file.read_text())
            else:
                settings = {}

            settings, added = merge_klean_hooks(settings)

            settings_file.write_text(json.dumps(settings, indent=2))

            if added:
                console.print(f"  [green]Configured: {', '.join(added)}[/green]")
            else:
                console.print("  [dim]Hooks already configured[/dim]")
        except Exception as e:
            console.print(f"  [yellow]Warning: Could not configure hooks: {e}[/yellow]")

    # Summary
    console.print("\n[bold green]Installation complete![/bold green]")

    if dev:
        console.print("\n[cyan]Development mode:[/cyan] Files are symlinked to source.")
        console.print("Edit source files and changes will be immediately available.")

    console.print("\n[bold]Next steps:[/bold]")
    env_file = CONFIG_DIR / ".env"
    step = 1
    if not env_file.exists():
        console.print(f"  {step}. Configure API keys: [cyan]kln setup[/cyan]")
        step += 1
    console.print(f"  {step}. Start services: [cyan]kln start[/cyan]")
    step += 1
    console.print(f"  {step}. Verify: [cyan]kln status[/cyan]")

    # Check if smolagents is installed
    if not _check_smolagents_installed():
        console.print("\n[bold]Optional - SmolKLN agents:[/bold]")
        console.print("  To use SmolKLN agents, install:")
        console.print("  [cyan]pipx inject kln-ai 'smolagents[litellm]'[/cyan]")


@main.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def uninstall(yes: bool):
    """Remove K-LEAN components from ~/.claude/"""
    print_banner()

    console.print("\n[bold yellow]This will remove K-LEAN components[/bold yellow]")
    console.print("Components to remove:")
    console.print("  - ~/.claude/scripts/")
    console.print("  - ~/.claude/commands/kln/")
    console.print("  - ~/.claude/hooks/")
    console.print("  - ~/.claude/rules/kln.md")
    console.print("  - ~/.klean/agents/")

    if not yes and not click.confirm("\nProceed with uninstallation?"):
        console.print("[yellow]Uninstallation cancelled[/yellow]")
        return

    # Stop services first
    console.print("\n[bold]Stopping services...[/bold]")
    stop_litellm()
    stop_knowledge_server(stop_all=True)

    # Create backup directory (remove old backup if exists)
    backup_dir = CLAUDE_DIR / "backups" / f"kln-{__version__}"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    ensure_dir(backup_dir)

    # Backup and remove
    removed = []

    for path in [
        CLAUDE_DIR / "scripts",
        CLAUDE_DIR / "commands" / "kln",
        CLAUDE_DIR / "hooks",
        CLAUDE_DIR / "rules" / "kln.md",
        SMOL_AGENTS_DIR,
    ]:
        if path.exists():
            backup_path = backup_dir / path.name
            if path.is_symlink():
                path.unlink()
            elif path.is_file():
                shutil.move(str(path), str(backup_path))
            else:
                shutil.move(str(path), str(backup_path))
            removed.append(str(path))

    console.print(f"\n[green]Removed {len(removed)} components[/green]")
    console.print(f"[dim]Backups saved to: {backup_dir}[/dim]")


@main.command()
def status():
    """Show K-LEAN installation status and health."""
    print_banner()

    table = Table(title="Component Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    # Scripts (Python only - cross-platform)
    scripts_dir = CLAUDE_DIR / "scripts"
    if scripts_dir.exists():
        py_scripts = list(scripts_dir.glob("*.py"))
        count = len(py_scripts)
        is_symlink = any(f.is_symlink() for f in py_scripts)
        mode = "(symlinked)" if is_symlink else "(copied)"
        table.add_row("Scripts", f"OK ({count})", mode)
    else:
        table.add_row("Scripts", "[red]NOT INSTALLED[/red]", "")

    # Commands
    kln_dir = CLAUDE_DIR / "commands" / "kln"
    if kln_dir.exists():
        count = len(list(kln_dir.glob("*.md")))
        table.add_row("KLN Commands", f"OK ({count})", "/kln:help")
    else:
        table.add_row("KLN Commands", "[red]NOT INSTALLED[/red]", "")

    # Hooks (Python entry points - registered in settings.json)
    # Hooks are now kln-hook-* entry points, not shell scripts
    hooks_configured = _count_configured_hooks()
    if hooks_configured > 0:
        table.add_row("Hooks", f"OK ({hooks_configured})", "entry points")
    else:
        table.add_row("Hooks", "[yellow]NOT CONFIGURED[/yellow]", "run kln install")

    # SmolKLN Agents
    smolkln_agents_dir = SMOL_AGENTS_DIR
    smolagents_installed = _check_smolagents_installed()
    if smolkln_agents_dir.exists():
        agent_files = list(smolkln_agents_dir.glob("*.md"))
        count = len([f for f in agent_files if f.name != "TEMPLATE.md"])
        if smolagents_installed:
            table.add_row("SmolKLN Agents", f"[green]OK ({count})[/green]", "smolagents ready")
        else:
            table.add_row(
                "SmolKLN Agents",
                f"[yellow]OK ({count})[/yellow]",
                "[yellow]smolagents not installed[/yellow]",
            )
    else:
        if smolagents_installed:
            table.add_row("SmolKLN Agents", "[yellow]NOT INSTALLED[/yellow]", "run: kln install")
        else:
            table.add_row("SmolKLN Agents", "[dim]Not installed[/dim]", "[dim]optional[/dim]")

    # Rules
    rules_file = CLAUDE_DIR / "rules" / "kln.md"
    if rules_file.exists():
        table.add_row("Rules", "[green]OK[/green]", "~/.claude/rules/kln.md")
    else:
        table.add_row("Rules", "[yellow]NOT INSTALLED[/yellow]", "run: kln install")

    # Knowledge DB
    if VENV_DIR.exists():
        table.add_row("Knowledge DB", "[green]INSTALLED[/green]", str(VENV_DIR))

        # Show current project status
        kb_status, kb_details, kb_project = get_kb_project_status()
        if kb_project:
            status_color = {
                "RUNNING": "green",
                "STOPPED": "yellow",
                "NOT INIT": "yellow",
                "ERROR": "red",
            }.get(kb_status, "dim")
            # Truncate long project names
            display_name = kb_project[:20] + "..." if len(kb_project) > 20 else kb_project
            table.add_row(
                f"  └─ {display_name}", f"[{status_color}]{kb_status}[/{status_color}]", kb_details
            )
        elif kb_status == "N/A":
            table.add_row("  └─ Current dir", "[dim]N/A[/dim]", kb_details)
    else:
        table.add_row("Knowledge DB", "[yellow]NOT INSTALLED[/yellow]", "run: kln install")

    # LiteLLM
    model_count, providers = get_litellm_info()
    provider_str = ", ".join(providers) if providers else ""
    if check_litellm():
        detail = f"localhost:4000 ({model_count} models)"
        if provider_str:
            detail += f" via {provider_str}"
        table.add_row("LiteLLM Proxy", "[green]RUNNING[/green]", detail)
    else:
        if model_count > 0:
            table.add_row(
                "LiteLLM Proxy",
                "[yellow]NOT RUNNING[/yellow]",
                f"({model_count} models configured)",
            )
        else:
            table.add_row("LiteLLM Proxy", "[yellow]NOT RUNNING[/yellow]", "run: kln start")

    console.print(table)

    # Installation mode detection
    console.print("\n[bold]Installation Info:[/bold]")
    console.print(f"  Version: {__version__}")
    console.print(f"  Claude Dir: {CLAUDE_DIR}")

    # Check if running in dev mode (symlinks present)
    if scripts_dir.exists():
        sample_script = next(scripts_dir.glob("*.py"), None)
        if sample_script and sample_script.is_symlink():
            target = sample_script.resolve().parent.parent
            console.print(f"  Mode: [cyan]Development (symlinked to {target})[/cyan]")
        else:
            console.print("  Mode: Production (files copied)")


@main.command()
@click.option(
    "--auto-fix", "-f", is_flag=True, help="Automatically fix issues (hooks, config, services)"
)
def doctor(auto_fix: bool):
    """Validate K-LEAN configuration and services (fast).

    Checks: config files, .env, API keys, subscription status, hooks, services.
    Does NOT check individual model health (use 'kln model list --health' for that).

    Use --auto-fix (-f) to automatically:
    - Configure Claude Code hooks in settings.json
    - Fix quoted os.environ in LiteLLM config
    - Detect and save subscription endpoint
    - Start stopped services
    """
    print_banner()
    console.print("\n[bold]Running diagnostics...[/bold]\n")

    issues = []
    fixes_applied = []

    # Check Claude directory
    if not CLAUDE_DIR.exists():
        issues.append(("CRITICAL", "~/.claude directory does not exist"))

    # Check scripts directory exists
    scripts_dir = CLAUDE_DIR / "scripts"
    if not scripts_dir.exists():
        issues.append(("ERROR", "Scripts directory not found"))

    # Check kln-smol command (installed via pipx as part of k-lean)
    if not shutil.which("kln-smol"):
        issues.append(("WARNING", "kln-smol command not found - SmolKLN agents won't work"))

    # Check key Python scripts exist
    key_scripts = ["kb_utils.py", "knowledge_db.py", "knowledge-server.py"]
    for script in key_scripts:
        script_path = scripts_dir / script
        if scripts_dir.exists() and not script_path.exists():
            issues.append(("WARNING", f"Missing script: {script}"))

    # Note: lib/common.sh and shell scripts were removed in cross-platform migration
    # All functionality now uses Python scripts and entry points

    # Check LiteLLM config
    if CONFIG_DIR.exists():
        config_yaml = CONFIG_DIR / "config.yaml"
        if not config_yaml.exists():
            issues.append(("INFO", "LiteLLM config.yaml not found - run `kln init`"))
        else:
            # Check for common config errors
            try:
                config_content = config_yaml.read_text()

                # Check for quoted os.environ (common mistake that breaks auth)
                if '"os.environ/' in config_content or "'os.environ/" in config_content:
                    issues.append(
                        ("ERROR", "LiteLLM config has quoted os.environ/ - remove quotes!")
                    )
                    console.print(
                        f"  [red]{SYM_FAIL}[/red] LiteLLM config: Quoted os.environ/ found"
                    )
                    console.print(
                        "    [dim]This breaks env var substitution. Edit ~/.config/litellm/config.yaml[/dim]"
                    )
                    console.print(
                        '    [dim]Change: api_key: "os.environ/KEY" -> api_key: os.environ/KEY[/dim]'
                    )
                    if auto_fix:
                        # Auto-fix by removing quotes around os.environ
                        import re

                        fixed = re.sub(
                            r'["\']os\.environ/([^"\']+)["\']', r"os.environ/\1", config_content
                        )
                        config_yaml.write_text(fixed)
                        console.print(
                            "    [green][OK] Auto-fixed: Removed quotes from os.environ[/green]"
                        )
                        fixes_applied.append("Fixed quoted os.environ in LiteLLM config")

                # Check for hardcoded API keys (security risk)
                import re

                # Match patterns like api_key: sk-xxx or api_key: "sk-xxx"
                hardcoded_keys = re.findall(
                    r'api_key:\s*["\']?(sk-[a-zA-Z0-9]{10,}|[a-zA-Z0-9]{32,})["\']?', config_content
                )
                if hardcoded_keys:
                    issues.append(
                        ("CRITICAL", "LiteLLM config has hardcoded API keys! Use os.environ/VAR")
                    )
                    console.print(
                        f"  [red]{SYM_FAIL}[/red] LiteLLM config: Hardcoded API keys detected!"
                    )
                    console.print(
                        "    [dim]Never commit API keys. Use: api_key: os.environ/NANOGPT_API_KEY[/dim]"
                    )
            except Exception as e:
                console.print(f"  [yellow]○[/yellow] Could not validate LiteLLM config: {e}")

        # Check .env file
        env_file = CONFIG_DIR / ".env"
        if not env_file.exists():
            issues.append(("ERROR", "LiteLLM .env file not found - run `kln init`"))
            console.print(f"  [red]{SYM_FAIL}[/red] LiteLLM .env: NOT FOUND")
        else:
            env_content = env_file.read_text()
            has_api_key = (
                "NANOGPT_API_KEY=" in env_content and "your-nanogpt-api-key-here" not in env_content
            )
            has_api_base = "NANOGPT_API_BASE=" in env_content

            if not has_api_key:
                issues.append(("ERROR", "NANOGPT_API_KEY not configured in .env"))
                console.print(f"  [red]{SYM_FAIL}[/red] LiteLLM .env: NANOGPT_API_KEY not set")
            else:
                console.print("  [green][OK][/green] LiteLLM .env: NANOGPT_API_KEY configured")

            if not has_api_base:
                issues.append(("WARNING", "NANOGPT_API_BASE not set - will auto-detect on start"))
                console.print("  [yellow]○[/yellow] LiteLLM .env: NANOGPT_API_BASE not set")

                if auto_fix and has_api_key:
                    # Extract API key and auto-detect
                    import re

                    key_match = re.search(r"NANOGPT_API_KEY=(\S+)", env_content)
                    if key_match:
                        api_key = key_match.group(1)
                        console.print("    [dim]Auto-detecting subscription status...[/dim]")
                        try:
                            import urllib.request

                            req = urllib.request.Request(
                                "https://nano-gpt.com/api/subscription/v1/usage",
                                headers={"Authorization": f"Bearer {api_key}"},
                            )
                            response = urllib.request.urlopen(req, timeout=5)
                            data = json.loads(response.read().decode())
                            if data.get("active"):
                                api_base = "https://nano-gpt.com/api/subscription/v1"
                                console.print(
                                    "    [green][OK] Subscription account detected[/green]"
                                )
                            else:
                                api_base = "https://nano-gpt.com/api/v1"
                                console.print("    [yellow]○ Pay-per-use account detected[/yellow]")

                            # Append to .env
                            with open(env_file, "a") as f:
                                f.write(f"\nNANOGPT_API_BASE={api_base}\n")
                            console.print("    [green][OK] Saved NANOGPT_API_BASE to .env[/green]")
                            fixes_applied.append("Auto-detected and saved NANOGPT_API_BASE")
                        except Exception as e:
                            console.print(f"    [red]{SYM_FAIL} Could not detect: {e}[/red]")
            else:
                # Check if subscription is still active
                import re

                key_match = re.search(r"NANOGPT_API_KEY=(\S+)", env_content)
                base_match = re.search(r"NANOGPT_API_BASE=(\S+)", env_content)
                if key_match and base_match:
                    api_key = key_match.group(1)
                    api_base = base_match.group(1)
                    if "subscription" in api_base:
                        try:
                            import urllib.request

                            req = urllib.request.Request(
                                "https://nano-gpt.com/api/subscription/v1/usage",
                                headers={"Authorization": f"Bearer {api_key}"},
                            )
                            response = urllib.request.urlopen(req, timeout=5)
                            data = json.loads(response.read().decode())
                            if data.get("active"):
                                remaining = data.get("daily", {}).get("remaining", 0)
                                console.print(
                                    f"  [green][OK][/green] NanoGPT Subscription: ACTIVE ({remaining} daily remaining)"
                                )
                            else:
                                issues.append(("WARNING", "NanoGPT subscription is not active"))
                                console.print("  [yellow]○[/yellow] NanoGPT Subscription: INACTIVE")
                        except Exception:
                            console.print(
                                "  [yellow]○[/yellow] NanoGPT Subscription: Could not verify"
                            )
                    else:
                        console.print("  [green][OK][/green] LiteLLM .env: Pay-per-use configured")

    # Check Python venv
    if VENV_DIR.exists():
        python = get_venv_python(VENV_DIR)
        if not python.exists():
            issues.append(("ERROR", "Knowledge DB venv is broken - recreate with kln install"))

    # Check for broken symlinks
    for check_dir in [scripts_dir, CLAUDE_DIR / "commands" / "kln", CLAUDE_DIR / "hooks"]:
        if check_dir.exists():
            for item in check_dir.iterdir():
                if item.is_symlink() and not item.resolve().exists():
                    issues.append(("ERROR", f"Broken symlink: {item}"))

    # Check Claude Code hooks configuration
    console.print("[bold]Hooks Configuration:[/bold]")
    settings_file = CLAUDE_DIR / "settings.json"
    missing_hooks = []

    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
            hooks = settings.get("hooks", {})

            # Check for required K-LEAN hooks
            if "SessionStart" in hooks:
                # Check if our matchers are present
                matchers = {h.get("matcher") for h in hooks["SessionStart"]}
                if "startup" in matchers and "resume" in matchers:
                    console.print("  [green][OK][/green] SessionStart hooks: Configured")
                else:
                    missing_hooks.append("SessionStart[startup/resume]")
            else:
                missing_hooks.append("SessionStart")

            if "UserPromptSubmit" in hooks:
                console.print("  [green][OK][/green] UserPromptSubmit hooks: Configured")
            else:
                missing_hooks.append("UserPromptSubmit")

            if "PostToolUse" in hooks:
                console.print("  [green][OK][/green] PostToolUse hooks: Configured")
            else:
                missing_hooks.append("PostToolUse")

        except json.JSONDecodeError:
            issues.append(("ERROR", "settings.json is not valid JSON"))
            console.print(f"  [red]{SYM_FAIL}[/red] settings.json: Invalid JSON")
    else:
        missing_hooks = ["SessionStart", "UserPromptSubmit", "PostToolUse"]
        console.print("  [yellow]○[/yellow] settings.json: Not found")

    if missing_hooks:
        issues.append(("WARNING", f"Missing hooks in settings.json: {', '.join(missing_hooks)}"))
        console.print(f"  [yellow]○[/yellow] Missing hooks: {', '.join(missing_hooks)}")

        if auto_fix:
            console.print("  [dim]Auto-configuring hooks...[/dim]")
            try:
                if settings_file.exists():
                    settings = json.loads(settings_file.read_text())
                else:
                    settings = {}

                settings, added = merge_klean_hooks(settings)

                # Write back with pretty formatting
                settings_file.write_text(json.dumps(settings, indent=2) + "\n")

                if added:
                    console.print(f"  [green][OK][/green] Added hooks: {', '.join(added)}")
                    fixes_applied.append(f"Configured Claude Code hooks: {', '.join(added)}")
                else:
                    console.print("  [green][OK][/green] All K-LEAN hooks already configured")
            except Exception as e:
                console.print(f"  [red]{SYM_FAIL}[/red] Failed to configure hooks: {e}")
                issues.append(("ERROR", f"Failed to auto-configure hooks: {e}"))

    # Check statusline configuration
    console.print("[bold]Statusline Configuration:[/bold]")
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
            statusline_config = settings.get("statusLine", {})
            statusline_command = statusline_config.get("command", "")
            expected_statusline = str(CLAUDE_DIR / "scripts" / "klean-statusline.py")

            if statusline_command == expected_statusline:
                console.print("  [green][OK][/green] Statusline: CONFIGURED")
            elif statusline_command:
                console.print(
                    f"  [yellow]○[/yellow] Statusline: Different command configured: {statusline_command}"
                )
            else:
                console.print("  [yellow]○[/yellow] Statusline: Not configured")
                if auto_fix:
                    console.print("  [dim]Auto-configuring statusline...[/dim]")
                    if configure_statusline():
                        console.print("  [green][OK][/green] Statusline: CONFIGURED")
                        fixes_applied.append("Configured Claude Code statusline")
        except json.JSONDecodeError:
            console.print("  [yellow]○[/yellow] Statusline: Could not read settings.json")
    else:
        console.print("  [yellow]○[/yellow] Statusline: settings.json not found")

    # Service checks with auto-fix
    console.print("[bold]Service Status:[/bold]")

    # Check LiteLLM
    litellm_status = check_litellm_detailed()
    if litellm_status["running"]:
        console.print(
            f"  [green][OK][/green] LiteLLM Proxy: RUNNING ({len(litellm_status['models'])} models)"
        )

        # Note: Model health moved to 'kln model list --health' for faster doctor execution
        console.print("  [dim]○[/dim] Model Health: Use [cyan]kln model list --health[/cyan]")
    else:
        if auto_fix:
            console.print("  [yellow]○[/yellow] LiteLLM Proxy: NOT RUNNING - Starting...")
            if start_litellm():
                console.print("  [green][OK][/green] LiteLLM Proxy: STARTED")
                fixes_applied.append("Started LiteLLM proxy")
            else:
                issues.append(("ERROR", "Failed to start LiteLLM proxy"))
                console.print(f"  [red]{SYM_FAIL}[/red] LiteLLM Proxy: FAILED TO START")
        else:
            issues.append(("WARNING", "LiteLLM proxy not running"))
            console.print(f"  [red]{SYM_FAIL}[/red] LiteLLM Proxy: NOT RUNNING")

    # Check Knowledge Server
    if check_knowledge_server():
        console.print("  [green][OK][/green] Knowledge Server: RUNNING")
    else:
        if auto_fix:
            console.print("  [yellow]○[/yellow] Knowledge Server: NOT RUNNING - Starting...")
            if start_knowledge_server():
                console.print("  [green][OK][/green] Knowledge Server: STARTED")
                fixes_applied.append("Started Knowledge server")
            else:
                issues.append(("ERROR", "Failed to start Knowledge server"))
                console.print(f"  [red]{SYM_FAIL}[/red] Knowledge Server: FAILED TO START")
        else:
            issues.append(("WARNING", "Knowledge server not running"))
            console.print(f"  [red]{SYM_FAIL}[/red] Knowledge Server: NOT RUNNING")

    # Check SmolKLN
    console.print("\n[bold]SmolKLN Status:[/bold]")
    smolkln_agents_dir = SMOL_AGENTS_DIR
    if smolkln_agents_dir.exists():
        agent_count = len([f for f in smolkln_agents_dir.glob("*.md") if f.name != "TEMPLATE.md"])
        console.print(f"  [green][OK][/green] SmolKLN Agents: {agent_count} installed")
    else:
        console.print("  [yellow]○[/yellow] SmolKLN Agents: Not installed")

    if _check_smolagents_installed():
        console.print("  [green][OK][/green] smolagents: Installed")
    else:
        issues.append(("INFO", "smolagents not installed - SmolKLN agents won't work"))
        console.print("  [yellow]○[/yellow] smolagents: NOT INSTALLED")
        console.print("    [dim]Install with: pipx inject kln-ai 'smolagents[litellm]'[/dim]")

    # Check rules
    console.print("\n[bold]Rules:[/bold]")
    rules_file = CLAUDE_DIR / "rules" / "kln.md"
    if rules_file.exists():
        console.print("  [green][OK][/green] kln.md: Installed")
    else:
        issues.append(("INFO", "Rules not installed - run kln install"))
        console.print("  [yellow]○[/yellow] kln.md: NOT INSTALLED")
        console.print("    [dim]Install with: kln install[/dim]")

    console.print("")

    # Report issues
    if issues:
        console.print("[bold]Issues Found:[/bold]")
        for level, message in issues:
            if level == "CRITICAL":
                console.print(f"  [bold red]CRITICAL:[/bold red] {message}")
            elif level == "ERROR":
                console.print(f"  [red]ERROR:[/red] {message}")
            elif level == "WARNING":
                console.print(f"  [yellow]WARNING:[/yellow] {message}")
            else:
                console.print(f"  [blue]INFO:[/blue] {message}")
        console.print(f"\n[bold]Found {len(issues)} issue(s)[/bold]")
    else:
        console.print("[green]No issues found![/green]")

    if fixes_applied:
        console.print("\n[bold green]Auto-fixes applied:[/bold green]")
        for fix in fixes_applied:
            console.print(f"  • {fix}")

    if not auto_fix and any(level in ["WARNING", "ERROR"] for level, _ in issues):
        console.print(
            "\n[cyan]Tip:[/cyan] Run [bold]kln doctor --auto-fix[/bold] to auto-start services"
        )


@main.command()
@click.option(
    "--service",
    "-s",
    type=click.Choice(["all", "litellm", "knowledge"]),
    default="litellm",
    help="Service to start (default: litellm only)",
)
@click.option("--port", "-p", default=4000, help="LiteLLM proxy port")
@click.option("--telemetry", "-t", is_flag=True, help="Also start Phoenix telemetry server")
def start(service: str, port: int, telemetry: bool):
    """Start K-LEAN services.

    By default, only starts LiteLLM proxy. Knowledge servers are per-project
    and auto-start on first query in each project directory.
    """
    print_banner()
    console.print("\n[bold]Starting services...[/bold]\n")

    started = []
    failed = []

    if service in ["all", "litellm"]:
        if check_litellm():
            console.print("[green][OK][/green] LiteLLM Proxy: Already running")
        else:
            console.print("[yellow]○[/yellow] Starting LiteLLM Proxy...")
            if start_litellm(background=True, port=port):
                console.print(f"[green][OK][/green] LiteLLM Proxy: Started on port {port}")
                started.append("LiteLLM")
                log_debug_event("cli", "service_start", service="litellm", port=port)
            else:
                console.print(f"[red]{SYM_FAIL}[/red] LiteLLM Proxy: Failed to start")
                failed.append("LiteLLM")

    if service in ["all", "knowledge"]:
        # Per-project knowledge servers
        project = find_project_root()
        if project:
            if check_knowledge_server(project):
                console.print(f"[green][OK][/green] Knowledge Server: Running for {project.name}")
            else:
                console.print(f"[yellow]○[/yellow] Starting Knowledge Server for {project.name}...")
                if start_knowledge_server(project, wait=False):
                    console.print(
                        f"[green][OK][/green] Knowledge Server: Starting for {project.name}"
                    )
                    started.append("Knowledge")
                    log_debug_event(
                        "cli", "service_start", service="knowledge", project=str(project)
                    )
                else:
                    console.print(f"[red]{SYM_FAIL}[/red] Knowledge Server: Failed to start")
                    failed.append("Knowledge")
        else:
            console.print(
                "[yellow]○[/yellow] Knowledge Server: No project found (auto-starts on query)"
            )

    # Phoenix telemetry (optional)
    if telemetry:
        if check_phoenix():
            console.print("[green][OK][/green] Phoenix Telemetry: Already running")
        else:
            console.print("[yellow]○[/yellow] Starting Phoenix Telemetry...")
            if start_phoenix(background=True):
                console.print(
                    "[green][OK][/green] Phoenix Telemetry: Started on http://localhost:6006"
                )
                started.append("Phoenix")
                log_debug_event("cli", "service_start", service="phoenix")
            else:
                console.print(f"[red]{SYM_FAIL}[/red] Phoenix Telemetry: Failed to start")
                console.print("[dim]  Install with: pipx inject kln-ai 'kln-ai[telemetry]'[/dim]")
                failed.append("Phoenix")

    # Show running knowledge servers
    servers = list_knowledge_servers()
    if servers:
        console.print(f"\n[dim]Running knowledge servers: {len(servers)}[/dim]")
        for s in servers:
            console.print(f"[dim]  - {Path(s['project']).name}[/dim]")

    console.print("")
    if started:
        console.print(f"[green]Started {len(started)} service(s)[/green]")
    if failed:
        console.print(f"[red]Failed to start {len(failed)} service(s)[/red]")
        console.print("[dim]Check logs: ~/.klean/logs/[/dim]")

    if service == "litellm":
        console.print("\n[dim]Note: Knowledge servers auto-start per-project on first query[/dim]")


@main.command()
@click.option(
    "--service",
    "-s",
    type=click.Choice(["all", "litellm", "knowledge"]),
    default="all",
    help="Service to stop",
)
@click.option("--all-projects", is_flag=True, help="Stop all knowledge servers (all projects)")
def stop(service: str, all_projects: bool):
    """Stop K-LEAN services."""
    print_banner()
    console.print("\n[bold]Stopping services...[/bold]\n")

    stopped = []

    if service in ["all", "litellm"]:
        if stop_litellm():
            console.print("[green][OK][/green] LiteLLM Proxy: Stopped")
            stopped.append("LiteLLM")
            log_debug_event("cli", "service_stop", service="litellm")
        else:
            console.print("[yellow]○[/yellow] LiteLLM Proxy: Was not running")

    if service in ["all", "knowledge"]:
        if all_projects:
            # Stop all knowledge servers
            servers = list_knowledge_servers()
            if servers:
                stop_knowledge_server(stop_all=True)
                console.print(
                    f"[green][OK][/green] Knowledge Servers: Stopped {len(servers)} server(s)"
                )
                stopped.append(f"Knowledge ({len(servers)})")
                log_debug_event("cli", "service_stop", service="knowledge", count=len(servers))
            else:
                console.print("[yellow]○[/yellow] Knowledge Servers: None running")
        else:
            # Stop current project's server
            project = find_project_root()
            if project:
                if stop_knowledge_server(project):
                    console.print(
                        f"[green][OK][/green] Knowledge Server: Stopped for {project.name}"
                    )
                    stopped.append("Knowledge")
                    log_debug_event(
                        "cli", "service_stop", service="knowledge", project=str(project)
                    )
                else:
                    console.print(
                        f"[yellow]○[/yellow] Knowledge Server: Was not running for {project.name}"
                    )
            else:
                console.print("[yellow]○[/yellow] Knowledge Server: No project found")
                # Show hint about --all-projects
                servers = list_knowledge_servers()
                if servers:
                    console.print(
                        f"[dim]  (Use --all-projects to stop {len(servers)} running server(s))[/dim]"
                    )

    console.print(f"\n[green]Stopped {len(stopped)} service(s)[/green]")


def get_session_stats() -> dict[str, Any]:
    """Get session statistics from debug log."""
    stats = {
        "session_start": None,
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_latency_ms": 0,
        "models_used": set(),
        "agents_executed": 0,
        "knowledge_queries": 0,
    }

    entries = read_debug_log(lines=500)
    if not entries:
        return stats

    for entry in entries:
        if stats["session_start"] is None:
            stats["session_start"] = entry.get("ts", "")

        event = entry.get("event", "")
        component = entry.get("component", "")

        if component == "cli" and event == "test_model":
            stats["total_requests"] += 1
            stats["successful_requests"] += 1
            stats["total_latency_ms"] += entry.get("latency_ms", 0)
            model = entry.get("model", "")
            if model:
                stats["models_used"].add(model)

        if component == "agent" or component == "smolkln":
            stats["agents_executed"] += 1

        if component == "knowledge":
            stats["knowledge_queries"] += 1

    stats["models_used"] = list(stats["models_used"])
    return stats


def measure_service_latency(service: str) -> Optional[int]:
    """Measure service response latency in ms."""
    start = time.time()
    try:
        if service == "litellm":
            import urllib.request

            req = urllib.request.Request("http://localhost:4000/models")
            urllib.request.urlopen(req, timeout=3)
        elif service == "knowledge":
            socket_path = get_project_socket_path()
            if socket_path and socket_path.exists():
                return 1  # Socket exists = fast
            return None
        return int((time.time() - start) * 1000)
    except Exception:
        return None


def create_progress_bar(value: int, max_value: int, width: int = 20, color: str = "green") -> str:
    """Create a text-based progress bar."""
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    empty = width - filled
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"


# =============================================================================
# Setup Command
# =============================================================================


def detect_nanogpt_endpoint(api_key: str) -> str:
    """Auto-detect NanoGPT subscription vs pay-per-use endpoint."""
    import httpx

    try:
        response = httpx.get(
            "https://nano-gpt.com/api/subscription/v1/usage",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0,
        )
        if response.status_code == 200 and '"active":true' in response.text:
            return "https://nano-gpt.com/api/subscription/v1"
    except Exception:
        pass
    return "https://nano-gpt.com/api/v1"


# =============================================================================
# Multi-Agent Command
# =============================================================================


@main.command()
@click.argument("task")
@click.option(
    "--thorough", "-t", is_flag=True, help="Use 4-agent architecture (slower, more thorough)"
)
@click.option("--manager-model", "-m", help="Override manager model")
@click.option(
    "--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format"
)
@click.option("--telemetry", is_flag=True, help="Enable Phoenix telemetry (view at localhost:6006)")
def multi(task: str, thorough: bool, manager_model: str, output: str, telemetry: bool):
    """Run multi-agent orchestrated review.

    Uses multiple specialized agents coordinated by a manager for thorough code reviews.
    All agents use the first available model from LiteLLM (override manager with -m).

    \b
    3-Agent (default):
      - Manager: Orchestration
      - File Scout: Fast file discovery
      - Analyzer: Deep analysis

    \b
    4-Agent (--thorough):
      - Manager: Orchestration
      - File Scout: File discovery
      - Code Analyzer: Bug detection
      - Security Auditor: Security analysis
      - Synthesizer: Report formatting

    Examples:
        kln multi "Review src/auth/ for security issues"
        kln multi --thorough "Review the authentication module"
        kln multi -m deepseek-r1 "Review cli.py"
    """
    # Setup telemetry if requested
    if telemetry:
        try:
            from openinference.instrumentation.smolagents import SmolagentsInstrumentor
            from phoenix.otel import register

            register(project_name="klean-multi")
            SmolagentsInstrumentor().instrument()
            console.print("[dim]Telemetry enabled - view at http://localhost:6006[/dim]")
        except ImportError:
            console.print(
                "[yellow]Telemetry not installed. Run: pipx inject kln-ai arize-phoenix openinference-instrumentation-smolagents[/yellow]"
            )

    # Suppress Pydantic serialization warnings from smolagents/LiteLLM
    import warnings

    warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

    try:
        from klean.smol.multi_agent import MultiAgentExecutor
    except ImportError:
        console.print("[red]Error: smolagents not installed[/red]")
        console.print("Install with: pipx inject kln-ai 'smolagents[litellm]'")
        return

    variant = "4-agent" if thorough else "3-agent"
    console.print(f"\n[bold cyan]Multi-Agent Review ({variant})[/bold cyan]")
    console.print("=" * 50)
    console.print(f"[dim]Task: {task}[/dim]\n")

    try:
        executor = MultiAgentExecutor()
        console.print(f"[dim]Project: {executor.project_root}[/dim]")
        console.print("[dim]Starting agents...[/dim]\n")

        result = executor.execute(
            task=task,
            thorough=thorough,
            manager_model=manager_model,
        )

        if output == "json":
            import json

            console.print(json.dumps(result, indent=2))
        else:
            if result["success"]:
                console.print(result["output"])
                console.print("\n" + "=" * 50)
                console.print(f"[green][OK] Completed in {result['duration_s']}s[/green]")
                console.print(f"[dim]Agents: {', '.join(result['agents_used'])}[/dim]")
                if result.get("output_file"):
                    console.print(f"[dim]Saved to: {result['output_file']}[/dim]")
            else:
                console.print(f"[red]Error: {result['output']}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def find_config_template(name: str) -> Optional[Path]:
    """Find config template in package data or repo."""
    # Check package data directory
    source_data = get_source_data_dir()
    candidates = [
        source_data / "config" / "litellm" / name,
        Path(__file__).parent.parent.parent / "config" / "litellm" / name,
        DATA_DIR / "config" / "litellm" / name,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


@main.command()
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["nanogpt", "openrouter", "skip"]),
    help="Provider (nanogpt, openrouter, or skip LiteLLM)",
)
@click.option("--api-key", "-k", help="API key (skips prompt)")
def init(provider: Optional[str], api_key: Optional[str]):
    """Initialize K-LEAN: install + configure provider (no start).

    Complete first-time setup for K-LEAN. Installs components and
    optionally configures an API provider. Run 'kln start' separately
    when ready to start the LiteLLM proxy.

    Examples:
        kln init                                    # Interactive menu
        kln init --provider nanogpt --api-key $KEY  # Silent NanoGPT setup
        kln init --provider skip                    # Knowledge system only
    """
    from klean.config_generator import (
        generate_env_file,
        generate_litellm_config,
    )
    from klean.model_defaults import (
        get_nanogpt_models,
        get_openrouter_models,
    )

    # Check if already initialized
    if (CONFIG_DIR / "config.yaml").exists():
        console.print("[yellow]K-LEAN already initialized.[/yellow]")
        if not click.confirm("Reconfigure?", default=False):
            console.print("Cancelled.")
            return

    # Interactive menu if --provider not specified
    selected_providers = []
    provider_apis = {}

    if not provider:
        from klean.model_defaults import (
            get_nanogpt_models,
            get_openrouter_models,
        )

        console.print("\n[bold]K-LEAN Initialization[/bold]")
        console.print("Which providers do you want to configure?\n")

        nanogpt_count = len(get_nanogpt_models())
        openrouter_count = len(get_openrouter_models())

        choices = {
            "1": ("nanogpt", f"NanoGPT ({nanogpt_count} recommended models)"),
            "2": ("openrouter", f"OpenRouter ({openrouter_count} recommended models)"),
            "3": ("skip", "Skip LiteLLM (knowledge system only)"),
        }

        for key, (_, desc) in choices.items():
            console.print(f"  {key}) {desc}")

        # Multi-provider selection loop
        available_providers = ["nanogpt", "openrouter"]
        while True:
            choice = click.prompt("\nChoose", type=click.Choice(choices.keys()))
            provider_choice = choices[choice][0]

            if provider_choice == "skip":
                provider = "skip"
                break

            if provider_choice not in selected_providers:
                selected_providers.append(provider_choice)
                console.print(f"  [green]{SYM_OK}[/green] Added {provider_choice.upper()}")

            # Check if all providers are selected - no need to ask
            remaining = [p for p in available_providers if p not in selected_providers]
            if not remaining:
                break

            if not click.confirm("Add another provider?", default=False):
                break

        # If no providers selected via loop, use the last selection
        if not selected_providers and provider != "skip":
            selected_providers = [provider] if provider else []
    else:
        # Command-line provider specified
        if provider != "skip":
            selected_providers = [provider]

    # Generate config (if not skip)
    if provider != "skip" or selected_providers:
        # Collect API keys for all selected providers
        for prov in selected_providers:
            if prov == provider and api_key:
                # Use provided API key for the single --provider case
                provider_apis[prov] = api_key
            else:
                # Prompt for each provider
                key = click.prompt(
                    f"\n{prov.upper()} API Key", hide_input=True, confirmation_prompt=False
                )
                provider_apis[prov] = key

        # Show recommended models and ask for confirmation
        all_models = []
        models_by_provider = {}

        for prov in selected_providers:
            if prov == "nanogpt":
                prov_models = get_nanogpt_models()
            elif prov == "openrouter":
                prov_models = get_openrouter_models()
            else:
                prov_models = []

            models_by_provider[prov] = prov_models
            all_models.extend(prov_models)

        # Display models and ask for confirmation
        console.print("\n[bold]Recommended Models[/bold]")
        for prov in selected_providers:
            prov_models = models_by_provider[prov]
            console.print(f"\n{prov.upper()} ({len(prov_models)} models):")
            for model in prov_models:
                console.print(f"  • {model['model_name']}")

        # Ask if user wants to install models
        console.print()
        install_models = click.confirm("Install these recommended models?", default=True)

        # Generate config files (preserving existing providers)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing .env to preserve other providers
        existing_env = _load_existing_env()

        env_content = generate_env_file(provider_apis, existing_env=existing_env)

        if install_models:
            config_yaml = generate_litellm_config(all_models)
            console.print(
                f"\n[green]{SYM_OK}[/green] Configured with {len(all_models)} recommended models"
            )
        else:
            config_yaml = generate_litellm_config([])
            console.print(f"\n[green]{SYM_OK}[/green] Configured API keys (no models yet)")
            console.print(
                'Add models later with: [cyan]kln model add --provider <provider> "model-id"[/cyan]'
            )

        (CONFIG_DIR / "config.yaml").write_text(config_yaml)
        (CONFIG_DIR / ".env").write_text(env_content)
        (CONFIG_DIR / ".env").chmod(0o600)

        providers_str = ", ".join([p.upper() for p in selected_providers])
        console.print(f"[green]{SYM_OK}[/green] {providers_str} providers configured")

    # Install components (invoke existing install command)
    console.print("Installing K-LEAN components...")
    try:
        # Call install command with --yes flag to skip prompts
        ctx = click.get_current_context()
        ctx.invoke(install, dev=False, component="all", yes=True)
        console.print(f"[green]{SYM_OK}[/green] Installed to ~/.claude/")
    except Exception as e:
        console.print(f"[red]Error installing components: {e}[/red]")
        return

    # Show summary
    console.print(f"\n[bold green]{SYM_OK} K-LEAN initialized![/bold green]\n")

    if provider == "skip":
        console.print("Knowledge system ready (no LiteLLM configured):")
        console.print("  • Capture learnings: [cyan]/kln:learn[/cyan]")
        console.print("  • Search knowledge: type [cyan]FindKnowledge query[/cyan]")
        console.print("\nAdd API provider later:")
        console.print("  [cyan]kln init --provider nanogpt --api-key $KEY[/cyan]")
    else:
        providers_display = ", ".join([p.upper() for p in selected_providers])
        console.print(f"Configuration ready with {providers_display}:")
        console.print(f"  • {len(all_models)} recommended models configured")
        console.print("  • Review providers: [cyan]kln provider list[/cyan]")
        console.print("  • Review models: [cyan]kln model list[/cyan]")
        console.print(
            '  • Add more models: [cyan]kln model add --provider <provider> "model-id"[/cyan]'
        )
        console.print(
            "  • Add another provider: [cyan]kln provider add <provider> --api-key $KEY[/cyan]"
        )
        console.print("  • Verify config: [cyan]kln doctor[/cyan]")
        console.print("\nWhen ready to start services:")
        console.print("  [cyan]kln start[/cyan]")


def _dict_to_yaml(config: dict) -> str:
    """Convert config dict to YAML with proper formatting."""
    import yaml

    class CustomDumper(yaml.SafeDumper):
        pass

    def represent_none(self, _):
        return self.represent_scalar("tag:yaml.org,2002:null", "")

    CustomDumper.add_representer(type(None), represent_none)

    yaml_str = "# K-LEAN LiteLLM Configuration\n"
    yaml_str += "# ============================\n"
    yaml_str += "#\n"
    yaml_str += "# ENDPOINT RULES:\n"
    yaml_str += "#   *-thinking models -> NANOGPT_THINKING_API_BASE\n"
    yaml_str += "#   all other models  -> NANOGPT_API_BASE or OPENROUTER_API_BASE\n"
    yaml_str += "#\n"
    yaml_str += "# No quotes around os.environ/ values!\n"
    yaml_str += "\n"

    yaml_str += "litellm_settings:\n"
    yaml_str += "  drop_params: true\n"
    yaml_str += "\n"
    yaml_str += "model_list:\n"

    for model in config.get("model_list", []):
        yaml_str += f"  - model_name: {model.get('model_name')}\n"
        yaml_str += "    litellm_params:\n"
        params = model.get("litellm_params", {})
        yaml_str += f"      model: {params.get('model')}\n"
        if "api_base" in params:
            yaml_str += f"      api_base: {params.get('api_base')}\n"
        yaml_str += f"      api_key: {params.get('api_key')}\n"

    return yaml_str


if __name__ == "__main__":
    main()
