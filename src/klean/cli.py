"""
K-LEAN CLI - Command line interface for K-LEAN installation and management.

Usage:
    k-lean install [--dev] [--component COMPONENT]
    k-lean uninstall
    k-lean status
    k-lean doctor [--auto-fix]
    k-lean start [--service SERVICE]
    k-lean stop [--service SERVICE]
    k-lean debug [--follow] [--filter COMPONENT]
    k-lean version
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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

console = Console()


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
        return ("N/A", "run k-lean install", "")

    kb_utils_path = scripts_dir / "kb_utils.py"
    if not kb_utils_path.exists():
        return ("N/A", "kb_utils missing", "")

    try:
        # Lazy import with path setup
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        from kb_utils import (
            find_project_root,
            get_socket_path,
            is_kb_initialized,
            is_server_running,
        )

        project = find_project_root(Path.cwd())
        if not project:
            return ("N/A", "not in a project", "")

        project_name = project.name

        if is_server_running(project):
            # Query server for entry count
            entries = _query_kb_entries(get_socket_path(project))
            return ("RUNNING", f"({entries} entries)", project_name)

        if is_kb_initialized(project):
            return ("STOPPED", "run InitKB", project_name)

        return ("NOT INIT", "run InitKB", project_name)

    except ImportError as e:
        return ("ERROR", f"import: {str(e)[:20]}", "")
    except Exception as e:
        return ("ERROR", str(e)[:25], "")


def _query_kb_entries(socket_path: str) -> str:
    """Query KB server for entry count via status command.

    Args:
        socket_path: Unix socket path

    Returns:
        Entry count as string, or "?" on failure
    """
    import socket

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(socket_path)
        sock.sendall(b'{"cmd":"status"}')
        response = sock.recv(4096).decode()
        sock.close()

        data = json.loads(response)
        return str(data.get("entries", "?"))
    except Exception:
        return "?"


def print_banner():
    """Print the K-LEAN banner."""
    console.print(Panel.fit(
        f"[bold cyan]K-LEAN Companion v{__version__}[/bold cyan]\n"
        "[dim]Multi-Model Code Review & Knowledge Capture System[/dim]",
        border_style="cyan"
    ))


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
                if dst_subdir.exists():
                    shutil.rmtree(dst_subdir)
                shutil.copytree(item, dst_subdir)
            count += 1

    return count


def make_executable(path: Path) -> None:
    """Make shell scripts executable."""
    for script in path.glob("*.sh"):
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


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


def get_project_socket_path(project_path: Path = None) -> Path:
    """Get per-project socket path using same hash as knowledge-server.py."""
    import hashlib
    if project_path is None:
        project_path = find_project_root()
    if not project_path:
        return None
    path_str = str(project_path.resolve())
    hash_val = hashlib.md5(path_str.encode()).hexdigest()[:8]
    return Path(f"/tmp/kb-{hash_val}.sock")


def find_project_root(start_path: Path = None) -> Path:
    """Find project root by walking up looking for .knowledge-db."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if (current / ".knowledge-db").exists():
            return current
        current = current.parent
    return None


def check_knowledge_server(project_path: Path = None) -> bool:
    """Check if knowledge server is running for a project via socket."""
    import socket as sock

    socket_path = get_project_socket_path(project_path)
    if not socket_path or not socket_path.exists():
        return False

    # Try to actually connect to verify it's alive
    try:
        client = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
        client.settimeout(1)
        client.connect(str(socket_path))
        client.close()
        return True
    except OSError:
        # Socket exists but no server - clean up stale socket
        try:
            socket_path.unlink()
        except Exception:
            pass
        return False


def list_knowledge_servers() -> list:
    """List all running knowledge servers."""
    import json
    import socket as sock

    servers = []
    for socket_file in Path("/tmp").glob("kb-*.sock"):
        pid_file = socket_file.with_suffix(".pid")
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                # Check if process is running
                os.kill(pid, 0)
                # Get project info via socket
                client = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
                client.settimeout(2)
                client.connect(str(socket_file))
                client.sendall(b'{"cmd":"status"}')
                response = json.loads(client.recv(65536).decode())
                client.close()
                servers.append({
                    "socket": str(socket_file),
                    "pid": pid,
                    "project": response.get("project", "unknown"),
                    "entries": response.get("entries", 0),
                    "idle": response.get("idle_seconds", 0)
                })
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
                cmd,
                stdout=open(log_file, "w"),
                stderr=subprocess.STDOUT,
                start_new_session=True
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


