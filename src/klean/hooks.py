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

# Import infer_type from kb_utils (in data/scripts/ or ~/.claude/scripts/)
try:
    from klean.data.scripts.kb_utils import infer_type
except ImportError:
    # Fallback: try from installed location
    _scripts_dir = Path.home() / ".claude" / "scripts"
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    try:
        from kb_utils import infer_type
    except ImportError:
        # Inline fallback if kb_utils not available
        def infer_type(title: str, insight: str) -> str:
            """Minimal fallback type inference."""
            text = f"{title} {insight}".lower()
            if any(w in text for w in ["don't", "avoid", "bug", "fails", "error"]):
                return "warning"
            if any(w in text for w in ["fixed", "solved", "solution"]):
                return "solution"
            if any(w in text for w in ["use ", "prefer", "pattern"]):
                return "pattern"
            return "finding"


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
    except (json.JSONDecodeError, OSError):
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
# Git Helpers
# =============================================================================


def _get_current_branch() -> str:
    """Get current git branch name.

    Returns:
        Branch name or empty string if not in a git repo.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


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
# KB Server Communication
# =============================================================================


def _kb_send(
    project_root: Path,
    cmd: dict,
    *,
    timeout: float = 2.0,
    recv_size: int = 1024,
) -> dict | None:
    """Send command to KB server and return parsed response.

    Args:
        project_root: Project root path.
        cmd: Command dict to send (e.g. {"cmd": "add", "entry": {...}}).
        timeout: Socket timeout in seconds.
        recv_size: Max bytes to receive.

    Returns:
        Parsed JSON response dict, or None on failure.
    """
    import socket

    try:
        port_file = get_kb_port_file(project_root)
        port = int(port_file.read_text().strip())

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps(cmd).encode())
        response = sock.recv(recv_size).decode()
        sock.close()
        return json.loads(response)
    except Exception:
        return None


# =============================================================================
# Hook Entry Points
# =============================================================================


def session_start() -> None:
    """SessionStart hook - auto-start LiteLLM + KB server + inject context.

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

            # Create journal entry on startup
            if source == "startup" and _is_kb_server_running(project_root):
                _create_session_journal(project_root)

            # Inject recent/important KB entries as context (only on startup/resume)
            if source in ("startup", "resume"):
                context = _get_kb_context(project_root)
                if context:
                    messages.append(context)

    # Output status
    if messages:
        _output_text("K-LEAN: " + "; ".join(messages))

    sys.exit(0)


def _create_session_journal(project_root: Path) -> None:
    """Create a journal entry when a session starts.

    Args:
        project_root: Project root path.
    """
    branch = _get_current_branch()
    branch_info = f" on {branch}" if branch else ""

    entry = {
        "title": f"Session started{branch_info}",
        "insight": f"New coding session started for {project_root.name}{branch_info}",
        "type": "journal",
        "priority": "low",
        "keywords": ["session", "start", project_root.name],
        "source": f"session:{datetime.now().strftime('%Y-%m-%d')}",
        "timestamp": datetime.now().isoformat(),
        "branch": branch,
    }

    result = _kb_send(project_root, {"cmd": "add", "entry": entry})
    if result:
        _debug_log("Created session journal entry")
    else:
        _debug_log("Failed to create session journal")


def pre_compact() -> None:
    """PreCompact hook - persist session log before context compaction.

    Input: {"transcript_path": "...", "trigger": "auto"|"manual", "cwd": "..."}
    Output: None (informational only, cannot block compaction)

    Exit code: 0 always
    """
    input_data = _read_input()
    trigger = input_data.get("trigger", "")
    transcript_path = input_data.get("transcript_path", "")

    _debug_log(f"pre_compact: trigger={trigger}")

    # Only run on auto-compact (natural session boundary)
    if trigger != "auto":
        sys.exit(0)

    project_root = find_project_root()
    if not project_root:
        sys.exit(0)

    memory_dir = project_root / ".serena" / "memories"
    if not memory_dir.exists():
        _debug_log("pre_compact: no .serena/memories/ directory")
        sys.exit(0)

    result = _persist_session_log(project_root, transcript_path)
    _debug_log(f"pre_compact: {result}")
    sys.exit(0)


