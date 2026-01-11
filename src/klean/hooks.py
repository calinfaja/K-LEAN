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
    """Get KB entries + Serena prompt for context injection.

    Retrieves:
    1. Top 10 critical/high priority warnings (any date)
    2. Last 10 newest entries (by date)
    3. Serena prompt for session history

    Args:
        project_root: Project root path.

    Returns:
        Formatted context string or empty string.
    """
    import socket

    if not _is_kb_server_running(project_root):
        return "[>] Session history: mcp__serena__read_memory lessons-learned"

    try:
        port_file = get_kb_port_file(project_root)
        port = int(port_file.read_text().strip())

        # Get more entries to filter locally
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "recent", "limit": 50}).encode())
        response = sock.recv(65536).decode()
        sock.close()

        data = json.loads(response)
        all_entries = data.get("entries", [])

        if not all_entries:
            return "[>] Session history: mcp__serena__read_memory lessons-learned"

        # 1. Get critical/high warnings (up to 10)
        warnings = [
            e
            for e in all_entries
            if e.get("type") == "warning" and e.get("priority") in ("critical", "high")
        ][:10]

        # 2. Get last 10 by date (excluding already-selected warnings)
        warning_ids = {e.get("id") for e in warnings}
        recent = [e for e in all_entries if e.get("id") not in warning_ids][:10]

        parts = []

        # Format warnings section
        if warnings:
            toon_warnings = _format_entries_toon(warnings)
            parts.append(f"[!] WARNINGS:\n{toon_warnings}")

        # Format recent section
        if recent:
            toon_recent = _format_entries_toon(recent)
            parts.append(f"[KB] RECENT:\n{toon_recent}")

        # Serena prompt
        parts.append("[>] Session history: mcp__serena__read_memory lessons-learned")

        return "\n\n".join(parts)
    except Exception:
        return "[>] Session history: mcp__serena__read_memory lessons-learned"


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

        # V3 Schema
        entry = {
            "title": f"Commit: {commit_msg[:80]}",
            "insight": f"Git commit {commit_hash} by {author}: {commit_msg}",
            "type": "commit",
            "priority": "low",
            "keywords": ["git", "commit"] + _extract_commit_tags(commit_msg) + changed_files[:3],
            "source": f"git:{commit_hash}",
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

    # Log documentation URLs for reference
    doc_patterns = ["docs.", "/docs/", "documentation", "readme", "wiki", "guide"]
    for url in urls:
        url_lower = url.lower()
        if any(p in url_lower for p in doc_patterns):
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
        import socket

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
            title_short = entry["title"][:50]
            return f"SaveInfo: Saved '{title_short}' from {url}"
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
    import socket

    try:
        entry = {
            "title": f"Web: {url[:60]}",
            "insight": f"URL saved for reference: {url}",
            "type": "finding",
            "priority": "low",
            "keywords": ["web", "url"],
            "source": url,
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