def start_knowledge_server(project_path: Path = None, wait: bool = True) -> bool:
    """Start knowledge server for a project in background if not running.

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

    try:
        knowledge_script = CLAUDE_DIR / "scripts" / "knowledge-server.py"
        if not knowledge_script.exists():
            return False

        # Use the venv python if available
        venv_python = VENV_DIR / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else sys.executable

        # Start server in background with log capture
        ensure_klean_dirs()
        log_file = LOGS_DIR / "knowledge-server.log"

        with open(log_file, 'a') as log:
            process = subprocess.Popen(
                [python_cmd, str(knowledge_script), "start", str(project_path)],
                stdout=log,
                stderr=log,
                cwd=str(project_path),
                start_new_session=True  # Detach from parent process
            )

        if not wait:
            return True  # Started, but not confirmed

        # Wait for socket (up to 60s for index loading)
        socket_path = get_project_socket_path(project_path)
        for _ in range(600):  # 60 seconds
            time.sleep(0.1)
            if socket_path and socket_path.exists():
                if check_knowledge_server(project_path):
                    return True

        # Process still running but socket not ready = OK, initializing
        if process.poll() is None:
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


def check_litellm_detailed() -> Dict[str, Any]:
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
KLEAN_HOOKS_CONFIG = {
    "SessionStart": [
        {
            "matcher": "startup",
            "hooks": [{"type": "command", "command": "~/.claude/hooks/session-start.sh", "timeout": 5}]
        },
        {
            "matcher": "resume",
            "hooks": [{"type": "command", "command": "~/.claude/hooks/session-start.sh", "timeout": 5}]
        }
    ],
    "UserPromptSubmit": [
        {
            "hooks": [{"type": "command", "command": "~/.claude/hooks/user-prompt-handler.sh", "timeout": 30}]
        }
    ],
    "PostToolUse": [
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "~/.claude/hooks/post-bash-handler.sh", "timeout": 15}]
        },
        {
            "matcher": "WebFetch|WebSearch",
            "hooks": [{"type": "command", "command": "~/.claude/hooks/post-web-handler.sh", "timeout": 10}]
        },
        {
            "matcher": "mcp__tavily__.*",
            "hooks": [{"type": "command", "command": "~/.claude/hooks/post-web-handler.sh", "timeout": 10}]
        }
    ]
}


def merge_klean_hooks(existing_settings: dict) -> tuple[dict, list[str]]:
    """Merge K-LEAN hooks into existing settings.json, preserving user hooks.

    Returns:
        tuple: (updated_settings, list of hooks added)
    """
    added = []

    if "hooks" not in existing_settings:
        existing_settings["hooks"] = {}

    hooks = existing_settings["hooks"]

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
                    klean_matcher = klean_hook["hooks"][0].get("command", "") if klean_hook["hooks"] else ""

                if klean_matcher not in existing_matchers:
                    hooks[hook_type].append(klean_hook)
                    added.append(f"{hook_type}[{klean_matcher or 'default'}]")

    return existing_settings, added


def start_litellm(background: bool = True, port: int = 4000) -> bool:
    """Start LiteLLM proxy server."""
    ensure_klean_dirs()

    # Check if already running
    if check_litellm():
        return True

    # Find start script (consolidated to single script)
    start_script = CLAUDE_DIR / "scripts" / "start-litellm.sh"

    if not start_script.exists():
        console.print("[red]Error: start-litellm.sh not found[/red]")
        console.print("   Run: k-lean install")
        return False

    # Check .env exists
    env_file = CONFIG_DIR / ".env"
    if not env_file.exists():
        console.print("[red]Error: ~/.config/litellm/.env not found[/red]")
        console.print("   Copy from .env.example and add your API key")
        return False

    # Check for litellm binary
    if not shutil.which("litellm"):
        console.print("[red]Error: litellm not installed. Run: pip install litellm[/red]")
        return False

    log_file = LOGS_DIR / "litellm.log"
    pid_file = get_litellm_pid_file()

    try:
        if background:
            # Start in background with nohup
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    ["bash", str(start_script), str(port)],
                    stdout=log,
                    stderr=log,
                    start_new_session=True
                )
                pid_file.write_text(str(process.pid))

            # Wait for proxy to be ready
            # LiteLLM can take 15-30s on cold start, but we don't block forever
            # Quick check (5s) to catch immediate failures, then trust it's starting
            for i in range(50):  # 5 seconds quick check
                time.sleep(0.1)
                if check_litellm():
                    return True

            # Process is running but not yet responding - that's OK
            # LiteLLM takes time to initialize, return success
            if process.poll() is None:  # Process still running
                return True  # Started, will be ready soon

            return False  # Process exited = real failure
        else:
            # Run in foreground
            subprocess.run(["bash", str(start_script), str(port)])
            return True
    except Exception as e:
        console.print(f"[red]Error starting LiteLLM: {e}[/red]")
        return False


def stop_litellm() -> bool:
    """Stop LiteLLM proxy server."""
    pid_file = get_litellm_pid_file()

    # Try to kill by PID file
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            pid_file.unlink()
            time.sleep(0.5)
            return True
        except (ProcessLookupError, ValueError):
            pid_file.unlink()

    # Try to find and kill litellm process
    try:
        result = subprocess.run(
            ["pkill", "-f", "litellm.*--port"],
            capture_output=True
        )
        return result.returncode == 0
    except Exception:
        return False


def stop_knowledge_server(project_path: Path = None, stop_all: bool = False) -> bool:
    """Stop knowledge server(s).

    Args:
        project_path: Stop server for specific project (auto-detect from CWD if None)
        stop_all: If True, stop ALL running knowledge servers
    """
    knowledge_script = CLAUDE_DIR / "scripts" / "knowledge-server.py"
    if not knowledge_script.exists():
        return False

    venv_python = VENV_DIR / "bin" / "python"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    if stop_all:
        # Stop all running servers
        servers = list_knowledge_servers()
        if not servers:
            return True  # Nothing to stop

        for server in servers:
            try:
                os.kill(server["pid"], signal.SIGTERM)
            except Exception:
                pass

        # Clean up all sockets
        for socket_file in Path("/tmp").glob("kb-*.sock"):
            try:
                socket_file.unlink()
            except Exception:
                pass
        for pid_file in Path("/tmp").glob("kb-*.pid"):
            try:
                pid_file.unlink()
            except Exception:
                pass
        return True

    # Stop server for specific project
    if project_path is None:
        project_path = find_project_root()

    if not project_path:
        return False  # No project found

    socket_path = get_project_socket_path(project_path)
    if not socket_path or not socket_path.exists():
        return True  # Not running

    try:
        subprocess.run(
            [python_cmd, str(knowledge_script), "stop", str(project_path)],
            capture_output=True,
            timeout=5
        )
        time.sleep(0.5)
    except Exception:
        pass

    # Verify stopped
    return not check_knowledge_server(project_path)


def log_debug_event(component: str, event: str, **kwargs) -> None:
    """Log a debug event to the unified log file."""
    ensure_klean_dirs()
    log_file = LOGS_DIR / "debug.log"

    entry = {
        "ts": datetime.now().isoformat(),
        "component": component,
        "event": event,
        **kwargs
    }

    try:
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silent fail for logging


def read_debug_log(lines: int = 50, component: Optional[str] = None) -> List[Dict]:
    """Read recent entries from debug log."""
    log_file = LOGS_DIR / "debug.log"
    if not log_file.exists():
        return []

    entries = []
    try:
        with open(log_file) as f:
            all_lines = f.readlines()
            for line in all_lines[-lines * 2:]:  # Read extra to filter
                try:
                    entry = json.loads(line.strip())
                    if component is None or entry.get("component") == component:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return entries[-lines:]


def discover_models() -> List[str]:
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


def query_phoenix_traces(limit: int = 20) -> Optional[Dict]:
    """Query Phoenix telemetry for recent LLM traces.

    Returns aggregated stats and recent spans from all projects.
    """
    if not check_phoenix():
        return None

    query = '''{
        projects {
            edges {
                node {
                    name
                    traceCount
                    spans(first: %d) {
                        edges {
                            node {
                                name
                                latencyMs
                                startTime
                                statusCode
                                attributes
                            }
                        }
                    }
                }
            }
        }
    }''' % limit

    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:6006/graphql",
            data=json.dumps({"query": query}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
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
            "projects": {}
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
                    result["llm_calls"].append({
                        "time": start_time,
                        "model": model_name.split("/")[-1] if "/" in model_name else model_name,
                        "latency_ms": int(latency),
                        "tokens_in": prompt_tokens,
                        "tokens_out": completion_tokens,
                        "status": status,
                        "project": project_name
                    })

        # Calculate averages
        if all_latencies:
            result["avg_latency_ms"] = int(sum(all_latencies) / len(all_latencies))

        # Sort LLM calls by time (most recent first)
        result["llm_calls"].sort(key=lambda x: x.get("time", ""), reverse=True)

        return result

    except Exception:
        return None


def get_model_health() -> Dict[str, str]:
    """Check health of each model."""
    health = {}
    health_script = CLAUDE_DIR / "scripts" / "health-check-model.sh"

    models = discover_models()
    for model in models:
        try:
            if health_script.exists():
                result = subprocess.run(
                    ["bash", str(health_script), model],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                health[model] = "OK" if result.returncode == 0 else "FAIL"
            else:
                health[model] = "UNKNOWN"
        except subprocess.TimeoutExpired:
            health[model] = "TIMEOUT"
        except Exception:
            health[model] = "ERROR"

    return health


@click.group()
@click.version_option(version=__version__, prog_name="k-lean")
def main():
    """K-LEAN: Multi-model code review and knowledge capture system for Claude Code."""
    # Services are started explicitly via `k-lean start`
    # Optional autostart can be configured in ~/.bashrc
    pass


@main.command()
@click.option("--dev", is_flag=True, help="Development mode: use symlinks instead of copies")
@click.option("--component", "-c",
              type=click.Choice(["all", "scripts", "commands", "hooks", "smolkln", "config", "core", "knowledge"]),
              default="all", help="Component to install")
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
    source_hooks = source_base / "hooks"
    source_config = source_base / "config"
    source_lib = source_base / "lib"
    source_core = source_base / "core"

    console.print(f"[dim]Source: {source_scripts.parent}[/dim]\n")

    if not yes and not click.confirm("Proceed with installation?"):
        console.print("[yellow]Installation cancelled[/yellow]")
        return

    installed = {}

    # Install scripts
    if component in ["all", "scripts"]:
        console.print("[bold]Installing scripts...[/bold]")
        scripts_dst = CLAUDE_DIR / "scripts"

        # Also copy lib/ for common.sh dependency
        if source_lib.exists():
            lib_dst = CLAUDE_DIR / "lib"
            count = copy_files(source_lib, lib_dst, "*.sh", symlink=dev)
            make_executable(lib_dst)

        if source_scripts.exists():
            count = copy_files(source_scripts, scripts_dst, "*.sh", symlink=dev)
            count += copy_files(source_scripts, scripts_dst, "*.py", symlink=dev)
            make_executable(scripts_dst)
            installed["scripts"] = count
            console.print(f"  [green]Installed {count} scripts[/green]")
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

    # Install hooks
    if component in ["all", "hooks"]:
        console.print("[bold]Installing hooks...[/bold]")
        hooks_dst = CLAUDE_DIR / "hooks"
        if source_hooks.exists():
            count = copy_files(source_hooks, hooks_dst, "*.sh", symlink=dev)
            make_executable(hooks_dst)
            installed["hooks"] = count
            console.print(f"  [green]Installed {count} hooks[/green]")
        else:
            console.print("  [yellow]Hooks source not found[/yellow]")

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

        # Note: smol-kln command is installed via pipx as part of k-lean package

    # Install config
    if component in ["all", "config"]:
        console.print("[bold]Installing configuration...[/bold]")

        # NOTE: We deliberately do NOT touch CLAUDE.md
        # K-LEAN uses slash commands (/kln:*) which are auto-discovered
        # This preserves user's existing CLAUDE.md configuration
        console.print("  [dim]CLAUDE.md: skipped (using pure plugin approach)[/dim]")

        # LiteLLM config
        litellm_src = source_config / "litellm" if not dev else source_scripts.parent / "config" / "litellm"
        if litellm_src.exists():
            ensure_dir(CONFIG_DIR)
            for cfg_file in litellm_src.glob("*.yaml"):
                dst = CONFIG_DIR / cfg_file.name
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
                    console.print(f"  [green]Installed {count} LiteLLM callbacks (thinking models)[/green]")

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
        core_dst = CLAUDE_DIR / "k-lean"
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
                if prompts_dst.exists():
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
        pip = VENV_DIR / "bin" / "pip"
        if pip.exists():
            console.print("  Installing Python dependencies...")
            console.print("  [dim](First install may take 2-5 minutes for ML models...)[/dim]")
            subprocess.run(
                [str(pip), "install", "--upgrade", "pip"],
                capture_output=True  # pip upgrade is fast, keep quiet
            )
            result = subprocess.run(
                [str(pip), "install", "txtai", "sentence-transformers"]
                # No -q or capture_output: show real-time download progress
            )
            if result.returncode == 0:
                console.print("  [green]Knowledge database ready[/green]")
            else:
                console.print("  [yellow]Warning: Some dependencies may not have installed[/yellow]")

    # Summary
    console.print("\n[bold green]Installation complete![/bold green]")

    if dev:
        console.print("\n[cyan]Development mode:[/cyan] Files are symlinked to source.")
        console.print("Edit source files and changes will be immediately available.")

    console.print("\n[bold]Next steps:[/bold]")
    env_file = CONFIG_DIR / ".env"
    step = 1
    if not env_file.exists():
        console.print(f"  {step}. Configure API keys: [cyan]k-lean setup[/cyan]")
        step += 1
    console.print(f"  {step}. Start services: [cyan]k-lean start[/cyan]")
    step += 1
    console.print(f"  {step}. Verify: [cyan]k-lean status[/cyan]")

    # Check if smolagents is installed
    if not _check_smolagents_installed():
        console.print("\n[bold]Optional - SmolKLN agents:[/bold]")
        console.print("  To use SmolKLN agents, install:")
        console.print("  [cyan]pipx inject k-lean 'smolagents[litellm]' 'txtai[ann]'[/cyan]")


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
    console.print("  - ~/.claude/rules/k-lean.md")
    console.print("  - ~/.klean/agents/")

    if not yes and not click.confirm("\nProceed with uninstallation?"):
        console.print("[yellow]Uninstallation cancelled[/yellow]")
        return

    # Stop services first
    console.print("\n[bold]Stopping services...[/bold]")
    stop_litellm()
    stop_knowledge_server(stop_all=True)

    # Create backup directory
    backup_dir = CLAUDE_DIR / "backups" / f"k-lean-{__version__}"
    ensure_dir(backup_dir)

    # Backup and remove
    removed = []

    for path in [
        CLAUDE_DIR / "scripts",
        CLAUDE_DIR / "commands" / "kln",
        CLAUDE_DIR / "hooks",
        CLAUDE_DIR / "rules" / "k-lean.md",
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

    # Scripts
    scripts_dir = CLAUDE_DIR / "scripts"
    if scripts_dir.exists():
        count = len(list(scripts_dir.glob("*.sh")))
        is_symlink = any(f.is_symlink() for f in scripts_dir.glob("*.sh"))
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

    # SuperClaude (external optional framework)
    sc_dir = CLAUDE_DIR / "commands" / "sc"
    if sc_dir.exists():
        count = len(list(sc_dir.glob("*.md")))
        table.add_row("SuperClaude", f"[dim]Available ({count})[/dim]", "[dim]optional framework[/dim]")
    else:
        table.add_row("SuperClaude", "[dim]Not installed[/dim]", "[dim]optional[/dim]")

    # Hooks
    hooks_dir = CLAUDE_DIR / "hooks"
    if hooks_dir.exists():
        count = len(list(hooks_dir.glob("*.sh")))
        table.add_row("Hooks", f"OK ({count})", "")
    else:
        table.add_row("Hooks", "[yellow]NOT INSTALLED[/yellow]", "optional")

    # SmolKLN Agents
    smolkln_agents_dir = SMOL_AGENTS_DIR
    smolagents_installed = _check_smolagents_installed()
    if smolkln_agents_dir.exists():
        agent_files = list(smolkln_agents_dir.glob("*.md"))
        count = len([f for f in agent_files if f.name != "TEMPLATE.md"])
        if smolagents_installed:
            table.add_row("SmolKLN Agents", f"[green]OK ({count})[/green]", "smolagents ready")
        else:
            table.add_row("SmolKLN Agents", f"[yellow]OK ({count})[/yellow]", "[yellow]smolagents not installed[/yellow]")
    else:
        if smolagents_installed:
            table.add_row("SmolKLN Agents", "[yellow]NOT INSTALLED[/yellow]", "run: k-lean install")
        else:
            table.add_row("SmolKLN Agents", "[dim]Not installed[/dim]", "[dim]optional[/dim]")

    # Rules
    rules_file = CLAUDE_DIR / "rules" / "k-lean.md"
    if rules_file.exists():
        table.add_row("Rules", "[green]OK[/green]", "~/.claude/rules/k-lean.md")
    else:
        table.add_row("Rules", "[yellow]NOT INSTALLED[/yellow]", "run: k-lean install")

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
                "ERROR": "red"
            }.get(kb_status, "dim")
            # Truncate long project names
            display_name = kb_project[:20] + "..." if len(kb_project) > 20 else kb_project
            table.add_row(
                f"  └─ {display_name}",
                f"[{status_color}]{kb_status}[/{status_color}]",
                kb_details
            )
        elif kb_status == "N/A":
            table.add_row("  └─ Current dir", "[dim]N/A[/dim]", kb_details)
    else:
        table.add_row("Knowledge DB", "[yellow]NOT INSTALLED[/yellow]", "run: k-lean install")

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
            table.add_row("LiteLLM Proxy", "[yellow]NOT RUNNING[/yellow]", f"({model_count} models configured)")
        else:
            table.add_row("LiteLLM Proxy", "[yellow]NOT RUNNING[/yellow]", "run: k-lean start")

    console.print(table)

    # Installation mode detection
    console.print("\n[bold]Installation Info:[/bold]")
    console.print(f"  Version: {__version__}")
    console.print(f"  Claude Dir: {CLAUDE_DIR}")

    # Check if running in dev mode (symlinks present)
    if scripts_dir.exists():
        sample_script = next(scripts_dir.glob("*.sh"), None)
        if sample_script and sample_script.is_symlink():
            target = sample_script.resolve().parent.parent
            console.print(f"  Mode: [cyan]Development (symlinked to {target})[/cyan]")
        else:
            console.print("  Mode: Production (files copied)")


@main.command()
def version():
    """Show K-LEAN version information."""
    console.print(f"K-LEAN version {__version__}")
    console.print(f"Python: {sys.version}")
    console.print(f"Install path: {Path(__file__).parent}")


@main.command()
@click.option("--auto-fix", "-f", is_flag=True, help="Automatically fix issues (hooks, config, services)")
def doctor(auto_fix: bool):
    """Validate K-LEAN configuration and services (fast).

    Checks: config files, .env, API keys, subscription status, hooks, services.
    Does NOT check individual model health (use 'k-lean models --health' for that).

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

    # Check scripts
    scripts_dir = CLAUDE_DIR / "scripts"
    if scripts_dir.exists():
        # Check key scripts
        key_scripts = ["quick-review.sh"]
        for script in key_scripts:
            script_path = scripts_dir / script
            if not script_path.exists():
                issues.append(("WARNING", f"Missing script: {script}"))
            elif not os.access(script_path, os.X_OK):
                issues.append(("WARNING", f"Script not executable: {script}"))
    else:
        issues.append(("ERROR", "Scripts directory not found"))

    # Check smol-kln command (installed via pipx as part of k-lean)
    if not shutil.which("smol-kln"):
        issues.append(("WARNING", "smol-kln command not found - SmolKLN agents won't work"))

    # Check lib/common.sh
    common_sh = CLAUDE_DIR / "lib" / "common.sh"
    if not common_sh.exists():
        issues.append(("WARNING", "lib/common.sh not found - scripts may fail"))

    # Check LiteLLM config
    if CONFIG_DIR.exists():
        config_yaml = CONFIG_DIR / "config.yaml"
        if not config_yaml.exists():
            issues.append(("INFO", "LiteLLM config.yaml not found - run setup-litellm.sh"))
        else:
            # Check for common config errors
            try:
                config_content = config_yaml.read_text()

                # Check for quoted os.environ (common mistake that breaks auth)
                if '"os.environ/' in config_content or "'os.environ/" in config_content:
                    issues.append(("ERROR", "LiteLLM config has quoted os.environ/ - remove quotes!"))
                    console.print("  [red]✗[/red] LiteLLM config: Quoted os.environ/ found")
                    console.print("    [dim]This breaks env var substitution. Edit ~/.config/litellm/config.yaml[/dim]")
                    console.print("    [dim]Change: api_key: \"os.environ/KEY\" → api_key: os.environ/KEY[/dim]")
                    if auto_fix:
                        # Auto-fix by removing quotes around os.environ
                        import re
                        fixed = re.sub(r'["\']os\.environ/([^"\']+)["\']', r'os.environ/\1', config_content)
                        config_yaml.write_text(fixed)
                        console.print("    [green][OK] Auto-fixed: Removed quotes from os.environ[/green]")
                        fixes_applied.append("Fixed quoted os.environ in LiteLLM config")

                # Check for hardcoded API keys (security risk)
                import re
                # Match patterns like api_key: sk-xxx or api_key: "sk-xxx"
                hardcoded_keys = re.findall(r'api_key:\s*["\']?(sk-[a-zA-Z0-9]{10,}|[a-zA-Z0-9]{32,})["\']?', config_content)
                if hardcoded_keys:
                    issues.append(("CRITICAL", "LiteLLM config has hardcoded API keys! Use os.environ/VAR"))
                    console.print("  [red]✗[/red] LiteLLM config: Hardcoded API keys detected!")
                    console.print("    [dim]Never commit API keys. Use: api_key: os.environ/NANOGPT_API_KEY[/dim]")
            except Exception as e:
                console.print(f"  [yellow]○[/yellow] Could not validate LiteLLM config: {e}")

        # Check .env file
        env_file = CONFIG_DIR / ".env"
        if not env_file.exists():
            issues.append(("ERROR", "LiteLLM .env file not found - run setup-litellm.sh"))
            console.print("  [red]✗[/red] LiteLLM .env: NOT FOUND")
        else:
            env_content = env_file.read_text()
            has_api_key = "NANOGPT_API_KEY=" in env_content and "your-nanogpt-api-key-here" not in env_content
            has_api_base = "NANOGPT_API_BASE=" in env_content

            if not has_api_key:
                issues.append(("ERROR", "NANOGPT_API_KEY not configured in .env"))
                console.print("  [red]✗[/red] LiteLLM .env: NANOGPT_API_KEY not set")
            else:
                console.print("  [green][OK][/green] LiteLLM .env: NANOGPT_API_KEY configured")

            if not has_api_base:
                issues.append(("WARNING", "NANOGPT_API_BASE not set - will auto-detect on start"))
                console.print("  [yellow]○[/yellow] LiteLLM .env: NANOGPT_API_BASE not set")

                if auto_fix and has_api_key:
                    # Extract API key and auto-detect
                    import re
                    key_match = re.search(r'NANOGPT_API_KEY=(\S+)', env_content)
                    if key_match:
                        api_key = key_match.group(1)
                        console.print("    [dim]Auto-detecting subscription status...[/dim]")
                        try:
                            import urllib.request
                            req = urllib.request.Request(
                                "https://nano-gpt.com/api/subscription/v1/usage",
                                headers={"Authorization": f"Bearer {api_key}"}
                            )
                            response = urllib.request.urlopen(req, timeout=5)
                            data = json.loads(response.read().decode())
                            if data.get("active"):
                                api_base = "https://nano-gpt.com/api/subscription/v1"
                                console.print("    [green][OK] Subscription account detected[/green]")
                            else:
                                api_base = "https://nano-gpt.com/api/v1"
                                console.print("    [yellow]○ Pay-per-use account detected[/yellow]")

                            # Append to .env
                            with open(env_file, "a") as f:
                                f.write(f"\nNANOGPT_API_BASE={api_base}\n")
                            console.print("    [green][OK] Saved NANOGPT_API_BASE to .env[/green]")
                            fixes_applied.append("Auto-detected and saved NANOGPT_API_BASE")
                        except Exception as e:
                            console.print(f"    [red]✗ Could not detect: {e}[/red]")
            else:
                # Check if subscription is still active
                import re
                key_match = re.search(r'NANOGPT_API_KEY=(\S+)', env_content)
                base_match = re.search(r'NANOGPT_API_BASE=(\S+)', env_content)
                if key_match and base_match:
                    api_key = key_match.group(1)
                    api_base = base_match.group(1)
                    if "subscription" in api_base:
                        try:
                            import urllib.request
                            req = urllib.request.Request(
                                "https://nano-gpt.com/api/subscription/v1/usage",
                                headers={"Authorization": f"Bearer {api_key}"}
                            )
                            response = urllib.request.urlopen(req, timeout=5)
                            data = json.loads(response.read().decode())
                            if data.get("active"):
                                remaining = data.get("daily", {}).get("remaining", 0)
                                console.print(f"  [green][OK][/green] NanoGPT Subscription: ACTIVE ({remaining} daily remaining)")
                            else:
                                issues.append(("WARNING", "NanoGPT subscription is not active"))
                                console.print("  [yellow]○[/yellow] NanoGPT Subscription: INACTIVE")
                        except Exception:
                            console.print("  [yellow]○[/yellow] NanoGPT Subscription: Could not verify")
                    else:
                        console.print("  [green][OK][/green] LiteLLM .env: Pay-per-use configured")

        # Check thinking models callback
        callbacks_dir = CONFIG_DIR / "callbacks"
        thinking_callback = callbacks_dir / "thinking_transform.py"
        if thinking_callback.exists():
            console.print("  [green][OK][/green] Thinking models: Callback installed")
        else:
            issues.append(("WARNING", "Thinking models callback not installed"))
            console.print("  [yellow]○[/yellow] Thinking models: Callback not installed")
            console.print("    [dim]SmolKLN won't work with glm-4.6-thinking, kimi-k2-thinking, etc.[/dim]")
            console.print("    [dim]Fix: k-lean install -c config[/dim]")

    # Check Python venv
    if VENV_DIR.exists():
        python = VENV_DIR / "bin" / "python"
        if not python.exists():
            issues.append(("ERROR", "Knowledge DB venv is broken - recreate with k-lean install"))

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
            console.print("  [red]✗[/red] settings.json: Invalid JSON")
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
                console.print(f"  [red]✗[/red] Failed to configure hooks: {e}")
                issues.append(("ERROR", f"Failed to auto-configure hooks: {e}"))

    # Service checks with auto-fix
    console.print("[bold]Service Status:[/bold]")

    # Check LiteLLM
    litellm_status = check_litellm_detailed()
    if litellm_status["running"]:
        console.print(f"  [green][OK][/green] LiteLLM Proxy: RUNNING ({len(litellm_status['models'])} models)")

        # Note: Model health moved to 'k-lean models --health' for faster doctor execution
        console.print("  [dim]○[/dim] Model Health: Use [cyan]k-lean models --health[/cyan]")
    else:
        if auto_fix:
            console.print("  [yellow]○[/yellow] LiteLLM Proxy: NOT RUNNING - Starting...")
            if start_litellm():
                console.print("  [green][OK][/green] LiteLLM Proxy: STARTED")
                fixes_applied.append("Started LiteLLM proxy")
            else:
                issues.append(("ERROR", "Failed to start LiteLLM proxy"))
                console.print("  [red]✗[/red] LiteLLM Proxy: FAILED TO START")
        else:
            issues.append(("WARNING", "LiteLLM proxy not running"))
            console.print("  [red]✗[/red] LiteLLM Proxy: NOT RUNNING")

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
                console.print("  [red]✗[/red] Knowledge Server: FAILED TO START")
        else:
            issues.append(("WARNING", "Knowledge server not running"))
            console.print("  [red]✗[/red] Knowledge Server: NOT RUNNING")

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
        console.print("    [dim]Install with: pipx inject k-lean 'smolagents[litellm]' 'txtai[ann]'[/dim]")

    # Check rules
    console.print("\n[bold]Rules:[/bold]")
    rules_file = CLAUDE_DIR / "rules" / "k-lean.md"
    if rules_file.exists():
        console.print("  [green][OK][/green] k-lean.md: Installed")
    else:
        issues.append(("INFO", "Rules not installed - run k-lean install"))
        console.print("  [yellow]○[/yellow] k-lean.md: NOT INSTALLED")
        console.print("    [dim]Install with: k-lean install[/dim]")

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
        console.print("\n[cyan]Tip:[/cyan] Run [bold]k-lean doctor --auto-fix[/bold] to auto-start services")


