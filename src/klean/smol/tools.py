"""Custom tools for K-LEAN SmolKLN agents.

Provides file operations and knowledge search tools.
"""

import re
import sys
from pathlib import Path
from typing import Any

# Import smolagents Tool class - required for this module
try:
    from smolagents import Tool, tool

    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    Tool = object  # Fallback for type hints

    def tool(f):
        return f  # No-op decorator


# =============================================================================
# Citation Validation for final_answer_checks
# =============================================================================


def validate_citations(final_answer: str, agent_memory=None, **kwargs) -> bool:
    """Verify all file:line citations in final answer exist in tool call history.

    This function is designed to be used with smolagents' final_answer_checks.
    smolagents calls: check_function(final_answer, self.memory, agent=self)

    Args:
        final_answer: The agent's final answer string
        agent_memory: List of agent memory steps (ActionStep objects)
        **kwargs: Accepts additional args (e.g., agent=) passed by smolagents

    Returns:
        True if all citations are valid or no citations present, False otherwise
    """
    if not final_answer or not agent_memory:
        return True  # No validation needed

    # Convert final_answer to string if needed (can be dict, int, etc.)
    answer_str = str(final_answer) if not isinstance(final_answer, str) else final_answer

    # Extract citations from answer (format: file.ext:123 or path/file.ext:123-456)
    citation_pattern = r"([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+):(\d+)(?:-(\d+))?"
    citations = re.findall(citation_pattern, answer_str)

    if not citations:
        return True  # No citations to validate

    # Collect all valid file:line references from tool outputs
    valid_refs = set()
    steps = agent_memory.get_full_steps() if hasattr(agent_memory, "get_full_steps") else []
    for step in steps:
        # Handle different memory step formats
        tool_output = None
        if hasattr(step, "observations"):
            tool_output = step.observations
        elif hasattr(step, "tool_output"):
            tool_output = step.tool_output
        elif isinstance(step, dict) and "observations" in step:
            tool_output = step["observations"]

        if tool_output:
            # Extract all file:line patterns from tool output
            refs = re.findall(r"([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+):(\d+)", str(tool_output))
            for file_path, line_num in refs:
                valid_refs.add((file_path, int(line_num)))
                # Also add basename for flexibility
                basename = Path(file_path).name
                valid_refs.add((basename, int(line_num)))

    # Verify each citation
    invalid_count = 0
    for file_path, line_start, _line_end in citations:
        line_num = int(line_start)
        basename = Path(file_path).name

        # Check if citation exists in valid refs (full path or basename)
        if (file_path, line_num) not in valid_refs and (basename, line_num) not in valid_refs:
            invalid_count += 1

    # Allow some tolerance - fail only if >= 20% citations are invalid
    total_citations = len(citations)
    if invalid_count > 0:
        invalid_ratio = invalid_count / total_citations
        if invalid_ratio >= 0.2:
            return False  # smolagents raises AgentError with function name

    return True


def validate_file_paths(final_answer: str, agent_memory=None, **kwargs) -> bool:
    """Verify all file paths cited in final answer actually exist on filesystem.

    This function prevents agents from hallucinating non-existent file paths.
    Used as a smolagents final_answer_check alongside validate_citations.

    Args:
        final_answer: The agent's final answer string
        agent_memory: List of agent memory steps (unused, but required by smolagents)
        **kwargs: Accepts additional args (e.g., agent=) passed by smolagents

    Returns:
        True if all cited files exist or no citations present, False otherwise
    """
    if not final_answer:
        return True

    answer_str = str(final_answer) if not isinstance(final_answer, str) else final_answer

    # Extract file paths from citations (format: file.ext:123 or path/file.ext:123-456)
    citation_pattern = r"([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+):(\d+)"
    citations = re.findall(citation_pattern, answer_str)

    if not citations:
        return True

    # Get project root from context or current directory
    project_root = Path.cwd()
    if "agent" in kwargs and hasattr(kwargs["agent"], "additional_args"):
        ctx = kwargs["agent"].additional_args.get("context", {})
        if "project_root" in ctx:
            project_root = Path(ctx["project_root"])

    # Check each cited file exists
    missing_files = []
    for file_path, _ in citations:
        full_path = project_root / file_path
        abs_path = Path(file_path)

        if not full_path.exists() and not abs_path.exists():
            missing_files.append(file_path)

    # Fail if >=50% of cited files don't exist (likely hallucination)
    if missing_files and len(missing_files) / len(citations) >= 0.5:
        return False

    return True


