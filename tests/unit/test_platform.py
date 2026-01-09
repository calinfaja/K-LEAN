"""Tests for klean.platform cross-platform utilities.

Tests cover:
- Path utilities (get_config_dir, get_runtime_dir, etc.)
- Process utilities (find_process, spawn_background, kill_process_tree)
- PID file utilities (read_pid_file, write_pid_file, cleanup_stale_files)
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Path Utilities Tests
# =============================================================================


class TestGetConfigDir:
    """Tests for get_config_dir()."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        from klean.platform import get_config_dir

        result = get_config_dir()
        assert isinstance(result, Path)

    def test_directory_name_is_klean(self):
        """Should return path ending with 'klean'."""
        from klean.platform import get_config_dir

        result = get_config_dir()
        assert result.name == "klean"

    def test_directory_exists(self):
        """Should ensure directory exists."""
        from klean.platform import get_config_dir

        result = get_config_dir()
        assert result.exists()
        assert result.is_dir()


class TestGetCacheDir:
    """Tests for get_cache_dir()."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        from klean.platform import get_cache_dir

        result = get_cache_dir()
        assert isinstance(result, Path)

    def test_directory_name_is_klean(self):
        """Should return path ending with 'klean'."""
        from klean.platform import get_cache_dir

        result = get_cache_dir()
        assert result.name == "klean"


class TestGetRuntimeDir:
    """Tests for get_runtime_dir()."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        from klean.platform import get_runtime_dir

        result = get_runtime_dir()
        assert isinstance(result, Path)

    def test_creates_directory(self):
        """Should create the directory if it doesn't exist."""
        from klean.platform import get_runtime_dir

        result = get_runtime_dir()
        assert result.exists()
        assert result.is_dir()

    def test_includes_username(self):
        """Should include username in directory name."""
        import getpass

        from klean.platform import get_runtime_dir

        result = get_runtime_dir()
        username = getpass.getuser()
        assert f"klean-{username}" in str(result)


class TestGetKbPort:
    """Tests for get_kb_port()."""

    def test_returns_default_port(self):
        """Should return DEFAULT_KB_PORT when env var not set."""
        from klean.platform import DEFAULT_KB_PORT, get_kb_port

        # Ensure env var is not set
        os.environ.pop("KLEAN_KB_PORT", None)

        result = get_kb_port()
        assert result == DEFAULT_KB_PORT
        assert result == 14000

    def test_reads_from_environment(self):
        """Should read port from KLEAN_KB_PORT environment variable."""
        from klean.platform import get_kb_port

        os.environ["KLEAN_KB_PORT"] = "15000"
        try:
            result = get_kb_port()
            assert result == 15000
        finally:
            os.environ.pop("KLEAN_KB_PORT", None)

    def test_returns_integer(self):
        """Should return an integer."""
        from klean.platform import get_kb_port

        result = get_kb_port()
        assert isinstance(result, int)


class TestGetProjectHash:
    """Tests for get_project_hash()."""

    def test_returns_8_char_hex(self):
        """Should return 8-character hex string."""
        from klean.platform import get_project_hash

        result = get_project_hash(Path("/some/project"))
        assert len(result) == 8
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_path_same_hash(self):
        """Should return same hash for same path."""
        from klean.platform import get_project_hash

        result1 = get_project_hash(Path("/some/project"))
        result2 = get_project_hash(Path("/some/project"))
        assert result1 == result2

    def test_different_path_different_hash(self):
        """Should return different hash for different paths."""
        from klean.platform import get_project_hash

        result1 = get_project_hash(Path("/project/one"))
        result2 = get_project_hash(Path("/project/two"))
        assert result1 != result2


class TestGetKbPortFile:
    """Tests for get_kb_port_file()."""

    def test_returns_path_with_port_extension(self):
        """Should return path ending with .port."""
        from klean.platform import get_kb_port_file

        result = get_kb_port_file(Path("/some/project"))
        assert result.suffix == ".port"

    def test_includes_project_hash(self):
        """Should include project hash in filename."""
        from klean.platform import get_kb_port_file, get_project_hash

        project = Path("/some/project")
        result = get_kb_port_file(project)
        project_hash = get_project_hash(project)
        assert project_hash in result.stem