@main.command()
def test():
    """Run comprehensive K-LEAN test suite.

    Tests all components: scripts, commands, hooks, services, knowledge DB,
    nano profile, and SmolKLN agents.
    """
    print_banner()
    console.print("\n[bold]K-LEAN Test Suite[/bold]\n")

    passed = 0
    failed = 0

    def test_pass(msg: str):
        nonlocal passed
        console.print(f"  [green][OK][/green] {msg}")
        passed += 1

    def test_fail(msg: str):
        nonlocal failed
        console.print(f"  [red]✗[/red] {msg}")
        failed += 1

    # Test 1: Installation structure
    console.print("[bold]1. Installation Structure[/bold]")
    test_pass("~/.claude directory") if CLAUDE_DIR.exists() else test_fail("~/.claude missing")
    test_pass("Scripts directory") if (CLAUDE_DIR / "scripts").exists() else test_fail("Scripts missing")
    test_pass("Commands directory") if (CLAUDE_DIR / "commands").exists() else test_fail("Commands missing")
    test_pass("KLN commands") if (CLAUDE_DIR / "commands" / "kln").exists() else test_fail("KLN commands missing")

    # Test 2: Scripts executable
    console.print("\n[bold]2. Scripts Executable[/bold]")
    key_scripts = ["quick-review.sh", "klean-statusline.py", "kb-doctor.sh"]
    scripts_dir = CLAUDE_DIR / "scripts"
    for script in key_scripts:
        script_path = scripts_dir / script
        if script_path.exists() and os.access(script_path, os.X_OK):
            test_pass(script)
        else:
            test_fail(f"{script} {'not found' if not script_path.exists() else 'not executable'}")

    # Test 3: KLN Commands
    console.print("\n[bold]3. KLN Commands[/bold]")
    kln_commands = ["quick.md", "multi.md", "agent.md", "rethink.md",
                    "remember.md", "status.md", "help.md", "doc.md"]
    kln_dir = CLAUDE_DIR / "commands" / "kln"
    for cmd in kln_commands:
        test_pass(cmd) if (kln_dir / cmd).exists() else test_fail(f"{cmd} missing")

    # Test 4: Hooks
    console.print("\n[bold]4. Hooks[/bold]")
    hooks = ["session-start.sh", "user-prompt-handler.sh", "post-bash-handler.sh"]
    hooks_dir = CLAUDE_DIR / "hooks"
    for hook in hooks:
        hook_path = hooks_dir / hook
        if hook_path.exists() and os.access(hook_path, os.X_OK):
            test_pass(hook)
        else:
            test_fail(f"{hook} {'not found' if not hook_path.exists() else 'not executable'}")

    # Test 5: LiteLLM
    console.print("\n[bold]5. LiteLLM Service[/bold]")
    litellm_status = check_litellm_detailed()
    if litellm_status["running"]:
        test_pass(f"LiteLLM running ({len(litellm_status['models'])} models)")
    else:
        test_fail("LiteLLM not running")

    # Test 6: Knowledge DB
    console.print("\n[bold]6. Knowledge System[/bold]")
    if VENV_DIR.exists():
        test_pass("Python venv exists")
        pip = VENV_DIR / "bin" / "pip"
        if pip.exists():
            try:
                # Use pip show instead of import (faster, no model loading)
                result = subprocess.run([str(pip), "show", "txtai"],
                                       capture_output=True, timeout=10)
                if result.returncode == 0:
                    test_pass("txtai installed")
                else:
                    test_fail("txtai not installed")
            except Exception as e:
                test_fail(f"txtai check failed: {e}")
        else:
            test_fail("pip not found in venv")
    else:
        test_fail("Python venv missing")

    # Test 7: Nano Profile
    console.print("\n[bold]7. Nano Profile[/bold]")
    nano_dir = Path.home() / ".claude-nano"
    if nano_dir.exists():
        test_pass("Nano profile directory")
        test_pass("settings.json") if (nano_dir / "settings.json").exists() else test_fail("settings.json missing")
        test_pass("Commands symlink") if (nano_dir / "commands").is_symlink() else test_fail("Commands symlink missing")
    else:
        test_fail("Nano profile directory missing")

    # Test 8: SmolKLN Agents
    console.print("\n[bold]8. SmolKLN Agents[/bold]")
    if SMOL_AGENTS_DIR.exists():
        agent_count = len([f for f in SMOL_AGENTS_DIR.glob("*.md") if f.name != "TEMPLATE.md"])
        test_pass(f"{agent_count} agents installed") if agent_count >= 8 else test_fail(f"Only {agent_count}/8 agents")
    else:
        test_fail("SmolKLN agents directory missing")

    # Summary
    console.print("\n" + "═" * 50)
    if failed == 0:
        console.print(f"[bold green]All {passed} tests passed![/bold green]")
    else:
        console.print(f"[bold]Results:[/bold] [green]{passed} passed[/green], [red]{failed} failed[/red]")

    sys.exit(0 if failed == 0 else 1)