def _persist_session_log(project_root: Path, transcript_path: str = "") -> str:
    """Generate session log entry from transcript + git log + KB via Claude Haiku.

    Args:
        project_root: Project root path.
        transcript_path: Path to conversation transcript JSONL.

    Returns:
        Status message.
    """
    import subprocess

    # 1. Extract context from transcript
    user_messages = _extract_user_messages(transcript_path) if transcript_path else ""

    # 2. Git log (concrete facts)
    git_log = ""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=6am"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5,
        )
        git_log = result.stdout.strip()
    except Exception:
        pass

    # 3. KB entries created today (findings, warnings, solutions)
    kb_entries = _get_today_kb_entries(project_root)

    # 4. Current branch
    branch = _get_current_branch() or "unknown"

    if not user_messages and not git_log:
        return "No activity to log"

    # 5. Build prompt for Haiku
    prompt = (
        "Summarize this coding session as a concise changelog entry.\n\n"
        f"User requests/questions during this session:\n{user_messages[:3000]}\n\n"
        f"Git commits:\n{git_log[:500]}\n\n"
    )
    if kb_entries:
        prompt += f"Knowledge captured this session:\n{kb_entries[:1500]}\n\n"
    prompt += (
        f"Branch: {branch}\n\n"
        "Output ONLY a markdown section in this exact format (no extra text):\n"
        f"## HH:MM - HH:MM | {branch}\n"
        "- <what was done, 3-5 bullets, be specific>\n"
        '- Commits: <commit messages or "none">\n'
        "- Status: <completed|in-progress|blocked>\n"
        '- Left: <unfinished items or "none">\n'
    )

    # 6. Call Haiku
    summary = _call_claude_haiku(prompt)
    if not summary:
        return "Claude Haiku not available"

    # 7. Append to session log file
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = project_root / ".serena" / "memories" / f"session-log-{today}.md"

    try:
        if memory_file.exists():
            content = memory_file.read_text() + "\n\n" + summary
        else:
            content = f"# Session Log: {today}\n\n{summary}"
        memory_file.write_text(content)
    except Exception as e:
        return f"Failed to write session log: {e}"

    # 8. Create searchable KB entry (idempotent)
    _create_session_kb_entry(project_root, branch, summary)

    return f"Session log updated: session-log-{today}"


def _extract_user_messages(transcript_path: str, limit: int = 10) -> str:
    """Extract last N user messages from transcript JSONL.

    Args:
        transcript_path: Path to the transcript JSONL file.
        limit: Max number of messages to extract.

    Returns:
        Formatted string of user messages.
    """
    path = Path(transcript_path)
    if not path.exists():
        return ""

    user_msgs: list[str] = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("type") != "user" or "message" not in obj:
                    continue
                content = obj["message"].get("content", "")
                if not isinstance(content, str) or len(content) < 10:
                    continue
                # Skip CLI command messages
                if "<local-command" in content or "<command-name>" in content:
                    continue
                clean = content[:200].strip()
                if clean:
                    user_msgs.append(clean)
    except Exception:
        return ""

    recent = user_msgs[-limit:]
    return "\n".join(f"- {msg}" for msg in recent)


