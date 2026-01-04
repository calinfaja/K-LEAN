#!/usr/bin/env python3
"""
Knowledge Search - CLI interface for semantic knowledge search

Usage:
    knowledge-search.py "query" [options]

Examples:
    knowledge-search.py "BLE power optimization"
    knowledge-search.py "authentication patterns" --limit 10
    knowledge-search.py "React hooks" --format compact
    knowledge-search.py "error handling" --format inject
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from knowledge_db import KnowledgeDB, find_project_root
except ImportError:
    # Fallback: define minimal find_project_root
    import os

    def find_project_root(start_path=None):
        current = Path(start_path or os.getcwd()).resolve()
        while current != current.parent:
            if (
                (current / ".serena").exists()
                or (current / ".claude").exists()
                or (current / ".knowledge-db").exists()
            ):
                return current
            current = current.parent
        return None


def format_compact(results):
    """Compact format for quick overview."""
    lines = []
    for r in results:
        score = r.get("score", 0)
        title = r.get("title", "Untitled")
        lines.append(f"[{score:.2f}] {title}")
    return "\n".join(lines)


def format_detailed(results):
    """Detailed format with all metadata."""
    lines = []
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        title = r.get("title", "Untitled")
        lines.append(f"\n{'=' * 60}")
        lines.append(f"[{i}] {title} (score: {score:.2f})")
        lines.append(f"{'=' * 60}")

        if r.get("url"):
            lines.append(f"URL: {r['url']}")
        if r.get("type"):
            lines.append(f"Type: {r['type']}")
        if r.get("found_date"):
            lines.append(f"Date: {r['found_date'][:10]}")
        if r.get("summary"):
            lines.append(f"\nSummary: {r['summary']}")
        if r.get("problem_solved"):
            lines.append(f"\nProblem Solved: {r['problem_solved']}")
        if r.get("key_concepts"):
            concepts = r["key_concepts"]
            if isinstance(concepts, str):
                # SQLite stored it as string, try to parse
                try:
                    import json

                    concepts = json.loads(concepts)
                except (json.JSONDecodeError, TypeError):
                    concepts = [concepts]
            if isinstance(concepts, list):
                lines.append(f"Concepts: {', '.join(concepts)}")
        if r.get("what_worked"):
            lines.append(f"\nWhat Worked: {r['what_worked']}")
        if r.get("constraints"):
            lines.append(f"Constraints: {r['constraints']}")

    return "\n".join(lines)


def format_inject(results):
    """
    Format for injection into LLM prompts.
    Optimized for headless Claude instances.
    """
    if not results:
        return "No relevant prior knowledge found."

    lines = ["RELEVANT PRIOR KNOWLEDGE:", ""]

    for r in results:
        score = r.get("score", 0)
        if score < 0.3:  # Skip low relevance
            continue

        title = r.get("title", "Untitled")
        lines.append(f"### {title} (relevance: {score:.0%})")

        if r.get("url"):
            lines.append(f"Source: {r['url']}")
        if r.get("summary"):
            lines.append(f"{r['summary']}")
        if r.get("problem_solved"):
            lines.append(f"Solves: {r['problem_solved']}")
        if r.get("what_worked"):
            lines.append(f"Solution: {r['what_worked']}")

        lines.append("")

    if len(lines) <= 2:
        return "No highly relevant prior knowledge found."

    return "\n".join(lines)


def format_json(results):
    """JSON format for programmatic use."""
    return json.dumps(results, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Semantic knowledge search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "BLE optimization"           # Basic search
  %(prog)s "auth" --format inject       # For LLM injection
  %(prog)s "React" -n 10 --json         # JSON output, 10 results
        """,
    )

    parser.add_argument("query", help="Search query (natural language)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Maximum results (default: 5)")
    parser.add_argument(
        "--format",
        "-f",
        choices=["compact", "detailed", "inject", "json"],
        default="detailed",
        help="Output format (default: detailed)",
    )
    parser.add_argument("--project", "-p", help="Project path (default: auto-detect)")
    parser.add_argument("--json", action="store_true", help="Shortcut for --format json")
    parser.add_argument(
        "--min-score", type=float, default=0.0, help="Minimum relevance score (0-1)"
    )

    args = parser.parse_args()

    # Handle --json shortcut
    if args.json:
        args.format = "json"

    # Find project and initialize DB
    try:
        db = KnowledgeDB(args.project)
    except ValueError as e:
        if args.format == "json":
            print(json.dumps({"error": str(e), "results": []}))
        elif args.format == "inject":
            print("No knowledge database found for this project.")
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.format == "json":
            print(json.dumps({"error": str(e), "results": []}))
        elif args.format == "inject":
            print("Knowledge database not available.")
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Search
    results = db.search(args.query, limit=args.limit)

    # Filter by minimum score
    if args.min_score > 0:
        results = [r for r in results if r.get("score", 0) >= args.min_score]

    # Format output
    formatters = {
        "compact": format_compact,
        "detailed": format_detailed,
        "inject": format_inject,
        "json": format_json,
    }

    output = formatters[args.format](results)
    print(output)

    # Return appropriate exit code
    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