@main.command()
@click.option("--service", "-s",
              type=click.Choice(["all", "litellm", "knowledge"]),
              default="litellm", help="Service to start (default: litellm only)")
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
                console.print("[red]✗[/red] LiteLLM Proxy: Failed to start")
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
                    console.print(f"[green][OK][/green] Knowledge Server: Starting for {project.name}")
                    started.append("Knowledge")
                    log_debug_event("cli", "service_start", service="knowledge", project=str(project))
                else:
                    console.print("[red]✗[/red] Knowledge Server: Failed to start")
                    failed.append("Knowledge")
        else:
            console.print("[yellow]○[/yellow] Knowledge Server: No project found (auto-starts on query)")

    # Phoenix telemetry (optional)
    if telemetry:
        if check_phoenix():
            console.print("[green][OK][/green] Phoenix Telemetry: Already running")
        else:
            console.print("[yellow]○[/yellow] Starting Phoenix Telemetry...")
            if start_phoenix(background=True):
                console.print("[green][OK][/green] Phoenix Telemetry: Started on http://localhost:6006")
                started.append("Phoenix")
                log_debug_event("cli", "service_start", service="phoenix")
            else:
                console.print("[red]✗[/red] Phoenix Telemetry: Failed to start")
                console.print("[dim]  Install with: pipx inject k-lean 'k-lean[telemetry]'[/dim]")
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
@click.option("--service", "-s",
              type=click.Choice(["all", "litellm", "knowledge"]),
              default="all", help="Service to stop")
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
                console.print(f"[green][OK][/green] Knowledge Servers: Stopped {len(servers)} server(s)")
                stopped.append(f"Knowledge ({len(servers)})")
                log_debug_event("cli", "service_stop", service="knowledge", count=len(servers))
            else:
                console.print("[yellow]○[/yellow] Knowledge Servers: None running")
        else:
            # Stop current project's server
            project = find_project_root()
            if project:
                if stop_knowledge_server(project):
                    console.print(f"[green][OK][/green] Knowledge Server: Stopped for {project.name}")
                    stopped.append("Knowledge")
                    log_debug_event("cli", "service_stop", service="knowledge", project=str(project))
                else:
                    console.print(f"[yellow]○[/yellow] Knowledge Server: Was not running for {project.name}")
            else:
                console.print("[yellow]○[/yellow] Knowledge Server: No project found")
                # Show hint about --all-projects
                servers = list_knowledge_servers()
                if servers:
                    console.print(f"[dim]  (Use --all-projects to stop {len(servers)} running server(s))[/dim]")

    console.print(f"\n[green]Stopped {len(stopped)} service(s)[/green]")