def get_citation_stats(final_answer: str, agent_memory=None) -> dict[str, Any]:
    """Get statistics about citations in the final answer.

    Useful for debugging and reporting on citation quality.

    Args:
        final_answer: The agent's final answer string
        agent_memory: List of agent memory steps

    Returns:
        Dict with citation statistics
    """
    citation_pattern = r"([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+):(\d+)(?:-(\d+))?"
    citations = re.findall(citation_pattern, final_answer or "")

    # Collect valid refs
    valid_refs = set()
    if agent_memory:
        steps = agent_memory.get_full_steps() if hasattr(agent_memory, "get_full_steps") else []
        for step in steps:
            tool_output = None
            if hasattr(step, "observations"):
                tool_output = step.observations
            elif hasattr(step, "tool_output"):
                tool_output = step.tool_output
            elif isinstance(step, dict) and "observations" in step:
                tool_output = step["observations"]

            if tool_output:
                refs = re.findall(r"([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+):(\d+)", str(tool_output))
                for file_path, line_num in refs:
                    valid_refs.add((file_path, int(line_num)))
                    valid_refs.add((Path(file_path).name, int(line_num)))

    # Check each citation
    valid_citations = []
    invalid_citations = []
    for file_path, line_start, line_end in citations:
        line_num = int(line_start)
        basename = Path(file_path).name
        citation = f"{file_path}:{line_start}"
        if line_end:
            citation += f"-{line_end}"

        if (file_path, line_num) in valid_refs or (basename, line_num) in valid_refs:
            valid_citations.append(citation)
        else:
            invalid_citations.append(citation)

    return {
        "total": len(citations),
        "valid": len(valid_citations),
        "invalid": len(invalid_citations),
        "valid_citations": valid_citations,
        "invalid_citations": invalid_citations,
        "validation_passed": len(invalid_citations) == 0
        or len(invalid_citations) / max(len(citations), 1) < 0.2,
    }


# =============================================================================
# Structured Grep Tool with Context
# =============================================================================


