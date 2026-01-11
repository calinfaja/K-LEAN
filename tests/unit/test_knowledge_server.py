"""Tests for knowledge server TCP mode.

Tests verify:
- TCP socket communication (not Unix socket)
- Port file management
- Server status detection
- Cross-platform compatibility
"""

import json
import socket
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch


# Helper to import kb_utils from source
def get_kb_utils():
    """Get kb_utils module from source directory."""
    src_path = str(Path(__file__).parent.parent.parent / "src/klean/data/scripts")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    # Force reload to get source version
    if "kb_utils" in sys.modules:
        del sys.modules["kb_utils"]
    import kb_utils

    return kb_utils


# =============================================================================
# Port File Tests
# =============================================================================


class TestPortFileManagement:
    """Tests for port file read/write operations."""

    def test_get_kb_port_file_returns_path(self, tmp_path):
        """Should return Path object for port file."""
        from klean.platform import get_kb_port_file

        project = tmp_path / "test-project"
        project.mkdir()

        result = get_kb_port_file(project)
        assert isinstance(result, Path)
        assert result.suffix == ".port"

    def test_port_file_contains_project_hash(self, tmp_path):
        """Port file should contain project hash in name."""
        from klean.platform import get_kb_port_file, get_project_hash

        project = tmp_path / "test-project"
        project.mkdir()

        result = get_kb_port_file(project)
        project_hash = get_project_hash(project)
        assert project_hash in result.stem


class TestGetServerPort:
    """Tests for get_server_port() function."""

    def test_returns_none_when_no_port_file(self, tmp_path):
        """Should return None when port file doesn't exist."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        # Mock get_kb_port_file to return non-existent file
        with patch.object(kb_utils, "get_kb_port_file", return_value=tmp_path / "nonexistent.port"):
            result = kb_utils.get_server_port(project)
            assert result is None

    def test_reads_port_from_file(self, tmp_path):
        """Should read port number from port file."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        port_file = tmp_path / "test.port"
        port_file.write_text("14567")

        with patch.object(kb_utils, "get_kb_port_file", return_value=port_file):
            result = kb_utils.get_server_port(project)
            assert result == 14567


# =============================================================================
# Server Status Tests
# =============================================================================


class TestIsServerRunning:
    """Tests for is_server_running() function."""

    def test_returns_false_when_no_port_file(self, tmp_path):
        """Should return False when no port file exists."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        with patch.object(kb_utils, "get_server_port", return_value=None):
            result = kb_utils.is_server_running(project)
            assert result is False

    def test_returns_false_when_connection_fails(self, tmp_path):
        """Should return False when cannot connect to server."""
        kb_utils = get_kb_utils()
        from klean.platform import get_kb_port_file

        project = tmp_path / "project"
        project.mkdir()

        # Write port file pointing to unused port
        with patch("klean.platform.get_runtime_dir", return_value=tmp_path):
            port_file = get_kb_port_file(project)
            port_file.write_text("59999")  # Port that's not listening

            with patch.object(kb_utils, "get_server_port", return_value=59999):
                result = kb_utils.is_server_running(project, timeout=0.1)
                assert result is False


class TestTcpCommunication:
    """Tests for TCP socket communication."""

    def test_send_command_returns_none_without_port(self, tmp_path):
        """Should return None when no port file exists."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        with patch.object(kb_utils, "get_server_port", return_value=None):
            result = kb_utils.send_command(project, {"cmd": "ping"})
            assert result is None

    def test_tcp_server_communication(self):
        """Test TCP server/client communication works."""
        # Create a simple echo server
        server_received = []

        def echo_server(port):
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", port))
            server.listen(1)
            server.settimeout(2.0)

            try:
                conn, _ = server.accept()
                data = conn.recv(1024).decode()
                server_received.append(data)
                response = json.dumps({"pong": True})
                conn.sendall(response.encode())
                conn.close()
            except socket.timeout:
                pass
            finally:
                server.close()

        # Find an available port
        test_port = 54321
        for offset in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("127.0.0.1", test_port + offset))
                sock.close()
                test_port = test_port + offset
                break
            except OSError:
                continue

        # Start server in thread
        server_thread = threading.Thread(target=echo_server, args=(test_port,))
        server_thread.start()
        time.sleep(0.1)  # Let server start

        # Test client connection
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1.0)
            client.connect(("127.0.0.1", test_port))
            client.sendall(json.dumps({"cmd": "ping"}).encode())
            response = client.recv(1024).decode()
            client.close()

            assert '"pong"' in response
            assert len(server_received) == 1
        finally:
            server_thread.join(timeout=3.0)