def get_session_stats() -> Dict[str, Any]:
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


@main.command()
@click.option("--follow/--no-follow", "-f/-F", default=True, help="Live updating (default: on)")
@click.option("--filter", "component_filter",
              type=click.Choice(["all", "litellm", "knowledge", "droid", "cli"]),
              default="all", help="Filter by component")
@click.option("--lines", "-n", default=20, help="Number of lines to show")
@click.option("--compact", "-c", is_flag=True, help="Compact single-line output")
@click.option("--interval", "-i", default=2, help="Refresh interval in seconds")
def debug(follow: bool, component_filter: str, lines: int, compact: bool, interval: int):
    """Real-time monitoring dashboard for K-LEAN services and activity.

    Live updating is ON by default. Use --no-follow for single snapshot."""
    ensure_klean_dirs()

    # Compact mode - single line for hooks/scripts
    if compact:
        litellm_ok = check_litellm()
        knowledge_ok = check_knowledge_server()
        models = discover_models() if litellm_ok else []
        healthy = sum(1 for m in models if m in ["qwen3-coder", "deepseek-v3-thinking"])  # Known working
        status = "[OK]" if litellm_ok and knowledge_ok else "[WARN]"
        console.print(f"{status} K-LEAN: LiteLLM({'OK' if litellm_ok else 'DOWN'}) Knowledge({'OK' if knowledge_ok else 'DOWN'}) Models({healthy}/{len(models)})")
        return

    def render_services_panel() -> Panel:
        """Render services status panel."""
        litellm_info = check_litellm_detailed()
        knowledge_ok = check_knowledge_server()
        litellm_latency = measure_service_latency("litellm") if litellm_info["running"] else None

        lines = []

        # LiteLLM
        if litellm_info["running"]:
            latency_str = f" {litellm_latency}ms" if litellm_latency else ""
            lines.append(f"[bold]LiteLLM[/bold]  [green]● ON[/green]{latency_str}")
        else:
            lines.append("[bold]LiteLLM[/bold]  [red]● OFF[/red]")

        # Knowledge DB
        if knowledge_ok:
            lines.append("[bold]Knowledge[/bold] [green]● ON[/green]")
        else:
            lines.append("[bold]Knowledge[/bold] [dim]○ OFF[/dim]")

        # Phoenix Telemetry - only show when running
        if check_phoenix():
            lines.append("[bold]Phoenix[/bold]   [green]● ON[/green] :6006")

        return Panel("\n".join(lines), title="[bold]Services[/bold]", border_style="blue")

    def render_models_panel() -> Panel:
        """Render models status panel - shows 10+ models with clean layout."""
        models = discover_models()
        if not models:
            return Panel("[dim]No models available\nIs LiteLLM running?[/dim]",
                        title="[bold]Models[/bold]", border_style="yellow")

        # Show up to 12 models for better visibility
        max_display = 12
        model_lines = []

        for i, model in enumerate(models[:max_display]):
            # Clean model name: remove provider prefix, truncate
            clean_name = model.split("/")[-1] if "/" in model else model
            clean_name = clean_name[:18] if len(clean_name) > 18 else clean_name

            # Alternate subtle styling for readability
            if i % 2 == 0:
                model_lines.append(f"[green]●[/green] [cyan]{clean_name}[/cyan]")
            else:
                model_lines.append(f"[green]●[/green] [dim cyan]{clean_name}[/dim cyan]")

        # Show count if more models exist
        if len(models) > max_display:
            remaining = len(models) - max_display
            model_lines.append(f"[dim]  +{remaining} more...[/dim]")

        content = "\n".join(model_lines)
        return Panel(content, title=f"[bold]Models ({len(models)})[/bold]", border_style="green")

    # Cache Phoenix data to avoid repeated queries
    phoenix_cache = {"data": None, "time": 0}

    def get_phoenix_data() -> Optional[Dict]:
        """Get Phoenix data with caching (5 second TTL)."""
        now = time.time()
        if phoenix_cache["data"] and (now - phoenix_cache["time"]) < 5:
            return phoenix_cache["data"]
        data = query_phoenix_traces(limit=30)
        if data:
            phoenix_cache["data"] = data
            phoenix_cache["time"] = now
        return data

    def render_stats_panel() -> Panel:
        """Render session statistics panel with Phoenix data."""
        phoenix = get_phoenix_data()
        lines_out = []

        if phoenix:
            # LLM Calls
            llm_count = len(phoenix.get("llm_calls", []))
            lines_out.append(f"[bold]LLM Calls:[/bold] [cyan]{llm_count}[/cyan]")

            # Total tokens with K formatting
            total_tokens = phoenix.get("total_tokens", 0)
            if total_tokens >= 1000:
                lines_out.append(f"[bold]Tokens:[/bold] [yellow]{total_tokens/1000:.1f}K[/yellow]")
            else:
                lines_out.append(f"[bold]Tokens:[/bold] [yellow]{total_tokens}[/yellow]")

            # Average latency
            avg_latency = phoenix.get("avg_latency_ms", 0)
            if avg_latency >= 1000:
                lines_out.append(f"[bold]Avg Latency:[/bold] [cyan]{avg_latency/1000:.1f}s[/cyan]")
            else:
                lines_out.append(f"[bold]Avg Latency:[/bold] [cyan]{avg_latency}ms[/cyan]")

            # Errors
            errors = phoenix.get("error_count", 0)
            if errors > 0:
                lines_out.append(f"[bold]Errors:[/bold] [red]{errors}[/red]")
            else:
                lines_out.append("[bold]Errors:[/bold] [green]0[/green]")

            # Traces by project
            lines_out.append("")
            lines_out.append("[bold]Traces:[/bold]")
            for proj, count in list(phoenix.get("projects", {}).items())[:3]:
                if count > 0:
                    lines_out.append(f"  [dim]{proj}:[/dim] {count}")

        else:
            # Fallback to debug.log stats
            stats = get_session_stats()
            lines_out.append("[dim]Phoenix not running[/dim]")
            lines_out.append("")
            lines_out.append(f"[bold]Requests:[/bold] {stats['total_requests']}")
            lines_out.append(f"[bold]Agents:[/bold] {stats['agents_executed']}")
            lines_out.append(f"[bold]KB Queries:[/bold] {stats['knowledge_queries']}")

        return Panel("\n".join(lines_out), title="[bold]Session Stats[/bold]", border_style="magenta")

    def render_llm_calls_panel() -> Panel:
        """Render recent LLM calls from Phoenix telemetry."""
        phoenix = get_phoenix_data()

        if not phoenix or not phoenix.get("llm_calls"):
            # Fallback to debug.log if Phoenix not available
            entries = read_debug_log(lines=10, component="cli")
            if not entries:
                return Panel(
                    "[dim]No LLM calls yet[/dim]\n\n"
                    "[dim]Run a review with --telemetry[/dim]\n"
                    "[dim]or use k-lean multi[/dim]",
                    title="[bold]Recent LLM Calls[/bold]", border_style="cyan"
                )
            # Show basic debug.log data
            lines_out = []
            for entry in entries[-8:]:
                if entry.get("event") == "test_model":
                    ts = entry.get("ts", "")[11:16]
                    model = entry.get("model", "?")[:12]
                    latency = entry.get("latency_ms", 0)
                    if latency >= 1000:
                        lat_str = f"{latency/1000:.1f}s"
                    else:
                        lat_str = f"{latency}ms"
                    lines_out.append(f"[dim]{ts}[/dim] [cyan]{model}[/cyan] {lat_str}")
            if lines_out:
                return Panel("\n".join(lines_out), title="[bold]Recent LLM Calls[/bold]", border_style="cyan")
            return Panel("[dim]No LLM calls recorded[/dim]", title="[bold]Recent LLM Calls[/bold]", border_style="cyan")

        # Show Phoenix LLM calls with rich metrics
        lines_out = []
        # Header row
        lines_out.append("[bold dim]Time    Model          Latency  Tokens[/bold dim]")
        lines_out.append("[dim]─────────────────────────────────────────[/dim]")

        for call in phoenix["llm_calls"][:8]:
            # Parse time
            time_str = call.get("time", "")
            if time_str:
                # Format: extract HH:MM from ISO timestamp
                time_str = time_str[11:16] if len(time_str) > 16 else time_str[:5]
            else:
                time_str = "??:??"

            model = call.get("model", "unknown")[:14]
            latency = call.get("latency_ms", 0)
            tokens_in = call.get("tokens_in", 0)
            tokens_out = call.get("tokens_out", 0)
            status = call.get("status", "OK")

            # Format latency
            if latency >= 1000:
                lat_str = f"{latency/1000:.1f}s"
            else:
                lat_str = f"{latency}ms"

            # Format tokens
            if tokens_in >= 1000:
                tok_in = f"{tokens_in/1000:.1f}K"
            else:
                tok_in = str(tokens_in)
            if tokens_out >= 1000:
                tok_out = f"{tokens_out/1000:.1f}K"
            else:
                tok_out = str(tokens_out)

            # Status color
            status_icon = "[green]●[/green]" if status == "OK" else "[red]●[/red]"

            # Compact format: time model latency tokens
            line = f"[dim]{time_str}[/dim] {status_icon} [cyan]{model:<14}[/cyan] [yellow]{lat_str:>5}[/yellow] [dim]{tok_in}→{tok_out}[/dim]"
            lines_out.append(line)

        if not lines_out:
            lines_out.append("[dim]No LLM calls recorded[/dim]")

        return Panel("\n".join(lines_out), title="[bold]Recent LLM Calls[/bold]", border_style="cyan")

    def render_history_panel() -> Panel:
        """Render run history from Phoenix traces grouped by day."""
        phoenix = get_phoenix_data()

        if not phoenix or not phoenix.get("llm_calls"):
            return Panel(
                "[dim]No data yet[/dim]\n\n"
                "[dim]Stats appear after[/dim]\n"
                "[dim]LLM calls with Phoenix[/dim]",
                title="[bold]Daily Summary[/bold]", border_style="yellow"
            )

        # Group by date and aggregate stats
        from datetime import datetime as dt
        today = dt.now().date()
        yesterday = today - timedelta(days=1)

        # Aggregate stats per day
        groups = {
            "Today": {"calls": 0, "tokens": 0, "latency": 0, "errors": 0},
            "Yesterday": {"calls": 0, "tokens": 0, "latency": 0, "errors": 0},
            "Earlier": {"calls": 0, "tokens": 0, "latency": 0, "errors": 0},
        }

        for call in phoenix["llm_calls"]:
            ts = call.get("time", "")
            if not ts:
                continue
            try:
                entry_date = dt.fromisoformat(ts[:10]).date()
                if entry_date == today:
                    group = "Today"
                elif entry_date == yesterday:
                    group = "Yesterday"
                else:
                    group = "Earlier"

                groups[group]["calls"] += 1
                groups[group]["tokens"] += call.get("tokens_in", 0) + call.get("tokens_out", 0)
                groups[group]["latency"] += call.get("latency_ms", 0)
                if call.get("status") != "OK":
                    groups[group]["errors"] += 1
            except (ValueError, TypeError):
                pass

        # Build output with header
        lines = []
        lines.append("[bold dim]Period    Calls Tokens  Time[/bold dim]")
        lines.append("[dim]────────────────────────────[/dim]")

        for group_name in ["Today", "Yesterday", "Earlier"]:
            stats = groups[group_name]
            if stats["calls"] == 0:
                continue

            calls = stats["calls"]
            tokens = stats["tokens"]
            latency = stats["latency"]
            errors = stats["errors"]

            # Format tokens
            if tokens >= 1000000:
                tok_str = f"{tokens/1000000:.1f}M"
            elif tokens >= 1000:
                tok_str = f"{tokens/1000:.0f}K"
            else:
                tok_str = str(tokens)

            # Format total time
            if latency >= 60000:
                time_str = f"{latency // 60000}m{(latency % 60000) // 1000}s"
            elif latency >= 1000:
                time_str = f"{latency // 1000}s"
            else:
                time_str = f"{latency}ms"

            # Error indicator
            err_icon = "[red]![/red]" if errors > 0 else ""

            lines.append(f"[bold]{group_name:<9}[/bold] {calls:>3} {tok_str:>5} {time_str:>5}{err_icon}")

        if len(lines) == 2:  # Only header
            lines.append("[dim]No activity yet[/dim]")

        return Panel("\n".join(lines), title="[bold]Daily Summary[/bold]", border_style="yellow")

    def render_full_dashboard():
        """Render the complete dashboard layout."""
        # Create layout
        layout = Layout()

        # Header with live clock and shortcuts
        header = Text()
        header.append("K-LEAN ", style="bold cyan")
        header.append("Dashboard", style="bold")
        header.append(f"  {datetime.now().strftime('%H:%M:%S')}", style="green")
        header.append("  ", style="dim")
        header.append("[Ctrl+C]", style="dim cyan")
        header.append(" exit  ", style="dim")
        if check_phoenix():
            header.append("[Phoenix :6006]", style="dim green")

        # Top section: Services + Stats + Models (3 columns)
        top_layout = Layout()
        top_layout.split_row(
            Layout(render_services_panel(), name="services", ratio=1),
            Layout(render_stats_panel(), name="stats", ratio=1),
            Layout(render_models_panel(), name="models", ratio=1),
        )

        # Bottom section: LLM Calls + History (2 columns)
        bottom_layout = Layout()
        bottom_layout.split_row(
            Layout(render_llm_calls_panel(), name="llm_calls", ratio=3),
            Layout(render_history_panel(), name="history", ratio=2),
        )

        # Combine: Header + Top row (Services/Stats/Models) + Bottom row (LLM Calls/History)
        layout.split_column(
            Layout(Panel(header, border_style="cyan"), size=3),
            Layout(top_layout, name="top", ratio=2),
            Layout(bottom_layout, name="bottom", ratio=3),
        )

        return layout

    if follow:
        console.print("[dim]K-LEAN Live Dashboard - Press Ctrl+C to exit[/dim]\n")
        try:
            with Live(render_full_dashboard(), refresh_per_second=1, console=console, screen=True) as live:
                while True:
                    time.sleep(interval)
                    live.update(render_full_dashboard())
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard closed[/yellow]")
    else:
        console.print(render_full_dashboard())
        console.print("\n[dim]Tip: Run 'k-lean debug' for live updates (Ctrl+C to exit)[/dim]")


