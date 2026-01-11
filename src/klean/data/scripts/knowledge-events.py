#!/usr/bin/env python3
"""
Knowledge Base Event Notifications - Phase 4

Simple file-based event log for knowledge system transparency.

Events are appended to $KLEAN_SOCKET_DIR/knowledge-events.log (default: /tmp)

Event types:
- knowledge:captured (new fact added)
- knowledge:search (search executed)
- knowledge:context_injected (agent context prepared)
- knowledge:index_rebuilt (index rebuilt with new facts)

Usage:
    from knowledge_events import KnowledgeEventLog

    log = KnowledgeEventLog()
    log.emit("knowledge:captured", {"entry_id": "...", "title": "..."})

Or via CLI:
    python knowledge-events.py emit knowledge:captured '{"entry_id":"...","title":"..."}'
    python knowledge-events.py tail 20  # Last 20 events
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

LOG_PATH = Path(os.environ.get("KLEAN_SOCKET_DIR", tempfile.gettempdir())) / "knowledge-events.log"


class KnowledgeEventLog:
    """Simple file-based event log"""

    def __init__(self, log_path: Optional[Path] = None):
        """Initialize event log"""
        self.log_path = log_path or LOG_PATH
        # Create log file if doesn't exist
        self.log_path.touch(exist_ok=True)

    def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Emit an event.

        Args:
            event_type: Type of event (e.g., "knowledge:captured")
            data: Event data dictionary
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": data,
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def tail(self, limit: int = 20) -> list:
        """Get most recent events"""
        if not self.log_path.exists():
            return []

        events = []
        with open(self.log_path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        return events[-limit:]

    def search_events(self, event_type: Optional[str] = None, limit: int = 50) -> list:
        """Search events by type"""
        if not self.log_path.exists():
            return []

        events = []
        with open(self.log_path) as f:
            for line in f:
                if line.strip():
                    try:
                        event = json.loads(line)
                        if not event_type or event.get("type") == event_type:
                            events.append(event)
                    except json.JSONDecodeError:
                        pass

        return events[-limit:]

    def clear(self) -> None:
        """Clear event log"""
        self.log_path.unlink(missing_ok=True)
        self.log_path.touch()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge event log")
    parser.add_argument("command", choices=["emit", "tail", "search", "clear", "stats"])
    parser.add_argument("event_type", nargs="?", help="Event type (for emit/search)")
    parser.add_argument("data", nargs="?", help="JSON data (for emit)")
    parser.add_argument("--limit", "-n", type=int, default=20, help="Result limit")

    args = parser.parse_args()

    log = KnowledgeEventLog()

    if args.command == "emit":
        if not args.event_type or not args.data:
            print("Usage: knowledge-events.py emit <type> '<json_data>'")
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            sys.exit(1)
        log.emit(args.event_type, data)
        print(f"[OK] Event emitted: {args.event_type}")

    elif args.command == "tail":
        events = log.tail(args.limit)
        print(f"Recent {len(events)} events:\n")
        for event in events:
            ts = event.get("timestamp", "?")[:19]
            et = event.get("type", "?")
            print(f"[{ts}] {et}")
            data = event.get("data", {})
            if "title" in data:
                print(f"      {data['title']}")

    elif args.command == "search":
        if not args.event_type:
            print("Usage: knowledge-events.py search <type>")
            sys.exit(1)
        events = log.search_events(args.event_type, args.limit)
        print(f"Found {len(events)} {args.event_type} events:")
        for event in events[-5:]:  # Show last 5
            ts = event.get("timestamp", "?")[:10]
            print(f"  {ts}: {event.get('data', {}).get('title', '...')[:50]}")

    elif args.command == "clear":
        log.clear()
        print("[OK] Event log cleared")

    elif args.command == "stats":
        events = log.tail(1000)  # Load recent events
        types = {}
        for event in events:
            et = event.get("type", "unknown")
            types[et] = types.get(et, 0) + 1
        print(f"Total events: {len(events)}\n")
        for et, count in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {et}: {count}")
