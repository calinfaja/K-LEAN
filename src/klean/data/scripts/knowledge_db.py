#!/usr/bin/env python3
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
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import shared utilities
try:
    from kb_utils import SCHEMA_V2_DEFAULTS, debug_log, find_project_root, migrate_entry  # noqa: F401
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import debug_log, find_project_root, migrate_entry

# txtai imports
try:
    from txtai import Embeddings
except ImportError:
    print("ERROR: txtai not installed. Run: ~/.venvs/knowledge-db/bin/pip install txtai[database,ann]")
    sys.exit(1)


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
        # WAL mode enables concurrent read/write access (fixes "database is locked" error)
        self.embeddings = Embeddings(
            content=True,  # Store content alongside vectors
            backend="sqlite",  # Use SQLite for storage
            path="sentence-transformers/all-MiniLM-L6-v2",  # Fast, good quality model
            sqlite={"wal": True}  # Enable WAL for concurrent access
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
                - confidence_score (optional): 0-1 confidence, default 0.7
                - tags (optional): List of searchable tags
                - usage_count (optional): Times referenced, default 0
                - last_used (optional): ISO timestamp of last use
                - source_quality (optional): high|medium|low, default medium

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

        # Add default metadata fields if not provided
        entry.setdefault("confidence_score", 0.7)
        entry.setdefault("tags", [])
        entry.setdefault("usage_count", 0)
        entry.setdefault("last_used", None)
        entry.setdefault("source_quality", "medium")

        # Build searchable text from key fields (including V2 fields)
        searchable_parts = [
            entry.get("title", ""),
            entry.get("summary", ""),
            entry.get("atomic_insight", ""),  # V2: one-sentence takeaway
            entry.get("problem_solved", ""),
            " ".join(entry.get("key_concepts", [])),
            " ".join(entry.get("tags", [])),
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
        # Escape single quotes to prevent SQL injection
        safe_query = query.replace("'", "''")
        sql_query = f"select id, text, title, summary, url, type, problem_solved, key_concepts, relevance_score, what_worked, constraints, found_date, confidence_score, tags, usage_count, last_used, source_quality, score from txtai where similar('{safe_query}') limit {limit}"

        try:
            results = self.embeddings.search(sql_query)
        except Exception as e:
            debug_log(f"SQL search failed, falling back: {e}")
            results = self.embeddings.search(query, limit=limit)

        # Load JSONL entries for enrichment
        jsonl_entries = {}
        if self.jsonl_path.exists():
            with open(self.jsonl_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if isinstance(entry, dict):
                                jsonl_entries[entry.get("id")] = entry
                        except json.JSONDecodeError:
                            pass

        # Format results with V2 fields and migration
        formatted = []
        for result in results:
            if isinstance(result, dict):
                entry_id = result.get("id")
                # Enrich with data from JSONL (especially list/JSON fields)
                jsonl_entry = jsonl_entries.get(entry_id, {})

                # Build entry with all fields
                entry = {
                    "score": result.get("score", 0),
                    "id": entry_id,
                    "title": result.get("title", ""),
                    "summary": result.get("summary", ""),
                    "url": result.get("url", ""),
                    "type": result.get("type", ""),
                    "problem_solved": result.get("problem_solved", ""),
                    "key_concepts": jsonl_entry.get("key_concepts", []),  # From JSONL
                    "relevance_score": result.get("relevance_score", 0),
                    "what_worked": result.get("what_worked", ""),
                    "constraints": result.get("constraints", ""),
                    "found_date": result.get("found_date", ""),
                    "confidence_score": result.get("confidence_score", 0.7),
                    "tags": jsonl_entry.get("tags", []),  # From JSONL
                    "usage_count": result.get("usage_count", 0),
                    "last_used": result.get("last_used"),
                    "source_quality": result.get("source_quality", "medium"),
                    # V2 fields
                    "atomic_insight": jsonl_entry.get("atomic_insight", result.get("atomic_insight", "")),
                    "quality": jsonl_entry.get("quality", result.get("quality", "medium")),
                    "source": jsonl_entry.get("source", result.get("source", "manual")),
                    "source_path": jsonl_entry.get("source_path", result.get("source_path", "")),
                }
                # Apply migration for any missing fields
                formatted.append(migrate_entry(entry))
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
            except Exception as e:
                debug_log(f"Embeddings count failed: {e}")
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
        Also migrates old schema entries with default values for new fields.

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

            # Migrate old schema: add defaults for all V2 fields
            entry = migrate_entry(entry)

            # Build searchable text with V2 fields
            searchable_parts = [
                entry.get("title", ""),
                entry.get("summary", ""),
                entry.get("atomic_insight", ""),  # V2
                entry.get("problem_solved", ""),
                " ".join(entry.get("key_concepts", [])),
                " ".join(entry.get("tags", [])),
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

    def add_structured(self, data: dict) -> str:
        """
        Add a pre-structured entry (from Claude session or smart-capture).

        Accepts V2 schema fields:
            title, summary, atomic_insight, type, tags, key_concepts,
            quality, source, source_path, relevance_score, etc.

        Returns:
            Entry ID (UUID)
        """
        # Build entry with all V2 fields
        entry = {
            "id": data.get("id") or str(uuid.uuid4()),
            "found_date": data.get("found_date") or datetime.now().isoformat(),
            "usage_count": data.get("usage_count", 0),
            "last_used": data.get("last_used"),
            "relevance_score": data.get("relevance_score", 0.8),
            "confidence_score": data.get("confidence_score", 0.8),
            # Core fields
            "title": data.get("title", ""),
            "summary": data.get("summary", ""),
            "type": data.get("type", "lesson"),
            "tags": data.get("tags", []),
            # V2 enhanced fields
            "atomic_insight": data.get("atomic_insight", ""),
            "key_concepts": data.get("key_concepts", []),
            "quality": data.get("quality", "medium"),
            "source": data.get("source", "conversation"),
            "source_path": data.get("source_path", ""),
            # Optional fields
            "url": data.get("url", ""),
            "problem_solved": data.get("problem_solved", ""),
            "what_worked": data.get("what_worked", ""),
            "constraints": data.get("constraints", ""),
            "source_quality": data.get("source_quality", "medium"),
        }

        # Validate required fields
        if not entry["title"] and not entry["summary"]:
            raise ValueError("Entry must have 'title' or 'summary'")

        # Use title as summary or vice versa if one is missing
        if not entry["title"]:
            entry["title"] = entry["summary"][:100]
        if not entry["summary"]:
            entry["summary"] = entry["title"]

        # Add using the standard add method
        return self.add(entry)

    def migrate_all(self, rewrite: bool = False) -> dict:
        """
        Migrate all entries to V2 schema.

        Args:
            rewrite: If True, rewrite entries.jsonl with migrated entries

        Returns:
            Dictionary with migration stats
        """
        if not self.jsonl_path.exists():
            return {"status": "no_entries", "total": 0, "migrated": 0}

        entries = []
        migrated_count = 0
        skipped_lines = 0

        with open(self.jsonl_path) as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    # Skip non-dict entries (e.g., string fragments from pretty-printed JSON)
                    if not isinstance(entry, dict):
                        skipped_lines += 1
                        continue

                    original_keys = set(entry.keys())
                    migrated = migrate_entry(entry)

                    # Check if any new fields were added
                    if set(migrated.keys()) != original_keys:
                        migrated_count += 1

                    entries.append(migrated)
                except json.JSONDecodeError:
                    # Skip malformed lines (e.g., pretty-printed JSON fragments)
                    skipped_lines += 1

        result = {
            "status": "checked",
            "total": len(entries),
            "migrated": migrated_count,
            "needs_migration": migrated_count > 0,
            "skipped_lines": skipped_lines,
        }

        if rewrite and migrated_count > 0:
            # Backup original
            backup_path = self.jsonl_path.with_suffix(".jsonl.bak")
            import shutil
            shutil.copy(self.jsonl_path, backup_path)

            # Rewrite with migrated entries
            with open(self.jsonl_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            result["status"] = "migrated"
            result["backup"] = str(backup_path)

        return result


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Database CLI")
    parser.add_argument("command", choices=["stats", "search", "recent", "add", "rebuild", "migrate"],
                        help="Command to run")
    parser.add_argument("query", nargs="?", help="Search query, entry JSON, or title for add")
    parser.add_argument("summary", nargs="?", help="Summary text (for simple add)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Result limit")
    parser.add_argument("--project", "-p", help="Project path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--json-input", dest="json_input", help="Add structured entry from JSON string")
    parser.add_argument("--check", action="store_true", help="Check migration status only (for migrate)")
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

    # Handle --json-input first (structured entry input from Claude/smart-capture)
    if args.json_input:
        try:
            data = json.loads(args.json_input)
            entry_id = db.add_structured(data)
            if args.json:
                print(json.dumps({"id": entry_id, "status": "added"}))
            else:
                print(f"Added structured entry: {entry_id}")
            sys.exit(0)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON input: {e}")
            sys.exit(1)
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

    elif args.command == "migrate":
        # Run migration check or full migration
        result = db.migrate_all(rewrite=not args.check)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "no_entries":
                print("No entries to migrate.")
            elif result["status"] == "checked":
                if result["needs_migration"]:
                    print(f"Migration needed: {result['migrated']}/{result['total']} entries need V2 fields")
                    print("Run with --check removed to apply migration")
                else:
                    print(f"All {result['total']} entries already have V2 schema fields")
            elif result["status"] == "migrated":
                print(f"Migrated {result['migrated']} entries to V2 schema")
                print(f"Backup saved to: {result['backup']}")
