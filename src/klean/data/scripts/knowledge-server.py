#!/usr/bin/env python3
"""
Knowledge Server - Per-project txtai daemon for fast searches

Each project gets its own server instance with dedicated socket.
Eliminates cold start by keeping embeddings loaded in memory.
Auto-shuts down after 1 hour of inactivity to free memory.

Usage:
    Start server:  knowledge-server.py start [project_path]
    Stop server:   knowledge-server.py stop [project_path]
    Status:        knowledge-server.py status [project_path]
    List all:      knowledge-server.py list

Socket naming: /tmp/kb-{project_hash}.sock
Each project has isolated index and server process.
"""

import hashlib
import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path

# Configuration
IDLE_TIMEOUT = 3600  # 1 hour in seconds
SOCKET_DIR = os.environ.get("KLEAN_SOCKET_DIR", "/tmp")


def get_project_hash(project_path: Path) -> str:
    """Generate short hash from project path for socket naming."""
    path_str = str(project_path.resolve())
    return hashlib.md5(path_str.encode()).hexdigest()[:8]


def get_socket_path(project_path: Path) -> str:
    """Get socket path for a project."""
    return f"{SOCKET_DIR}/kb-{get_project_hash(project_path)}.sock"


def get_pid_path(project_path: Path) -> str:
    """Get PID file path for a project."""
    return f"{SOCKET_DIR}/kb-{get_project_hash(project_path)}.pid"


def find_project_root(start_path=None):
    """Find project root by walking up looking for .knowledge-db.

    Returns the first directory containing .knowledge-db, or None.
    """
    current = Path(start_path or os.getcwd()).resolve()

    while current != current.parent:
        if (current / ".knowledge-db").exists():
            return current
        current = current.parent

    return None


def list_running_servers():
    """List all running knowledge servers."""
    servers = []
    for f in Path(SOCKET_DIR).glob("kb-*.sock"):
        pid_file = f.with_suffix(".pid")
        if pid_file.exists():
            try:
                with open(pid_file) as pf:
                    pid = int(pf.read().strip())
                # Check if process is running
                os.kill(pid, 0)
                # Get project info via socket
                info = send_command_to_socket(str(f), {"cmd": "status"})
                if info and "project" in info:
                    servers.append({
                        "socket": str(f),
                        "pid": pid,
                        "project": info.get("project", "unknown"),
                        "load_time": info.get("load_time", 0)
                    })
            except (ProcessLookupError, ValueError, FileNotFoundError):
                # Stale socket/pid, clean up
                try:
                    f.unlink()
                    pid_file.unlink()
                except:
                    pass
    return servers


