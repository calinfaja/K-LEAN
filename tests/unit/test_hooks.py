"""Tests for klean.hooks module.

Tests cover:
- Hook I/O helpers (read_input, output_json)
- Service management (LiteLLM, KB server detection)
- Keyword dispatch (FindKnowledge, SaveInfo, InitKB)
- Timeline logging
"""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Hook I/O Tests
# =============================================================================


class TestReadInput:
    """Tests for _read_input() function."""

    def test_parses_valid_json(self):
        """Should parse valid JSON from stdin."""
        from klean.hooks import _read_input

        with patch("sys.stdin", StringIO('{"prompt": "test"}')):
            result = _read_input()
            assert result == {"prompt": "test"}

    def test_returns_empty_dict_on_invalid_json(self):
        """Should return empty dict on invalid JSON."""
        from klean.hooks import _read_input

        with patch("sys.stdin", StringIO("not valid json")):
            result = _read_input()
            assert result == {}

    def test_returns_empty_dict_on_empty_input(self):
        """Should return empty dict on empty input."""
        from klean.hooks import _read_input

        with patch("sys.stdin", StringIO("")):
            result = _read_input()
            assert result == {}


class TestOutputJson:
    """Tests for _output_json() function."""

    def test_outputs_json_string(self, capsys):
        """Should output JSON string to stdout."""
        from klean.hooks import _output_json

        _output_json({"test": "value"})
        captured = capsys.readouterr()
        assert json.loads(captured.out) == {"test": "value"}


class TestOutputText:
    """Tests for _output_text() function."""

    def test_outputs_plain_text(self, capsys):
        """Should output plain text to stdout."""
        from klean.hooks import _output_text

        _output_text("Hello world")
        captured = capsys.readouterr()
        assert "Hello world" in captured.out


# =============================================================================
# Service Management Tests
# =============================================================================


class TestIsLitellmRunning:
    """Tests for _is_litellm_running() function."""

    def test_returns_false_when_no_connection(self):
        """Should return False when cannot connect to port 4000."""
        from klean.hooks import _is_litellm_running

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 1  # Connection refused
            mock_socket.return_value = mock_sock

            result = _is_litellm_running()
            assert result is False

    def test_returns_true_when_connected(self):
        """Should return True when port 4000 is open."""
        from klean.hooks import _is_litellm_running

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0  # Connection successful
            mock_socket.return_value = mock_sock

            result = _is_litellm_running()
            assert result is True


class TestIsKbServerRunning:
    """Tests for _is_kb_server_running() function."""

    def test_returns_false_when_no_port_file(self, tmp_path):
        """Should return False when port file doesn't exist."""
        from klean.hooks import _is_kb_server_running

        project = tmp_path / "project"
        project.mkdir()

        with patch("klean.hooks.get_kb_port_file") as mock_port_file:
            mock_port_file.return_value = tmp_path / "nonexistent.port"
            result = _is_kb_server_running(project)
            assert result is False

    def test_returns_false_when_connection_fails(self, tmp_path):
        """Should return False when cannot connect to server."""
        from klean.hooks import _is_kb_server_running

        project = tmp_path / "project"
        project.mkdir()
        port_file = tmp_path / "test.port"
        port_file.write_text("59999")

        with patch("klean.hooks.get_kb_port_file", return_value=port_file):
            result = _is_kb_server_running(project)
            assert result is False


# =============================================================================
# Handler Tests
# =============================================================================


class TestHandleFindKnowledge:
    """Tests for _handle_find_knowledge() function."""

    def test_returns_no_project_when_not_found(self):
        """Should return message when no project found."""
        from klean.hooks import _handle_find_knowledge

        with patch("klean.hooks.find_project_root", return_value=None):
            result = _handle_find_knowledge("test query")
            assert "No project found" in result

    def test_returns_not_initialized_when_no_kb_dir(self, tmp_path):
        """Should return message when KB dir doesn't exist."""
        from klean.hooks import _handle_find_knowledge

        project = tmp_path / "project"
        project.mkdir()

        with patch("klean.hooks.find_project_root", return_value=project):
            result = _handle_find_knowledge("test query")
            assert "not initialized" in result


class TestHandleInitKb:
    """Tests for _handle_init_kb() function."""

    def test_creates_kb_directory(self, tmp_path):
        """Should create .knowledge-db directory."""
        from klean.hooks import _handle_init_kb

        project = tmp_path / "project"
        project.mkdir()

        with patch("klean.hooks.find_project_root", return_value=project):
            result = _handle_init_kb()
            assert "initialized" in result
            assert (project / ".knowledge-db").exists()

    def test_reports_existing_kb(self, tmp_path):
        """Should report when KB already exists."""
        from klean.hooks import _handle_init_kb

        project = tmp_path / "project"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        with patch("klean.hooks.find_project_root", return_value=project):
            result = _handle_init_kb()
            assert "already exists" in result


# =============================================================================
# Timeline Tests
# =============================================================================


