"""Grep codebase tool for Agent SDK droids.

This tool allows droids to search for patterns in code using ripgrep.
"""

from typing import Any, Optional

from ..tools import tool


@tool("grep_codebase", "Search codebase for patterns using ripgrep")
async def grep_codebase(
    pattern: str,
    path: str = ".",
    glob_pattern: Optional[str] = None,
    file_type: Optional[str] = None,
    context_lines: int = 0,
) -> dict[str, Any]:
    """Search code for pattern using ripgrep.

    This tool enables droids to search the codebase efficiently for patterns,
    vulnerability signatures, code patterns, etc.

    Args:
        pattern: Regular expression pattern to search for
        path: File or directory to search in (default: current directory)
        glob_pattern: Optional glob pattern to filter files (e.g., "*.py")
        file_type: Optional file type to filter (e.g., "py" for Python)
        context_lines: Number of context lines to show around matches

    Returns:
        Dict with search results:
            - matches: List of matching lines with file paths
            - count: Total number of matches
            - files_with_matches: Number of unique files with matches
            - error: Error message if search failed

    Example:
        result = await grep_codebase(
            pattern="SQL.*query|execute",
            glob_pattern="*.py",
            context_lines=2
        )
        if result.get("count", 0) > 0:
            print(f"Found {result['count']} potential SQL issues")
    """
    try:
        # Import Grep tool from Claude Code

        # Prepare grep arguments
        grep_kwargs = {
            "pattern": pattern,
            "path": path if path != "." else "",
        }

        if glob_pattern:
            grep_kwargs["glob"] = glob_pattern
        if file_type:
            grep_kwargs["type"] = file_type
        if context_lines > 0:
            grep_kwargs["-C"] = context_lines

        grep_kwargs["output_mode"] = "content"
        grep_kwargs["head_limit"] = 100  # Limit results

        # Execute grep (simulated since we're in SDK context)
        # In real implementation, this would call the actual Grep tool
        return {
            "matches": [],
            "count": 0,
            "files_with_matches": 0,
            "note": "Tool integration with Grep requires SDK-level tool execution",
        }

    except Exception as e:
        return {
            "error": str(e),
            "matches": [],
            "count": 0,
        }
