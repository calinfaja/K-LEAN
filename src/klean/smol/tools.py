"""Custom tools for K-LEAN SmolKLN agents.

Provides file operations and knowledge search tools.
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
def read_file(file_path: str, start_line: int = 1, max_lines: int = 500) -> str:
    """
    Read contents of a file from the project with pagination support for large files.

    Args:
        file_path: Path to the file (relative to project root or absolute)
        start_line: Line number to start reading from (1-indexed, default: 1)
        max_lines: Maximum number of lines to read (default: 500, max: 1000)

    Returns:
        File contents with line numbers, or error message if file not found.
        For large files, includes instructions to read remaining portions.
    """
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"

    # Clamp max_lines
    max_lines = min(max_lines, 1000)
    start_line = max(1, start_line)

    try:
        content = path.read_text()
        lines = content.splitlines()
        total_lines = len(lines)

        # Adjust start_line to 0-indexed
        start_idx = start_line - 1
        end_idx = min(start_idx + max_lines, total_lines)

        # Get the requested lines
        selected_lines = lines[start_idx:end_idx]

        # Format with line numbers
        output_lines = []
        for i, line in enumerate(selected_lines, start=start_line):
            output_lines.append(f"{i:4d}| {line}")

        output = "\n".join(output_lines)

        # Add header with file info
        header = f"## {file_path} (lines {start_line}-{end_idx} of {total_lines})\n\n"

        # Add navigation hints for large files
        if end_idx < total_lines:
            remaining = total_lines - end_idx
            footer = f"\n\n... [{remaining} more lines. Use start_line={end_idx + 1} to continue reading]"
            return header + output + footer
        elif start_line > 1:
            return header + output + "\n\n[End of file]"
        else:
            return header + output

    except Exception as e:
        return f"Error reading file: {e}"


@tool
def search_files(pattern: str, path: str = ".", recursive: bool = True) -> str:
    """
    Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.ts")
        path: Directory to search in (default: current directory)
        recursive: If True, search recursively in subdirectories (default: True)

    Returns:
        List of matching file paths.
    """
    base = Path(path)
    if not base.exists():
        return f"Path not found: {path}"

    # If pattern doesn't contain ** and recursive is True, search recursively
    if recursive and "**" not in pattern:
        # Try recursive pattern first
        matches = list(base.glob(f"**/{pattern}"))
        if not matches:
            # Fall back to exact pattern
            matches = list(base.glob(pattern))
    else:
        matches = list(base.glob(pattern))

    if not matches:
        return f"No files matching '{pattern}' in {path}"

    # Sort by path for consistent output
    matches = sorted(matches, key=lambda p: str(p))
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


@tool
def git_diff(commits: int = 3, path: str = ".") -> str:
    """
    Get git diff for recent commits showing what changed.

    Args:
        commits: Number of recent commits to show diff for (default: 3)
        path: Directory path of the git repository (default: current directory)

    Returns:
        Git diff output showing file changes in recent commits.
    """
    import subprocess
    from pathlib import Path

    repo_path = Path(path)
    if not repo_path.exists():
        return f"Path not found: {path}"

    # Check if it's a git repo
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        # Try parent directories
        for parent in repo_path.parents:
            if (parent / ".git").exists():
                repo_path = parent
                break
        else:
            return f"Not a git repository: {path}"

    try:
        # Get recent commits
        log_result = subprocess.run(
            ["git", "log", f"-{commits}", "--oneline"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        if log_result.returncode != 0:
            return f"Git error: {log_result.stderr}"

        commits_list = log_result.stdout.strip()

        # Get diff for recent commits
        diff_result = subprocess.run(
            ["git", "diff", f"HEAD~{commits}", "HEAD", "--stat"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30
        )

        # Get detailed diff (limited to avoid huge output)
        detailed_diff = subprocess.run(
            ["git", "diff", f"HEAD~{commits}", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60
        )

        output = f"## Recent {commits} Commits\n{commits_list}\n\n"
        output += f"## Summary\n{diff_result.stdout}\n\n"

        # Truncate detailed diff if too long
        diff_content = detailed_diff.stdout
        if len(diff_content) > 30000:
            diff_content = diff_content[:30000] + "\n\n... [truncated - diff too large]"

        output += f"## Detailed Changes\n```diff\n{diff_content}\n```"

        return output

    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Git error: {e}"


@tool
def git_status(path: str = ".") -> str:
    """
    Get git status showing staged/unstaged changes.

    Args:
        path: Directory path of the git repository (default: current directory)

    Returns:
        Git status output showing current repository state.
    """
    import subprocess
    from pathlib import Path

    repo_path = Path(path)
    if not repo_path.exists():
        return f"Path not found: {path}"

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return f"Git error: {result.stderr}"

        # Also get branch info
        branch_result = subprocess.run(
            ["git", "branch", "-v"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10
        )

        output = f"## Git Status\n{result.stdout}\n\n"
        output += f"## Branches\n{branch_result.stdout}"

        return output

    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Git error: {e}"


@tool
def git_log(commits: int = 10, path: str = ".") -> str:
    """
    Get git commit history with details.

    Args:
        commits: Number of commits to show (default: 10)
        path: Directory path of the git repository (default: current directory)

    Returns:
        Git log showing commit history with authors, dates, and messages.
    """
    import subprocess
    from pathlib import Path

    repo_path = Path(path)
    if not repo_path.exists():
        return f"Path not found: {path}"

    try:
        result = subprocess.run(
            ["git", "log", f"-{commits}", "--pretty=format:%h|%an|%ar|%s"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return f"Git error: {result.stderr}"

        output = "## Git Commit History\n\n"
        output += "| Hash | Author | Date | Message |\n"
        output += "|------|--------|------|----------|\n"

        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 3)
                if len(parts) == 4:
                    output += f"| {parts[0]} | {parts[1]} | {parts[2]} | {parts[3]} |\n"

        return output

    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Git error: {e}"


@tool
def list_directory(path: str = ".", recursive: bool = False, max_depth: int = 2) -> str:
    """
    List contents of a directory.

    Args:
        path: Directory path to list (default: current directory)
        recursive: If True, list recursively up to max_depth (default: False)
        max_depth: Maximum recursion depth when recursive=True (default: 2)

    Returns:
        Directory listing showing files and subdirectories.
    """
    from pathlib import Path

    base = Path(path)
    if not base.exists():
        return f"Path not found: {path}"
    if not base.is_dir():
        return f"Not a directory: {path}"

    def list_dir(p: Path, depth: int = 0) -> list:
        items = []
        indent = "  " * depth
        try:
            for item in sorted(p.iterdir()):
                if item.name.startswith('.'):
                    continue  # Skip hidden files
                if item.is_dir():
                    items.append(f"{indent}📁 {item.name}/")
                    if recursive and depth < max_depth:
                        items.extend(list_dir(item, depth + 1))
                else:
                    size = item.stat().st_size
                    size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    items.append(f"{indent}📄 {item.name} ({size_str})")
        except PermissionError:
            items.append(f"{indent}⛔ Permission denied")
        return items

    output = f"## Directory: {path}\n\n"
    items = list_dir(base)

    if not items:
        return output + "Empty directory"

    # Limit output
    if len(items) > 100:
        items = items[:100]
        items.append(f"\n... and {len(items) - 100} more items")

    return output + "\n".join(items)


@tool
def get_file_info(file_path: str) -> str:
    """
    Get metadata about a file (size, modified date, type).

    Args:
        file_path: Path to the file

    Returns:
        File information including size, modification date, and type.
    """
    from pathlib import Path
    from datetime import datetime

    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"

    try:
        stat = path.stat()
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime)

        # Determine file type
        suffix = path.suffix.lower()
        type_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C Header',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
            '.sql': 'SQL',
            '.sh': 'Shell Script',
        }
        file_type = type_map.get(suffix, suffix if suffix else 'Unknown')

        # Count lines if text file
        lines = "N/A"
        if size < 1_000_000:  # Only for files < 1MB
            try:
                content = path.read_text()
                lines = len(content.splitlines())
            except Exception:
                pass

        size_str = f"{size:,} bytes"
        if size > 1024:
            size_str += f" ({size/1024:.1f} KB)"
        if size > 1024 * 1024:
            size_str = f"{size:,} bytes ({size/1024/1024:.1f} MB)"

        return f"""## File Info: {path.name}

