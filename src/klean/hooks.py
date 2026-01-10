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

            # Inject recent/important KB entries as context (only on startup/resume)
            if source in ("startup", "resume"):
                context = _get_kb_context(project_root)
                if context:
                    messages.append(context)

    # Output status
    if messages:
        _output_text("K-LEAN: " + "; ".join(messages))

    sys.exit(0)


def _get_kb_context(project_root: Path) -> str:
    """Get recent/important KB entries for context injection.

    Args:
        project_root: Project root path.

    Returns:
        Formatted context string or empty string.
    """
    import socket

    if not _is_kb_server_running(project_root):
        return ""

    try:
        port_file = get_kb_port_file(project_root)
        port = int(port_file.read_text().strip())

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "recent", "limit": 3}).encode())
        response = sock.recv(65536).decode()
        sock.close()

        data = json.loads(response)
        entries = data.get("entries", [])

        if not entries:
            return ""

        # Format as brief context
        lines = ["Recent learnings:"]
        for e in entries:
            title = e.get("title", "")[:60]
            entry_type = e.get("type", "lesson")
            lines.append(f"  [{entry_type}] {title}")

        return "\n".join(lines)
    except Exception:
        return ""


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

    _debug_log(f"post_bash: {command[:50]}...")

    # Detect git commit and capture to KB
    if "git commit" in command and "-m" in command:
        _capture_git_commit()

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

        commit_hash = parts[0][:8]  # Short hash
        commit_msg = parts[1] if len(parts) > 1 else ""
        author = parts[2] if len(parts) > 2 else ""

        # Get changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        changed_files = result.stdout.strip().split("\n") if result.returncode == 0 else []
        changed_files = [f for f in changed_files if f][:10]  # Limit to 10 files

        # Log to timeline
        _log_to_timeline("commit", f"[{commit_hash}] {commit_msg[:60]}")

        # Save to KB if server is running
        if not _is_kb_server_running(project_root):
            return

        import socket

        entry = {
            "title": f"Commit: {commit_msg[:80]}",
            "summary": f"Git commit {commit_hash} by {author}: {commit_msg}",
            "type": "commit",
            "source": "git",
            "source_path": f"git:{commit_hash}",
            "tags": ["git", "commit"] + _extract_commit_tags(commit_msg),
            "key_concepts": changed_files[:5],
            "priority": "low",
            "quality": "medium",
        }

        port_file = get_kb_port_file(project_root)
        port = int(port_file.read_text().strip())

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "add", "entry": entry}).encode())
        sock.recv(1024)
        sock.close()

        _debug_log(f"Captured commit {commit_hash} to KB")
    except Exception as e:
        _debug_log(f"Failed to capture commit: {e}")


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

            # Track usage for returned results
            result_ids = [r.get("id") for r in results if r.get("id")]
            if result_ids:
                _update_usage(project_root, result_ids)

            output = [f"Found {len(results)} results for '{query}':\n"]
            for r in results:
                score = r.get("score", 0)
                title = r.get("title", r.get("id", "?"))
                summary = r.get("summary", "")[:200]
                output.append(f"  [{score:.2f}] {title}")
                if summary:
                    output.append(f"    {summary}...")

            return "\n".join(output)
        except Exception as e:
            return f"Search error: {e}"

    return "Knowledge server not running. Start it with: kln start"


def _update_usage(project_root: Path, entry_ids: list[str]) -> None:
    """Update usage stats for retrieved entries.

    Args:
        project_root: Project root path.
        entry_ids: List of entry IDs to update.
    """
    import socket

    try:
        port_file = get_kb_port_file(project_root)
        if not port_file.exists():
            return

        port = int(port_file.read_text().strip())
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "update_usage", "ids": entry_ids}).encode())
        sock.recv(1024)  # Discard response
        sock.close()
    except Exception:
        pass  # Non-critical, fail silently


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

        # Save to KB
        import socket

        entry = {
            "title": extracted.get("title", url[:60]),
            "summary": extracted.get("summary", text[:500]),
            "atomic_insight": extracted.get("atomic_insight", ""),
            "type": "web",
            "source": "web",
            "source_path": url,
            "tags": extracted.get("tags", ["web"]),
            "key_concepts": extracted.get("key_concepts", []),
            "priority": "medium",
            "quality": "medium",
        }

        port_file = get_kb_port_file(project_root)
        port = int(port_file.read_text().strip())

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "add", "entry": entry}).encode())
        response = sock.recv(1024).decode()
        sock.close()

        result = json.loads(response)
        if result.get("status") == "ok":
            title = entry["title"][:50]
            return f"SaveInfo: Saved '{title}' from {url}"
        else:
            return f"SaveInfo: Failed to save - {result.get('error', 'unknown')}"

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
        Dict with title, summary, atomic_insight, key_concepts, tags.
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
  "summary": "2-3 sentence summary of key information",
  "atomic_insight": "Single sentence actionable takeaway",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "tags": ["tag1", "tag2"]
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
    import socket

    try:
        entry = {
            "title": f"Web: {url[:60]}",
            "summary": f"URL saved for reference: {url}",
            "type": "web",
            "source": "web",
            "source_path": url,
            "tags": ["web", "url"],
            "priority": "low",
            "quality": "low",
        }

        port_file = get_kb_port_file(project_root)
        port = int(port_file.read_text().strip())

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "add", "entry": entry}).encode())
        sock.recv(1024)
        sock.close()

        return f"SaveInfo: Saved URL (no LLM extraction): {url}"
    except Exception as e:
        return f"SaveInfo: Failed to save URL - {e}"


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
