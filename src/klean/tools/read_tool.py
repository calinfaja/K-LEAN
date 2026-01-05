"""Read file tool for Agent SDK droids.

This tool allows droids to read file contents for analysis.
"""

from pathlib import Path
from typing import Any, Optional

from ..tools import tool


@tool("read_file", "Read file contents for analysis")
async def read_file(
    path: str,
    lines: Optional[int] = None,
    offset: Optional[int] = None,
) -> dict[str, Any]:
    """Read file contents for code analysis.

    This tool enables droids to read files for deeper analysis, code inspection,
    understanding specific implementations, etc.

    Args:
        path: Path to file to read
        lines: Optional limit on number of lines to read
        offset: Optional line offset to start from

    Returns:
        Dict with file contents:
            - content: File contents as string
            - lines: Number of lines in content
            - path: Full path to file
            - size_bytes: File size in bytes
            - truncated: Whether output was truncated
            - error: Error message if read failed

    Example:
        result = await read_file(
            path="src/auth.py",
            lines=50,
            offset=100
        )
        if "password" in result.get("content", ""):
            print("Warning: Found 'password' in file")
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            return {
                "error": f"File not found: {path}",
                "path": str(file_path),
            }

        if not file_path.is_file():
            return {
                "error": f"Path is not a file: {path}",
                "path": str(file_path),
            }

        # Read file content
        content = file_path.read_text(errors="ignore")

        # Apply line limits if requested
        if offset or lines:
            content_lines = content.split("\n")
            start = offset or 0
            end = start + (lines or len(content_lines))
            content_lines = content_lines[start:end]
            truncated = end < len(content.split("\n"))
            content = "\n".join(content_lines)
        else:
            truncated = False

        return {
            "content": content,
            "lines": len(content.split("\n")),
            "path": str(file_path.absolute()),
            "size_bytes": len(content),
            "truncated": truncated,
        }

    except Exception as e:
        return {
            "error": str(e),
            "path": path,
        }