def _get_today_kb_entries(project_root: Path) -> str:
    """Get KB entries created today (findings, warnings, solutions, patterns).

    Args:
        project_root: Project root path.

    Returns:
        Formatted list of today's KB entries, or empty string.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    resp = _kb_send(
        project_root,
        {"cmd": "search_by_date", "start": today, "end": today},
        recv_size=8192,
    )
    if not resp or resp.get("status") != "ok":
        return ""

    entries = resp.get("entries", [])
    useful_types = {"finding", "warning", "solution", "pattern", "lesson", "best-practice"}
    lines = []
    for e in entries:
        etype = e.get("type", "")
        if etype not in useful_types:
            continue
        title = e.get("title", "")[:100]
        lines.append(f"- [{etype}] {title}")

    return "\n".join(lines[:15])


def _create_session_kb_entry(project_root: Path, branch: str, summary: str) -> None:
    """Create a searchable KB entry from the session log summary.

    Idempotent: skips if a session entry for today already exists.
    Includes related_to path to the full session log file for graph traversal.

    Args:
        project_root: Project root path.
        branch: Current git branch.
        summary: Haiku-generated session summary markdown.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    source = f"session-log:{today}"

    # Idempotency check: search for existing session entry with this source
    resp = _kb_send(
        project_root,
        {"cmd": "search", "query": source, "limit": 3},
        recv_size=4096,
    )
    if resp and resp.get("status") == "ok":
        for e in resp.get("results", []):
            if e.get("source") == source:
                return  # Already exists

    # Extract first 3-5 bullet lines as insight
    bullets = [ln.strip() for ln in summary.split("\n") if ln.strip().startswith("- ")]
    insight = "\n".join(bullets[:5]) if bullets else summary[:300]

    # Full path to session log for graph traversal
    log_path = str(project_root / ".serena" / "memories" / f"session-log-{today}.md")

    entry = {
        "title": f"Session: {today} on {branch}",
        "insight": insight,
        "type": "session",
        "priority": "low",
        "keywords": ["session", "log", branch, today],
        "source": source,
        "branch": branch,
        "related_to": [log_path],
    }
    _kb_send(project_root, {"cmd": "add", "entry": entry})


def _call_claude_haiku(prompt: str) -> str:
    """Call Claude Haiku via claude CLI print mode ($0, uses subscription).

    Args:
        prompt: The prompt to send to Haiku.

    Returns:
        Haiku's response text, or empty string on failure.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "haiku", "--no-session-persistence"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _read_latest_session_log(project_root: Path) -> str:
    """Read the most recent session log from .serena/memories/.

    Args:
        project_root: Project root path.

    Returns:
        Content of the most recent session-log-*.md file, or empty string.
    """
    memory_dir = project_root / ".serena" / "memories"
    if not memory_dir.exists():
        return ""

    logs = sorted(memory_dir.glob("session-log-*.md"), reverse=True)
    if not logs:
        return ""

    try:
        return logs[0].read_text()
    except Exception:
        return ""


def _format_entries_toon(entries: list) -> str:
    """Format KB entries in TOON format for token reduction.

    Args:
        entries: List of KB entry dicts.

    Returns:
        TOON formatted string.
    """
    from toon import encode

    # Select minimal fields for injection
    # Short keys: t=title, y=type, p=priority, k=keywords
    minimal = []
    for e in entries:
        entry = {
            "t": e.get("title", "")[:80],
            "y": e.get("type", "finding"),
            "k": e.get("keywords", e.get("tags", []))[:5],
        }
        # Include priority for warnings
        if e.get("type") == "warning":
            entry["p"] = e.get("priority", "medium")
        minimal.append(entry)

    return encode(minimal)


def _get_kb_context(project_root: Path) -> str:
    """Get session-aware KB context for injection.

    Structure:
    1. Previous session log (if exists)
    2. Grouped warnings with count
    3. Recent entries in TOON format (up to 8)
    4. Serena prompt for session history

    Args:
        project_root: Project root path.

    Returns:
        Formatted context string or empty string.
    """
    serena_prompt = "[>] Session history: mcp__serena__read_memory lessons-learned"

    if not _is_kb_server_running(project_root):
        return serena_prompt

    data = _kb_send(project_root, {"cmd": "recent", "limit": 50}, recv_size=65536)
    all_entries = (data or {}).get("entries", [])

    if not all_entries:
        return serena_prompt

    parts = []

    # 1. Read latest session log from Serena memories
    session_log = _read_latest_session_log(project_root)
    if session_log:
        sections = session_log.split("\n## ")
        if len(sections) > 1:
            last = sections[-1][:200].strip()
            parts.append(f"[SESSION] {last}")

    # 2. Grouped warnings (critical/high)
    warnings = [
        e for e in all_entries
        if e.get("type") == "warning" and e.get("priority") in ("critical", "high")
    ]
    if warnings:
        count = len(warnings)
        titles = [w.get("title", "?")[:60] for w in warnings[:2]]
        warning_str = " | ".join(f'"{t}"' for t in titles)
        if count > 2:
            warning_str += f" | +{count - 2} more"
        parts.append(f"[!] WARNINGS ({count}): {warning_str}")

    # 3. Recent entries (non-warning), TOON format, limit 8
    warning_ids = {e.get("id") for e in warnings}
    recent = [
        e for e in all_entries
        if e.get("id") not in warning_ids and e.get("type") not in ("session", "journal")
    ][:8]

    if recent:
        toon_recent = _format_entries_toon(recent)
        parts.append(f"[KB] RECENT:\n{toon_recent}")

    # 4. Serena prompt
    parts.append(serena_prompt)

    return "\n\n".join(parts)


def prompt_handler() -> None:
    """UserPromptSubmit hook - keyword dispatch.

    Input: {"prompt": "user text", ...}
    Output: {"decision": "block", "reason": "..."} OR context text

    Handles keywords:
    - FindKnowledge <query> - Search knowledge DB (compact index)
    - FindKnowledgeDetail <id> - Full entry by ID
    - SaveInfo <url> - Smart save with LLM evaluation
    - InitKB - Initialize knowledge DB

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

    # === FindKnowledgeDetail <id> ===
    if prompt_lower.startswith("findknowledgedetail "):
        entry_id = prompt[19:].strip()
        if entry_id:
            result = _handle_find_knowledge_detail(entry_id)
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

    # No keyword matched - continue normally
    sys.exit(0)


