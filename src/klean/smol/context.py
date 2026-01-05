"""Project context awareness for SmolKLN agents.

This module provides project detection and context gathering so agents
know about:
- Current project root (git or cwd)
- CLAUDE.md project instructions
- Knowledge DB location
- Serena memories (if available)
- .claude folder configuration
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ProjectContext:
    """Complete project context for agent execution."""

    # Project identification
    project_root: Path
    project_name: str

    # Project instructions
    claude_md: Optional[str] = None

    # Knowledge DB
    knowledge_db_path: Optional[Path] = None
    has_knowledge_db: bool = False

    # Serena integration
    serena_available: bool = False
    serena_memories: dict[str, str] = field(default_factory=dict)

    # .claude folder
    claude_dir: Path = field(default_factory=lambda: Path.home() / ".claude")
    scripts_dir: Optional[Path] = None

    # Git info
    git_branch: Optional[str] = None
    git_status_summary: Optional[str] = None


def detect_project_root(start_path: Path = None) -> Path:
    """Detect project root from git or use cwd.

    Walks up from start_path looking for .git directory.
    Falls back to current working directory if not in a git repo.
    """
    start = start_path or Path.cwd()

    # Try git first
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass

    # Walk up looking for .git
    current = start.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Fallback to cwd
    return Path.cwd().resolve()


def get_git_info(project_root: Path) -> dict[str, str]:
    """Get current git branch and status summary."""
    info = {}

    try:
        # Current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()

        # Status summary (short)
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines and lines[0]:
                info["status"] = f"{len(lines)} files changed"
            else:
                info["status"] = "clean"
    except Exception:
        pass

    return info


def load_claude_md(project_root: Path) -> Optional[str]:
    """Load CLAUDE.md project instructions if exists."""
    claude_md_path = project_root / "CLAUDE.md"

    if claude_md_path.exists():
        try:
            content = claude_md_path.read_text()
            # Truncate if too long (keep first 5000 chars)
            if len(content) > 5000:
                content = content[:5000] + "\n\n... [truncated]"
            return content
        except Exception:
            pass

    return None


def find_knowledge_db(project_root: Path) -> Optional[Path]:
    """Find knowledge DB for this project."""
    kb_path = project_root / ".knowledge-db"

    if kb_path.exists() and kb_path.is_dir():
        # Check if it has the index (multiple formats for backwards compatibility)
        has_fastembed = (kb_path / "embeddings.npy").exists() and (kb_path / "index.json").exists()
        has_txtai = (kb_path / "index").is_dir()
        has_embeddings = (kb_path / "embeddings").is_dir()
        if has_fastembed or has_txtai or has_embeddings:
            return kb_path

    return None


def load_mcp_config() -> dict[str, Any]:
    """Load MCP server configuration from Claude settings."""
    config_paths = [
        Path.home() / ".claude.json",
        Path.home() / ".claude" / "claude_desktop_config.json",
        Path.home() / ".claude" / "settings.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                if "mcpServers" in data:
                    return data["mcpServers"]
            except Exception:
                continue

    return {}


def get_serena_config() -> Optional[dict[str, Any]]:
    """Get Serena MCP server configuration if available."""
    mcp_config = load_mcp_config()
    return mcp_config.get("serena")


def check_serena_available() -> bool:
    """Check if Serena is configured and potentially available."""
    return get_serena_config() is not None


def get_claude_scripts() -> list[Path]:
    """Get list of available K-LEAN scripts."""
    scripts_dir = Path.home() / ".claude" / "scripts"

    if scripts_dir.exists():
        return list(scripts_dir.glob("*.sh")) + list(scripts_dir.glob("*.py"))

    return []


def gather_project_context(start_path: Path = None) -> ProjectContext:
    """Gather complete project context.

    This is the main entry point. Call this to get all project
    context for agent execution.
    """
    # Detect project root
    project_root = detect_project_root(start_path)

    # Get git info
    git_info = get_git_info(project_root)

    # Find knowledge DB
    kb_path = find_knowledge_db(project_root)

    # Check Serena
    serena_available = check_serena_available()

    # Scripts dir
    scripts_dir = Path.home() / ".claude" / "scripts"
    if not scripts_dir.exists():
        scripts_dir = None

    return ProjectContext(
        project_root=project_root,
        project_name=project_root.name,
        claude_md=load_claude_md(project_root),
        knowledge_db_path=kb_path,
        has_knowledge_db=kb_path is not None,
        serena_available=serena_available,
        scripts_dir=scripts_dir,
        git_branch=git_info.get("branch"),
        git_status_summary=git_info.get("status"),
    )


def format_context_for_prompt(ctx: ProjectContext) -> str:
    """Format project context for inclusion in agent prompt.

    Returns a markdown-formatted string with relevant project info.
    """
    parts = []

    # Project header
    parts.append(f"## Project: {ctx.project_name}")
    parts.append(f"Root: `{ctx.project_root}`")

    if ctx.git_branch:
        parts.append(f"Branch: `{ctx.git_branch}` ({ctx.git_status_summary})")

    # Project instructions
    if ctx.claude_md:
        parts.append("\n## Project Instructions (CLAUDE.md)")
        parts.append(ctx.claude_md)

    # Knowledge DB status
    if ctx.has_knowledge_db:
        parts.append(f"\n## Knowledge DB: Available at `{ctx.knowledge_db_path}`")
        parts.append("Use `knowledge_search` tool to query prior solutions and lessons.")

    # Serena status
    if ctx.serena_available:
        parts.append("\n## Serena Memory: Available")
        parts.append("Project memories and lessons-learned are accessible.")

    return "\n".join(parts)