class GrepWithContextTool(Tool if SMOLAGENTS_AVAILABLE else object):
    """Enhanced grep tool that returns structured output with context lines.

    This tool provides file:line references that can be validated by
    the validate_citations final_answer_check.
    """

    name = "grep_with_context"
    description = (
        "Search for text patterns in files with context lines. Returns structured "
        "results with exact file:line references for citations. Use this for findings "
        "that need to be cited in the review output."
    )
    inputs = {
        "pattern": {"type": "string", "description": "Text or regex pattern to search for"},
        "path": {
            "type": "string",
            "description": "Directory to search in (default: current directory)",
            "nullable": True,
        },
        "file_pattern": {
            "type": "string",
            "description": "Glob pattern for files to search (e.g., '*.py', '*.c')",
            "nullable": True,
        },
        "context_lines": {
            "type": "integer",
            "description": "Number of context lines before and after match (default: 2)",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, project_path: str = None):
        if SMOLAGENTS_AVAILABLE:
            super().__init__()
        self.project_path = project_path or "."

    def forward(
        self, pattern: str, path: str = None, file_pattern: str = None, context_lines: int = None
    ) -> str:
        """Execute grep with context and return structured output."""
        search_path = Path(path) if path else Path(self.project_path)
        file_glob = file_pattern or "*"
        ctx_lines = context_lines if context_lines is not None else 2

        if not search_path.exists():
            return f"Path not found: {search_path}"

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        results = []
        files_searched = 0

        for file_path in search_path.glob(f"**/{file_glob}"):
            if not file_path.is_file():
                continue
            files_searched += 1

            try:
                content = file_path.read_text()
                lines = content.splitlines()

                for i, line in enumerate(lines):
                    if regex.search(line):
                        line_num = i + 1  # 1-indexed

                        # Get context lines
                        start_ctx = max(0, i - ctx_lines)
                        end_ctx = min(len(lines), i + ctx_lines + 1)

                        context_before = []
                        for j in range(start_ctx, i):
                            context_before.append(f"  {j + 1:4d}| {lines[j]}")

                        context_after = []
                        for j in range(i + 1, end_ctx):
                            context_after.append(f"  {j + 1:4d}| {lines[j]}")

                        # Format result with clear file:line reference
                        result = f"\n### {file_path}:{line_num}\n"
                        if context_before:
                            result += "\n".join(context_before) + "\n"
                        result += f"> {line_num:4d}| {line}\n"  # Highlighted match line
                        if context_after:
                            result += "\n".join(context_after)

                        results.append(result)

                        if len(results) >= 30:  # Limit results
                            break

            except Exception:
                continue

            if len(results) >= 30:
                break

        if not results:
            return f"No matches for '{pattern}' in {search_path} ({files_searched} files searched). Try: broader pattern, different keywords, or list_directory first to see what files exist."

        header = f"## Search Results for '{pattern}'\n"
        header += f"Files searched: {files_searched} | Matches: {len(results)}\n"
        header += "Use file:line references below for citations.\n"

        return header + "\n".join(results)


# =============================================================================
# Test Coverage Analysis Tool
# =============================================================================


class TestCoverageAnalyzerTool(Tool if SMOLAGENTS_AVAILABLE else object):
    """Analyze test coverage by mapping source functions to test functions.

    Helps identify which source code functions have corresponding tests.
    """

    name = "analyze_test_coverage"
    description = (
        "Analyze test coverage by finding which functions in source files have "
        "corresponding test functions. Returns a coverage matrix showing tested "
        "and untested functions."
    )
    inputs = {
        "source_path": {
            "type": "string",
            "description": "Path to source file or directory to analyze",
        },
        "test_pattern": {
            "type": "string",
            "description": "Glob pattern for test files (default: 'test_*.py' or '*_test.c')",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, project_path: str = None):
        if SMOLAGENTS_AVAILABLE:
            super().__init__()
        self.project_path = project_path or "."

    def forward(self, source_path: str, test_pattern: str = None) -> str:
        """Analyze test coverage for source files."""
        src_path = Path(source_path)
        if not src_path.is_absolute():
            src_path = Path(self.project_path) / src_path

        if not src_path.exists():
            return f"Source path not found: {source_path}"

        # Determine file type and patterns
        if src_path.is_file():
            source_files = [src_path]
            suffix = src_path.suffix
        else:
            # Get all source files in directory
            source_files = (
                list(src_path.glob("**/*.py"))
                + list(src_path.glob("**/*.c"))
                + list(src_path.glob("**/*.js"))
                + list(src_path.glob("**/*.ts"))
            )
            suffix = ".py"  # Default

        # Determine test pattern based on file type
        if test_pattern:
            t_pattern = test_pattern
        elif suffix == ".py":
            t_pattern = "test_*.py"
        elif suffix in [".c", ".h"]:
            t_pattern = "*_test.c"
        else:
            t_pattern = "*.test.*"

        # Find test files
        project_root = Path(self.project_path)
        test_files = list(project_root.glob(f"**/{t_pattern}"))

        # Extract function names from source files
        func_pattern_py = r"^\s*def\s+(\w+)\s*\("
        func_pattern_c = r"^\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*\{"

        source_functions = {}
        for src_file in source_files:
            try:
                content = src_file.read_text()
                if src_file.suffix == ".py":
                    funcs = re.findall(func_pattern_py, content, re.MULTILINE)
                else:
                    funcs = re.findall(func_pattern_c, content, re.MULTILINE)
                # Filter out common non-function matches
                funcs = [f for f in funcs if not f.startswith("_") or f.startswith("__init")]
                source_functions[str(src_file)] = funcs
            except Exception:
                continue

        # Extract test function names
        test_functions = set()
        for test_file in test_files:
            try:
                content = test_file.read_text()
                # Look for test_ prefix functions
                tests = re.findall(r"def\s+(test_\w+)", content)
                test_functions.update(tests)
                # Also look for Test classes
                tests = re.findall(r"class\s+(Test\w+)", content)
                test_functions.update(tests)
            except Exception:
                continue

        # Build coverage report
        output = "## Test Coverage Analysis\n\n"
        output += f"Source files: {len(source_files)}\n"
        output += f"Test files: {len(test_files)}\n"
        output += f"Test functions found: {len(test_functions)}\n\n"

        total_funcs = 0
        tested_funcs = 0
        untested_list = []

        for src_file, funcs in source_functions.items():
            output += f"### {Path(src_file).name}\n"
            file_tested = 0
            file_untested = []

            for func in funcs:
                total_funcs += 1
                # Check if function has a corresponding test
                test_name = f"test_{func}"
                if test_name in test_functions or any(
                    func.lower() in t.lower() for t in test_functions
                ):
                    file_tested += 1
                    tested_funcs += 1
                    output += f"  [TESTED] {func}\n"
                else:
                    file_untested.append(func)
                    untested_list.append(f"{Path(src_file).name}:{func}")
                    output += f"  [MISSING] {func}\n"

            coverage_pct = (file_tested / len(funcs) * 100) if funcs else 0
            output += f"  Coverage: {file_tested}/{len(funcs)} ({coverage_pct:.0f}%)\n\n"

        # Summary
        overall_coverage = (tested_funcs / total_funcs * 100) if total_funcs > 0 else 0
        output += "## Summary\n"
        output += (
            f"- **Overall Coverage**: {tested_funcs}/{total_funcs} ({overall_coverage:.0f}%)\n"
        )
        output += f"- **Tested**: {tested_funcs}\n"
        output += f"- **Untested**: {total_funcs - tested_funcs}\n\n"

        if untested_list:
            output += "### Priority: Untested Functions\n"
            for item in untested_list[:20]:  # Show top 20
                output += f"- {item}\n"
            if len(untested_list) > 20:
                output += f"... and {len(untested_list) - 20} more\n"

        return output


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
            "description": "Search query - use affirmative statements for best results",
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
            return "Knowledge DB not available. Install with: pip install fastembed numpy"

        try:
            results = self.db.search(query, limit=5)
        except Exception as e:
            return f"Knowledge DB error: {e}"

        if not results:
            return "No relevant prior knowledge found. Try: different keywords, or proceed with file-based search using search_files and grep."

        output = "RELEVANT PRIOR KNOWLEDGE:\n\n"
        for r in results:
            # RRF scores are small (0.01-0.03), reranker handles relevance filtering
            output += f"### {r.get('title', 'Untitled')}\n"
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
        pattern: Glob pattern (e.g., "*.py", "src/**/*.ts"). ONE pattern only, no '|'.
        path: Directory to search in (default: current directory)
        recursive: If True, search recursively in subdirectories (default: True)

    Returns:
        List of matching file paths.
    """
    # Validate pattern
    if "|" in pattern:
        return f"Invalid pattern '{pattern}'. Use ONE pattern at a time, not '|' separated. Call multiple times for multiple patterns."
    if pattern == "**":
        return (
            "Invalid pattern '**'. Use '**/*' to match all files or '**/*.py' for specific types."
        )

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
        return f"No files matching '{pattern}' in {path}. Try: broader glob (e.g., '*.py' instead of 'auth*.py'), or use list_directory to explore the structure first."

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
        return f"No matches for '{pattern}' in {path}. Try: different search terms, broader file_pattern (e.g., '*' instead of '*.py'), or check spelling."

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
            timeout=30,
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
            timeout=30,
        )

        # Get detailed diff (limited to avoid huge output)
        detailed_diff = subprocess.run(
            ["git", "diff", f"HEAD~{commits}", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60,
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
            timeout=30,
        )
        if result.returncode != 0:
            return f"Git error: {result.stderr}"

        # Also get branch info
        branch_result = subprocess.run(
            ["git", "branch", "-v"], cwd=str(repo_path), capture_output=True, text=True, timeout=10
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
            timeout=30,
        )
        if result.returncode != 0:
            return f"Git error: {result.stderr}"

        output = "## Git Commit History\n\n"
        output += "| Hash | Author | Date | Message |\n"
        output += "|------|--------|------|----------|\n"

        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    output += f"| {parts[0]} | {parts[1]} | {parts[2]} | {parts[3]} |\n"

        return output

    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Git error: {e}"


@tool
def git_show(commit: str = "HEAD", path: str = ".") -> str:
    """
    Show the diff for a specific commit.

    Args:
        commit: Commit hash (e.g., "abc123", "HEAD", "HEAD~1"). Use 'commit' NOT 'hash'.
        path: Directory path of the git repository (default: current directory)

    Returns:
        Commit message and diff showing what changed in that commit.
    """
    import subprocess
    from pathlib import Path

    repo_path = Path(path)
    if not repo_path.exists():
        return f"Path not found: {path}"

    try:
        # Get commit info and diff
        result = subprocess.run(
            ["git", "show", commit, "--stat", "--patch"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"Git error: {result.stderr}. Try: git_log() first to see valid commit hashes."

        output = result.stdout
        # Truncate if too long
        if len(output) > 30000:
            output = output[:30000] + "\n\n... [truncated - diff too large]"

        return f"## Commit: {commit}\n\n```diff\n{output}\n```"

    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Git error: {e}"


@tool
def scan_secrets(path: str = ".", file_pattern: str = "*") -> str:
    """
    Scan files for potential hardcoded secrets (API keys, passwords, tokens).

    Args:
        path: Directory to scan (default: current directory)
        file_pattern: Glob pattern for files to scan (e.g., "*.py", "*.js")

    Returns:
        List of potential secrets found with file:line references.
    """
    import re
    from pathlib import Path

    base = Path(path)
    if not base.exists():
        return f"Path not found: {path}"

    # Common secret patterns
    patterns = {
        "API Key": r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        "AWS Key": r"(?i)(AKIA[0-9A-Z]{16})",
        "AWS Secret": r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
        "Password": r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
        "Token": r'(?i)(token|auth[_-]?token|access[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',
        "Private Key": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "GitHub Token": r"gh[pousr]_[a-zA-Z0-9]{36,}",
        "Generic Secret": r'(?i)secret\s*[=:]\s*["\']([^"\']{8,})["\']',
        "Bearer Token": r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}",
        "Basic Auth": r"(?i)basic\s+[a-zA-Z0-9+/=]{20,}",
    }

    findings = []
    files_scanned = 0

    # Skip common non-code directories
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".knowledge-db"}

    for file_path in base.glob(f"**/{file_pattern}"):
        if any(skip in file_path.parts for skip in skip_dirs):
            continue
        if not file_path.is_file():
            continue
        # Skip binary files
        if file_path.suffix in [".pyc", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".gif"]:
            continue

        files_scanned += 1
        try:
            content = file_path.read_text(errors="ignore")
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                # Skip comments and obvious test data
                if "example" in line.lower() or "test" in line.lower() or "xxx" in line.lower():
                    continue

                for secret_type, pattern in patterns.items():
                    if re.search(pattern, line):
                        # Mask the actual secret value
                        masked_line = (
                            line.strip()[:80] + "..." if len(line.strip()) > 80 else line.strip()
                        )
                        findings.append(
                            f"**{secret_type}** at `{file_path}:{i}`\n  `{masked_line}`"
                        )
                        break  # One finding per line

        except Exception:
            continue

        if len(findings) >= 50:
            break

    if not findings:
        return f"No potential secrets found in {path} ({files_scanned} files scanned). Note: This is a basic scan - use dedicated tools like 'detect-secrets' or 'gitleaks' for thorough scanning."

    output = "## Potential Secrets Found\n\n"
    output += f"Files scanned: {files_scanned}\n"
    output += f"Findings: {len(findings)}\n\n"
    output += "**WARNING**: Review each finding - some may be false positives.\n\n"
    output += "\n\n".join(findings)

    return output


@tool
def get_complexity(file_path: str) -> str:
    """
    Analyze code complexity metrics for a source file.

    Supports Python (.py) via ast module, and C/C++ (.c, .cpp, .h, .hpp, .cc, .cxx) via lizard.

    Args:
        file_path: Path to the source file to analyze

    Returns:
        Complexity metrics including function length, cyclomatic complexity, and nesting depth.
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"

    ext = path.suffix.lower()

    # Route to appropriate analyzer
    if ext == ".py":
        return _python_complexity(path)
    elif ext in [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"]:
        return _lizard_complexity(path)
    else:
        return f"Unsupported file type: {ext}. Supported: .py, .c, .cpp, .cc, .cxx, .h, .hpp"


def _lizard_complexity(path) -> str:
    """Analyze C/C++ complexity using lizard."""
    try:
        import lizard
    except ImportError:
        return "lizard not installed. Install with: pipx inject kln-ai lizard"

    result = lizard.analyze_file(str(path))
    if not result:
        return f"Could not analyze {path.name}"

    functions = result.function_list
    total_lines = result.nloc

    output = f"## Complexity Analysis: {path.name}\n\n"
    output += f"Total NLOC: {total_lines}\n"
    output += f"Functions analyzed: {len(functions)}\n\n"

    if not functions:
        return output + "No functions found in file."

    # Summary table
    output += "| Function | Line | NLOC | CCN | Params | Status |\n"
    output += "|----------|------|------|-----|--------|--------|\n"

    critical_count = 0
    warn_count = 0
    problem_funcs = []

    for f in functions:
        status = "OK"
        issues = []

        if f.nloc > 50:
            issues.append(f"long ({f.nloc} lines)")
            status = "WARN"
        if f.cyclomatic_complexity > 10:
            issues.append(f"complex (CCN={f.cyclomatic_complexity})")
            status = "WARN"
        if f.parameter_count > 6:
            issues.append(f"many params ({f.parameter_count})")
            status = "WARN"

        if f.nloc > 100 or f.cyclomatic_complexity > 15:
            status = "CRITICAL"

        if status == "CRITICAL":
            critical_count += 1
        elif status == "WARN":
            warn_count += 1

        if issues:
            problem_funcs.append((f, issues))

        name = f.name[:30] if len(f.name) > 30 else f.name
        output += f"| {name} | {f.start_line} | {f.nloc} | {f.cyclomatic_complexity} | {f.parameter_count} | {status} |\n"

    output += f"\n**Summary**: {critical_count} critical, {warn_count} warnings, {len(functions) - critical_count - warn_count} OK\n"

    if problem_funcs:
        output += "\n### Issues Found\n\n"
        for f, issues in problem_funcs:
            output += f"- `{path.name}:{f.start_line}` **{f.name}**: {', '.join(issues)}\n"

    return output


def _python_complexity(path) -> str:
    """Analyze Python complexity using ast module."""
    import ast

    try:
        content = path.read_text()
        tree = ast.parse(content)
    except SyntaxError as e:
        return f"Syntax error in {path}: {e}"

    lines = content.splitlines()
    total_lines = len(lines)

    functions = []

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_function = None
            self.max_nesting = 0
            self.current_nesting = 0

        def visit_FunctionDef(self, node):
            self._analyze_function(node)

        def visit_AsyncFunctionDef(self, node):
            self._analyze_function(node)

        def _analyze_function(self, node):
            func_name = node.name
            start_line = node.lineno
            end_line = node.end_lineno or start_line
            func_length = end_line - start_line + 1

            # Count branches (if, for, while, try, with)
            branches = 0
            max_nesting = 0

            for child in ast.walk(node):
                if isinstance(
                    child,
                    (
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.Try,
                        ast.With,
                        ast.AsyncFor,
                        ast.AsyncWith,
                        ast.ExceptHandler,
                    ),
                ):
                    branches += 1

            # Simple nesting calculation
            def get_nesting(n, depth=0):
                max_d = depth
                for child in ast.iter_child_nodes(n):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                        max_d = max(max_d, get_nesting(child, depth + 1))
                    else:
                        max_d = max(max_d, get_nesting(child, depth))
                return max_d

            max_nesting = get_nesting(node)

            # Cognitive complexity approximation
            cognitive = branches + (max_nesting * 2)

            status = "OK"
            issues = []
            if func_length > 50:
                issues.append(f"too long ({func_length} lines)")
                status = "WARN"
            if max_nesting > 4:
                issues.append(f"deep nesting ({max_nesting})")
                status = "WARN"
            if cognitive > 15:
                issues.append(f"high complexity ({cognitive})")
                status = "WARN"
            if func_length > 100 or max_nesting > 6 or cognitive > 25:
                status = "CRITICAL"

            functions.append(
                {
                    "name": func_name,
                    "line": start_line,
                    "length": func_length,
                    "branches": branches,
                    "nesting": max_nesting,
                    "cognitive": cognitive,
                    "status": status,
                    "issues": issues,
                }
            )

            self.generic_visit(node)

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    # Build output
    output = f"## Complexity Analysis: {path.name}\n\n"
    output += f"Total lines: {total_lines}\n"
    output += f"Functions analyzed: {len(functions)}\n\n"

    if not functions:
        return output + "No functions found in file."

    # Summary table
    output += "| Function | Line | Length | Branches | Nesting | Status |\n"
    output += "|----------|------|--------|----------|---------|--------|\n"

    critical_count = 0
    warn_count = 0

    for f in functions:
        status_icon = (
            "OK" if f["status"] == "OK" else ("WARN" if f["status"] == "WARN" else "CRITICAL")
        )
        if f["status"] == "CRITICAL":
            critical_count += 1
        elif f["status"] == "WARN":
            warn_count += 1
        output += f"| {f['name'][:30]} | {f['line']} | {f['length']} | {f['branches']} | {f['nesting']} | {status_icon} |\n"

    output += f"\n**Summary**: {critical_count} critical, {warn_count} warnings, {len(functions) - critical_count - warn_count} OK\n"

    # Details for problematic functions
    problem_funcs = [f for f in functions if f["issues"]]
    if problem_funcs:
        output += "\n### Issues Found\n\n"
        for f in problem_funcs:
            output += f"- `{path.name}:{f['line']}` **{f['name']}**: {', '.join(f['issues'])}\n"

    return output


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
                if item.name.startswith("."):
                    continue  # Skip hidden files
                if item.is_dir():
                    items.append(f"{indent}[DIR] {item.name}/")
                    if recursive and depth < max_depth:
                        items.extend(list_dir(item, depth + 1))
                else:
                    size = item.stat().st_size
                    size_str = f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
                    items.append(f"{indent}[FILE] {item.name} ({size_str})")
        except PermissionError:
            items.append(f"{indent}[ERROR] Permission denied")
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
    from datetime import datetime
    from pathlib import Path

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
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React JSX",
            ".tsx": "React TSX",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C Header",
            ".md": "Markdown",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            ".xml": "XML",
            ".html": "HTML",
            ".css": "CSS",
            ".sql": "SQL",
            ".sh": "Shell Script",
        }
        file_type = type_map.get(suffix, suffix if suffix else "Unknown")

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
            size_str += f" ({size / 1024:.1f} KB)"
        if size > 1024 * 1024:
            size_str = f"{size:,} bytes ({size / 1024 / 1024:.1f} MB)"

        return f"""## File Info: {path.name}

- **Path**: {file_path}
- **Type**: {file_type}
- **Size**: {size_str}
- **Lines**: {lines}
- **Modified**: {modified.strftime("%Y-%m-%d %H:%M:%S")}
"""

    except Exception as e:
        return f"Error getting file info: {e}"


def get_default_tools(
    project_path: str = None, use_mcp: bool = True, mcp_servers: list = None
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
    tool_names: list[str],
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
                pattern: Glob pattern (e.g., "*.py", "src/**/*.ts"). ONE pattern only, no '|'.
                path: Directory to search in (default: project root)
                recursive: If True, search recursively in subdirectories

            Returns:
                List of matching file paths.
            """
            # Validate pattern
            if "|" in pattern:
                return f"Invalid pattern '{pattern}'. Use ONE pattern, not '|' separated."
            if pattern == "**":
                return "Invalid pattern '**'. Use '**/*' or '**/*.py'."

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
                return f"No files matching '{pattern}' in {path}. Try: broader glob (e.g., '*.py'), or use list_directory to see what exists."

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
                return f"No matches for '{pattern}' in {path}. Try: different keywords, broader file_pattern, or search_files first to find relevant files."

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
    if "git_show" in tool_names:
        tools.append(git_show)

    # Add security and analysis tools
    if "scan_secrets" in tool_names:
        tools.append(scan_secrets)
    if "get_complexity" in tool_names:
        tools.append(get_complexity)

    # Add file info tools
    if "list_directory" in tool_names:
        tools.append(list_directory)
    if "get_file_info" in tool_names:
        tools.append(get_file_info)

    # Add enhanced tools for citation-aware output
    if "grep_with_context" in tool_names:
        tools.append(GrepWithContextTool(project_path))
    if "analyze_test_coverage" in tool_names:
        tools.append(TestCoverageAnalyzerTool(project_path))

    return tools
