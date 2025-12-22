"""Custom tools for K-LEAN SmolKLN agents.

This module is INDEPENDENT - no imports from src/klean/droids/.
"""

from pathlib import Path
from typing import Optional, List
import sys

# Import smolagents Tool class - required for this module
try:
    from smolagents import Tool, tool
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    Tool = object  # Fallback for type hints
    tool = lambda f: f  # No-op decorator


class KnowledgeRetrieverTool(Tool if SMOLAGENTS_AVAILABLE else object):
    """Retriever tool for K-LEAN knowledge database (Agentic RAG).

    This implements the smolagents Tool interface for semantic search
    over the project's knowledge database.
    """

    name = "knowledge_search"
    description = (
        "Search the project's knowledge database for relevant prior solutions, "
        "lessons learned, patterns, and documentation. Use affirmative statements "
        "for better retrieval (e.g., 'BLE power optimization techniques' not "
        "'how to optimize BLE power?')."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "Search query - use affirmative statements for best results"
        }
    }
    output_type = "string"

    def __init__(self, project_path: str = None):
        if SMOLAGENTS_AVAILABLE:
            super().__init__()
        self.project_path = project_path
        self._db = None

    @property
    def db(self):
        """Lazy-load knowledge DB."""
        if self._db is None:
            # Add scripts dir to path
            scripts_dir = Path(__file__).parent.parent / "data" / "scripts"
            sys.path.insert(0, str(scripts_dir))
            try:
                from knowledge_db import KnowledgeDB
                self._db = KnowledgeDB(self.project_path)
            except ImportError:
                # Knowledge DB not available, return None
                return None
        return self._db

    def forward(self, query: str) -> str:
        """Execute knowledge search."""
        if self.db is None:
            return "Knowledge DB not available. Install with: pip install txtai"

        try:
            results = self.db.search(query, limit=5)
        except Exception as e:
            return f"Knowledge DB error: {e}"

        if not results:
            return "No relevant prior knowledge found for this query."

        output = "RELEVANT PRIOR KNOWLEDGE:\n\n"
        for r in results:
            score = r.get("score", 0)
            if score < 0.3:
                continue
            output += f"### {r.get('title', 'Untitled')} (relevance: {score:.0%})\n"
            if r.get("url"):
                output += f"Source: {r['url']}\n"
            if r.get("summary"):
                output += f"{r['summary']}\n"
            if r.get("problem_solved"):
                output += f"Problem: {r['problem_solved']}\n"
            if r.get("what_worked"):
                output += f"Solution: {r['what_worked']}\n"
            output += "\n"

        return output if len(output) > 50 else "No highly relevant prior knowledge found."


@tool
def read_file(file_path: str) -> str:
    """
    Read contents of a file from the project.

    Args:
        file_path: Path to the file (relative to project root or absolute)

    Returns:
        File contents as string, or error message if file not found.
    """
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
    try:
        content = path.read_text()
        # Truncate large files
        if len(content) > 50000:
            return content[:50000] + "\n\n... [truncated - file too large]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def search_files(pattern: str, path: str = ".") -> str:
    """
    Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.ts")
        path: Directory to search in (default: current directory)

    Returns:
        List of matching file paths.
    """
    base = Path(path)
    if not base.exists():
        return f"Path not found: {path}"

    matches = list(base.glob(pattern))
    if not matches:
        return f"No files matching '{pattern}' in {path}"

    return "\n".join(str(m) for m in matches[:50])  # Limit to 50 results


@tool
def grep(pattern: str, path: str = ".", file_pattern: str = "*") -> str:
    """
    Search for text pattern in files.

    Args:
        pattern: Text or regex pattern to search for
        path: Directory to search in
        file_pattern: Glob pattern for files to search (e.g., "*.py")

    Returns:
        Matching lines with file paths.
    """
    import re
    base = Path(path)
    if not base.exists():
        return f"Path not found: {path}"

    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        # If not valid regex, use literal match
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    for file_path in base.glob(f"**/{file_pattern}"):
        if file_path.is_file():
            try:
                content = file_path.read_text()
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{file_path}:{i}: {line.strip()}")
                        if len(results) >= 50:
                            break
            except Exception:
                continue
        if len(results) >= 50:
            break

    if not results:
        return f"No matches for '{pattern}' in {path}"

    return "\n".join(results)


def get_default_tools(
    project_path: str = None,
    use_mcp: bool = True,
    mcp_servers: list = None
) -> list:
    """Get the default tool set for agents.

    Args:
        project_path: Project root path for Knowledge DB
        use_mcp: Whether to load MCP tools (default: True)
        mcp_servers: Specific MCP servers to load (default: auto-detect)

    Returns:
        List of tools including MCP servers if available.
    """
    tools = []

    # Always include Knowledge DB tool
    tools.append(KnowledgeRetrieverTool(project_path))

    # Try to load MCP tools
    if use_mcp:
        try:
            from .mcp_tools import get_mcp_tools
            mcp_tools = get_mcp_tools(mcp_servers)
            if mcp_tools:
                tools.extend(mcp_tools)
        except ImportError:
            pass
        except Exception:
            # MCP failed, fallback to basic tools
            pass

    # Always include basic tools as fallback/supplement
    tools.extend([read_file, search_files, grep])

    return tools
