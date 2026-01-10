#!/usr/bin/env python3
"""
Knowledge Server - Per-project fastembed daemon for fast searches

Each project gets its own server instance with dedicated TCP port.
Eliminates cold start by keeping embeddings loaded in memory.
Auto-shuts down after 1 hour of inactivity to free memory.

Cross-platform: Works on Windows, Linux, and macOS using TCP sockets.

Usage:
    Start server:  knowledge-server.py start [project_path]
    Stop server:   knowledge-server.py stop [project_path]
    Status:        knowledge-server.py status [project_path]
    List all:      knowledge-server.py list

Port/PID files stored in runtime directory (platform-specific).
"""

import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path

# Import from kb_utils (self-contained, no external dependencies)
sys.path.insert(0, str(Path(__file__).parent))

from kb_utils import (
    cleanup_stale_files,
    find_project_root,
    get_kb_pid_file,
    get_kb_port,
    get_kb_port_file,
    get_project_hash,
    get_runtime_dir,
    is_process_running,
    kill_process_tree,
    read_pid_file,
    write_pid_file,
)

# Configuration
IDLE_TIMEOUT = 3600  # 1 hour in seconds
HOST = "127.0.0.1"


def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """Find an available TCP port starting from start_port.

    Args:
        start_port: Port to start searching from.
        max_attempts: Maximum number of ports to try.

    Returns:
        Available port number.

    Raises:
        RuntimeError: If no available port found.
    """
    for offset in range(max_attempts):
        port = start_port + offset
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((HOST, port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")


def read_port_file(project_path: Path) -> int | None:
    """Read port from project's port file.

    Args:
        project_path: Path to project root.

    Returns:
        Port number or None if file doesn't exist.
    """
    port_file = get_kb_port_file(project_path)
    try:
        if port_file.exists():
            return int(port_file.read_text().strip())
    except (ValueError, OSError):
        pass
    return None


def write_port_file(project_path: Path, port: int) -> None:
    """Write port to project's port file.

    Args:
        project_path: Path to project root.
        port: Port number to write.
    """
    port_file = get_kb_port_file(project_path)
    port_file.write_text(str(port))


def list_running_servers() -> list[dict]:
    """List all running knowledge servers.

    Returns:
        List of server info dicts with port, pid, project.
    """
    servers = []
    runtime_dir = get_runtime_dir()

    for port_file in runtime_dir.glob("kb-*.port"):
        pid_file = port_file.with_suffix(".pid")
        if not pid_file.exists():
            continue

        try:
            port = int(port_file.read_text().strip())
            pid = int(pid_file.read_text().strip())

            # Check if process is running
            if not is_process_running(pid):
                # Stale files, clean up
                port_file.unlink(missing_ok=True)
                pid_file.unlink(missing_ok=True)
                continue

            # Get project info via TCP
            info = send_command_to_port(port, {"cmd": "status"})
            if info and "project" in info:
                servers.append(
                    {
                        "port": port,
                        "pid": pid,
                        "project": info.get("project", "unknown"),
                        "load_time": info.get("load_time", 0),
                    }
                )
        except (ValueError, OSError):
            # Invalid file content, skip
            pass

    return servers


class KnowledgeServer:
    """TCP-based knowledge server for fast semantic search."""

    def __init__(self, project_path: str | Path | None = None):
        """Initialize server for a project.

        Args:
            project_path: Path to project root (auto-detected if None).

        Raises:
            ValueError: If no .knowledge-db found.
        """
        self.project_root = find_project_root(Path(project_path) if project_path else None)
        if not self.project_root:
            raise ValueError(f"No .knowledge-db found from {project_path or os.getcwd()}")

        self.port = 0  # Will be assigned on start
        self.db = None
        self.embeddings = None  # Legacy alias
        self.running = False
        self.load_time = 0.0
        self.last_activity = time.time()

    def load_index(self) -> bool:
        """Load fastembed-based knowledge index.

        Returns:
            True if index loaded successfully.
        """
        db_path = self.project_root / ".knowledge-db"
        has_fastembed = (db_path / "embeddings.npy").exists()
        has_txtai = (db_path / "index").exists()
        has_entries = (db_path / "entries.jsonl").exists()

        if not has_fastembed and not has_txtai and not has_entries:
            # Auto-initialize empty database
            db_path.mkdir(parents=True, exist_ok=True)
            (db_path / "entries.jsonl").touch()
            print(f"Auto-initialized empty Knowledge DB at {db_path}")

        print(f"Loading index from {db_path}...")
        start = time.time()

        # Import KnowledgeDB (fastembed-based)
        sys.path.insert(0, str(Path(__file__).parent))
        from knowledge_db import KnowledgeDB

        # KnowledgeDB handles auto-migration from txtai
        self.db = KnowledgeDB(str(self.project_root))
        self.embeddings = self.db  # Alias for compatibility

        self.load_time = time.time() - start
        count = self.db.count() if hasattr(self.db, "count") else len(self.db._id_to_row)
        print(f"Index loaded in {self.load_time:.2f}s ({count} entries)")
        return True

    def search(self, query: str, limit: int = 5) -> dict:
        """Perform semantic search.

        Args:
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            Dict with results, search_time_ms, and query.
        """
        self.last_activity = time.time()

        if not self.db:
            return {"error": "No index loaded"}

        start = time.time()
        results = self.db.search(query, limit)
        search_time = time.time() - start

        return {"results": results, "search_time_ms": round(search_time * 1000, 2), "query": query}

    def handle_client(self, conn: socket.socket) -> None:
        """Handle a client connection.

        Args:
            conn: Client socket connection.
        """
        self.last_activity = time.time()
        try:
            data = conn.recv(4096).decode("utf-8")
            if not data:
                return

            request = json.loads(data)
            cmd = request.get("cmd", "search")

            if cmd == "search":
                query = request.get("query", "")
                limit = request.get("limit", 5)
                response = self.search(query, limit)
            elif cmd == "status":
                idle_time = time.time() - self.last_activity
                response = {
                    "status": "running",
                    "project": str(self.project_root),
                    "port": self.port,
                    "load_time": self.load_time,
                    "index_loaded": self.db is not None,
                    "idle_seconds": int(idle_time),
                    "entries": self.db.count() if self.db else 0,
                    "backend": "fastembed",
                }
            elif cmd == "ping":
                response = {"pong": True, "project": str(self.project_root), "port": self.port}
            elif cmd == "add":
                # Add entry via server (ensures index stays in sync)
                entry = request.get("entry")
                if not entry:
                    response = {"error": "No entry provided"}
                elif not self.db:
                    response = {"error": "No index loaded"}
                else:
                    try:
                        entry_id = self.db.add(entry)
                        response = {"status": "ok", "id": entry_id}
                    except Exception as e:
                        response = {"error": f"Failed to add entry: {e}"}
            elif cmd == "update_usage":
                # Track usage: increment usage_count, update last_used
                entry_ids = request.get("ids", [])
                if not entry_ids:
                    response = {"error": "No ids provided"}
                elif not self.db:
                    response = {"error": "No index loaded"}
                else:
                    try:
                        updated = self.db.update_usage(entry_ids)
                        response = {"status": "ok", "updated": updated}
                    except Exception as e:
                        response = {"error": f"Failed to update usage: {e}"}
            elif cmd == "recent":
                # Get recent/high-priority entries for context injection
                limit = request.get("limit", 3)
                if not self.db:
                    response = {"error": "No index loaded"}
                else:
                    try:
                        entries = self.db.get_recent_important(limit)
                        response = {"status": "ok", "entries": entries}
                    except Exception as e:
                        response = {"error": f"Failed to get recent: {e}"}
            else:
                response = {"error": f"Unknown command: {cmd}"}

            conn.sendall(json.dumps(response).encode("utf-8"))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"error": str(e)}).encode("utf-8"))
            except OSError:
                pass
        finally:
            conn.close()

    def check_idle_timeout(self) -> bool:
        """Check if server should shut down due to inactivity.

        Returns:
            True if idle timeout reached.
        """
        idle_time = time.time() - self.last_activity
        if idle_time > IDLE_TIMEOUT:
            print(f"\nIdle timeout ({IDLE_TIMEOUT}s) reached. Shutting down...")
            return True
        return False

    def start(self) -> None:
        """Start the TCP server."""
        # Load index first
        if not self.load_index():
            print("ERROR: No index found in .knowledge-db/")
            print("  Create index first with: knowledge_db.py rebuild")
            sys.exit(1)

        # Find available port
        base_port = get_kb_port()
        project_hash = get_project_hash(self.project_root)
        # Use hash to offset port for this project (0-255 range)
        hash_offset = int(project_hash[:2], 16) % 256
        self.port = find_available_port(base_port + hash_offset)

        # Create TCP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, self.port))
        server.listen(5)

        # Write PID and port files
        pid_file = get_kb_pid_file(self.project_root)
        port_file = get_kb_port_file(self.project_root)
        write_pid_file(pid_file, os.getpid())
        write_port_file(self.project_root, self.port)

        print("Knowledge server started")
        print(f"  Port:    {HOST}:{self.port}")
        print(f"  Project: {self.project_root}")
        print(f"  Timeout: {IDLE_TIMEOUT}s idle")
        print("Ready for queries (Ctrl+C to stop)")

        self.running = True

        def signal_handler(sig, frame):
            print("\nShutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            try:
                server.settimeout(60.0)  # Check idle every minute
                conn, _ = server.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                if self.check_idle_timeout():
                    break
                continue
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")

        # Cleanup
        server.close()
        pid_file.unlink(missing_ok=True)
        port_file.unlink(missing_ok=True)
        print("Server stopped")


def send_command_to_port(port: int, cmd_data: dict, timeout: float = 5.0) -> dict | None:
    """Send command to server on specified port.

    Args:
        port: TCP port number.
        cmd_data: Command dict to send.
        timeout: Socket timeout in seconds.

    Returns:
        Response dict or None on error.
    """
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect((HOST, port))
        client.sendall(json.dumps(cmd_data).encode("utf-8"))
        response = client.recv(65536).decode("utf-8")
        client.close()
        return json.loads(response)
    except Exception as e:
        return {"error": str(e)}


def send_command(project_path: Path, cmd_data: dict) -> dict | None:
    """Send command to the server for a project.

    Args:
        project_path: Path to project root.
        cmd_data: Command dict to send.

    Returns:
        Response dict or None if server not running.
    """
    port = read_port_file(project_path)
    if not port:
        return None
    return send_command_to_port(port, cmd_data)


def main() -> None:
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: knowledge-server.py [start|stop|status|list|search <query>] [project_path]")
        print("\nPer-project knowledge server. Each project gets its own server.")
        print("\nCommands:")
        print("  start [path]    Start server for project (auto-detects from CWD)")
        print("  stop [path]     Stop server for project")
        print("  status [path]   Show server status for project")
        print("  list            List all running servers")
        print("  search <query>  Search in current project's knowledge DB")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        servers = list_running_servers()
        if servers:
            print(f"Running knowledge servers ({len(servers)}):\n")
            for s in servers:
                print(f"  {s['project']}")
                print(f"    PID: {s['pid']}, Port: {s['port']}, Load: {s['load_time']:.1f}s\n")
        else:
            print("No knowledge servers running")
        return

    # Commands that need a project
    project_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    project_root = find_project_root(project_path)

    if cmd == "start":
        if not project_root:
            print("ERROR: No .knowledge-db found")
            print("  Run from a project directory or specify path")
            sys.exit(1)

        # Clean up stale files first
        cleanup_stale_files(project_root)

        # Check if already running
        port = read_port_file(project_root)
        if port:
            result = send_command_to_port(port, {"cmd": "ping"})
            if result and result.get("pong"):
                print(f"Server already running for {project_root} on port {port}")
                return

        server = KnowledgeServer(project_path)
        server.start()

    elif cmd == "stop":
        if not project_root:
            print("ERROR: No .knowledge-db found")
            sys.exit(1)

        pid_file = get_kb_pid_file(project_root)
        port_file = get_kb_port_file(project_root)
        pid = read_pid_file(pid_file)

        if pid and is_process_running(pid):
            kill_process_tree(pid)
            print(f"Stopped server for {project_root} (PID {pid})")
            # Cleanup files
            pid_file.unlink(missing_ok=True)
            port_file.unlink(missing_ok=True)
        else:
            print(f"No server running for {project_root}")
            # Clean up stale files
            cleanup_stale_files(project_root)

    elif cmd == "status":
        if not project_root:
            # Show all servers
            servers = list_running_servers()
            if servers:
                print(f"Running servers: {len(servers)}")
                for s in servers:
                    print(f"  - {s['project']} (port {s['port']})")
            else:
                print("No servers running")
            return

        result = send_command(project_root, {"cmd": "status"})
        if result and "error" not in result:
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Project: {result.get('project', 'none')}")
            print(f"Port: {result.get('port', 'none')}")
            print(f"Entries: {result.get('entries', 0)}")
            print(f"Load time: {result.get('load_time', 0):.2f}s")
            print(f"Idle: {result.get('idle_seconds', 0)}s")
        else:
            print(f"Server not running for {project_root}")

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: knowledge-server.py search <query> [limit]")
            sys.exit(1)

        if not project_root:
            print("ERROR: No .knowledge-db found")
            sys.exit(1)

        query = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5

        result = send_command(project_root, {"cmd": "search", "query": query, "limit": limit})
        if result:
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Search time: {result.get('search_time_ms', '?')}ms")
                for r in result.get("results", []):
                    score = r.get("score", 0)
                    title = r.get("title", r.get("id", "?"))
                    print(f"  [{score:.2f}] {title}")
        else:
            print(f"Server not running for {project_root}")
            print("Start with: knowledge-server.py start")

    elif cmd == "ping":
        if not project_root:
            print("No project found")
            sys.exit(1)
        result = send_command(project_root, {"cmd": "ping"})
        if result and result.get("pong"):
            print(
                f"Server running for {result.get('project', project_root)} on port {result.get('port')}"
            )
        else:
            print("Server not running")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