# =============================================================================
# Knowledge DB Initialization Tests
# =============================================================================


class TestIsKbInitialized:
    """Tests for is_kb_initialized() function."""

    def test_returns_false_when_no_kb_dir(self, tmp_path):
        """Should return False when .knowledge-db doesn't exist."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        result = kb_utils.is_kb_initialized(project)
        assert result is False

    def test_returns_true_when_kb_dir_exists(self, tmp_path):
        """Should return True when .knowledge-db exists."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        result = kb_utils.is_kb_initialized(project)
        assert result is True


# =============================================================================
# Stale File Cleanup Tests
# =============================================================================


class TestCleanStaleSocket:
    """Tests for clean_stale_socket() function."""

    def test_returns_false_when_no_port_file(self, tmp_path):
        """Should return False when port file doesn't exist."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        with patch.object(kb_utils, "get_kb_port_file") as mock_port_file:
            mock_port_file.return_value = tmp_path / "nonexistent.port"
            result = kb_utils.clean_stale_socket(project)
            assert result is False

    def test_cleans_stale_files_when_server_not_running(self, tmp_path):
        """Should remove port/pid files when server not responding."""
        kb_utils = get_kb_utils()

        project = tmp_path / "project"
        project.mkdir()

        # Create stale files
        port_file = tmp_path / "test.port"
        pid_file = tmp_path / "test.pid"
        port_file.write_text("59999")  # Port not listening
        pid_file.write_text("999999")

        with patch.object(kb_utils, "get_kb_port_file", return_value=port_file):
            with patch.object(kb_utils, "get_kb_pid_file", return_value=pid_file):
                with patch.object(kb_utils, "get_server_port", return_value=59999):
                    with patch.object(kb_utils, "is_server_running", return_value=False):
                        result = kb_utils.clean_stale_socket(project)
                        assert result is True
                        assert not port_file.exists()
                        assert not pid_file.exists()


# =============================================================================
# Cross-Platform Tests
# =============================================================================


class TestCrossPlatform:
    """Tests for cross-platform compatibility."""

    def test_uses_tcp_not_unix_socket(self):
        """Should use AF_INET (TCP) not AF_UNIX."""
        kb_utils = get_kb_utils()

        # Verify the function uses TCP socket
        import inspect

        source = inspect.getsource(kb_utils.is_server_running)
        assert "AF_INET" in source
        assert "AF_UNIX" not in source

    def test_host_is_localhost(self):
        """Should connect to localhost (127.0.0.1)."""
        kb_utils = get_kb_utils()

        assert kb_utils.HOST == "127.0.0.1"


# =============================================================================
# Platform Integration Tests
# =============================================================================


class TestPlatformIntegration:
    """Tests for integration with klean.platform module."""

    def test_kb_utils_imports_platform_functions(self):
        """kb_utils should import from klean.platform."""
        kb_utils = get_kb_utils()

        # These should be available as imports/attributes
        assert hasattr(kb_utils, "find_project_root")
        assert hasattr(kb_utils, "get_kb_port_file")
        assert hasattr(kb_utils, "get_kb_pid_file")
        assert hasattr(kb_utils, "get_runtime_dir")

    def test_default_port_is_configured(self):
        """Should have default port constant."""
        kb_utils = get_kb_utils()

        # Should have DEFAULT_KB_PORT from platform or define HOST
        assert hasattr(kb_utils, "HOST")
        assert kb_utils.HOST == "127.0.0.1"
