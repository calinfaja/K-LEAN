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
    """Compact format for quick overview -- human-readable, no raw scores."""
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        entry_type = r.get("type", "")
        date = (r.get("date") or r.get("found_date", ""))[:10]
        entry_id = r.get("id", "")[:8]
        insight = r.get("insight") or r.get("summary") or ""
        # Truncate insight to ~80 chars at word boundary
        if len(insight) > 80:
            insight = insight[:77].rsplit(" ", 1)[0] + "..."
        lines.append(f"{i}. [{entry_type}] {title} ({date}) [id:{entry_id}]")
        if insight:
            lines.append(f"   {insight}")
    return "\n".join(lines)


def format_detailed(results):
    """Detailed format with all metadata."""
    lines = []
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        title = r.get("title", "Untitled")
        entry_id = r.get("id", "")
        lines.append(f"\n{'=' * 60}")
        lines.append(f"[{i}] {title} (score: {score:.2f})")
        lines.append(f"{'=' * 60}")
        lines.append(f"ID: {entry_id}")

        if r.get("type"):
            lines.append(f"Type: {r['type']}")
        if r.get("priority"):
            lines.append(f"Priority: {r['priority']}")
        if r.get("date") or r.get("found_date"):
            lines.append(f"Date: {(r.get('date') or r.get('found_date', ''))[:10]}")
        if r.get("source"):
            lines.append(f"Source: {r['source']}")
        if r.get("branch"):
            lines.append(f"Branch: {r['branch']}")

        # V3 insight (preferred) or V2 summary
        insight = r.get("insight") or r.get("summary")
        if insight:
            lines.append(f"\nInsight: {insight}")
        if r.get("keywords") or r.get("tags"):
            kw = r.get("keywords") or r.get("tags", [])
            if isinstance(kw, list):
                lines.append(f"Keywords: {', '.join(kw)}")
        if r.get("pinned"):
            lines.append("Pinned: yes")

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


def format_single_entry(entry):
    """Format a single entry for --id detail view."""
    lines = [f"{'=' * 60}"]
    lines.append(f"Title: {entry.get('title', 'Untitled')}")
    lines.append(f"ID: {entry.get('id', '')}")
    lines.append(f"Type: {entry.get('type', 'finding')}")
    lines.append(f"Priority: {entry.get('priority', 'medium')}")
    if entry.get("date"):
        lines.append(f"Date: {entry['date'][:10]}")
    if entry.get("source"):
        lines.append(f"Source: {entry['source']}")
    if entry.get("branch"):
        lines.append(f"Branch: {entry['branch']}")
    if entry.get("pinned"):
        lines.append("Pinned: yes")

    insight = entry.get("insight") or entry.get("summary")
    if insight:
        lines.append(f"\nInsight:\n{insight}")

    kw = entry.get("keywords") or entry.get("tags", [])
    if isinstance(kw, list) and kw:
        lines.append(f"\nKeywords: {', '.join(kw)}")

    related = entry.get("related_to", [])
    if related:
        lines.append(f"Related: {', '.join(related)}")

    lines.append(f"{'=' * 60}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Semantic knowledge search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "BLE optimization"                       # Basic search
  %(prog)s "auth" --format inject                   # For LLM injection
  %(prog)s "React" -n 10 --json                     # JSON output, 10 results
  %(prog)s "memory leak" --since 2026-02-01         # Recent entries only
  %(prog)s "crash" --type warning                   # Only warnings
  %(prog)s --id abc12345                            # Get entry by ID
        """,
    )

    parser.add_argument("query", nargs="?", default="", help="Search query (natural language)")
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
    # Filters (passed to KnowledgeDB.search())
    parser.add_argument("--since", help="Entries from this date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Entries up to this date (YYYY-MM-DD)")
    parser.add_argument("--type", dest="entry_type", help="Filter by type (warning, solution, etc)")
    parser.add_argument("--branch", help="Filter by git branch")
    # Detail retrieval
    parser.add_argument("--id", dest="entry_id", help="Get a specific entry by ID (full or prefix)")

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

    # Detail retrieval mode
    if args.entry_id:
        entry = db.get(args.entry_id)
        # Try prefix match if exact match fails
        if not entry:
            for e in db._entries:
                if e.get("id", "").startswith(args.entry_id):
                    entry = e
                    break
        if entry:
            if args.format == "json":
                print(json.dumps(entry, indent=2))
            else:
                print(format_single_entry(entry))
            sys.exit(0)
        else:
            if args.format == "json":
                print(json.dumps({"error": f"Entry not found: {args.entry_id}"}))
            else:
                print(f"Entry not found: {args.entry_id}", file=sys.stderr)
            sys.exit(1)

    # Search mode requires a query
    if not args.query:
        parser.error("query is required (or use --id for detail retrieval)")

    # Search with filters
    results = db.search(
        args.query,
        limit=args.limit,
        date_from=args.since,
        date_to=args.until,
        entry_type=args.entry_type,
        branch=args.branch,
    )

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