@main.command()
@click.option("--test", is_flag=True, help="Test each model with API call and show latency")
@click.option("--health", is_flag=True, help="Show model health summary from LiteLLM")
def models(test: bool, health: bool):
    """List available models from LiteLLM proxy.

    Use --health to check which models are healthy/unhealthy.
    Use --test to test each model with an API call and measure latency.
    """
    print_banner()

    if not check_litellm():
        console.print("\n[red]LiteLLM proxy is not running![/red]")
        console.print("Start it with: [cyan]k-lean start --service litellm[/cyan]")
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
                console.print(f"[red]✗ All {unhealthy_count} models unhealthy![/red]")
                console.print("[dim]Check: k-lean doctor -f[/dim]\n")
            else:
                console.print(f"[yellow]○ {healthy_count}/{total} models healthy ({unhealthy_count} failing)[/yellow]\n")

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
                console.print(f"\n[green]Healthy models:[/green] {', '.join(e.get('model', '?').split('/')[-1] for e in healthy_endpoints)}")

        except Exception as e:
            console.print(f"[red]✗ Could not check health: {e}[/red]")
        return

    if test:
        console.print("\n[dim]Testing models (5s timeout, uses tokens)...[/dim]")
        import urllib.request

        # Test each model and record latency
        results = []  # [(model, latency_ms or None)]
        for model in models_list:
            try:
                start = time.time()
                data = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": "1"}],
                    "max_tokens": 1
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:4000/chat/completions",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=5)
                latency = int((time.time() - start) * 1000)
                results.append((model, latency))
                console.print(f"  [green][OK][/green] {model}: {latency}ms")
            except Exception:
                results.append((model, None))
                console.print(f"  [red]✗[/red] {model}: FAIL")

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
        console.print(f"\n[bold]Total:[/bold] {len(models_list)} models")
        console.print("[dim]Use --test to measure latency (costs tokens)[/dim]")