def post_bash() -> None:
    """PostToolUse (Bash) hook - git commit detection and capture.

    Input: {"tool_name": "Bash", "tool_input": {"command": "..."}, ...}
    Output: {"systemMessage": "..."} for notifications

    Detects git commits and saves them to KB.

    Exit code: 0 always
    """
    input_data = _read_input()

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    tool_result = input_data.get("tool_result", {})
    exit_code = tool_result.get("exitCode") if isinstance(tool_result, dict) else None

    _debug_log(f"post_bash: {command[:50]}...")

    # Detect git commit and capture to KB
    if "git commit" in command and "-m" in command:
        _capture_git_commit()

    # Detect test failures (non-zero exit)
    elif exit_code and exit_code != 0:
        test_cmds = ["pytest", "npm test", "cargo test", "go test", "jest", "vitest"]
        if any(tc in command for tc in test_cmds):
            _capture_bash_event(
                command, tool_result,
                entry_type="finding",
                priority="high",
                prefix="Test failure",
                extra_keywords=["test", "failure"],
            )

        # Detect build errors (non-zero exit)
        build_cmds = ["make", "cargo build", "npm run build", "go build", "tsc", "gcc", "g++"]
        if any(bc in command for bc in build_cmds):
            _capture_bash_event(
                command, tool_result,
                entry_type="finding",
                priority="high",
                prefix="Build error",
                extra_keywords=["build", "error"],
            )

    # Detect package installs
    elif any(pc in command for pc in ["pip install", "npm install", "cargo add"]):
        _capture_bash_event(
            command, tool_result,
            entry_type="finding",
            priority="low",
            prefix="Package install",
            extra_keywords=["dependency", "install"],
        )

    sys.exit(0)


