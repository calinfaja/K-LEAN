#!/usr/bin/env python3
"""
K-LEAN Status Line for Claude Code
========================================
Optimized statusline with actionable metrics:

1. Model     - Claude model with tier coloring
2. Project   - Project root directory
3. Git       - Branch + dirty state + lines changed
4. Services  - LiteLLM + Knowledge DB status

Layout: [opus] │ myproject │ main● +45-12 │ llm:6 kb:[OK]

Knowledge DB Status:
- kb:[OK]        (green)  - Server running
- run InitKB  (cyan)   - Not initialized, prompts user
- kb:starting (yellow) - Server starting up
- kb:—        (dim)    - No project root found
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Pre-compiled regexes for git diff parsing
RE_INSERTIONS = re.compile(r"(\d+) insertion")
RE_DELETIONS = re.compile(r"(\d+) deletion")

# Import shared utilities
try:
    from kb_utils import (  # noqa: F401
        clean_stale_socket,
        get_socket_path,
        is_kb_initialized,
        is_server_running,
    )
    from kb_utils import find_project_root as _find_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import clean_stale_socket, is_kb_initialized, is_server_running
    from kb_utils import find_project_root as _find_project_root


# ============================================================================
# ANSI Colors
# ============================================================================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_WHITE = "\033[97m"


SEP = f" {C.DIM}│{C.RESET} "


# ============================================================================
# Field 1: Model
# ============================================================================
def get_model(data: dict) -> str:
    """Get model display name with tier coloring."""
    model = data.get("model", {})
    display = model.get("display_name", "?")
    name_lower = display.lower()

    if "opus" in name_lower:
        color = C.MAGENTA
    elif "sonnet" in name_lower:
        color = C.CYAN
    elif "haiku" in name_lower:
        color = C.GREEN
    else:
        color = C.WHITE

    # Shorten display name - handle both "claude " and "claude-" prefixes
    short = re.sub(r"^claude[\s-]*", "", name_lower)
    # Replace dashes with spaces, collapse multiple spaces
    short = re.sub(r"[-\s]+", " ", short).strip()
    # Keep up to 10 chars to preserve versions like "sonnet 4.5"
    if len(short) > 10:
        short = short[:10]

    return f"{color}[{short}]{C.RESET}"


# ============================================================================
# Field 2: Project + Current Directory
# ============================================================================
def get_project(data: dict) -> str:
    """Show project/relative_path or just project if in root."""
    workspace = data.get("workspace", {})
    project_dir = workspace.get("project_dir", "")
    current_dir = workspace.get("current_dir", "")

    project = Path(project_dir).name or "?"

    if current_dir and project_dir and current_dir != project_dir:
        try:
            rel = Path(current_dir).relative_to(project_dir)
            return f"{C.BRIGHT_WHITE}{project}{C.DIM}/{C.YELLOW}{rel}{C.RESET}"
        except ValueError:
            pass

    return f"{C.BRIGHT_WHITE}{project}{C.RESET}"


# ============================================================================
# Field 5: Git (Branch + Dirty + Lines Changed)
# ============================================================================
def get_git(data: dict) -> str:
    """Get git branch, dirty state, and lines added/removed."""
    workspace = data.get("workspace", {})
    cwd = workspace.get("project_dir", os.getcwd())

    try:
        # Check if git lock exists - skip polling to avoid conflicts
        git_dir = Path(cwd) / ".git"
        if (git_dir / "index.lock").exists():
            # Return cached/minimal info when lock exists
            return f"{C.DIM}git:(...){C.RESET}"

        # Get branch (--no-optional-locks prevents creating index.lock)
        branch_result = subprocess.run(
            ["git", "--no-optional-locks", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=cwd,
        )
        if branch_result.returncode != 0:
            return f"{C.DIM}no-git{C.RESET}"

        branch = branch_result.stdout.strip() or "HEAD"

        # Truncate long branch names
        if len(branch) > 12:
            branch = branch[:9] + "..."

        # Check dirty state (--no-optional-locks prevents lock conflicts)
        status_result = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=cwd,
        )
        dirty = "●" if status_result.stdout.strip() else ""

        # Get lines added/removed (staged + unstaged)
        diff_result = subprocess.run(
            ["git", "--no-optional-locks", "diff", "--shortstat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=cwd,
        )

        added, removed = 0, 0
        diff_out = diff_result.stdout.strip()
        if diff_out:
            # Parse "X files changed, Y insertions(+), Z deletions(-)"
            ins_match = RE_INSERTIONS.search(diff_out)
            del_match = RE_DELETIONS.search(diff_out)
            if ins_match:
                added = int(ins_match.group(1))
            if del_match:
                removed = int(del_match.group(1))

        # Build output
        dirty_colored = f"{C.YELLOW}{dirty}{C.RESET}" if dirty else ""

        # Lines string
        if added > 0 or removed > 0:
            lines_str = f" {C.GREEN}+{added}{C.RESET}{C.RED}-{removed}{C.RESET}"
        else:
            lines_str = ""

        return f"{C.BLUE}git:({C.BRIGHT_RED}{branch}{dirty_colored}{C.BLUE}){C.RESET}{lines_str}"

    except Exception:
        return f"{C.DIM}no-git{C.RESET}"


# ============================================================================
# Field 6: Services (LiteLLM + Knowledge DB)
# ============================================================================
def check_litellm() -> tuple[int, bool]:
    """Check LiteLLM proxy health."""
    try:
        import urllib.request

        req = urllib.request.Request(
            "http://localhost:4000/models", headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            data = json.loads(resp.read().decode())
            return len(data.get("data", [])), True
    except Exception:
        return 0, False


def check_knowledge_db(workspace: dict) -> str:
    """Check knowledge DB status for the project.

    Returns:
        "running" - server is up and responding
        "stopped" - .knowledge-db exists but server not running
        "init"    - no .knowledge-db directory (needs initialization)
        "no-project" - no project root found
    """
    project_dir = workspace.get("project_dir", os.getcwd())
    project_root = _find_project_root(project_dir)

    if not project_root:
        return "no-project"

    project_root_str = str(project_root)

    if not is_kb_initialized(project_root_str):
        return "init"

    if is_server_running(project_root_str, timeout=0.3):
        return "running"

    # Clean stale socket if exists
    clean_stale_socket(project_root_str)
    return "stopped"


def get_services(data: dict) -> str:
    """Get K-LEAN services status."""
    llm_count, llm_running = check_litellm()
    workspace = data.get("workspace", {})
    kb_status = check_knowledge_db(workspace)

    # LiteLLM status
    if llm_running and llm_count >= 1:
        llm = f"{C.GREEN}{llm_count}{C.RESET}"
    else:
        llm = f"{C.RED}[X]{C.RESET}"

    # Knowledge DB status - meaningful messages
    if kb_status == "running":
        kb = f"{C.GREEN}[OK]{C.RESET}"
    elif kb_status == "init":
        # Not initialized - cyan prompt to run InitKB
        return f"{C.DIM}llm:{llm}{C.RESET} {C.CYAN}run InitKB{C.RESET}"
    elif kb_status == "stopped":
        # Initialized but server not running
        kb = f"{C.YELLOW}starting{C.RESET}"
    else:  # no-project
        kb = f"{C.DIM}—{C.RESET}"

    return f"{C.DIM}llm:{llm} kb:{kb}{C.RESET}"


# ============================================================================
# Main
# ============================================================================
def main():
    try:
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}
    except Exception:
        data = {}

    # Build fields
    model = get_model(data)
    project = get_project(data)
    git = get_git(data)
    services = get_services(data)

    # Assemble: [opus] │ myproject │ main● +45-12 │ llm:18 kb:[OK]
    line = f"{model}{SEP}{project}{SEP}{git}{SEP}{services}"

    print(line)


if __name__ == "__main__":
    main()