@main.command()
@click.argument("model", required=False)
@click.argument("prompt", required=False)
def test_model(model: Optional[str], prompt: Optional[str]):
    """Test a model with a quick prompt."""
    if not check_litellm():
        console.print("[red]LiteLLM proxy is not running![/red]")
        return

    models_list = discover_models()

    if not model:
        console.print("[bold]Available models:[/bold]")
        for m in models_list:
            console.print(f"  • {m}")
        console.print("\nUsage: [cyan]k-lean test-model <model> [prompt][/cyan]")
        return

    if model not in models_list:
        console.print(f"[red]Model '{model}' not found[/red]")
        console.print(f"Available: {', '.join(models_list)}")
        return

    if not prompt:
        prompt = "Say 'Hello from K-LEAN!' in exactly 5 words."

    console.print(f"\n[bold]Testing model:[/bold] {model}")
    console.print(f"[bold]Prompt:[/bold] {prompt}\n")

    try:
        import urllib.request
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100
        }).encode()

        req = urllib.request.Request(
            "http://localhost:4000/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        start_time = time.time()
        response = urllib.request.urlopen(req, timeout=30)
        elapsed = time.time() - start_time

        result = json.loads(response.read().decode())
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")

        console.print(f"[green]Response:[/green] {content}")
        console.print(f"[dim]Latency: {elapsed:.2f}s[/dim]")

        log_debug_event("cli", "test_model", model=model, latency_ms=int(elapsed * 1000))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.option("--check", is_flag=True, help="Only check sync status, don't modify files")
@click.option("--clean", is_flag=True, help="Remove stale files from package before syncing")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed file-by-file changes")
def sync(check: bool, clean: bool, verbose: bool):
    """Sync root directories to src/klean/data/ for PyPI packaging.

    This command ensures the package data directory is in sync with the
    canonical source directories (scripts/, hooks/, commands/, etc.).

    Use before building for PyPI release.

    Examples:
        k-lean sync           # Sync files to package
        k-lean sync --check   # Check if in sync (for CI)
        k-lean sync --clean   # Remove stale files first
    """
    print_banner()

    # Find repo root (parent of src/)
    repo_root = Path(__file__).parent.parent.parent
    data_dir = repo_root / "src" / "klean" / "data"

    # Directories to sync: (source_name, dest_subpath, patterns)
    sync_dirs = [
        ("scripts", "scripts", ["*.sh", "*.py"]),
        ("hooks", "hooks", ["*.sh"]),
        ("commands/kln", "commands/kln", ["*.md"]),
        ("config", "config", ["*.md", "*.yaml"]),
        ("config/litellm", "config/litellm", ["*.yaml", ".env.example"]),
        ("lib", "lib", ["*.sh"]),
        ("rules", "rules", ["*.md"]),
    ]

    console.print(f"\n[bold]Repository root:[/bold] {repo_root}")
    console.print(f"[bold]Package data:[/bold] {data_dir}\n")

    if check:
        console.print("[bold cyan]Checking sync status...[/bold cyan]\n")
    else:
        console.print("[bold cyan]Syncing files to package...[/bold cyan]\n")

    total_synced = 0
    total_missing = 0
    total_stale = 0

    for src_subdir, dst_subdir, patterns in sync_dirs:
        src_dir = repo_root / src_subdir
        dst_dir = data_dir / dst_subdir

        if not src_dir.exists():
            if verbose:
                console.print(f"[dim]Skip: {src_subdir} (source not found)[/dim]")
            continue

        # Get source files
        src_files = set()
        for pattern in patterns:
            for f in src_dir.glob(pattern):
                if f.is_file():
                    src_files.add(f.name)

        # Get destination files
        dst_files = set()
        if dst_dir.exists():
            for pattern in patterns:
                for f in dst_dir.glob(pattern):
                    if f.is_file():
                        dst_files.add(f.name)

        # Find missing files (in source, not in dest)
        missing = src_files - dst_files

        # Find stale files (in dest, not in source)
        stale = dst_files - src_files

        # Find files that need updating (different content)
        needs_update = []
        for name in src_files & dst_files:
            src_file = src_dir / name
            dst_file = dst_dir / name
            if src_file.read_bytes() != dst_file.read_bytes():
                needs_update.append(name)

        if missing or stale or needs_update:
            console.print(f"[bold]{src_subdir}/[/bold]")

            if missing:
                total_missing += len(missing)
                for name in sorted(missing):
                    console.print(f"  [green]+[/green] {name}")
                    if not check:
                        dst_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_dir / name, dst_dir / name)
                        total_synced += 1

            if needs_update:
                for name in sorted(needs_update):
                    console.print(f"  [yellow]~[/yellow] {name}")
                    if not check:
                        shutil.copy2(src_dir / name, dst_dir / name)
                        total_synced += 1

            if stale:
                total_stale += len(stale)
                for name in sorted(stale):
                    console.print(f"  [red]-[/red] {name} (stale)")
                    if clean and not check:
                        (dst_dir / name).unlink()

        elif verbose:
            console.print(f"[dim]{src_subdir}/ - {len(src_files)} files in sync[/dim]")

    # Summary
    console.print()
    if check:
        if total_missing == 0 and total_stale == 0:
            console.print("[green][OK] Package is in sync with source[/green]")
            sys.exit(0)
        else:
            console.print("[red]✗ Package is out of sync:[/red]")
            if total_missing:
                console.print(f"  [yellow]• {total_missing} files need to be added[/yellow]")
            if total_stale:
                console.print(f"  [yellow]• {total_stale} stale files to remove (use --clean)[/yellow]")
            console.print("\n[dim]Run 'k-lean sync' to sync, or 'k-lean sync --clean' to also remove stale files[/dim]")
            sys.exit(1)
    else:
        console.print(f"[green][OK] Synced {total_synced} files[/green]")
        if total_stale and not clean:
            console.print(f"[yellow]! {total_stale} stale files remain (use --clean to remove)[/yellow]")

        # Make scripts executable
        for subdir in ["scripts", "hooks"]:
            target_dir = data_dir / subdir
            if target_dir.exists():
                for script in target_dir.glob("*.sh"):
                    script.chmod(script.stat().st_mode | 0o111)
                for script in target_dir.glob("*.py"):
                    script.chmod(script.stat().st_mode | 0o111)

        console.print("\n[dim]Package ready for: python -m build[/dim]")


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
            timeout=5.0
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
@click.option("--thorough", "-t", is_flag=True, help="Use 4-agent architecture (slower, more thorough)")
@click.option("--manager-model", "-m", help="Override manager model")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--telemetry", is_flag=True, help="Enable Phoenix telemetry (view at localhost:6006)")
def multi(task: str, thorough: bool, manager_model: str, output: str, telemetry: bool):
    """Run multi-agent orchestrated review.

    Uses multiple specialized agents coordinated by a manager for thorough code reviews.

    \b
    3-Agent (default):
      - Manager (glm-4.6-thinking): Orchestration
      - File Scout (qwen3-coder): Fast file discovery
      - Analyzer (kimi-k2-thinking): Deep analysis

    \b
    4-Agent (--thorough):
      - Manager (glm-4.6-thinking): Orchestration
      - File Scout (qwen3-coder): File discovery
      - Code Analyzer (deepseek-v3-thinking): Bug detection
      - Security Auditor (deepseek-v3-thinking): Security analysis
      - Synthesizer (kimi-k2): Report formatting

    Examples:
        k-lean multi "Review src/auth/ for security issues"
        k-lean multi --thorough "Review the authentication module"
        k-lean multi -m kimi-k2-thinking "Review cli.py"
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
            console.print("[yellow]Telemetry not installed. Run: pipx inject k-lean arize-phoenix openinference-instrumentation-smolagents[/yellow]")

    try:
        from klean.smol.multi_agent import MultiAgentExecutor
    except ImportError:
        console.print("[red]Error: smolagents not installed[/red]")
        console.print("Install with: pipx inject k-lean 'smolagents[litellm]'")
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
@click.option("--provider", "-p", type=click.Choice(['nanogpt', 'openrouter']),
              help="Provider to configure (skips menu)")
def setup(provider: Optional[str]):
    """Configure LiteLLM API provider (interactive wizard).

    Interactive setup for configuring LiteLLM with NanoGPT or OpenRouter.
    Creates ~/.config/litellm/config.yaml and ~/.config/litellm/.env

    Examples:
        k-lean setup                # Interactive menu
        k-lean setup -p nanogpt     # Direct NanoGPT setup
        k-lean setup -p openrouter  # Direct OpenRouter setup
    """
    print_banner()

    console.print("\n[bold cyan]LiteLLM Setup Wizard[/bold cyan]")
    console.print("=" * 40)

    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = CONFIG_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)

    # Backup existing config if present
    existing_config = CONFIG_DIR / "config.yaml"
    if existing_config.exists():
        import time
        timestamp = int(time.time())
        backup_path = backup_dir / f"config.yaml.{timestamp}"
        shutil.copy(existing_config, backup_path)
        console.print(f"[dim]Backed up existing config to {backup_path}[/dim]")

    # Provider selection
    if not provider:
        console.print("\nSelect your API provider:\n")
        console.print("  [cyan]1)[/cyan] NanoGPT (12 models, subscription)")
        console.print("  [cyan]2)[/cyan] OpenRouter (diverse models, pay-per-use)")
        console.print("  [cyan]3)[/cyan] Skip setup (use existing config)")
        console.print()

        choice = click.prompt("Enter choice", type=click.Choice(['1', '2', '3']), default='1')

        if choice == '1':
            provider = 'nanogpt'
        elif choice == '2':
            provider = 'openrouter'
        else:
            console.print("[yellow]Skipping setup[/yellow]")
            return

    # Configure based on provider
    if provider == 'nanogpt':
        console.print("\n[bold]Configuring NanoGPT...[/bold]")
        console.print("[dim]Get your API key from https://nano-gpt.com[/dim]\n")

        api_key = click.prompt("Enter your NanoGPT API key", hide_input=True)

        if not api_key:
            console.print("[red]API key cannot be empty[/red]")
            return

        # Auto-detect subscription
        console.print("[dim]Detecting account type...[/dim]")
        api_base = detect_nanogpt_endpoint(api_key)

        if "subscription" in api_base:
            console.print("[green][OK] Subscription account detected[/green]")
        else:
            console.print("[cyan][INFO] Pay-per-use account detected[/cyan]")

        # Create .env file
        env_content = f"""# K-LEAN LiteLLM Environment Variables - NanoGPT