class KnowledgeServer:
    def __init__(self, project_path=None):
        self.project_root = find_project_root(project_path)
        if not self.project_root:
            raise ValueError(f"No .knowledge-db found from {project_path or os.getcwd()}")

        self.socket_path = get_socket_path(self.project_root)
        self.pid_path = get_pid_path(self.project_root)
        self.embeddings = None
        self.running = False
        self.load_time = 0
        self.last_activity = time.time()

    def load_index(self):
        """Load txtai embeddings index."""
        index_path = self.project_root / ".knowledge-db" / "index"
        if not index_path.exists():
            return False

        print(f"Loading index from {index_path}...")
        start = time.time()

        # Heavy imports happen once
        from txtai import Embeddings

        # Use WAL mode for concurrent read/write access
        self.embeddings = Embeddings(sqlite={"wal": True})
        self.embeddings.load(str(index_path))

        self.load_time = time.time() - start
        print(f"Index loaded in {self.load_time:.2f}s ({self.embeddings.count()} entries)")
        return True

    def search(self, query, limit=5):
        """Perform semantic search."""
        self.last_activity = time.time()

        if not self.embeddings:
            return {"error": "No index loaded"}

        start = time.time()
        results = self.embeddings.search(query, limit)
        search_time = time.time() - start

        # Format results
        formatted = []
        for item in results:
            if isinstance(item, dict):
                formatted.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                score, data = item[0], item[1]
                if isinstance(data, dict):
                    data["score"] = score
                    formatted.append(data)
                else:
                    formatted.append({"id": data, "score": score})
            else:
                formatted.append({"data": str(item), "score": 0})

        return {
            "results": formatted,
            "search_time_ms": round(search_time * 1000, 2),
            "query": query
        }

    def handle_client(self, conn):
        """Handle a client connection."""
        self.last_activity = time.time()
        try:
            data = conn.recv(4096).decode('utf-8')
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
                    "load_time": self.load_time,
                    "index_loaded": self.embeddings is not None,
                    "idle_seconds": int(idle_time),
                    "entries": self.embeddings.count() if self.embeddings else 0
                }
            elif cmd == "ping":
                response = {"pong": True, "project": str(self.project_root)}
            else:
                response = {"error": f"Unknown command: {cmd}"}

            conn.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"error": str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def check_idle_timeout(self):
        """Check if server should shut down due to inactivity."""
        idle_time = time.time() - self.last_activity
        if idle_time > IDLE_TIMEOUT:
            print(f"\nIdle timeout ({IDLE_TIMEOUT}s) reached. Shutting down...")
            return True
        return False

    def start(self):
        """Start the server."""
        # Clean up old socket if exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        # Load index
        if not self.load_index():
            print("ERROR: No index found in .knowledge-db/index")
            print("  Create index first with: knowledge_db.py rebuild")
            sys.exit(1)

        # Create socket
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(5)
        os.chmod(self.socket_path, 0o666)

        # Write PID file
        with open(self.pid_path, 'w') as f:
            f.write(str(os.getpid()))

        print(f"Knowledge server started")
        print(f"  Socket:  {self.socket_path}")
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
                threading.Thread(target=self.handle_client, args=(conn,)).start()
            except socket.timeout:
                if self.check_idle_timeout():
                    break
                continue
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")

        # Cleanup
        server.close()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        if os.path.exists(self.pid_path):
            os.unlink(self.pid_path)
        print("Server stopped")


def send_command_to_socket(socket_path: str, cmd_data: dict):
    """Send command to a specific socket."""
    if not os.path.exists(socket_path):
        return None

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(socket_path)
        client.sendall(json.dumps(cmd_data).encode('utf-8'))
        response = client.recv(65536).decode('utf-8')
        client.close()
        return json.loads(response)
    except Exception as e:
        return {"error": str(e)}


def send_command(project_path, cmd_data):
    """Send command to the server for a project."""
    socket_path = get_socket_path(project_path)
    return send_command_to_socket(socket_path, cmd_data)


def main():
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
                print(f"    PID: {s['pid']}, Load: {s['load_time']:.1f}s")
                print(f"    Socket: {s['socket']}\n")
        else:
            print("No knowledge servers running")
        return

    # Commands that need a project
    project_path = sys.argv[2] if len(sys.argv) > 2 else None
    project_root = find_project_root(project_path)

    if cmd == "start":
        if not project_root:
            print("ERROR: No .knowledge-db found")
            print("  Run from a project directory or specify path")
            sys.exit(1)

        # Check if already running
        socket_path = get_socket_path(project_root)
        if os.path.exists(socket_path):
            result = send_command(project_root, {"cmd": "ping"})
            if result and result.get("pong"):
                print(f"Server already running for {project_root}")
                return

        server = KnowledgeServer(project_path)
        server.start()

    elif cmd == "stop":
        if not project_root:
            print("ERROR: No .knowledge-db found")
            sys.exit(1)

        pid_path = get_pid_path(project_root)
        socket_path = get_socket_path(project_root)

        if os.path.exists(pid_path):
            with open(pid_path) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Stopped server for {project_root} (PID {pid})")
            except ProcessLookupError:
                print("Server not running")
            # Cleanup
            for p in [pid_path, socket_path]:
                if os.path.exists(p):
                    os.unlink(p)
        else:
            print(f"No server running for {project_root}")

    elif cmd == "status":
        if not project_root:
            # Show all servers
            servers = list_running_servers()
            if servers:
                print(f"Running servers: {len(servers)}")
                for s in servers:
                    print(f"  - {s['project']}")
            else:
                print("No servers running")
            return

        result = send_command(project_root, {"cmd": "status"})
        if result and "error" not in result:
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Project: {result.get('project', 'none')}")
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
            print(f"Server running for {result.get('project', project_root)}")
        else:
            print("Server not running")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