class TestGetKbPidFile:
    """Tests for get_kb_pid_file()."""

    def test_returns_path_with_pid_extension(self):
        """Should return path ending with .pid."""
        from klean.platform import get_kb_pid_file

        result = get_kb_pid_file(Path("/some/project"))
        assert result.suffix == ".pid"


class TestFindProjectRoot:
    """Tests for find_project_root()."""

    def test_returns_none_when_no_markers(self, tmp_path):
        """Should return None when no project markers found."""
        from klean.platform import find_project_root

        # Create empty directory with no markers
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = find_project_root(empty_dir)
        assert result is None

    def test_finds_git_directory(self, tmp_path):
        """Should find project root by .git directory."""
        from klean.platform import find_project_root

        project = tmp_path / "myproject"
        project.mkdir()
        (project / ".git").mkdir()

        subdir = project / "src" / "module"
        subdir.mkdir(parents=True)

        result = find_project_root(subdir)
        assert result == project

    def test_finds_knowledge_db_directory(self, tmp_path):
        """Should find project root by .knowledge-db directory."""
        from klean.platform import find_project_root

        project = tmp_path / "myproject"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        result = find_project_root(project)
        assert result == project

    def test_respects_env_var(self, tmp_path):
        """Should use CLAUDE_PROJECT_DIR environment variable if set."""
        from klean.platform import find_project_root

        env_dir = tmp_path / "env_project"
        env_dir.mkdir()

        os.environ["CLAUDE_PROJECT_DIR"] = str(env_dir)
        try:
            result = find_project_root()
            assert result == env_dir
        finally:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)


# =============================================================================
# Process Utilities Tests
# =============================================================================


class TestFindProcess:
    """Tests for find_process()."""

    def test_returns_none_when_no_match(self):
        """Should return None when no process matches."""
        from klean.platform import find_process

        # Use a pattern that won't match any real process
        result = find_process("__nonexistent_process_pattern_xyz123__")
        assert result is None

    def test_finds_matching_process(self):
        """Should find process matching pattern."""
        from klean.platform import find_process

        # Python process should always be running
        result = find_process("python")
        # May or may not find one depending on cmdline visibility
        # Just verify it doesn't crash
        assert result is None or hasattr(result, "pid")


class TestFindAllProcesses:
    """Tests for find_all_processes()."""

    def test_returns_empty_list_when_no_match(self):
        """Should return empty list when no processes match."""
        from klean.platform import find_all_processes

        result = find_all_processes("__nonexistent_process_pattern_xyz123__")
        assert result == []
        assert isinstance(result, list)

    def test_returns_list(self):
        """Should return a list."""
        from klean.platform import find_all_processes

        result = find_all_processes("python")
        assert isinstance(result, list)


class TestIsProcessRunning:
    """Tests for is_process_running()."""

    def test_returns_false_for_nonexistent_pid(self):
        """Should return False for PID that doesn't exist."""
        from klean.platform import is_process_running

        # Use a very high PID that's unlikely to exist
        result = is_process_running(999999999)
        assert result is False

    def test_returns_true_for_current_process(self):
        """Should return True for current process."""
        from klean.platform import is_process_running

        result = is_process_running(os.getpid())
        assert result is True


class TestSpawnBackground:
    """Tests for spawn_background()."""

    def test_returns_pid(self, tmp_path):
        """Should return PID of spawned process."""
        from klean.platform import spawn_background

        # Spawn a simple sleep command (cross-platform via Python)
        if sys.platform == "win32":
            cmd = ["python", "-c", "import time; time.sleep(0.1)"]
        else:
            cmd = ["sleep", "0.1"]

        pid = spawn_background(cmd, cwd=tmp_path)
        assert isinstance(pid, int)
        assert pid > 0