# Generated by k-lean setup

NANOGPT_API_BASE={api_base}
NANOGPT_API_KEY={api_key}
"""
        env_file = CONFIG_DIR / ".env"
        env_file.write_text(env_content)
        env_file.chmod(0o600)

        # Copy config template
        template = find_config_template("config.yaml")
        if template:
            shutil.copy(template, CONFIG_DIR / "config.yaml")
            console.print("[green][OK] NanoGPT configuration created[/green]")
        else:
            console.print("[yellow]! Config template not found - run 'k-lean install' first[/yellow]")

    elif provider == 'openrouter':
        console.print("\n[bold]Configuring OpenRouter...[/bold]")
        console.print("[dim]Get your API key from https://openrouter.ai[/dim]\n")

        api_key = click.prompt("Enter your OpenRouter API key", hide_input=True)

        if not api_key:
            console.print("[red]API key cannot be empty[/red]")
            return

        # Create .env file
        env_content = f"""# K-LEAN LiteLLM Environment Variables - OpenRouter
# Generated by k-lean setup

OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_API_KEY={api_key}
"""
        env_file = CONFIG_DIR / ".env"
        env_file.write_text(env_content)
        env_file.chmod(0o600)

        # Copy config template
        template = find_config_template("openrouter.yaml")
        if template:
            shutil.copy(template, CONFIG_DIR / "config.yaml")
            console.print("[green][OK] OpenRouter configuration created[/green]")
        else:
            console.print("[yellow]! Config template not found - run 'k-lean install' first[/yellow]")

    # Summary
    console.print("\n" + "=" * 40)
    console.print("[bold green]Setup Complete![/bold green]")
    console.print("=" * 40)
    console.print("\nConfiguration saved to:")
    console.print(f"  Config:  [cyan]{CONFIG_DIR}/config.yaml[/cyan]")
    console.print(f"  Secrets: [cyan]{CONFIG_DIR}/.env[/cyan] (keep safe!)")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Start LiteLLM: [cyan]k-lean start[/cyan]")
    console.print("  2. Verify models: [cyan]k-lean models --health[/cyan]")
    console.print("  3. Test in Claude: [cyan]healthcheck[/cyan]")


if __name__ == "__main__":
    main()