def _capture_git_commit() -> None:
    """Capture the latest git commit to Knowledge DB.

    Extracts commit hash, message, and changed files.
    Saves as a 'commit' type entry.
    """
    import subprocess

    project_root = find_project_root()
    if not project_root:
        return

    try:
        # Get commit info: hash|subject|author
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H|%s|%an"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return

        parts = result.stdout.strip().split("|", 2)
        if len(parts) < 2:
            return

        full_hash = parts[0]
        short_hash = full_hash[:8]
        commit_msg = parts[1] if len(parts) > 1 else ""
        author = parts[2] if len(parts) > 2 else ""

        # Get changed files with stat
        result = subprocess.run(
            ["git", "diff", "--stat", "--name-only", "HEAD~1", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        changed_files = result.stdout.strip().split("\n") if result.returncode == 0 else []
        changed_files = [f for f in changed_files if f][:10]  # Limit to 10 files

        # Log to timeline
        _log_to_timeline("commit", f"[{short_hash}] {commit_msg[:60]}")

        # Save to KB if server is running
        if not _is_kb_server_running(project_root):
            return

        # Build insight with changed files for searchability
        files_str = ", ".join(changed_files[:5]) if changed_files else "no files"
        insight = f"Git commit {short_hash} by {author}: {commit_msg}. Changed: {files_str}"

        # V3.1 Schema
        entry = {
            "title": f"Commit: {commit_msg[:80]}",
            "insight": insight,
            "type": "commit",
            "priority": "low",
            "keywords": ["git", "commit"] + _extract_commit_tags(commit_msg) + changed_files[:5],
            "source": f"git:{full_hash}",
            "timestamp": datetime.now().isoformat(),
            "branch": _get_current_branch(),
        }

        _kb_send(project_root, {"cmd": "add", "entry": entry})
        _debug_log(f"Captured commit {short_hash} to KB")
    except Exception as e:
        _debug_log(f"Failed to capture commit: {e}")


def _capture_bash_event(
    command: str,
    tool_result: Any,
    entry_type: str,
    priority: str,
    prefix: str,
    extra_keywords: list[str],
) -> None:
    """Capture a bash event (test failure, build error, etc.) to Knowledge DB.

    Args:
        command: The bash command that was run.
        tool_result: Tool result dict (may contain stdout/stderr).
        entry_type: KB entry type (finding, warning, etc.).
        priority: KB entry priority.
        prefix: Title prefix (e.g., "Test failure").
        extra_keywords: Additional keywords for the entry.
    """
    project_root = find_project_root()
    if not project_root or not _is_kb_server_running(project_root):
        return

    # Truncate command for title
    cmd_short = command[:80].replace("\n", " ")
    # Get stderr/stdout snippet for insight
    stderr = ""
    stdout = ""
    if isinstance(tool_result, dict):
        stderr = (tool_result.get("stderr") or "")[:300]
        stdout = (tool_result.get("stdout") or "")[:300]
    error_context = stderr or stdout or "No output captured"

    entry = {
        "title": f"{prefix}: {cmd_short}",
        "insight": f"{prefix} running '{cmd_short}': {error_context}",
        "type": entry_type,
        "priority": priority,
        "keywords": (extra_keywords + [command.split()[0]]) if command.split() else extra_keywords,
        "source": f"bash:{cmd_short[:60]}",
        "timestamp": datetime.now().isoformat(),
        "branch": _get_current_branch(),
    }

    result = _kb_send(project_root, {"cmd": "add", "entry": entry})
    if result:
        _debug_log(f"Captured {prefix} to KB")
    else:
        _debug_log(f"Failed to capture {prefix}")


def _extract_commit_tags(commit_msg: str) -> list[str]:
    """Extract tags from conventional commit message.

    Args:
        commit_msg: Git commit message.

    Returns:
        List of tags extracted from commit type/scope.
    """
    tags = []
    # Match conventional commit: type(scope)!: message
    if ":" in commit_msg:
        prefix = commit_msg.split(":")[0].lower()
        # Strip breaking change indicator "!" before parsing
        prefix = prefix.rstrip("!")
        # Extract type and scope
        if "(" in prefix:
            commit_type = prefix.split("(")[0]
            scope = prefix.split("(")[1].rstrip(")").rstrip("!")
            if commit_type:
                tags.append(commit_type)
            if scope:
                tags.append(scope)
        else:
            if prefix:
                tags.append(prefix)
    return tags[:3]  # Limit tags


def post_web() -> None:
    """PostToolUse (Web*) hook - smart web capture.

    Handles:
    - WebFetch: Direct URL fetches
    - WebSearch: Search results with URLs
    - mcp__tavily__*: Tavily search/extract with URLs
    - mcp__context7__*: Context7 documentation queries

    Input: {"tool_name": "...", "tool_input": {...}, "tool_result": {...}}

    Exit code: 0 always
    """
    input_data = _read_input()

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_result = input_data.get("tool_result", {})

    _debug_log(f"post_web: tool={tool_name}")

    urls = []

    # Extract URLs based on tool type
    if tool_name == "WebFetch":
        url = tool_input.get("url", "")
        if url:
            urls.append(url)

    elif tool_name == "WebSearch":
        # WebSearch returns search results
        # Extract URLs from result if present
        if isinstance(tool_result, dict):
            for item in tool_result.get("results", []):
                if isinstance(item, dict) and item.get("url"):
                    urls.append(item["url"])

    elif tool_name.startswith("mcp__tavily__"):
        # Tavily tools return results with url field
        if isinstance(tool_result, dict):
            for item in tool_result.get("results", []):
                if isinstance(item, dict) and item.get("url"):
                    urls.append(item["url"])

    elif tool_name.startswith("mcp__context7__"):
        # Context7 returns documentation - log the library being queried
        library_id = tool_input.get("libraryId", "")
        query = tool_input.get("query", "")
        if library_id:
            _log_to_timeline("docs", f"Context7: {library_id} - {query[:50]}")

    # Log documentation URLs and create KB entries for doc-pattern URLs
    doc_patterns = ["docs.", "/docs/", "documentation", "readme", "wiki", "guide",
                    "reference", "api.", "/api/", "tutorial"]
    project_root = find_project_root()

    for url in urls:
        url_lower = url.lower()
        if any(p in url_lower for p in doc_patterns):
            _log_to_timeline("web", f"Fetched docs: {url}")

            # Create KB entry for doc URLs
            if project_root and _is_kb_server_running(project_root):
                from urllib.parse import urlparse

                parsed = urlparse(url)
                domain = parsed.netloc
                path_summary = parsed.path.rstrip("/").split("/")[-1] or domain

                entry = {
                    "title": f"Docs: {domain} - {path_summary}",
                    "insight": f"Documentation reference captured from {tool_name}: {url}",
                    "type": "discovery",
                    "priority": "low",
                    "keywords": ["docs", "reference", domain, path_summary],
                    "source": url,
                    "timestamp": datetime.now().isoformat(),
                    "branch": _get_current_branch(),
                }

                if _kb_send(project_root, {"cmd": "add", "entry": entry}):
                    _debug_log(f"Captured doc URL to KB: {url[:60]}")
                else:
                    _debug_log(f"Failed to capture doc URL: {url[:60]}")

    sys.exit(0)


# =============================================================================
# Handler Functions
# =============================================================================


def _parse_find_knowledge_query(raw_query: str) -> tuple[str, dict]:
    """Parse FindKnowledge query with optional filters.

    Supports syntax like:
        FindKnowledge auth since:2026-02-01
        FindKnowledge auth branch:feature/auth
        FindKnowledge auth type:decision
        FindKnowledge auth since:2026-02-01 until:2026-02-07

    Args:
        raw_query: Raw query string after "FindKnowledge ".

    Returns:
        Tuple of (clean_query, filters_dict).
    """
    filters = {}
    query_parts = []

    for token in raw_query.split():
        if token.startswith("since:"):
            filters["date_from"] = token[6:]
        elif token.startswith("until:") or token.startswith("before:"):
            filters["date_to"] = token.split(":", 1)[1]
        elif token.startswith("branch:"):
            filters["branch"] = token[7:]
        elif token.startswith("type:"):
            filters["entry_type"] = token[5:]
        else:
            query_parts.append(token)

    return " ".join(query_parts), filters


def _handle_find_knowledge(query: str) -> str:
    """Handle FindKnowledge keyword with optional date/branch/type filters.

    Returns compact index with entry IDs for progressive disclosure.
    Use FindKnowledgeDetail <id> to get full entry details.

    Supports:
        FindKnowledge auth
        FindKnowledge auth since:2026-02-01
        FindKnowledge auth branch:feature/auth type:decision

    Args:
        query: Search query (may include filter tokens).

    Returns:
        Search results as compact formatted string.
    """
    project_root = find_project_root()
    if not project_root:
        return "No project found"

    kb_dir = project_root / ".knowledge-db"
    if not kb_dir.exists():
        return "Knowledge DB not initialized. Use InitKB to create it."

    # Parse filters from query
    clean_query, filters = _parse_find_knowledge_query(query)

    # Try to query via server
    if not _is_kb_server_running(project_root):
        return "Knowledge server not running. Start it with: kln start"

    cmd = {"cmd": "search", "query": clean_query or "*", "limit": 10}
    cmd.update(filters)

    data = _kb_send(project_root, cmd, timeout=5.0, recv_size=65536)
    if data is None:
        return "Search error: failed to communicate with KB server"

    results = data.get("results", [])

    if not results:
        filter_desc = f" (filters: {filters})" if filters else ""
        return f"No results found for: {clean_query}{filter_desc}"

    # Track usage for returned results
    result_ids = [r.get("id") for r in results if r.get("id")]
    if result_ids:
        _update_usage(project_root, result_ids)

    filter_desc = ""
    if filters:
        filter_desc = f" [filters: {', '.join(f'{k}={v}' for k, v in filters.items())}]"

    output = [f"Found {len(results)} results for '{clean_query}'{filter_desc}:\n"]
    for r in results:
        score = r.get("score", 0)
        title = r.get("title", r.get("id", "?"))
        entry_type = r.get("type", "")
        date = r.get("date", "")
        entry_id = r.get("id", "")

        meta_parts = []
        if entry_type:
            meta_parts.append(entry_type)
        if date:
            meta_parts.append(date)
        meta = f" ({', '.join(meta_parts)})" if meta_parts else ""

        id_str = f" [id:{entry_id[:8]}]" if entry_id else ""
        output.append(f"  [{score:.2f}] {title}{meta}{id_str}")

    output.append('\nTip: "FindKnowledgeDetail <id>" for full entry')
    return "\n".join(output)


def _handle_find_knowledge_detail(entry_id: str) -> str:
    """Fetch and display full details of a knowledge entry by ID.

    Supports both full UUIDs and short prefixes (8+ chars).

    Args:
        entry_id: Full or partial entry UUID.

    Returns:
        Formatted entry details or error message.
    """
    project_root = find_project_root()
    if not project_root:
        return "No project found"

    if not _is_kb_server_running(project_root):
        return "Knowledge server not running. Start it with: kln start"

    # Resolve entry: short ID prefix vs full UUID
    if len(entry_id) < 36:
        data = _kb_send(
            project_root, {"cmd": "recent", "limit": 200},
            timeout=3.0, recv_size=131072,
        )
        if not data:
            return f"Error fetching entry: {entry_id}"

        matches = [
            e for e in data.get("entries", [])
            if e.get("id", "").startswith(entry_id)
        ]
        if not matches:
            return f"No entry found matching ID prefix: {entry_id}"
        if len(matches) > 1:
            return f"Ambiguous ID prefix '{entry_id}', matches {len(matches)} entries"
        entry = matches[0]
    else:
        data = _kb_send(
            project_root, {"cmd": "get", "id": entry_id},
            timeout=3.0, recv_size=65536,
        )
        if not data or "error" in data:
            return f"Entry not found: {entry_id}"
        entry = data.get("entry", {})

    # Format full entry
    lines = [f"=== {entry.get('title', 'Untitled')} ==="]
    lines.append(f"Type: {entry.get('type', '?')} | Priority: {entry.get('priority', '?')}")
    lines.append(f"Date: {entry.get('date', '?')} | Branch: {entry.get('branch', '?')}")

    insight = entry.get("insight", entry.get("summary", ""))
    if insight:
        lines.append(f"\n{insight}")

    keywords = entry.get("keywords", entry.get("tags", []))
    if keywords:
        lines.append(f"\nKeywords: {', '.join(keywords)}")

    source = entry.get("source", "")
    if source:
        lines.append(f"Source: {source}")

    related = entry.get("related_to", [])
    if related:
        lines.append(f"Related: {', '.join(related[:5])}")

    lines.append(f"ID: {entry.get('id', '?')}")
    return "\n".join(lines)


def _update_usage(project_root: Path, entry_ids: list[str]) -> None:
    """Update usage stats for retrieved entries.

    Args:
        project_root: Project root path.
        entry_ids: List of entry IDs to update.
    """
    _kb_send(project_root, {"cmd": "update_usage", "ids": entry_ids})


def _handle_save_info(content: str) -> str:
    """Handle SaveInfo keyword - extract and save knowledge from URL.

    Uses LiteLLM with dynamic model discovery to extract key points.

    Args:
        content: URL to fetch and process.

    Returns:
        Result message.
    """
    project_root = find_project_root()
    if not project_root:
        return "No project found"

    # Check if it's a URL
    if not content.startswith(("http://", "https://")):
        return "SaveInfo: Expected a URL"

    url = content.strip()

    # Check if KB server is running
    if not _is_kb_server_running(project_root):
        return "SaveInfo: Knowledge server not running. Start with: kln start"

    try:
        # Fetch URL content
        import httpx

        _debug_log(f"SaveInfo: Fetching {url}")
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()

        # Get text content (strip HTML if needed)
        content_type = resp.headers.get("content-type", "")
        if "html" in content_type:
            # Simple HTML stripping - just get text
            import re

            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
        else:
            text = resp.text

        # Truncate for LLM
        text = text[:8000]

        # Get model from discovery
        model = _get_first_healthy_model()
        if not model:
            # Fallback: save raw URL without extraction
            return _save_url_raw(project_root, url)

        # Extract knowledge using LLM
        _debug_log(f"SaveInfo: Extracting with model {model}")
        extracted = _extract_from_url(url, text, model)

        if not extracted:
            return _save_url_raw(project_root, url)

        # Build V3 schema entry
        title = extracted.get("title", url[:60])
        insight = extracted.get("insight", text[:500])

        # Auto-infer type from content using centralized logic
        entry_type = infer_type(title, insight)

        entry = {
            "title": title,
            "insight": insight,
            "type": entry_type,
            "priority": "medium",
            "keywords": extracted.get("keywords", ["web"]),
            "source": url,
        }

        # Save to KB
        result = _kb_send(project_root, {"cmd": "add", "entry": entry}, timeout=5.0)
        if result and result.get("status") == "ok":
            title_short = entry["title"][:50]
            return f"SaveInfo: Saved '{title_short}' from {url}"
        else:
            error = (result or {}).get("error", "unknown")
            return f"SaveInfo: Failed to save - {error}"

    except httpx.HTTPError as e:
        return f"SaveInfo: Failed to fetch URL - {e}"
    except Exception as e:
        _debug_log(f"SaveInfo error: {e}")
        return f"SaveInfo: Error processing URL - {e}"


def _get_first_healthy_model() -> str | None:
    """Get first available model from LiteLLM using dynamic discovery.

    Returns:
        Model name or None if LiteLLM not available.
    """
    try:
        import httpx

        resp = httpx.get("http://localhost:4000/v1/models", timeout=3)
        if resp.status_code == 200:
            models = [m["id"] for m in resp.json().get("data", [])]
            return models[0] if models else None
    except Exception:
        pass
    return None


def _extract_from_url(url: str, text: str, model: str) -> dict | None:
    """Extract knowledge from URL content using LLM.

    Args:
        url: Source URL.
        text: Page content.
        model: LiteLLM model to use.

    Returns:
        Dict with V3 schema fields: title, insight, keywords.
    """
    try:
        import httpx

        prompt = f"""Extract knowledge from this web page content. Return JSON only.

URL: {url}

Content:
{text[:6000]}

Return this exact JSON structure:
{{
  "title": "Short descriptive title (max 80 chars)",
  "insight": "2-4 sentence explanation of the key information and why it matters. Be specific and actionable.",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}

JSON:"""

        resp = httpx.post(
            "http://localhost:4000/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            return None

        content = resp.json()["choices"][0]["message"]["content"]

        # Handle thinking models that return in reasoning_content
        if not content:
            content = resp.json()["choices"][0]["message"].get("reasoning_content", "")

        # Extract JSON from response
        import re

        json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

    except Exception as e:
        _debug_log(f"LLM extraction failed: {e}")

    return None


def _save_url_raw(project_root: Path, url: str) -> str:
    """Save URL without LLM extraction (fallback).

    Args:
        project_root: Project root path.
        url: URL to save.

    Returns:
        Result message.
    """
    entry = {
        "title": f"Web: {url[:60]}",
        "insight": f"URL saved for reference: {url}",
        "type": "finding",
        "priority": "low",
        "keywords": ["web", "url"],
        "source": url,
    }

    result = _kb_send(project_root, {"cmd": "add", "entry": entry}, timeout=5.0)
    if result:
        return f"SaveInfo: Saved URL (no LLM extraction): {url}"
    return "SaveInfo: Failed to save URL"


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
        print("Hooks: session_start, prompt_handler, post_bash, post_web, pre_compact")
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
    elif hook_name == "pre_compact":
        pre_compact()
    else:
        print(f"Unknown hook: {hook_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