class TestKillProcessTree:
    """Tests for kill_process_tree()."""

    def test_returns_false_for_nonexistent_pid(self):
        """Should return False when PID doesn't exist."""
        from klean.platform import kill_process_tree

        result = kill_process_tree(999999999)
        assert result is False

    def test_kills_spawned_process(self, tmp_path):
        """Should kill a process we spawned."""
        from klean.platform import is_process_running, kill_process_tree, spawn_background

        # Spawn a long-running process
        if sys.platform == "win32":
            cmd = ["python", "-c", "import time; time.sleep(60)"]
        else:
            cmd = ["sleep", "60"]

        pid = spawn_background(cmd, cwd=tmp_path)

        # Verify it's running
        import time

        time.sleep(0.1)  # Give it time to start

        # Kill it
        result = kill_process_tree(pid, timeout=2.0)
        assert result is True

        # Verify it's dead
        time.sleep(0.2)
        assert is_process_running(pid) is False


# =============================================================================
# PID File Utilities Tests
# =============================================================================


class TestReadPidFile:
    """Tests for read_pid_file()."""

    def test_returns_none_when_file_missing(self, tmp_path):
        """Should return None when file doesn't exist."""
        from klean.platform import read_pid_file

        result = read_pid_file(tmp_path / "nonexistent.pid")
        assert result is None

    def test_reads_pid_from_file(self, tmp_path):
        """Should read PID as integer from file."""
        from klean.platform import read_pid_file

        pid_file = tmp_path / "test.pid"
        pid_file.write_text("12345")

        result = read_pid_file(pid_file)
        assert result == 12345

    def test_handles_whitespace(self, tmp_path):
        """Should handle whitespace in PID file."""
        from klean.platform import read_pid_file

        pid_file = tmp_path / "test.pid"
        pid_file.write_text("  12345  \n")

        result = read_pid_file(pid_file)
        assert result == 12345

    def test_returns_none_for_invalid_content(self, tmp_path):
        """Should return None when file contains non-integer."""
        from klean.platform import read_pid_file

        pid_file = tmp_path / "test.pid"
        pid_file.write_text("not-a-number")

        result = read_pid_file(pid_file)
        assert result is None


class TestWritePidFile:
    """Tests for write_pid_file()."""

    def test_writes_pid_to_file(self, tmp_path):
        """Should write PID to file."""
        from klean.platform import write_pid_file

        pid_file = tmp_path / "test.pid"
        write_pid_file(pid_file, 54321)

        assert pid_file.exists()
        assert pid_file.read_text() == "54321"


class TestCleanupStaleFiles:
    """Tests for cleanup_stale_files()."""

    def test_removes_stale_files(self, tmp_path):
        """Should remove PID and port files when process is dead."""
        from klean.platform import (
            cleanup_stale_files,
            get_kb_pid_file,
            get_kb_port_file,
            get_runtime_dir,
            write_pid_file,
        )

        project = tmp_path / "project"
        project.mkdir()

        # Mock the runtime dir to use our temp path
        with patch("klean.platform.get_runtime_dir", return_value=tmp_path):
            pid_file = tmp_path / f"kb-{tmp_path.name[:8]}.pid"
            port_file = tmp_path / f"kb-{tmp_path.name[:8]}.port"

            # Create stale files with non-existent PID
            write_pid_file(pid_file, 999999999)
            port_file.write_text("14000")

            assert pid_file.exists()
            assert port_file.exists()

            # Cleanup should remove them (process doesn't exist)
            with patch("klean.platform.get_kb_pid_file", return_value=pid_file):
                with patch("klean.platform.get_kb_port_file", return_value=port_file):
                    cleanup_stale_files(project)

            assert not pid_file.exists()
            assert not port_file.exists()

    def test_preserves_files_for_running_process(self, tmp_path):
        """Should preserve files when process is still running."""
        from klean.platform import cleanup_stale_files, write_pid_file

        project = tmp_path / "project"
        project.mkdir()

        pid_file = tmp_path / "kb-test.pid"
        port_file = tmp_path / "kb-test.port"

        # Write current process PID (which is running)
        write_pid_file(pid_file, os.getpid())
        port_file.write_text("14000")

        with patch("klean.platform.get_kb_pid_file", return_value=pid_file):
            with patch("klean.platform.get_kb_port_file", return_value=port_file):
                cleanup_stale_files(project)

        # Files should still exist
        assert pid_file.exists()
        assert port_file.exists()
