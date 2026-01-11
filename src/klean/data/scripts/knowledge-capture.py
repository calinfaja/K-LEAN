#!/usr/bin/env python3
"""
K-LEAN Knowledge Capture Script

Saves lessons, findings, and insights to the knowledge database.
Supports both simple CLI input and structured JSON for Claude integration.

Usage:
  knowledge-capture.py <content> [--type TYPE] [--tags TAG1,TAG2] [--priority LEVEL] [--url URL]
  knowledge-capture.py --json-input '<json>' [--json]

Types: warning, solution, pattern, finding (auto-inferred if omitted)
Priority: critical, high, medium, low

JSON Input (V3 Schema):
  {
    "title": "Short descriptive title (max 80 chars)",
    "insight": "2-4 sentence explanation with actionable details",
    "type": "warning|solution|pattern|finding",
    "priority": "critical|high|medium|low",
    "keywords": ["searchable", "terms"],
    "source": "https://url or file:path:line or git:hash or conv:YYYY-MM-DD"
  }

Examples:
  knowledge-capture.py "Always validate user input" --type warning --tags security,validation
  knowledge-capture.py --json-input '{"title":"Input Validation","insight":"Always validate user input server-side","keywords":["security","validation"]}' --json
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
        infer_type,
        is_server_running,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import (
        PYTHON_BIN,
        debug_log,
        infer_type,
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


def create_entry(content, entry_type="finding", tags=None, priority="medium", url=None):
    """Create a knowledge database entry (simple mode, V3 schema)."""
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Normalize legacy types
    if entry_type in ("lesson", "best-practice"):
        entry_type = "finding"

    # Generate a unique ID
    entry_id = f"{entry_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # V3 Schema
    entry = {
        "id": entry_id,
        "title": content[:100] if len(content) <= 100 else content[:97] + "...",
        "insight": content,
        "type": entry_type,
        "priority": priority,
        "keywords": tags[:10],
        "source": url or f"conv:{datetime.now().strftime('%Y-%m-%d')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    return entry


def create_entry_from_json(data: dict):
    """Create a knowledge database entry from structured JSON.

    Always outputs V3 schema, but accepts both V2 and V3 input field names.
    V3 Schema: id, title, insight, type, priority, keywords, source, date
    """
    entry_type = data.get("type", "")

    # Normalize legacy types or infer from content
    if not entry_type or entry_type in ("lesson", "best-practice"):
        title = data.get("title", "")
        insight = data.get("insight") or data.get("atomic_insight") or data.get("summary") or ""
        entry_type = infer_type(title, insight)

    entry_id = data.get("id") or f"{entry_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Merge insight sources: insight > atomic_insight > summary
    insight = (
        data.get("insight")
        or data.get("atomic_insight")
        or data.get("summary")
        or ""
    )

    # Merge keyword sources: keywords > tags + key_concepts
    keywords = data.get("keywords")
    if not keywords:
        tags = data.get("tags", [])
        concepts = data.get("key_concepts", [])
        keywords = list(dict.fromkeys(tags + concepts))  # Dedupe, preserve order

    # Merge source: source > url > source_path
    source = data.get("source", "")
    if not source or source in ("manual", "conversation", "review"):
        source = (
            data.get("url")
            or data.get("source_path")
            or f"conv:{datetime.now().strftime('%Y-%m-%d')}"
        )

    # V3 Schema output
    entry = {
        "id": entry_id,
        "title": data.get("title", ""),
        "insight": insight,
        "type": entry_type,
        "priority": data.get("priority", "medium"),
        "keywords": keywords[:10],
        "source": source,
        "date": data.get("date") or datetime.now().strftime("%Y-%m-%d"),
    }

    # Ensure title exists
    if not entry["title"] and entry["insight"]:
        entry["title"] = entry["insight"][:100]

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
        description="Capture knowledge to K-LEAN database (V3 schema)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Always validate user input" --type warning --tags security
  %(prog)s "Memory leak in pools" --type finding --priority high
  %(prog)s "Use async/await for I/O" --type pattern --tags python,async
  %(prog)s --json-input '{"title":"...","insight":"...","keywords":[...]}' --json
        """,
    )
    parser.add_argument("content", nargs="?", default="", help="The content to capture")
    parser.add_argument(
        "--type",
        dest="entry_type",
        default="finding",
        choices=["finding", "solution", "pattern", "warning"],
        help="Type of entry (default: finding, auto-inferred if omitted)",
    )
    parser.add_argument("--tags", default="", help="Comma-separated keywords")
    parser.add_argument(
        "--priority",
        default="medium",
        choices=["low", "medium", "high", "critical"],
        help="Priority level (default: medium)",
    )
    parser.add_argument("--url", default="", help="Source URL for the entry")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument(
        "--json-input", dest="json_input", help="Add structured entry from JSON string (V3 schema)"
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
        log_to_timeline(entry.get("insight", content_display), entry_type, knowledge_dir)

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
            print(f"  Saved to: {knowledge_dir}/entries.jsonl")
            if entry.get("keywords"):
                print(f"  Keywords: {', '.join(entry['keywords'])}")

        return 0

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"[ERROR] Error capturing knowledge: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
