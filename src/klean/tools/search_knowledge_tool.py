"""Search knowledge database tool for Agent SDK droids.

This tool allows droids to query the knowledge database in real-time during analysis.
Uses TCP connection to the knowledge server (cross-platform).
"""

from typing import Any

from ..tools import tool


@tool("search_knowledge", "Search knowledge database for information")
async def search_knowledge(
    query: str,
    limit: int = 5,
    min_score: float = 0.3,
) -> dict[str, Any]:
    """Search knowledge database for relevant information.

    This tool enables droids to integrate knowledge from the project's
    knowledge database, enhancing analysis with learned patterns,
    best practices, and historical findings.

    Uses TCP connection to the knowledge server (cross-platform).

    Args:
        query: Search query (e.g., "SQL injection prevention")
        limit: Maximum results to return (default: 5)
        min_score: Minimum relevance score 0.0-1.0 (default: 0.3)

    Returns:
        Dict with search results:
            - success: Whether search succeeded
            - query: Original search query
            - results: List of matching knowledge items
            - total: Number of results found
            - error: Error message if search failed

    Example:
        # In SecurityAuditorDroid.Turn2:
        kb_result = await search_knowledge(
            query="CWE-89 SQL injection OWASP",
            limit=3
        )
        if kb_result["success"]:
            for item in kb_result["results"]:
                print(f"Found: {item.get('title')}")
    """
    import sys
    from pathlib import Path

    try:
        # Add scripts dir to path for kb_utils import (inside function to avoid import issues)
        scripts_dir = Path(__file__).parent.parent / "data" / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        # Import kb_utils for TCP communication
        try:
            from kb_utils import find_project_root, search
        except ImportError:
            return {
                "success": False,
                "error": "kb_utils not available - knowledge server may not be installed",
                "query": query,
            }

        # Find project root
        project_path = find_project_root()
        if not project_path:
            return {
                "success": False,
                "error": "Not in a project directory (no .git, .claude, or .knowledge-db found)",
                "query": query,
            }

        # Query via TCP
        result = search(project_path, query, limit=limit)

        if result is None:
            return {
                "success": False,
                "error": "Knowledge server not running. Start with: kln start -s knowledge",
                "query": query,
            }

        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "query": query,
            }

        # Extract results
        results = result.get("results", [])

        # Filter by relevance score
        filtered = [
            r for r in results if isinstance(r, dict) and r.get("relevance_score", 0) >= min_score
        ]

        return {
            "success": True,
            "query": query,
            "results": filtered,
            "total": len(filtered),
            "search_time_ms": result.get("search_time_ms"),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
        }
