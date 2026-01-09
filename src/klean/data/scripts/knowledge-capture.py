#!/usr/bin/env python3
"""
K-LEAN Knowledge Capture Script

Saves lessons, findings, and insights to the knowledge database.
Supports both simple CLI input and structured JSON for Claude integration.

Usage:
  knowledge-capture.py <content> [--type TYPE] [--tags TAG1,TAG2] [--priority LEVEL] [--url URL]
  knowledge-capture.py --json-input '<json>' [--json]

Types: lesson, finding, solution, pattern, warning, best-practice
Priority: low, medium, high, critical

JSON Input (V2 Schema):
  {
    "title": "Short title",
    "summary": "Full description",
    "atomic_insight": "One-sentence takeaway",
    "key_concepts": ["term1", "term2"],
    "quality": "high|medium|low",
    "source": "conversation|web|file|manual",
    "source_path": "optional URL or file path",
    "tags": ["tag1", "tag2"],
    "type": "lesson|finding|solution|pattern"
  }

Examples:
  knowledge-capture.py "Always validate user input" --type lesson --tags security,validation
  knowledge-capture.py --json-input '{"title":"Validation","summary":"Always validate","atomic_insight":"Validate all inputs"}' --json
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Import shared utilities
try:
    from kb_utils import (  # noqa: F401
        PYTHON_BIN,
        debug_log,
        find_project_root,
        get_socket_path,
        is_server_running,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import (
        PYTHON_BIN,
        debug_log,
        is_server_running,
    )


# Result of initialization
class InitResult:
    def __init__(self, path, newly_created=False, server_started=False):
        self.path = path
        self.newly_created = newly_created
        self.server_started = server_started


def start_kb_server(project_path):
    """Start the KB server for a project."""
    # Import KB_SCRIPTS_DIR from kb_utils (set from environment)
    from kb_utils import KB_SCRIPTS_DIR

    server_script = KB_SCRIPTS_DIR / "knowledge-server.py"

    if not server_script.exists() or not PYTHON_BIN.exists():
        debug_log(f"Missing server script or Python: {server_script}, {PYTHON_BIN}")
        return False

    try:
        # Start server in background
        subprocess.Popen(
            [str(PYTHON_BIN), str(server_script), "start", str(project_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Wait briefly for server to start
        import time

        for _ in range(10):  # Wait up to 5 seconds
            time.sleep(0.5)
            if is_server_running(project_path):
                return True
        debug_log("KB server failed to start within timeout")
        return False
    except Exception as e:
        debug_log(f"Error starting KB server: {e}")
        return False


def get_knowledge_dir():
    """Get the knowledge database directory with auto-initialization.

    Returns an InitResult with:
    - path: Path to .knowledge-db
    - newly_created: True if directory was just created
    - server_started: True if KB server was just started
    """
    # Try CLAUDE_PROJECT_DIR first (set by Claude Code)
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
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
    """Create a knowledge database entry (simple mode)."""
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Generate a unique ID
    entry_id = f"{entry_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Calculate relevance score based on priority
    priority_scores = {"critical": 1.0, "high": 0.9, "medium": 0.8, "low": 0.7}

    # Map priority to quality
    quality_map = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}

    entry = {
        "id": entry_id,
        "title": content[:100] + "..." if len(content) > 100 else content,
        "summary": content,
        "type": entry_type,
        "source": "manual",
        "source_path": url or "",
        "found_date": datetime.now().isoformat(),
        "relevance_score": priority_scores.get(priority, 0.8),
        "priority": priority,
        "key_concepts": tags,
        "tags": tags,
        "auto_extracted": False,
        # V2 schema fields
        "atomic_insight": "",
        "quality": quality_map.get(priority, "medium"),
        "confidence_score": priority_scores.get(priority, 0.8),
    }

    if url:
        entry["url"] = url

    return entry


def create_entry_from_json(data: dict):
    """Create a knowledge database entry from structured JSON (V2 schema)."""
    entry_type = data.get("type", "lesson")
    entry_id = data.get("id") or f"{entry_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Get quality and map to relevance score
    quality = data.get("quality", "medium")
    quality_scores = {"high": 0.9, "medium": 0.8, "low": 0.7}

    entry = {
        "id": entry_id,
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "type": entry_type,
        "source": data.get("source", "conversation"),
        "source_path": data.get("source_path", ""),
        "found_date": data.get("found_date") or datetime.now().isoformat(),
        "relevance_score": data.get("relevance_score", quality_scores.get(quality, 0.8)),
        "key_concepts": data.get("key_concepts", []),
        "tags": data.get("tags", []),
        "auto_extracted": data.get("auto_extracted", False),
        # V2 schema fields
        "atomic_insight": data.get("atomic_insight", ""),
        "quality": quality,
        "confidence_score": data.get("confidence_score", quality_scores.get(quality, 0.8)),
        "usage_count": data.get("usage_count", 0),
        "last_used": data.get("last_used"),
        "source_quality": data.get("source_quality", "medium"),
    }

    # Optional fields
    if data.get("url"):
        entry["url"] = data["url"]
    if data.get("problem_solved"):
        entry["problem_solved"] = data["problem_solved"]
    if data.get("what_worked"):
        entry["what_worked"] = data["what_worked"]

    # Ensure title exists (use first 100 chars of summary if not)
    if not entry["title"] and entry["summary"]:
        entry["title"] = entry["summary"][:100]
    if not entry["summary"] and entry["title"]:
        entry["summary"] = entry["title"]

    return entry


def send_entry_to_server(entry: dict, project_path: str) -> bool:
    """Send entry to running KB server via TCP.

    This is the preferred method - ensures entry is immediately searchable
    because the server's in-memory index is updated atomically.

    Args:
        entry: Knowledge entry dictionary.
        project_path: Path to project root.

    Returns:
        True if entry was added via server, False otherwise.
    """
    import socket

    try:
        from kb_utils import get_kb_port_file
    except ImportError:
        return False

    # Get server port
    port_file = get_kb_port_file(Path(project_path))
    if not port_file.exists():
        debug_log("KB server not running (no port file)")
        return False

    try:
        port = int(port_file.read_text().strip())
    except (ValueError, OSError):
        debug_log("Invalid port file")
        return False

    # Send to server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("127.0.0.1", port))
        sock.sendall(json.dumps({"cmd": "add", "entry": entry}).encode("utf-8"))
        response = sock.recv(65536).decode("utf-8")
        sock.close()

        result = json.loads(response)
        if result.get("status") == "ok":
            debug_log(f"Entry added via server: {result.get('id')}")
            return True
        else:
            debug_log(f"Server rejected entry: {result.get('error')}")
            return False
    except Exception as e:
        debug_log(f"Failed to send to server: {e}")
        return False


def save_entry(entry, knowledge_dir):
    """Save entry to knowledge database with proper indexing.

    Preferred flow (txtai/Mem0 pattern):
    1. Try TCP to running server (immediate index sync)
    2. Fall back to direct KnowledgeDB.add() (new process, writes to file)
    3. Fall back to JSONL-only (searchable after server restart)
    """
    project_path = str(knowledge_dir.parent)

    # Method 1: Try server (best - immediate sync)
    if send_entry_to_server(entry, project_path):
        return True

    # Method 2: Direct KnowledgeDB (writes to file, but server has stale index)
    try:
        from knowledge_db import KnowledgeDB

        db = KnowledgeDB(project_path)
        db.add(entry)
        debug_log("Entry added via direct KnowledgeDB (server index may be stale)")
        return True
    except ImportError:
        debug_log("KnowledgeDB not available, falling back to JSONL-only")
    except Exception as e:
        debug_log(f"KnowledgeDB.add() failed: {e}, falling back to JSONL-only")

    # Method 3: JSONL-only fallback (searchable after server restart)
    entries_file = knowledge_dir / "entries.jsonl"
    with open(entries_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    debug_log("Entry appended to JSONL (searchable after server restart)")

    return True


def log_to_timeline(content, entry_type, knowledge_dir):
    """Log to timeline for chronological tracking."""
    timeline_file = knowledge_dir / "timeline.txt"
    timestamp = datetime.now().strftime("%m-%d %H:%M")

    # Truncate content for timeline
    short_content = content[:80].replace("\n", " ")
    timeline_entry = f"{timestamp} | {entry_type} | {short_content}"

    with open(timeline_file, "a") as f:
        f.write(timeline_entry + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Capture knowledge to K-LEAN database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Always validate user input" --type lesson
  %(prog)s "Memory leak in pools" --type finding --priority high
  %(prog)s "Use async/await" --type best-practice --tags python,async
  %(prog)s --json-input '{"title":"...","summary":"..."}' --json
        """,
    )
    parser.add_argument("content", nargs="?", default="", help="The content to capture")
    parser.add_argument(
        "--type",
        dest="entry_type",
        default="lesson",
        choices=["lesson", "finding", "solution", "pattern", "warning", "best-practice"],
        help="Type of entry (default: lesson)",
    )
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument(
        "--priority",
        default="medium",
        choices=["low", "medium", "high", "critical"],
        help="Priority level (default: medium)",
    )
    parser.add_argument("--url", default="", help="URL associated with the entry")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument(
        "--json-input", dest="json_input", help="Add structured entry from JSON string (V2 schema)"
    )

    args = parser.parse_args()

    # Validate: must have content or json-input
    if not args.content and not args.json_input:
        parser.error("Either content or --json-input is required")

    try:
        init_result = get_knowledge_dir()
        knowledge_dir = init_result.path

        # Silent init - only mention if both new dir AND server started (and not json mode)
        if init_result.newly_created and init_result.server_started and not args.json:
            print("[init: .knowledge-db + server]")

        # Create entry based on input mode
        if args.json_input:
            # Structured JSON input (V2 schema)
            try:
                data = json.loads(args.json_input)
            except json.JSONDecodeError as e:
                if args.json:
                    print(json.dumps({"error": f"Invalid JSON: {e}"}))
                else:
                    print(f"[ERROR] Invalid JSON input: {e}", file=sys.stderr)
                return 1

            entry = create_entry_from_json(data)
            content_display = entry.get("title", "")[:60]
            entry_type = entry.get("type", "lesson")
        else:
            # Simple content input
            entry = create_entry(
                content=args.content,
                entry_type=args.entry_type,
                tags=args.tags,
                priority=args.priority,
                url=args.url if args.url else None,
            )
            content_display = args.content[:60]
            entry_type = args.entry_type

        # Save to database
        save_entry(entry, knowledge_dir)

        # Log to timeline
        log_to_timeline(entry.get("summary", content_display), entry_type, knowledge_dir)

        # Output based on mode
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "id": entry["id"],
                        "title": entry["title"],
                        "type": entry_type,
                        "path": str(knowledge_dir / "entries.jsonl"),
                    }
                )
            )
        else:
            print(
                f"[OK] Captured {entry_type}: {content_display}{'...' if len(content_display) >= 60 else ''}"
            )
            print(f" Saved to: {knowledge_dir}/entries.jsonl")
            if entry.get("tags"):
                print(f"  Tags: {', '.join(entry['tags'])}")
            if entry.get("atomic_insight"):
                print(f" Insight: {entry['atomic_insight'][:80]}")

        return 0

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"[ERROR] Error capturing knowledge: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
