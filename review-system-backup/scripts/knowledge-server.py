#!/home/calin/.venvs/knowledge-db/bin/python
"""
Knowledge Server - Persistent txtai daemon for fast searches

Eliminates cold start by keeping embeddings loaded in memory.
Communicates via Unix socket for instant (~50ms) searches.

Usage:
    Start server:  knowledge-server.py start [project_path]
    Stop server:   knowledge-server.py stop
    Status:        knowledge-server.py status

The server auto-detects project root and loads the knowledge-db index.
"""

import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path

# Socket configuration
SOCKET_PATH = "/tmp/knowledge-server.sock"
PID_FILE = "/tmp/knowledge-server.pid"


def find_project_root(start_path=None):
    """Find project root by looking for knowledge-db markers."""
    current = Path(start_path or os.getcwd()).resolve()
    while current != current.parent:
        if (current / ".knowledge-db").exists():
            return current
        if (current / ".serena").exists():
            return current
        if (current / ".claude").exists():
            return current
        current = current.parent
    return None


class KnowledgeServer:
    def __init__(self, project_path=None):
        self.project_root = find_project_root(project_path)
        self.embeddings = None
        self.running = False
        self.load_time = 0

    def load_index(self):
        """Load txtai embeddings index."""
        if not self.project_root:
            return False

        index_path = self.project_root / ".knowledge-db" / "index"
        if not index_path.exists():
            return False

        print(f"Loading index from {index_path}...")
        start = time.time()

        # Heavy imports happen once
        from txtai import Embeddings

        self.embeddings = Embeddings()
        self.embeddings.load(str(index_path))

        self.load_time = time.time() - start
        print(f"Index loaded in {self.load_time:.2f}s")
        return True

    def search(self, query, limit=5):
        """Perform semantic search."""
        if not self.embeddings:
            return {"error": "No index loaded"}

        start = time.time()
        results = self.embeddings.search(query, limit)
        search_time = time.time() - start

        # Format results - txtai returns list of dicts with 'score' already included
        formatted = []
        for item in results:
            if isinstance(item, dict):
                formatted.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # Legacy format: (score, data)
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
                response = {
                    "status": "running",
                    "project": str(self.project_root),
                    "load_time": self.load_time,
                    "index_loaded": self.embeddings is not None
                }
            elif cmd == "ping":
                response = {"pong": True}
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

    def start(self):
        """Start the server."""
        # Clean up old socket
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        # Load index (optional - server works without, returns "no index" for queries)
        if not self.load_index():
            print("WARNING: No knowledge-db index found in current project")
            print("   Server will start but queries will return 'no index'")
            print("   To create index: k-lean install --component knowledge")

        # Create socket
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCKET_PATH)
        server.listen(5)
        os.chmod(SOCKET_PATH, 0o666)

        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        print(f"Knowledge server started on {SOCKET_PATH}")
        print(f"Project: {self.project_root or 'none (no index)'}")
        print("Ready for queries (Ctrl+C to stop)")

        self.running = True

        def signal_handler(sig, frame):
            print("\nShutting down...")
            self.running = False
            server.close()
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
            if os.path.exists(PID_FILE):
                os.unlink(PID_FILE)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            try:
                server.settimeout(1.0)
                conn, _ = server.accept()
                threading.Thread(target=self.handle_client, args=(conn,)).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")


def send_command(cmd_data):
    """Send command to running server."""
    if not os.path.exists(SOCKET_PATH):
        return None

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.sendall(json.dumps(cmd_data).encode('utf-8'))
        response = client.recv(65536).decode('utf-8')
        client.close()
        return json.loads(response)
    except Exception as e:
        return {"error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: knowledge-server.py [start|stop|status|search <query>]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        project_path = sys.argv[2] if len(sys.argv) > 2 else None
        server = KnowledgeServer(project_path)
        server.start()

    elif cmd == "stop":
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Stopped server (PID {pid})")
            except ProcessLookupError:
                print("Server not running")
            if os.path.exists(PID_FILE):
                os.unlink(PID_FILE)
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
        else:
            print("Server not running")

    elif cmd == "status":
        result = send_command({"cmd": "status"})
        if result and "error" not in result:
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Project: {result.get('project', 'none')}")
            print(f"Load time: {result.get('load_time', 0):.2f}s")
        else:
            print("Server not running")

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: knowledge-server.py search <query> [limit]")
            sys.exit(1)
        query = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5

        result = send_command({"cmd": "search", "query": query, "limit": limit})
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
            print("Server not running. Start with: knowledge-server.py start")

    elif cmd == "ping":
        result = send_command({"cmd": "ping"})
        if result and result.get("pong"):
            print("Server is running")
        else:
            print("Server not running")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
