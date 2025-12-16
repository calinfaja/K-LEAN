#!/usr/bin/env python3
"""
K-LEAN Knowledge Capture Script

Saves lessons, findings, and insights to the knowledge database.

Usage:
  knowledge-capture.py <content> [--type TYPE] [--tags TAG1,TAG2] [--priority LEVEL] [--url URL]

Types: lesson, finding, solution, pattern, warning, best-practice
Priority: low, medium, high, critical

Examples:
  knowledge-capture.py "Always validate user input" --type lesson --tags security,validation
  knowledge-capture.py "Found memory leak in connection pool" --type finding --priority high
  knowledge-capture.py "Use connection pooling for DB" --type best-practice --tags database,performance
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import argparse

def get_knowledge_dir():
    """Get the knowledge database directory."""
    # Try CLAUDE_PROJECT_DIR first (set by Claude Code)
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    knowledge_db = Path(project_dir) / ".knowledge-db"

    # Create if doesn't exist
    knowledge_db.mkdir(parents=True, exist_ok=True)
    return knowledge_db

def create_entry(content, entry_type="lesson", tags=None, priority="medium", url=None):
    """Create a knowledge database entry."""
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    # Generate a unique ID
    entry_id = f"{entry_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Calculate relevance score based on priority
    priority_scores = {
        "critical": 1.0,
        "high": 0.9,
        "medium": 0.8,
        "low": 0.7
    }

    entry = {
        "id": entry_id,
        "title": content[:100] + "..." if len(content) > 100 else content,
        "summary": content,
        "type": entry_type,
        "source": "manual",
        "found_date": datetime.now().isoformat(),
        "relevance_score": priority_scores.get(priority, 0.8),
        "priority": priority,
        "key_concepts": tags,
        "auto_extracted": False
    }

    if url:
        entry["url"] = url

    return entry

def save_entry(entry, knowledge_dir):
    """Save entry to knowledge database."""
    entries_file = knowledge_dir / "entries.jsonl"

    # Append entry as JSONL
    with open(entries_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    return True

def log_to_timeline(content, entry_type, knowledge_dir):
    """Log to timeline for chronological tracking."""
    timeline_file = knowledge_dir / "timeline.txt"
    timestamp = datetime.now().strftime('%m-%d %H:%M')

    # Truncate content for timeline
    short_content = content[:80].replace('\n', ' ')
    timeline_entry = f"{timestamp} | {entry_type} | {short_content}"

    with open(timeline_file, 'a') as f:
        f.write(timeline_entry + '\n')

def main():
    parser = argparse.ArgumentParser(
        description='Capture knowledge to K-LEAN database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Always validate user input" --type lesson
  %(prog)s "Memory leak in pools" --type finding --priority high
  %(prog)s "Use async/await" --type best-practice --tags python,async
        """
    )
    parser.add_argument('content', help='The content to capture')
    parser.add_argument('--type', dest='entry_type', default='lesson',
                       choices=['lesson', 'finding', 'solution', 'pattern', 'warning', 'best-practice'],
                       help='Type of entry (default: lesson)')
    parser.add_argument('--tags', default='',
                       help='Comma-separated tags')
    parser.add_argument('--priority', default='medium',
                       choices=['low', 'medium', 'high', 'critical'],
                       help='Priority level (default: medium)')
    parser.add_argument('--url', default='',
                       help='URL associated with the entry')

    args = parser.parse_args()

    try:
        knowledge_dir = get_knowledge_dir()

        # Create entry
        entry = create_entry(
            content=args.content,
            entry_type=args.entry_type,
            tags=args.tags,
            priority=args.priority,
            url=args.url if args.url else None
        )

        # Save to database
        save_entry(entry, knowledge_dir)

        # Log to timeline
        log_to_timeline(args.content, args.entry_type, knowledge_dir)

        # Output success message
        print(f"✅ Captured {args.entry_type}: {args.content[:60]}{'...' if len(args.content) > 60 else ''}")
        print(f"📁 Saved to: {knowledge_dir}/entries.jsonl")
        if args.tags:
            print(f"🏷️  Tags: {args.tags}")
        if args.priority != 'medium':
            print(f"⚡ Priority: {args.priority}")

        return 0

    except Exception as e:
        print(f"❌ Error capturing knowledge: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
