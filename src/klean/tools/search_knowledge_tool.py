"""Search knowledge database tool for Agent SDK droids.

This tool allows droids to query the knowledge database in real-time during analysis.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from ..tools import tool


@tool("search_knowledge", "Search knowledge database for information")
async def search_knowledge(
    query: str,
    limit: int = 5,
    min_score: float = 0.3,
) -> Dict[str, Any]:
    """Search knowledge database for relevant information.

    This tool enables droids to integrate knowledge from the project's
    knowledge database, enhancing analysis with learned patterns,
    best practices, and historical findings.

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
    try:
        # Try to query knowledge server via socket
        script_path = Path.home() / ".claude" / "scripts" / "knowledge-query.sh"

        if not script_path.exists():
            return {
                "success": False,
                "error": "Knowledge query script not found",
                "query": query,
            }

        # Execute knowledge query
        result = subprocess.run(
            [str(script_path), query],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr if result.stderr else "Query failed",
                "query": query,
            }

        # Parse results
        try:
            results = json.loads(result.stdout)
            if not isinstance(results, list):
                results = [results] if results else []
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON from knowledge server",
                "query": query,
                "raw": result.stdout[:500],
            }

        # Filter by relevance score
        filtered = [
            r for r in results
            if isinstance(r, dict) and r.get("relevance_score", 0) >= min_score
        ]

        # Limit results
        filtered = filtered[:limit]

        return {
            "success": True,
            "query": query,
            "results": filtered,
            "total": len(filtered),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Knowledge search timeout",
            "query": query,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
        }
