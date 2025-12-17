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
import hashlib
import subprocess
import socket
from datetime import datetime
from pathlib import Path
import argparse

# Result of initialization
class InitResult:
    def __init__(self, path, newly_created=False, server_started=False):
        self.path = path
        self.newly_created = newly_created
        self.server_started = server_started


def get_socket_path(project_path):
    """Get KB server socket path for a project."""
    path_str = str(Path(project_path).resolve())
    hash_val = hashlib.md5(path_str.encode()).hexdigest()[:8]
    return f"/tmp/kb-{hash_val}.sock"


def is_server_running(project_path):
    """Check if KB server is running for this project."""
    sock_path = get_socket_path(project_path)
    if not os.path.exists(sock_path):
        return False

    # Try to ping the server
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(sock_path)
        s.sendall(b'{"cmd":"ping"}')
        response = s.recv(1024).decode()
        s.close()
        return '"pong": true' in response or '"pong":true' in response
    except:
        return False


def start_kb_server(project_path):
    """Start the KB server for a project."""
    server_script = Path.home() / ".claude/scripts/knowledge-server.py"
    python_bin = Path.home() / ".venvs/knowledge-db/bin/python"

    if not server_script.exists() or not python_bin.exists():
        return False

    try:
        # Start server in background
        subprocess.Popen(
            [str(python_bin), str(server_script), "start", str(project_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Wait briefly for server to start
        import time
        for _ in range(10):  # Wait up to 5 seconds
            time.sleep(0.5)
            if is_server_running(project_path):
                return True
        return False
    except:
        return False


def get_knowledge_dir():
    """Get the knowledge database directory with auto-initialization.

    Returns an InitResult with:
    - path: Path to .knowledge-db
    - newly_created: True if directory was just created
    - server_started: True if KB server was just started
    """
    # Try CLAUDE_PROJECT_DIR first (set by Claude Code)
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    knowledge_db = Path(project_dir) / ".knowledge-db"

    # Check if it already exists
    newly_created = not knowledge_db.exists()

    # Create if doesn't exist
    knowledge_db.mkdir(parents=True, exist_ok=True)

    # Check if server needs to be started
    server_started = False
    if not is_server_running(project_dir):
        # Only try to start if we have an index or this is new
        index_dir = knowledge_db / "index"
        if index_dir.exists() or newly_created:
            server_started = start_kb_server(project_dir)

    return InitResult(knowledge_db, newly_created, server_started)

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
        init_result = get_knowledge_dir()
        knowledge_dir = init_result.path

        # Silent init - only mention if both new dir AND server started
        if init_result.newly_created and init_result.server_started:
            print(f"[init: .knowledge-db + server]")

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
