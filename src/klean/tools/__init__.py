"""K-LEAN Tools - Custom tools for SmolKLN agents.

This module provides a framework for defining custom tools that can be used
by SmolKLN agents for enhanced code analysis capabilities.
"""

from typing import Any, Callable, Dict, Optional


def tool(
    name: str,
    description: str,
    schema: Optional[dict[str, Any]] = None,
):
    """Decorator for defining Agent SDK tools.

    This decorator marks a function as a tool that can be used by
    SmolKLN agents. Tools are async functions that can be called
    by Claude during analysis.

    Args:
        name: Tool name (e.g., "grep_codebase")
        description: Human-readable description of what the tool does
        schema: Optional JSON Schema for tool parameters

    Example:
        @tool("grep_codebase", "Search for patterns in code")
        async def grep(pattern: str, path: str = ".") -> str:
            # implementation
            return results

    Returns:
        Decorator function that marks a function as a tool
    """

    def decorator(func: Callable) -> Callable:
        # Mark function as a tool
        func._is_tool = True
        func._tool_name = name
        func._tool_description = description
        func._tool_schema = schema or {}
        return func

    return decorator


# Import all tools
from .grep_tool import grep_codebase
from .read_tool import read_file
from .search_knowledge_tool import search_knowledge
from .testing_tool import run_tests

__all__ = [
    "tool",
    "grep_codebase",
    "read_file",
    "search_knowledge",
    "run_tests",
]