class TestLogToTimeline:
    """Tests for _log_to_timeline() function."""

    def test_creates_timeline_entry(self, tmp_path):
        """Should append entry to timeline.txt."""
        from klean.hooks import _log_to_timeline

        project = tmp_path / "project"
        project.mkdir()
        kb_dir = project / ".knowledge-db"
        kb_dir.mkdir()

        with patch("klean.hooks.find_project_root", return_value=project):
            _log_to_timeline("commit", "Test commit message")

        timeline_file = kb_dir / "timeline.txt"
        assert timeline_file.exists()
        content = timeline_file.read_text()
        assert "commit" in content
        assert "Test commit message" in content

    def test_handles_missing_kb_dir(self, tmp_path):
        """Should do nothing when KB dir doesn't exist."""
        from klean.hooks import _log_to_timeline

        project = tmp_path / "project"
        project.mkdir()

        with patch("klean.hooks.find_project_root", return_value=project):
            # Should not raise
            _log_to_timeline("commit", "Test")


# =============================================================================
# Hook Entry Point Tests
# =============================================================================


class TestSessionStartHook:
    """Tests for session_start() hook."""

    def test_exits_with_code_zero(self):
        """Should always exit with code 0."""
        from klean.hooks import session_start

        with patch("sys.stdin", StringIO("{}")):
            with patch("klean.hooks._is_litellm_running", return_value=True):
                with patch("klean.hooks.find_project_root", return_value=None):
                    with pytest.raises(SystemExit) as exc_info:
                        session_start()
                    assert exc_info.value.code == 0


class TestPromptHandlerHook:
    """Tests for prompt_handler() hook."""

    def test_exits_zero_on_no_prompt(self):
        """Should exit 0 when no prompt found."""
        from klean.hooks import prompt_handler

        with patch("sys.stdin", StringIO("{}")):
            with pytest.raises(SystemExit) as exc_info:
                prompt_handler()
            assert exc_info.value.code == 0

    def test_handles_findknowledge_keyword(self, tmp_path):
        """Should handle FindKnowledge keyword."""
        from klean.hooks import prompt_handler

        project = tmp_path / "project"
        project.mkdir()

        input_data = {"prompt": "FindKnowledge test query"}

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch("klean.hooks.find_project_root", return_value=project):
                with pytest.raises(SystemExit) as exc_info:
                    prompt_handler()
                assert exc_info.value.code == 0

    def test_handles_initkb_keyword(self, tmp_path, capsys):
        """Should handle InitKB keyword."""
        from klean.hooks import prompt_handler

        project = tmp_path / "project"
        project.mkdir()

        input_data = {"prompt": "InitKB"}

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch("klean.hooks.find_project_root", return_value=project):
                with pytest.raises(SystemExit) as exc_info:
                    prompt_handler()
                assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "systemMessage" in captured.out


class TestPostBashHook:
    """Tests for post_bash() hook."""

    def test_exits_zero_on_empty_command(self):
        """Should exit 0 when no command found."""
        from klean.hooks import post_bash

        with patch("sys.stdin", StringIO("{}")):
            with pytest.raises(SystemExit) as exc_info:
                post_bash()
            assert exc_info.value.code == 0

    def test_logs_git_commit(self, tmp_path):
        """Should log git commit to timeline."""
        from klean.hooks import post_bash

        project = tmp_path / "project"
        project.mkdir()
        kb_dir = project / ".knowledge-db"
        kb_dir.mkdir()

        input_data = {"tool_input": {"command": 'git commit -m "test commit"'}}

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch("klean.hooks.find_project_root", return_value=project):
                with pytest.raises(SystemExit) as exc_info:
                    post_bash()
                assert exc_info.value.code == 0

        timeline = kb_dir / "timeline.txt"
        if timeline.exists():
            assert "commit" in timeline.read_text()


class TestPostWebHook:
    """Tests for post_web() hook."""

    def test_exits_zero_on_empty_url(self):
        """Should exit 0 when no URL found."""
        from klean.hooks import post_web

        with patch("sys.stdin", StringIO("{}")):
            with pytest.raises(SystemExit) as exc_info:
                post_web()
            assert exc_info.value.code == 0

    def test_processes_documentation_url(self, tmp_path):
        """Should process documentation URLs."""
        from klean.hooks import post_web

        project = tmp_path / "project"
        project.mkdir()
        kb_dir = project / ".knowledge-db"
        kb_dir.mkdir()

        input_data = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://docs.example.com/api"},
        }

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch("klean.hooks.find_project_root", return_value=project):
                with pytest.raises(SystemExit) as exc_info:
                    post_web()
                assert exc_info.value.code == 0


# =============================================================================
# Entry Point Tests
# =============================================================================


class TestMainEntryPoint:
    """Tests for main() CLI entry point."""

    def test_exits_on_no_args(self, capsys):
        """Should exit with usage message when no args."""
        from klean.hooks import main

        with patch("sys.argv", ["hooks"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_exits_on_unknown_hook(self, capsys):
        """Should exit with error on unknown hook."""
        from klean.hooks import main

        with patch("sys.argv", ["hooks", "unknown_hook"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
