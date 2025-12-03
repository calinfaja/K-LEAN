#!/home/calin/.venvs/knowledge-db/bin/python
"""
Knowledge Database - Core txtai integration for semantic search

This module provides a KnowledgeDB class that wraps txtai for:
- Storing knowledge entries with metadata
- Semantic search across all entries
- Auto-detection of project's .knowledge-db directory

Usage:
    from knowledge_db import KnowledgeDB

    db = KnowledgeDB()  # Auto-detects project root
    db.add({
        "title": "BLE Optimization",
        "summary": "Nordic's guide on connection intervals",
        "url": "https://...",
        ...
    })
    results = db.search("power optimization")
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# txtai imports
try:
    from txtai import Embeddings
except ImportError:
    print("ERROR: txtai not installed. Run: ~/.venvs/knowledge-db/bin/pip install txtai[database,ann]")
    sys.exit(1)


def find_project_root(start_path: str = None) -> Optional[Path]:
    """
    Find project root by looking for .serena, .claude, or .knowledge-db directories.
    Walks up from start_path until found or reaches root.
    """
    current = Path(start_path or os.getcwd()).resolve()

    while current != current.parent:
        # Check for project markers
        if (current / ".serena").exists() or \
           (current / ".claude").exists() or \
           (current / ".knowledge-db").exists():
            return current
        current = current.parent

    return None


class KnowledgeDB:
    """
    Semantic knowledge database using txtai.

    Stores entries in project's .knowledge-db/ directory with:
    - SQLite backend for metadata storage
    - Vector embeddings for semantic search
    - JSONL backup for human-readable records
    """

    def __init__(self, project_path: str = None):
        """
        Initialize KnowledgeDB.

        Args:
            project_path: Path to project root. If None, auto-detects.
        """
        if project_path:
            self.project_root = Path(project_path).resolve()
        else:
            self.project_root = find_project_root()

        if not self.project_root:
            raise ValueError(
                "Could not find project root. "
                "Make sure you're in a directory with .serena, .claude, or .knowledge-db"
            )

        self.db_path = self.project_root / ".knowledge-db"
        self.index_path = self.db_path / "index"
        self.jsonl_path = self.db_path / "entries.jsonl"

        # Create directory if needed
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize embeddings with SQLite backend
        self.embeddings = Embeddings(
            content=True,  # Store content alongside vectors
            backend="sqlite",  # Use SQLite for storage
            path="sentence-transformers/all-MiniLM-L6-v2"  # Fast, good quality model
        )

        # Load existing index if present
        if self.index_path.exists():
            self.embeddings.load(str(self.index_path))

    def add(self, entry: Dict[str, Any]) -> str:
        """
        Add a knowledge entry to the database.

        Args:
            entry: Dictionary with knowledge entry fields:
                - title (required): Short title
                - summary (required): What was found
                - type: web|code|solution|lesson
                - url: Source URL
                - problem_solved: What problem this solves
                - key_concepts: List of keywords/concepts
                - relevance_score: 0-1 score from Haiku
                - project_context: Related project/topic
                - what_worked: For solutions, what worked
                - constraints: Any limitations

        Returns:
            Entry ID (UUID)
        """
        # Generate ID if not provided
        entry_id = entry.get("id") or str(uuid.uuid4())
        entry["id"] = entry_id

        # Add timestamp
        entry["found_date"] = entry.get("found_date") or datetime.now().isoformat()

        # Ensure required fields
        if "title" not in entry:
            raise ValueError("Entry must have 'title' field")
        if "summary" not in entry:
            raise ValueError("Entry must have 'summary' field")

        # Build searchable text from key fields
        searchable_parts = [
            entry.get("title", ""),
            entry.get("summary", ""),
            entry.get("problem_solved", ""),
            " ".join(entry.get("key_concepts", [])),
            entry.get("what_worked", ""),
        ]
        searchable_text = " ".join(filter(None, searchable_parts))

        # Upsert in txtai - format: (id, {"text": ..., ...metadata}, None)
        # Use upsert to add or update entries (not overwrite entire index)
        doc = {"text": searchable_text, **entry}
        self.embeddings.upsert([(entry_id, doc, None)])

        # Save index
        self.embeddings.save(str(self.index_path))

        # Append to JSONL backup
        with open(self.jsonl_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry_id

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search across all entries.

        Args:
            query: Natural language search query
            limit: Maximum number of results

        Returns:
            List of matching entries with scores
        """
        if not self.index_path.exists():
            return []

        # Use SQL query to get full content with metadata
        sql_query = f"select id, text, title, summary, url, type, problem_solved, key_concepts, relevance_score, what_worked, constraints, found_date, score from txtai where similar('{query}') limit {limit}"

        try:
            results = self.embeddings.search(sql_query)
        except Exception:
            # Fallback to simple search if SQL fails
            results = self.embeddings.search(query, limit=limit)

        # Format results
        formatted = []
        for result in results:
            if isinstance(result, dict):
                formatted.append({
                    "score": result.get("score", 0),
                    "id": result.get("id"),
                    "title": result.get("title", ""),
                    "summary": result.get("summary", ""),
                    "url": result.get("url", ""),
                    "type": result.get("type", ""),
                    "problem_solved": result.get("problem_solved", ""),
                    "key_concepts": result.get("key_concepts", []),
                    "relevance_score": result.get("relevance_score", 0),
                    "what_worked": result.get("what_worked", ""),
                    "constraints": result.get("constraints", ""),
                    "found_date": result.get("found_date", ""),
                })
            elif isinstance(result, tuple):
                # Handle tuple format (id, score)
                formatted.append({
                    "score": result[1] if len(result) > 1 else 0,
                    "id": result[0]
                })

        return formatted

    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific entry by ID.

        Args:
            entry_id: Entry UUID

        Returns:
            Entry dictionary or None if not found
        """
        results = self.embeddings.search(
            f"select * from txtai where id = '{entry_id}'"
        )
        return results[0] if results else None

    def stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with count, size, last_updated
        """
        count = 0
        size_bytes = 0
        last_updated = None

        if self.index_path.exists():
            # Count entries
            try:
                count = self.embeddings.count()
            except:
                # Fallback: count JSONL lines
                if self.jsonl_path.exists():
                    with open(self.jsonl_path) as f:
                        count = sum(1 for _ in f)

            # Get size
            for f in self.db_path.rglob("*"):
                if f.is_file():
                    size_bytes += f.stat().st_size

            # Last modified
            last_updated = datetime.fromtimestamp(
                self.index_path.stat().st_mtime
            ).isoformat()

        return {
            "count": count,
            "size_bytes": size_bytes,
            "size_human": f"{size_bytes / 1024:.1f} KB",
            "last_updated": last_updated,
            "db_path": str(self.db_path)
        }

    def rebuild_index(self) -> int:
        """
        Rebuild the txtai index from JSONL backup.
        This reads all entries from entries.jsonl and creates a fresh index.

        Returns:
            Number of entries indexed
        """
        if not self.jsonl_path.exists():
            return 0

        # Read all entries from JSONL
        entries = []
        with open(self.jsonl_path) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entries.append(entry)

        if not entries:
            return 0

        # Remove existing index
        import shutil
        if self.index_path.exists():
            shutil.rmtree(self.index_path)

        # Re-initialize embeddings
        self.embeddings = Embeddings(
            content=True,
            backend="sqlite",
            path="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Build documents for batch indexing
        documents = []
        for entry in entries:
            entry_id = entry.get("id") or str(uuid.uuid4())
            searchable_parts = [
                entry.get("title", ""),
                entry.get("summary", ""),
                entry.get("problem_solved", ""),
                " ".join(entry.get("key_concepts", [])),
                entry.get("what_worked", ""),
            ]
            searchable_text = " ".join(filter(None, searchable_parts))
            doc = {"text": searchable_text, **entry}
            documents.append((entry_id, doc, None))

        # Index all at once
        self.embeddings.index(documents)
        self.embeddings.save(str(self.index_path))

        return len(documents)

    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List most recent entries.

        Args:
            limit: Maximum number of entries

        Returns:
            List of recent entries
        """
        entries = []
        if self.jsonl_path.exists():
            with open(self.jsonl_path) as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))

        # Sort by date descending
        entries.sort(key=lambda x: x.get("found_date", ""), reverse=True)
        return entries[:limit]


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Database CLI")
    parser.add_argument("command", choices=["stats", "search", "recent", "add", "rebuild"],
                        help="Command to run")
    parser.add_argument("query", nargs="?", help="Search query, entry JSON, or title for add")
    parser.add_argument("summary", nargs="?", help="Summary text (for simple add)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Result limit")
    parser.add_argument("--project", "-p", help="Project path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    # Simple add arguments
    parser.add_argument("--title", "-t", help="Entry title (alternative to positional)")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--source", "-s", help="Source identifier")
    parser.add_argument("--url", "-u", help="Source URL")

    args = parser.parse_args()

    try:
        db = KnowledgeDB(args.project)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.command == "stats":
        stats = db.stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Knowledge DB: {stats['db_path']}")
            print(f"Entries: {stats['count']}")
            print(f"Size: {stats['size_human']}")
            print(f"Last updated: {stats['last_updated']}")

    elif args.command == "search":
        if not args.query:
            print("ERROR: Search requires a query")
            sys.exit(1)

        results = db.search(args.query, limit=args.limit)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print("No results found.")
            else:
                print(f"Found {len(results)} results:\n")
                for r in results:
                    score = r.get("score", 0)
                    title = r.get("title", r.get("id", "Unknown"))
                    print(f"[{score:.2f}] {title}")
                    if r.get("url"):
                        print(f"       URL: {r['url']}")
                    if r.get("summary"):
                        print(f"       {r['summary'][:100]}...")
                    print()

    elif args.command == "recent":
        entries = db.list_recent(args.limit)

        if args.json:
            print(json.dumps(entries, indent=2))
        else:
            for e in entries:
                print(f"[{e.get('found_date', 'N/A')[:10]}] {e.get('title', 'Untitled')}")
                if e.get("url"):
                    print(f"  URL: {e['url']}")

    elif args.command == "add":
        entry = None

        # Try JSON first (for backwards compatibility)
        if args.query and args.query.startswith("{"):
            try:
                entry = json.loads(args.query)
            except json.JSONDecodeError:
                pass

        # If not JSON, use simple positional/flag arguments
        if entry is None:
            title = args.title or args.query
            summary = args.summary or args.query  # Use title as summary if no summary

            if not title:
                print("ERROR: Add requires title")
                print("Usage: knowledge_db.py add \"Title\" \"Summary\" [--tags t1,t2] [--source src] [--url url]")
                print("   or: knowledge_db.py add '{\"title\":\"...\", \"summary\":\"...\"}'")
                sys.exit(1)

            entry = {
                "title": title,
                "summary": summary if summary != title else title,
            }

            if args.tags:
                entry["tags"] = [t.strip() for t in args.tags.split(",")]
            if args.source:
                entry["source"] = args.source
            if args.url:
                entry["url"] = args.url

        try:
            entry_id = db.add(entry)
            print(f"Added entry: {entry_id}")
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    elif args.command == "rebuild":
        print("Rebuilding index from JSONL backup...")
        count = db.rebuild_index()
        print(f"Rebuilt index with {count} entries")
