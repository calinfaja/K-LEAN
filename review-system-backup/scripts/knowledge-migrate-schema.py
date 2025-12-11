#!/home/calin/.venvs/knowledge-db/bin/python
"""
Knowledge DB Schema Migration - Phase 1 Enhancement

This script migrates existing entries to the new enhanced schema by:
1. Reading all entries from entries.jsonl
2. Adding default values for new fields if missing:
   - confidence_score: 0.7 (default medium confidence)
   - tags: [] (empty list)
   - usage_count: 0
   - last_used: None
   - source_quality: "medium"
3. Backing up original JSONL
4. Writing updated entries back to JSONL
5. Rebuilding the txtai index with new schema

Usage:
    python knowledge-migrate-schema.py [--project /path/to/project]

This is a safe operation - it creates a backup before modifying anything.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_db import KnowledgeDB, find_project_root


def migrate_schema(project_path=None):
    """
    Migrate existing knowledge entries to enhanced schema.

    Args:
        project_path: Optional project path, auto-detects if None

    Returns:
        Tuple of (success: bool, message: str, count: int)
    """
    try:
        # Initialize database
        db = KnowledgeDB(project_path)
        jsonl_path = db.jsonl_path
        index_path = db.index_path

        print(f"Knowledge DB: {db.db_path}")
        print(f"JSONL file: {jsonl_path}")
        print()

        # Check if JSONL exists
        if not jsonl_path.exists():
            print("No entries.jsonl found. Starting fresh with new schema.")
            return True, "No migration needed", 0

        # Read all entries
        entries = []
        with open(jsonl_path) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entries.append(entry)

        if not entries:
            print("No entries found in JSONL. Database is empty.")
            return True, "Empty database", 0

        print(f"Found {len(entries)} existing entries to migrate")
        print()

        # Create backup
        backup_path = jsonl_path.with_stem(f"entries.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        jsonl_path.rename(backup_path)
        print(f"✓ Created backup: {backup_path}")

        # Migrate entries
        migrated_count = 0
        with open(jsonl_path, "w") as f:
            for entry in entries:
                # Add new fields with defaults
                entry.setdefault("confidence_score", 0.7)
                entry.setdefault("tags", [])
                entry.setdefault("usage_count", 0)
                entry.setdefault("last_used", None)
                entry.setdefault("source_quality", "medium")

                # Write updated entry
                f.write(json.dumps(entry) + "\n")
                migrated_count += 1

        print(f"✓ Migrated {migrated_count} entries with new schema")
        print()

        # Rebuild index with new schema
        print("Rebuilding txtai index with new schema...")
        count = db.rebuild_index()
        print(f"✓ Rebuilt index with {count} entries")
        print()

        # Verify
        stats = db.stats()
        print("Verification:")
        print(f"  Entries in DB: {stats['count']}")
        print(f"  Size: {stats['size_human']}")
        print(f"  Last updated: {stats['last_updated']}")
        print()

        # Test search to ensure everything works
        print("Testing search functionality...")
        test_results = db.search("knowledge", limit=3)
        if test_results:
            print(f"✓ Search test successful ({len(test_results)} results)")
            # Show first result with new fields
            first = test_results[0]
            print(f"  First result: '{first.get('title', 'Unknown')}'")
            print(f"    - confidence_score: {first.get('confidence_score', 'N/A')}")
            print(f"    - tags: {first.get('tags', [])}")
            print(f"    - usage_count: {first.get('usage_count', 0)}")
            print(f"    - source_quality: {first.get('source_quality', 'N/A')}")
        else:
            print("⚠ Search returned no results (may be expected for empty DB)")
        print()

        return True, f"Successfully migrated {migrated_count} entries", migrated_count

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False, str(e), 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate knowledge DB to enhanced schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect project
  python knowledge-migrate-schema.py

  # Specify project
  python knowledge-migrate-schema.py --project /path/to/project
        """
    )
    parser.add_argument("--project", "-p", help="Project path (auto-detect if not provided)")

    args = parser.parse_args()

    print("=" * 60)
    print("Knowledge DB Schema Migration - Phase 1 Enhancement")
    print("=" * 60)
    print()

    success, message, count = migrate_schema(args.project)

    print("=" * 60)
    if success:
        print(f"✓ SUCCESS: {message}")
        sys.exit(0)
    else:
        print(f"✗ FAILED: {message}")
        sys.exit(1)
