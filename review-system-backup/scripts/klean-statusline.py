#!/usr/bin/env python3
"""
K-LEAN Status Line v2 for Claude Code
======================================
Optimized statusline with actionable metrics:

1. Model     - Claude model with tier coloring
2. Project   - Project root directory
3. Git       - Branch + dirty state + lines changed
4. Services  - LiteLLM + Knowledge DB status

Layout: [opus] │ myproject │ main● +45-12 │ llm:6 kb:✓
"""

import json
import os
import subprocess
import socket
import sys
from pathlib import Path

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

    # Shorten display name
    short = display.lower().replace("claude ", "").replace("-", "")
    if len(short) > 8:
        short = short[:8]

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
        # Get branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=1, cwd=cwd
        )
        if branch_result.returncode != 0:
            return f"{C.DIM}no-git{C.RESET}"

        branch = branch_result.stdout.strip() or "HEAD"

        # Truncate long branch names
        if len(branch) > 12:
            branch = branch[:9] + "..."

        # Check dirty state
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=1, cwd=cwd
        )
        dirty = "●" if status_result.stdout.strip() else ""

        # Get lines added/removed (staged + unstaged)
        diff_result = subprocess.run(
            ["git", "diff", "--shortstat", "HEAD"],
            capture_output=True, text=True, timeout=1, cwd=cwd
        )

        added, removed = 0, 0
        diff_out = diff_result.stdout.strip()
        if diff_out:
            # Parse "X files changed, Y insertions(+), Z deletions(-)"
            import re
            ins_match = re.search(r'(\d+) insertion', diff_out)
            del_match = re.search(r'(\d+) deletion', diff_out)
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
            "http://localhost:4000/models",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            data = json.loads(resp.read().decode())
            return len(data.get("data", [])), True
    except Exception:
        return 0, False

def find_project_root(start_dir: str) -> str | None:
    """Find project root by walking up looking for .knowledge-db."""
    current = Path(start_dir)
    while current != current.parent:
        if (current / ".knowledge-db").is_dir():
            return str(current)
        current = current.parent
    return None

def get_project_socket_path(project_path: str) -> str:
    """Get per-project socket path using same hash as knowledge-server.py."""
    import hashlib
    path_str = str(Path(project_path).resolve())
    hash_val = hashlib.md5(path_str.encode()).hexdigest()[:8]
    return f"/tmp/kb-{hash_val}.sock"

def check_knowledge_db(workspace: dict) -> bool:
    """Check if per-project knowledge DB server is running."""
    # Get project directory from workspace data
    project_dir = workspace.get("project_dir", os.getcwd())

    # Find actual project root (might be different from project_dir)
    project_root = find_project_root(project_dir)
    if not project_root:
        return False  # No .knowledge-db found

    # Get per-project socket path
    socket_path = get_project_socket_path(project_root)

    if not os.path.exists(socket_path):
        return False
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        sock.connect(socket_path)
        sock.close()
        return True
    except Exception:
        # Stale socket - clean it up
        try:
            os.unlink(socket_path)
        except:
            pass
        return False

def get_services(data: dict) -> str:
    """Get K-LEAN services status."""
    llm_count, llm_running = check_litellm()
    workspace = data.get("workspace", {})
    kb_running = check_knowledge_db(workspace)

    if llm_running and llm_count >= 1:
        llm = f"{C.GREEN}{llm_count}{C.RESET}"
    else:
        llm = f"{C.RED}✗{C.RESET}"

    kb = f"{C.GREEN}✓{C.RESET}" if kb_running else f"{C.RED}✗{C.RESET}"

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

    # Assemble: [opus] │ myproject │ main● +45-12 │ llm:6 kb:✓
    line = f"{model}{SEP}{project}{SEP}{git}{SEP}{services}"

    print(line)

if __name__ == "__main__":
    main()
