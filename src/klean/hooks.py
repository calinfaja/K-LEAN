#!/usr/bin/env python3
"""K-LEAN Hooks for Claude Code Integration.

Cross-platform Python hooks that replace shell-based hooks.
Each hook function is an entry point that can be called by Claude Code.

Hooks:
- session_start: Auto-start LiteLLM proxy and Knowledge Server
- prompt_handler: Dispatch keywords (FindKnowledge, SaveInfo, etc.)
- post_bash: Detect git commits, log to timeline
- post_web: Smart capture for URLs

Hook Protocol:
- Read JSON from stdin with event-specific fields
- Output JSON to stdout (or plain text for context)
- Exit codes: 0=success, 2=block with reason
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from klean.platform import (
    cleanup_stale_files,
    find_project_root,
    get_kb_port_file,
    spawn_background,
)


# =============================================================================
# Hook I/O Helpers
# =============================================================================


def _read_input() -> dict[str, Any]:
    """Read JSON input from stdin.

    Returns:
        Parsed JSON dict, or empty dict on error.
    """
    try:
        data = sys.stdin.read()
        if data:
            return json.loads(data)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _output_json(data: dict[str, Any]) -> None:
    """Output JSON response to stdout.

    Args:
        data: Dict to output as JSON.
    """
    print(json.dumps(data))


def _output_text(text: str) -> None:
    """Output plain text to stdout.

    Args:
        text: Text to output.
    """
    print(text)


def _debug_log(msg: str) -> None:
    """Log debug message to stderr if KLEAN_DEBUG is set.

    Args:
        msg: Message to log.
    """
    if os.environ.get("KLEAN_DEBUG"):
        print(f"[klean-hook] {msg}", file=sys.stderr)


# =============================================================================
# Service Management
# =============================================================================


def _is_litellm_running() -> bool:
    """Check if LiteLLM proxy is running.

    Returns:
        True if LiteLLM responds on localhost:4000.
    """
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(("127.0.0.1", 4000))
        sock.close()
        return result == 0
    except Exception:
        return False


def _start_litellm() -> bool:
    """Start LiteLLM proxy if config exists.

    Returns:
        True if started successfully.
    """
    config_dir = Path.home() / ".config" / "litellm"
    config_file = config_dir / "config.yaml"
    env_file = config_dir / ".env"

    if not config_file.exists():
        _debug_log("LiteLLM config not found")
        return False

    if not env_file.exists():
        _debug_log("LiteLLM .env not found")
        return False

    try:
        # Start LiteLLM in background
        cmd = [
            sys.executable,
            "-m",
            "litellm",
            "--config",
            str(config_file),
            "--port",
            "4000",
        ]
        spawn_background(cmd)
        _debug_log("Started LiteLLM proxy")
        return True
    except Exception as e:
        _debug_log(f"Failed to start LiteLLM: {e}")
        return False


def _is_kb_server_running(project_path: Path) -> bool:
    """Check if Knowledge Server is running for project.

    Args:
        project_path: Path to project root.

    Returns:
        True if server responds.
    """
    import socket

    port_file = get_kb_port_file(project_path)
    if not port_file.exists():
        return False

    try:
        port = int(port_file.read_text().strip())
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect(("127.0.0.1", port))
        sock.sendall(b'{"cmd":"ping"}')
        response = sock.recv(1024).decode()
        sock.close()
        return '"pong"' in response
    except Exception:
        return False


def _start_kb_server(project_path: Path) -> bool:
    """Start Knowledge Server for project.

    Args:
        project_path: Path to project root.

    Returns:
        True if started successfully.
    """
    kb_dir = project_path / ".knowledge-db"
    if not kb_dir.exists():
        return False

    # Clean up stale files first
    cleanup_stale_files(project_path)

    # Check if already running
    if _is_kb_server_running(project_path):
        return True

    try:
        # Find knowledge-server.py
        scripts_dir = Path(__file__).parent / "data" / "scripts"
        server_script = scripts_dir / "knowledge-server.py"

        if not server_script.exists():
            # Try installed location
            server_script = Path.home() / ".claude" / "scripts" / "knowledge-server.py"

        if not server_script.exists():
            _debug_log("knowledge-server.py not found")
            return False

        cmd = [sys.executable, str(server_script), "start", str(project_path)]
        spawn_background(cmd, cwd=project_path)
        _debug_log(f"Started KB server for {project_path}")
        return True
    except Exception as e:
        _debug_log(f"Failed to start KB server: {e}")
        return False


# =============================================================================
# Hook Entry Points
# =============================================================================


def session_start() -> None:
    """SessionStart hook - auto-start LiteLLM + KB server.

    Input: {"source": "startup"|"resume"|"clear"|"compact", ...}
    Output: Plain text context or JSON with additionalContext

    Exit code: 0 always (don't block session start)
    """
    input_data = _read_input()
    source = input_data.get("source", "startup")
    _debug_log(f"session_start: source={source}")

    messages = []

    # Start LiteLLM if not running
    if not _is_litellm_running():
        if _start_litellm():
            messages.append("LiteLLM proxy started")
        else:
            # Check what's missing
            config_dir = Path.home() / ".config" / "litellm"
            if not (config_dir / "config.yaml").exists():
                messages.append("[WARN] LiteLLM config not found. Run: kln setup")
            elif not (config_dir / ".env").exists():
                messages.append("[WARN] LiteLLM .env not found. Add API keys.")

    # Start KB server for current project
    project_root = find_project_root()
    if project_root:
        kb_dir = project_root / ".knowledge-db"
        if kb_dir.exists():
            if not _is_kb_server_running(project_root):
                if _start_kb_server(project_root):
                    messages.append(f"Knowledge server started for {project_root.name}")

    # Output status
    if messages:
        _output_text("K-LEAN: " + "; ".join(messages))

    sys.exit(0)


def prompt_handler() -> None:
    """UserPromptSubmit hook - keyword dispatch.

    Input: {"prompt": "user text", ...}
    Output: {"decision": "block", "reason": "..."} OR context text

    Handles keywords:
    - FindKnowledge <query> - Search knowledge DB
    - SaveInfo <url> - Smart save with LLM evaluation
    - InitKB - Initialize knowledge DB
    - asyncReview - Background review

    Exit code: 0=continue, 2=block with reason
    """
    input_data = _read_input()

    # Extract prompt from various possible fields
    prompt = (
        input_data.get("prompt") or input_data.get("message") or input_data.get("content") or ""
    )

    if not prompt or prompt == "null":
        sys.exit(0)

    _debug_log(f"prompt_handler: {prompt[:50]}...")

    prompt_lower = prompt.lower().strip()

    # === FindKnowledge <query> ===
    if prompt_lower.startswith("findknowledge "):
        query = prompt[14:].strip()  # Remove "FindKnowledge "
        if query:
            result = _handle_find_knowledge(query)
            if result:
                _output_json({"additionalContext": result})
        sys.exit(0)

    # === SaveInfo <url> ===
    if prompt_lower.startswith("saveinfo "):
        content = prompt[9:].strip()  # Remove "SaveInfo "
        if content:
            result = _handle_save_info(content)
            _output_json({"systemMessage": result})
        sys.exit(0)

    # === InitKB ===
    if prompt_lower == "initkb" or prompt_lower.startswith("initkb "):
        result = _handle_init_kb()
        _output_json({"systemMessage": result})
        sys.exit(0)

    # === asyncReview / asyncConsensus ===
    if "asyncreview" in prompt_lower or "asyncconsensus" in prompt_lower:
        result = _handle_async_review(prompt)
        _output_json({"systemMessage": result})
        sys.exit(0)

    # No keyword matched - continue normally
    sys.exit(0)


def post_bash() -> None:
    """PostToolUse (Bash) hook - git commit detection.

    Input: {"tool_name": "Bash", "tool_input": {"command": "..."}, ...}
    Output: {"systemMessage": "..."} for notifications

    Detects git commits and logs to timeline.

    Exit code: 0 always
    """
    input_data = _read_input()

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    _debug_log(f"post_bash: {command[:50]}...")

    # Detect git commit
    if "git commit" in command and "-m" in command:
        _log_to_timeline("commit", f"Git commit: {command[:100]}")

    sys.exit(0)


def post_web() -> None:
    """PostToolUse (Web*) hook - smart web capture.

    Input: {"tool_name": "WebFetch", "tool_input": {"url": "..."}, ...}

    Optionally triggers smart capture for documentation URLs.

    Exit code: 0 always
    """
    input_data = _read_input()

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    url = tool_input.get("url", "")

    if not url:
        sys.exit(0)

    _debug_log(f"post_web: {tool_name} {url[:50]}...")

    # Could trigger smart capture for documentation URLs
    # For now, just log
    if any(pattern in url for pattern in ["docs.", "/docs/", "documentation"]):
        _log_to_timeline("web", f"Fetched docs: {url}")

    sys.exit(0)


# =============================================================================
# Handler Functions
# =============================================================================


def _handle_find_knowledge(query: str) -> str:
    """Handle FindKnowledge keyword.

    Args:
        query: Search query.

    Returns:
        Search results as formatted string.
    """
    project_root = find_project_root()
    if not project_root:
        return "No project found"

    kb_dir = project_root / ".knowledge-db"
    if not kb_dir.exists():
        return "Knowledge DB not initialized. Use InitKB to create it."

    # Try to query via server
    if _is_kb_server_running(project_root):
        import socket

        try:
            port_file = get_kb_port_file(project_root)
            port = int(port_file.read_text().strip())

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(("127.0.0.1", port))
            sock.sendall(json.dumps({"cmd": "search", "query": query, "limit": 5}).encode())
            response = sock.recv(65536).decode()
            sock.close()

            data = json.loads(response)
            results = data.get("results", [])

            if not results:
                return f"No results found for: {query}"

            output = [f"Found {len(results)} results for '{query}':\n"]
            for r in results:
                score = r.get("score", 0)
                title = r.get("title", r.get("id", "?"))
                content = r.get("content", "")[:200]
                output.append(f"  [{score:.2f}] {title}")
                if content:
                    output.append(f"    {content}...")

            return "\n".join(output)
        except Exception as e:
            return f"Search error: {e}"

    return "Knowledge server not running. Start it with: kln start"


def _handle_save_info(content: str) -> str:
    """Handle SaveInfo keyword.

    Args:
        content: URL or text to save.

    Returns:
        Result message.
    """
    project_root = find_project_root()
    if not project_root:
        return "No project found"

    # Check if it's a URL
    if content.startswith(("http://", "https://")):
        # Would trigger smart capture here
        return f"SaveInfo: URL capture not yet implemented in Python hooks. URL: {content}"

    return "SaveInfo: Expected a URL"


def _handle_init_kb() -> str:
    """Handle InitKB keyword.

    Returns:
        Result message.
    """
    project_root = find_project_root()
    if not project_root:
        return "No project found"

    kb_dir = project_root / ".knowledge-db"
    if kb_dir.exists():
        return f"Knowledge DB already exists at {kb_dir}"

    try:
        kb_dir.mkdir(exist_ok=True)
        (kb_dir / "entries.jsonl").touch()
        return f"Knowledge DB initialized at {kb_dir}"
    except Exception as e:
        return f"Failed to initialize: {e}"


def _handle_async_review(prompt: str) -> str:
    """Handle async review keywords.

    Args:
        prompt: Original prompt.

    Returns:
        Result message.
    """
    # Would trigger background review here
    return "Async review triggered (implementation pending)"


def _log_to_timeline(event_type: str, message: str) -> None:
    """Log event to project timeline.

    Args:
        event_type: Type of event (commit, web, etc.)
        message: Event message.
    """
    project_root = find_project_root()
    if not project_root:
        return

    kb_dir = project_root / ".knowledge-db"
    if not kb_dir.exists():
        return

    timeline_file = kb_dir / "timeline.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(timeline_file, "a") as f:
            f.write(f"[{timestamp}] [{event_type}] {message}\n")
    except Exception:
        pass


# =============================================================================
# CLI Entry Points (for testing)
# =============================================================================


def main() -> None:
    """Main entry point for CLI testing."""
    if len(sys.argv) < 2:
        print("Usage: python -m klean.hooks <hook_name>")
        print("Hooks: session_start, prompt_handler, post_bash, post_web")
        sys.exit(1)

    hook_name = sys.argv[1]

    if hook_name == "session_start":
        session_start()
    elif hook_name == "prompt_handler":
        prompt_handler()
    elif hook_name == "post_bash":
        post_bash()
    elif hook_name == "post_web":
        post_web()
    else:
        print(f"Unknown hook: {hook_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