- **Path**: {file_path}
- **Type**: {file_type}
- **Size**: {size_str}
- **Lines**: {lines}
- **Modified**: {modified.strftime('%Y-%m-%d %H:%M:%S')}
"""

    except Exception as e:
        return f"Error getting file info: {e}"


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

    # Web research tools (DuckDuckGo search + webpage fetcher)
    try:
        from smolagents import DuckDuckGoSearchTool, VisitWebpageTool
        tools.append(DuckDuckGoSearchTool(max_results=5))
        tools.append(VisitWebpageTool(max_output_length=20000))
    except ImportError:
        pass  # smolagents web tools not available

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


def get_tools_for_agent(
    tool_names: List[str],
    project_path: str = None,
) -> list:
    """Get specific tools by name for multi-agent system.

    Args:
        tool_names: List of tool names to include
        project_path: Project root path for Knowledge DB

    Returns:
        List of requested tools.
    """
    tools = []

    # Create project-aware versions of file tools
    def make_read_file(root: str):
        @tool
        def project_read_file(file_path: str, start_line: int = 1, max_lines: int = 500) -> str:
            """Read contents of a file from the project with pagination support.

            Args:
                file_path: Path to the file (relative to project root or absolute)
                start_line: Line number to start reading from (1-indexed, default: 1)
                max_lines: Maximum number of lines to read (default: 500, max: 1000)

            Returns:
                File contents with line numbers. For large files, includes instructions to read more.
            """
            path = Path(file_path)
            if not path.is_absolute():
                path = Path(root) / path
            if not path.exists():
                return f"File not found: {file_path}"

            # Clamp max_lines
            max_lines = min(max_lines, 1000)
            start_line = max(1, start_line)

            try:
                content = path.read_text()
                lines = content.splitlines()
                total_lines = len(lines)

                # Adjust start_line to 0-indexed
                start_idx = start_line - 1
                end_idx = min(start_idx + max_lines, total_lines)

                # Get the requested lines
                selected_lines = lines[start_idx:end_idx]

                # Format with line numbers
                output_lines = []
                for i, line in enumerate(selected_lines, start=start_line):
                    output_lines.append(f"{i:4d}| {line}")

                output = "\n".join(output_lines)

                # Add header with file info
                header = f"## {file_path} (lines {start_line}-{end_idx} of {total_lines})\n\n"

                # Add navigation hints for large files
                if end_idx < total_lines:
                    remaining = total_lines - end_idx
                    footer = f"\n\n... [{remaining} more lines. Use start_line={end_idx + 1} to continue reading]"
                    return header + output + footer
                elif start_line > 1:
                    return header + output + "\n\n[End of file]"
                else:
                    return header + output

            except Exception as e:
                return f"Error reading file: {e}"
        return project_read_file

    def make_search_files(root: str):
        @tool
        def project_search_files(pattern: str, path: str = ".", recursive: bool = True) -> str:
            """Search for files matching a glob pattern.

            Args:
                pattern: Glob pattern (e.g., "*.py", "src/**/*.ts")
                path: Directory to search in (default: project root)
                recursive: If True, search recursively in subdirectories

            Returns:
                List of matching file paths.
            """
            base = Path(path)
            if not base.is_absolute():
                base = Path(root) / base
            if not base.exists():
                return f"Path not found: {path}"

            if recursive and "**" not in pattern:
                matches = list(base.glob(f"**/{pattern}"))
                if not matches:
                    matches = list(base.glob(pattern))
            else:
                matches = list(base.glob(pattern))

            if not matches:
                return f"No files matching '{pattern}' in {path}"

            matches = sorted(matches, key=lambda p: str(p))
            return "\n".join(str(m) for m in matches[:50])
        return project_search_files

    def make_grep(root: str):
        @tool
        def project_grep(pattern: str, path: str = ".", file_pattern: str = "*") -> str:
            """Search for text pattern in files.

            Args:
                pattern: Text or regex pattern to search for
                path: Directory to search in (default: project root)
                file_pattern: Glob pattern for files to search (e.g., "*.py")

            Returns:
                Matching lines with file paths.
            """
            import re
            base = Path(path)
            if not base.is_absolute():
                base = Path(root) / base
            if not base.exists():
                return f"Path not found: {path}"

            results = []
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
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
        return project_grep

    # Add Knowledge DB if requested
    if "knowledge_search" in tool_names:
        tools.append(KnowledgeRetrieverTool(project_path))

    # Add web tools if requested
    if "web_search" in tool_names:
        try:
            from smolagents import DuckDuckGoSearchTool
            tools.append(DuckDuckGoSearchTool(max_results=5))
        except ImportError:
            pass

    if "visit_webpage" in tool_names:
        try:
            from smolagents import VisitWebpageTool
            tools.append(VisitWebpageTool(max_output_length=20000))
        except ImportError:
            pass

    # Add project-aware file tools
    root = project_path or str(Path.cwd())
    if "read_file" in tool_names:
        tools.append(make_read_file(root))
    if "search_files" in tool_names:
        tools.append(make_search_files(root))
    if "grep" in tool_names:
        tools.append(make_grep(root))

    # Add git tools
    if "git_diff" in tool_names:
        tools.append(git_diff)
    if "git_status" in tool_names:
        tools.append(git_status)
    if "git_log" in tool_names:
        tools.append(git_log)

    # Add file info tools
    if "list_directory" in tool_names:
        tools.append(list_directory)
    if "get_file_info" in tool_names:
        tools.append(get_file_info)

    return tools
