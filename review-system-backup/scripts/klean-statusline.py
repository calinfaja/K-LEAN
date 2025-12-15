#!/usr/bin/env python3
"""
K-LEAN Status Line for Claude Code
===================================
Professional, minimal statusline with 5 key fields:
1. Model - Current Claude model
2. Context % - Color-coded context window usage
3. Workspace - Current directory name
4. Git - Branch + dirty status
5. Services - LiteLLM health + Knowledge DB status

Usage: Configure in ~/.claude/settings.json:
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/scripts/klean-statusline.py",
    "padding": 0
  }
}
"""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

# ============================================================================
# ANSI Colors
# ============================================================================
class C:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_WHITE = "\033[97m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"

# Separator
SEP = f"{C.DIM}│{C.RESET}"

# ============================================================================
# Field 1: Model
# ============================================================================
def get_model(data: dict) -> str:
    """Get current model display name."""
    model = data.get("model", {})
    display = model.get("display_name", "?")

    # Color based on model tier
    name_lower = display.lower()
    if "opus" in name_lower:
        color = C.MAGENTA
    elif "sonnet" in name_lower:
        color = C.CYAN
    elif "haiku" in name_lower:
        color = C.GREEN
    else:
        color = C.WHITE

    return f"{color}[{display.lower()}]{C.RESET}"

# ============================================================================
# Field 2: Context Percentage
# ============================================================================
def get_context(data: dict) -> str:
    """Get context window usage percentage with color coding."""
    ctx = data.get("context_window", {})
    input_tokens = ctx.get("total_input_tokens", 0)
    output_tokens = ctx.get("total_output_tokens", 0)
    window_size = ctx.get("context_window_size", 200000)

    if window_size == 0:
        return f"{C.DIM}ctx:?%{C.RESET}"

    total = input_tokens + output_tokens
    percent = (total / window_size) * 100

    # Color coding: green < 70%, yellow 70-85%, red > 85%
    if percent < 70:
        color = C.GREEN
    elif percent < 85:
        color = C.YELLOW
    else:
        color = C.BRIGHT_RED

    return f"{color}ctx:{percent:.0f}%{C.RESET}"

# ============================================================================
# Field 3: Workspace
# ============================================================================
def get_workspace(data: dict) -> str:
    """Get workspace directory name."""
    workspace = data.get("workspace", {})
    current_dir = workspace.get("current_dir", os.getcwd())
    project_dir = workspace.get("project_dir", current_dir)

    # Get just the directory name
    dir_name = Path(current_dir).name or "/"

    # Highlight if we've navigated away from project root
    if current_dir != project_dir:
        # Show relative path from project
        try:
            rel_path = Path(current_dir).relative_to(project_dir)
            dir_name = str(rel_path)
        except ValueError:
            pass
        return f"{C.YELLOW}{dir_name}{C.RESET}"

    return f"{C.BRIGHT_WHITE}{dir_name}{C.RESET}"

# ============================================================================
# Field 4: Git Branch + Status (Oh-My-Zsh style)
# ============================================================================
def get_git(data: dict) -> str:
    """Get git branch and status in Oh-My-Zsh style: git:(branch●)"""
    workspace = data.get("workspace", {})
    cwd = workspace.get("current_dir", os.getcwd())

    try:
        # Get current branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=1,
            cwd=cwd
        )
        if branch.returncode != 0:
            return f"{C.DIM}no-git{C.RESET}"

        branch_name = branch.stdout.strip() or "HEAD"

        # Check for uncommitted changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=1,
            cwd=cwd
        )

        dirty = "●" if status.stdout.strip() else ""
        dirty_colored = f"{C.YELLOW}{dirty}{C.RESET}" if dirty else ""

        # Oh-My-Zsh style: git:(branch●)
        return f"{C.BLUE}git:({C.BRIGHT_RED}{branch_name}{dirty_colored}{C.BLUE}){C.RESET}"

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return f"{C.DIM}no-git{C.RESET}"

# ============================================================================
# Field 5: K-LEAN Services (LiteLLM + Knowledge DB)
# ============================================================================
def check_litellm() -> tuple[int, bool]:
    """
    Check LiteLLM proxy health.
    Returns (healthy_count, is_running).
    """
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:4000/models",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("data", [])
            return len(models), True
    except Exception:
        return 0, False

def check_knowledge_db() -> bool:
    """Check if knowledge DB server is running via socket."""
    socket_path = "/tmp/knowledge-server.sock"

    if not os.path.exists(socket_path):
        return False

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect(socket_path)
        sock.close()
        return True
    except Exception:
        return False

def get_services() -> str:
    """Get K-LEAN services status with clear labels."""
    # LiteLLM check
    llm_count, llm_running = check_litellm()

    if not llm_running:
        llm_str = f"{C.DIM}llm:{C.RED}✗{C.RESET}"
    elif llm_count >= 3:
        llm_str = f"{C.DIM}llm:{C.GREEN}{llm_count}{C.RESET}"
    elif llm_count >= 1:
        llm_str = f"{C.DIM}llm:{C.YELLOW}{llm_count}{C.RESET}"
    else:
        llm_str = f"{C.DIM}llm:{C.RED}0{C.RESET}"

    # Knowledge DB check
    kb_running = check_knowledge_db()
    if kb_running:
        kb_str = f"{C.DIM}kb:{C.GREEN}✓{C.RESET}"
    else:
        kb_str = f"{C.DIM}kb:{C.RED}✗{C.RESET}"

    return f"{llm_str} {kb_str}"

# ============================================================================
# Main
# ============================================================================
def main():
    """Generate statusline from Claude Code JSON input."""
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}
    except (json.JSONDecodeError, Exception):
        data = {}

    # Build status line fields
    model = get_model(data)
    context = get_context(data)
    workspace = get_workspace(data)
    git = get_git(data)
    services = get_services()

    # Assemble the line
    # [opus] ctx:67% │ claudeAgentic │ main● │ ⚡4 📚✓
    line = f"{model} {context} {SEP} {workspace} {SEP} {git} {SEP} {services}"

    print(line)

if __name__ == "__main__":
    main()
