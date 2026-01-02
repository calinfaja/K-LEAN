#!/usr/bin/env python3
"""
Knowledge Database - Fastembed implementation for semantic search

This module provides a KnowledgeDB class using fastembed + numpy for:
- Storing knowledge entries with metadata
- Semantic search across all entries
- Auto-detection of project's .knowledge-db directory

Replaces txtai backend with lightweight fastembed (ONNX-based).
Install size: ~200 MB vs 7+ GB with txtai/PyTorch.

Usage:
    from knowledge_db_fastembed import KnowledgeDB

    db = KnowledgeDB()  # Auto-detects project root
    db.add({
        "title": "BLE Optimization",
        "summary": "Nordic's guide on connection intervals",
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

import numpy as np

# Import shared utilities
try:
    from kb_utils import debug_log, find_project_root, migrate_entry
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import debug_log, find_project_root, migrate_entry

# Fastembed imports
try:
    from fastembed import TextEmbedding
except ImportError:
    print("ERROR: fastembed not installed. Run: pip install fastembed")
    sys.exit(1)


# Global model instance (singleton for performance)
_model: Optional[TextEmbedding] = None


def get_embedding_model() -> TextEmbedding:
    """Get or create singleton embedding model."""
    global _model
    if _model is None:
        # Use same model as sentence-transformers for compatibility
        # bge-small-en-v1.5 has 384 dimensions, same as all-MiniLM-L6-v2
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _model


class KnowledgeDB:
    """
    Semantic knowledge database using fastembed + numpy.

    Stores entries in project's .knowledge-db/ directory with:
    - Numpy array for vector embeddings
    - JSON index for entry ID to row mapping
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
        self.embeddings_path = self.db_path / "embeddings.npy"
        self.index_path = self.db_path / "index.json"
        self.jsonl_path = self.db_path / "entries.jsonl"
        self.old_txtai_path = self.db_path / "index"  # Old txtai SQLite

        # Create directory if needed
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize model (lazy load on first use)
        self._model: Optional[TextEmbedding] = None

        # In-memory index
        self._embeddings: Optional[np.ndarray] = None
        self._id_to_row: Dict[str, int] = {}
        self._row_to_id: Dict[int, str] = {}
        self._entries: List[Dict[str, Any]] = []  # Cached entries

        # Load existing index if present
        self._load_index()

        # Auto-migrate from txtai if needed
        if self._needs_migration():
            debug_log("Detected old txtai index, migrating to fastembed...")
            self.rebuild_index()

    @property
    def model(self) -> TextEmbedding:
        """Lazy load embedding model."""
        if self._model is None:
            self._model = get_embedding_model()
        return self._model

    def _needs_migration(self) -> bool:
        """Check if migration from txtai is needed."""
        # Has old txtai index but no new fastembed index
        has_old = self.old_txtai_path.exists()
        has_new = self.embeddings_path.exists()
        has_entries = self.jsonl_path.exists()
        return has_old and not has_new and has_entries

    def _load_index(self) -> None:
        """Load embeddings, index, and entries from disk."""
        if self.embeddings_path.exists() and self.index_path.exists():
            try:
                self._embeddings = np.load(str(self.embeddings_path))
                with open(self.index_path) as f:
                    self._id_to_row = json.load(f)
                self._row_to_id = {v: k for k, v in self._id_to_row.items()}

                # Load entries into memory
                self._entries = []
                if self.jsonl_path.exists():
                    with open(self.jsonl_path) as f:
                        for line in f:
                            if line.strip():
                                try:
                                    e = json.loads(line)
                                    if isinstance(e, dict):
                                        self._entries.append(migrate_entry(e))
                                except json.JSONDecodeError:
                                    pass

                # Validate consistency
                if len(self._embeddings) != len(self._entries):
                    debug_log(f"WARNING: Index/entries mismatch ({len(self._embeddings)} vs {len(self._entries)})")

                debug_log(f"Loaded {len(self._id_to_row)} embeddings from disk")
            except Exception as e:
                debug_log(f"Failed to load index: {e}")
                self._embeddings = None
                self._id_to_row = {}
                self._row_to_id = {}
                self._entries = []

    def _save_index(self) -> None:
        """Save embeddings and index to disk."""
        if self._embeddings is not None:
            np.save(str(self.embeddings_path), self._embeddings)
            with open(self.index_path, "w") as f:
                json.dump(self._id_to_row, f)
            debug_log(f"Saved {len(self._id_to_row)} embeddings to disk")

    def _build_searchable_text(self, entry: Dict[str, Any]) -> str:
        """Build searchable text from entry fields."""
        searchable_parts = [
            entry.get("title", ""),
            entry.get("summary", ""),
            entry.get("atomic_insight", ""),
            entry.get("problem_solved", ""),
            " ".join(entry.get("key_concepts", [])),
            " ".join(entry.get("tags", [])),
            entry.get("what_worked", ""),
        ]
        return " ".join(filter(None, searchable_parts))

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
                - relevance_score: 0-1 score
                - confidence_score: 0-1 confidence
                - tags: List of searchable tags
                - etc.

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

        # Add default metadata fields
        entry.setdefault("confidence_score", 0.7)
        entry.setdefault("tags", [])
        entry.setdefault("usage_count", 0)
        entry.setdefault("last_used", None)
        entry.setdefault("source_quality", "medium")

        # Build searchable text
        searchable_text = self._build_searchable_text(entry)

        # Generate embedding
        embedding = list(self.model.embed([searchable_text]))[0]

        # Add to in-memory index
        if self._embeddings is None:
            self._embeddings = embedding.reshape(1, -1)
        else:
            self._embeddings = np.vstack([self._embeddings, embedding])

        row_idx = len(self._id_to_row)
        self._id_to_row[entry_id] = row_idx
        self._row_to_id[row_idx] = entry_id
        self._entries.append(entry)  # Add to cache

        # Save to disk
        self._save_index()

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
        if self._embeddings is None or len(self._embeddings) == 0:
            return []

        # Generate query embedding
        query_embedding = list(self.model.embed([query]))[0]

        # Compute cosine similarity (embeddings are normalized)
        scores = self._embeddings @ query_embedding

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:limit]

        # Format results from cached entries
        results = []
        for idx in top_indices:
            idx = int(idx)
            if idx < len(self._entries):
                entry = self._entries[idx].copy()
                entry["score"] = float(scores[idx])
                results.append(entry)

        return results

    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific entry by ID.

        Args:
            entry_id: Entry UUID

        Returns:
            Entry dictionary or None if not found
        """
        if not self.jsonl_path.exists():
            return None

        with open(self.jsonl_path) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict) and entry.get("id") == entry_id:
                            return migrate_entry(entry)
                    except json.JSONDecodeError:
                        pass
        return None

    def stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with count, size, last_updated
        """
        count = len(self._id_to_row) if self._id_to_row else 0
        size_bytes = 0
        last_updated = None

        # Get size
        for f in self.db_path.rglob("*"):
            if f.is_file():
                size_bytes += f.stat().st_size

        # Last modified
        if self.embeddings_path.exists():
            last_updated = datetime.fromtimestamp(
                self.embeddings_path.stat().st_mtime
            ).isoformat()

        return {
            "count": count,
            "size_bytes": size_bytes,
            "size_human": f"{size_bytes / 1024:.1f} KB",
            "last_updated": last_updated,
            "db_path": str(self.db_path),
            "backend": "fastembed",
        }

    def rebuild_index(self) -> int:
        """
        Rebuild the index from JSONL backup.
        Migrates from txtai format or rebuilds fastembed index.

        Returns:
            Number of entries indexed
        """
        if not self.jsonl_path.exists():
            return 0

        # Read all entries from JSONL
        entries = []
        needs_id_update = False
        with open(self.jsonl_path) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict):
                            entry = migrate_entry(entry)
                            # Ensure every entry has an ID
                            if not entry.get("id"):
                                entry["id"] = str(uuid.uuid4())
                                needs_id_update = True
                            entries.append(entry)
                    except json.JSONDecodeError:
                        pass

        if not entries:
            return 0

        # Update JSONL if we assigned new IDs
        if needs_id_update:
            debug_log("Updating entries with missing IDs...")
            with open(self.jsonl_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

        # Build searchable texts
        texts = [self._build_searchable_text(e) for e in entries]

        # Generate embeddings in batch
        debug_log(f"Generating embeddings for {len(texts)} entries...")
        embeddings_list = list(self.model.embed(texts))
        self._embeddings = np.array(embeddings_list)

        # Build index and cache
        self._id_to_row = {}
        self._row_to_id = {}
        self._entries = entries  # Cache all entries
        for idx, entry in enumerate(entries):
            entry_id = entry["id"]  # Now guaranteed to exist
            self._id_to_row[entry_id] = idx
            self._row_to_id[idx] = entry_id

        # Save to disk
        self._save_index()

        # Remove old txtai index if present
        if self.old_txtai_path.exists():
            import shutil
            shutil.rmtree(self.old_txtai_path)
            debug_log("Removed old txtai index")

        debug_log(f"Rebuilt index with {len(entries)} entries")
        return len(entries)

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
                        try:
                            entry = json.loads(line)
                            if isinstance(entry, dict):
                                entries.append(migrate_entry(entry))
                        except json.JSONDecodeError:
                            pass

        # Sort by date descending
        entries.sort(key=lambda x: x.get("found_date", ""), reverse=True)
        return entries[:limit]

    def add_structured(self, data: dict) -> str:
        """
        Add a pre-structured entry (from Claude session or smart-capture).

        Returns:
            Entry ID (UUID)
        """
        entry = {
            "id": data.get("id") or str(uuid.uuid4()),
            "found_date": data.get("found_date") or datetime.now().isoformat(),
            "usage_count": data.get("usage_count", 0),
            "last_used": data.get("last_used"),
            "relevance_score": data.get("relevance_score", 0.8),
            "confidence_score": data.get("confidence_score", 0.8),
            "title": data.get("title", ""),
            "summary": data.get("summary", ""),
            "type": data.get("type", "lesson"),
            "tags": data.get("tags", []),
            "atomic_insight": data.get("atomic_insight", ""),
            "key_concepts": data.get("key_concepts", []),
            "quality": data.get("quality", "medium"),
            "source": data.get("source", "conversation"),
            "source_path": data.get("source_path", ""),
            "url": data.get("url", ""),
            "problem_solved": data.get("problem_solved", ""),
            "what_worked": data.get("what_worked", ""),
            "constraints": data.get("constraints", ""),
            "source_quality": data.get("source_quality", "medium"),
        }

        if not entry["title"] and not entry["summary"]:
            raise ValueError("Entry must have 'title' or 'summary'")

        if not entry["title"]:
            entry["title"] = entry["summary"][:100]
        if not entry["summary"]:
            entry["summary"] = entry["title"]

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
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if not isinstance(entry, dict):
                        skipped_lines += 1
                        continue

                    original_keys = set(entry.keys())
                    migrated = migrate_entry(entry)

                    if set(migrated.keys()) != original_keys:
                        migrated_count += 1

                    entries.append(migrated)
                except json.JSONDecodeError:
                    skipped_lines += 1

        result = {
            "status": "checked",
            "total": len(entries),
            "migrated": migrated_count,
            "needs_migration": migrated_count > 0,
            "skipped_lines": skipped_lines,
        }

        if rewrite and migrated_count > 0:
            backup_path = self.jsonl_path.with_suffix(".jsonl.bak")
            import shutil
            shutil.copy(self.jsonl_path, backup_path)

            with open(self.jsonl_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            result["status"] = "migrated"
            result["backup"] = str(backup_path)

        return result

    def count(self) -> int:
        """Return number of entries."""
        return len(self._id_to_row) if self._id_to_row else 0


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Database CLI (fastembed)")
    parser.add_argument("command", choices=["stats", "search", "recent", "add", "rebuild", "migrate"],
                        help="Command to run")
    parser.add_argument("query", nargs="?", help="Search query or entry data")
    parser.add_argument("summary", nargs="?", help="Summary text (for simple add)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Result limit")
    parser.add_argument("--project", "-p", help="Project path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--json-input", dest="json_input", help="Add structured entry from JSON")
    parser.add_argument("--check", action="store_true", help="Check migration status only")
    parser.add_argument("--title", "-t", help="Entry title")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--source", "-s", help="Source identifier")
    parser.add_argument("--url", "-u", help="Source URL")

    args = parser.parse_args()

    try:
        db = KnowledgeDB(args.project)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Handle --json-input
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
            print(f"Backend: {stats['backend']}")
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

        if args.query and args.query.startswith("{"):
            try:
                entry = json.loads(args.query)
            except json.JSONDecodeError:
                pass

        if entry is None:
            title = args.title or args.query
            summary = args.summary or args.query

            if not title:
                print("ERROR: Add requires title")
                print("Usage: knowledge_db_fastembed.py add \"Title\" \"Summary\" [--tags t1,t2]")
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
        print(f"Rebuilt index with {count} entries (backend: fastembed)")

    elif args.command == "migrate":
        result = db.migrate_all(rewrite=not args.check)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "no_entries":
                print("No entries to migrate.")
            elif result["status"] == "checked":
                if result["needs_migration"]:
                    print(f"Migration needed: {result['migrated']}/{result['total']} entries")
                else:
                    print(f"All {result['total']} entries have V2 schema")
            elif result["status"] == "migrated":
                print(f"Migrated {result['migrated']} entries")
                print(f"Backup: {result['backup']}")
