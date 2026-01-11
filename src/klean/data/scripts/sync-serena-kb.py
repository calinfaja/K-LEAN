#!/usr/bin/env python3
"""Sync Serena lessons-learned to Knowledge DB.

Makes curated Serena lessons searchable by SmolKLN agents.

Usage:
    python sync-serena-kb.py                    # Sync all lessons
    python sync-serena-kb.py --dry-run          # Show what would be synced
    python sync-serena-kb.py --serena-path FILE # Custom Serena file
"""

import argparse
import sys
from pathlib import Path

# Add scripts dir to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))


def parse_serena_lessons(content: str) -> list:
    """Parse Serena lessons-learned markdown into structured lessons."""
    lessons = []
    current_lesson = {}
    current_content = []

    for line in content.split("\n"):
        # Detect lesson headers (### GOTCHA:, ### TIP:, ### PATTERN:, etc.)
        if line.startswith("### "):
            # Save previous lesson if exists
            if current_lesson.get("title"):
                lessons.append({**current_lesson, "content": "\n".join(current_content).strip()})

            # Parse new lesson header
            header = line[4:].strip()
            lesson_type = "lesson"
            if header.startswith("GOTCHA:"):
                lesson_type = "warning"
                header = header[7:].strip()
            elif header.startswith("TIP:"):
                lesson_type = "tip"
                header = header[4:].strip()
            elif header.startswith("PATTERN:"):
                lesson_type = "pattern"
                header = header[8:].strip()
            elif header.startswith("Remember:"):
                lesson_type = "summary"
                header = header[9:].strip()

            current_lesson = {
                "title": header,
                "type": lesson_type,
            }
            current_content = []

        elif line.startswith("**Date**:"):
            current_lesson["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Context**:"):
            current_lesson["context"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Topics**:"):
            current_lesson["topics"] = line.split(":", 1)[1].strip()
        elif current_lesson.get("title"):
            current_content.append(line)

    # Save last lesson
    if current_lesson.get("title"):
        lessons.append({**current_lesson, "content": "\n".join(current_content).strip()})

    return lessons


def sync_to_kb(lessons: list, db, dry_run: bool = False) -> int:
    """Sync parsed lessons to Knowledge DB."""
    synced = 0

    for lesson in lessons:
        # Skip "Remember:" summaries - they're just indexes
        if lesson.get("type") == "summary":
            continue

        # Skip if already exists
        try:
            existing = db.search(lesson["title"], limit=1)
            for e in existing:
                if e.get("source") == "serena" and e.get("title") == lesson["title"]:
                    continue  # Already synced
        except Exception:
            pass

        if dry_run:
            print(f"  Would sync: [{lesson['type']}] {lesson['title'][:60]}")
            synced += 1
            continue

        try:
            db.add_structured(
                {
                    "title": lesson["title"],
                    "summary": lesson["content"][:1000],
                    "type": lesson.get("type", "lesson"),
                    "source": "serena",
                    "tags": ["serena", "lessons-learned", lesson.get("type", "lesson")],
                    "key_concepts": [lesson.get("context", "")] if lesson.get("context") else [],
                    "quality": "high",
                    "source_path": f"serena:{lesson.get('date', 'unknown')}",
                }
            )
            synced += 1
            print(f"  [OK] [{lesson['type']}] {lesson['title'][:60]}")
        except Exception as e:
            print(f"  [X] Failed: {lesson['title'][:40]} - {e}")

    return synced


def main():
    parser = argparse.ArgumentParser(description="Sync Serena lessons to Knowledge DB")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced")
    parser.add_argument("--serena-path", help="Path to Serena lessons-learned file")
    parser.add_argument("--project", "-p", help="Project path for Knowledge DB")
    args = parser.parse_args()

    # Find Serena file
    if args.serena_path:
        serena_path = Path(args.serena_path)
    else:
        # Try common locations
        candidates = [
            Path.cwd() / ".serena" / "memories" / "lessons-learned.md",
            Path.home() / "claudeAgentic" / ".serena" / "memories" / "lessons-learned.md",
        ]
        serena_path = None
        for c in candidates:
            if c.exists():
                serena_path = c
                break

    if not serena_path or not serena_path.exists():
        print("[ERROR] Serena lessons-learned not found")
        print("   Tried:", candidates if not args.serena_path else [args.serena_path])
        sys.exit(1)

    print(f"📖 Reading Serena: {serena_path}")
    content = serena_path.read_text()

    # Parse lessons
    lessons = parse_serena_lessons(content)
    print(f"   Found {len(lessons)} lessons")

    if not lessons:
        print("   No lessons to sync")
        sys.exit(0)

    # Initialize Knowledge DB
    if not args.dry_run:
        try:
            from knowledge_db import KnowledgeDB

            db = KnowledgeDB(args.project)
            print(f"📚 Knowledge DB: {db.db_path}")
        except ImportError:
            print("[ERROR] knowledge_db module not found")
            print("   Install: pip install fastembed numpy")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Knowledge DB error: {e}")
            sys.exit(1)
    else:
        db = None
        print(" Dry run - showing what would be synced:")

    # Sync
    synced = sync_to_kb(lessons, db, args.dry_run)

    if args.dry_run:
        print(f"\n Would sync {synced} lessons")
    else:
        print(f"\n[OK] Synced {synced} Serena lessons to Knowledge DB")
        print("   SmolKLN agents can now search these lessons!")


if __name__ == "__main__":
    main()
