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


# =============================================================================
# TOON Format Tests
# =============================================================================


class TestFormatEntriesToon:
    """Tests for _format_entries_toon() function."""

    def test_formats_basic_entries(self):
        """Should format entries into TOON with minimal fields."""
        from klean.hooks import _format_entries_toon

        entries = [
            {"title": "Auth refactor", "type": "solution", "keywords": ["auth", "jwt"]},
            {"title": "SQL injection risk", "type": "warning", "priority": "high", "keywords": []},
        ]
        result = _format_entries_toon(entries)
        assert isinstance(result, str)
        assert len(result) > 0
        # TOON should contain the title data
        assert "Auth refactor" in result
        assert "SQL injection risk" in result

    def test_includes_priority_for_warnings(self):
        """Should include priority field only for warning-type entries."""
        from klean.hooks import _format_entries_toon

        entries = [
            {"title": "A warning", "type": "warning", "priority": "critical", "keywords": []},
            {"title": "A finding", "type": "finding", "keywords": ["test"]},
        ]
        result = _format_entries_toon(entries)
        assert "critical" in result

    def test_truncates_long_titles(self):
        """Should truncate titles to 80 chars."""
        from klean.hooks import _format_entries_toon

        long_title = "x" * 120
        entries = [{"title": long_title, "type": "finding", "keywords": []}]
        result = _format_entries_toon(entries)
        # The full 120-char title should NOT appear
        assert long_title not in result

    def test_limits_keywords_to_five(self):
        """Should include at most 5 keywords."""
        from klean.hooks import _format_entries_toon

        entries = [
            {
                "title": "Test",
                "type": "finding",
                "keywords": ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "theta"],
            }
        ]
        result = _format_entries_toon(entries)
        # Only first 5 keywords should appear
        assert "epsilon" in result
        assert "zeta" not in result
        assert "theta" not in result

    def test_handles_empty_entries(self):
        """Should handle empty entry list."""
        from klean.hooks import _format_entries_toon

        result = _format_entries_toon([])
        assert isinstance(result, str)


# =============================================================================
# Session Summary Tests
# =============================================================================


class TestExtractUserMessages:
    """Tests for _extract_user_messages() function."""

    def test_extracts_user_messages_from_jsonl(self, tmp_path):
        """Should extract user messages from transcript JSONL."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "file-history-snapshot", "snapshot": {}}),
            json.dumps({"type": "user", "message": {"content": "Fix the auth bug in login"}}),
            json.dumps({"type": "assistant", "message": {"content": "I'll fix that."}}),
            json.dumps({"type": "user", "message": {"content": "Now run the tests please"}}),
        ]
        transcript.write_text("\n".join(lines))

        result = _extract_user_messages(str(transcript))
        assert "Fix the auth bug" in result
        assert "run the tests" in result
        assert "I'll fix" not in result

    def test_skips_command_messages(self, tmp_path):
        """Should skip CLI command messages."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {
                "content": "<command-name>/clear</command-name>"
            }}),
            json.dumps({"type": "user", "message": {
                "content": "<local-command-caveat>some caveat</local-command-caveat>"
            }}),
            json.dumps({"type": "user", "message": {
                "content": "Actual user question about the code"
            }}),
        ]
        transcript.write_text("\n".join(lines))

        result = _extract_user_messages(str(transcript))
        assert "clear" not in result
        assert "caveat" not in result
        assert "Actual user question" in result

    def test_limits_message_count(self, tmp_path):
        """Should return only the last N messages."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": f"Message number {i} here"}})
            for i in range(20)
        ]
        transcript.write_text("\n".join(lines))

        result = _extract_user_messages(str(transcript), limit=3)
        assert "Message number 17" in result
        assert "Message number 18" in result
        assert "Message number 19" in result
        assert "Message number 0" not in result

    def test_returns_empty_for_missing_file(self):
        """Should return empty string for non-existent file."""
        from klean.hooks import _extract_user_messages

        result = _extract_user_messages("/nonexistent/path.jsonl")
        assert result == ""

    def test_skips_short_messages(self, tmp_path):
        """Should skip messages shorter than 10 chars."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": "yes"}}),
            json.dumps({"type": "user", "message": {"content": "ok"}}),
            json.dumps({"type": "user", "message": {
                "content": "Please fix the authentication bug"
            }}),
        ]
        transcript.write_text("\n".join(lines))

        result = _extract_user_messages(str(transcript))
        assert "yes" not in result
        assert "authentication bug" in result


class TestCallClaudeHaiku:
    """Tests for _call_claude_haiku() function."""

    def test_returns_output_on_success(self):
        """Should return Haiku's response on success."""
        from klean.hooks import _call_claude_haiku

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "## 14:00 - 15:30 | main\n- Fixed auth bug"

        with patch("subprocess.run", return_value=mock_result):
            result = _call_claude_haiku("test prompt")
            assert "Fixed auth bug" in result

    def test_returns_empty_on_failure(self):
        """Should return empty string on non-zero exit."""
        from klean.hooks import _call_claude_haiku

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = _call_claude_haiku("test prompt")
            assert result == ""

    def test_returns_empty_when_claude_not_found(self):
        """Should return empty string when claude CLI not installed."""
        from klean.hooks import _call_claude_haiku

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _call_claude_haiku("test prompt")
            assert result == ""

    def test_returns_empty_on_timeout(self):
        """Should return empty string on timeout."""
        import subprocess

        from klean.hooks import _call_claude_haiku

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 30)):
            result = _call_claude_haiku("test prompt")
            assert result == ""


class TestPersistSessionLog:
    """Tests for _persist_session_log() function."""

    def test_returns_no_activity_when_empty(self, tmp_path):
        """Should return 'No activity' when no transcript and no git log."""
        from klean.hooks import _persist_session_log

        mock_result = MagicMock()
        mock_result.stdout = ""

        with (
            patch("subprocess.run", return_value=mock_result),
            patch("klean.hooks._get_current_branch", return_value="main"),
            patch("klean.hooks._get_today_kb_entries", return_value=""),
        ):
            result = _persist_session_log(tmp_path, "")
            assert "No activity" in result

    def test_creates_new_session_log_file(self, tmp_path):
        """Should create a new session log file when none exists."""
        from klean.hooks import _persist_session_log

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        mock_git = MagicMock()
        mock_git.stdout = "abc1234 feat: add auth"

        with (
            patch("subprocess.run", return_value=mock_git),
            patch("klean.hooks._get_current_branch", return_value="main"),
            patch("klean.hooks._get_today_kb_entries", return_value=""),
            patch("klean.hooks._call_claude_haiku", return_value="## 14:00 - 15:00 | main\n- Test"),
            patch("klean.hooks._create_session_kb_entry") as mock_kb,
        ):
            result = _persist_session_log(tmp_path, "")
            assert "Session log updated" in result

            # Check file was created
            log_files = list(memory_dir.glob("session-log-*.md"))
            assert len(log_files) == 1
            content = log_files[0].read_text()
            assert "# Session Log:" in content
            assert "14:00 - 15:00" in content

            # Check KB entry creation was called
            mock_kb.assert_called_once()

    def test_appends_to_existing_log(self, tmp_path):
        """Should append to existing session log file."""
        from klean.hooks import _persist_session_log

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = memory_dir / f"session-log-{today}.md"
        log_file.write_text("# Session Log: " + today + "\n\n## 10:00 - 11:00 | main\n- Earlier")

        mock_git = MagicMock()
        mock_git.stdout = "def5678 fix: resolve bug"

        with (
            patch("subprocess.run", return_value=mock_git),
            patch("klean.hooks._get_current_branch", return_value="main"),
            patch("klean.hooks._get_today_kb_entries", return_value=""),
            patch(
                "klean.hooks._call_claude_haiku",
                return_value="## 14:00 - 15:00 | main\n- Later work",
            ),
            patch("klean.hooks._create_session_kb_entry"),
        ):
            result = _persist_session_log(tmp_path, "")
            assert "Session log updated" in result

            content = log_file.read_text()
            assert "10:00 - 11:00" in content  # Original preserved
            assert "14:00 - 15:00" in content  # New appended

    def test_returns_haiku_unavailable(self, tmp_path):
        """Should return message when Haiku is not available."""
        from klean.hooks import _persist_session_log

        mock_git = MagicMock()
        mock_git.stdout = "abc1234 feat: test"

        with (
            patch("subprocess.run", return_value=mock_git),
            patch("klean.hooks._get_current_branch", return_value="main"),
            patch("klean.hooks._get_today_kb_entries", return_value=""),
            patch("klean.hooks._call_claude_haiku", return_value=""),
        ):
            result = _persist_session_log(tmp_path, "")
            assert "Haiku not available" in result

    def test_includes_kb_entries_in_prompt(self, tmp_path):
        """Should include KB entries in the Haiku prompt when available."""
        from klean.hooks import _persist_session_log

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        mock_git = MagicMock()
        mock_git.stdout = "abc1234 feat: test"

        kb_entries = "- [finding] Auth uses weak hashing\n- [warning] SQL injection risk"

        with (
            patch("subprocess.run", return_value=mock_git),
            patch("klean.hooks._get_current_branch", return_value="main"),
            patch("klean.hooks._get_today_kb_entries", return_value=kb_entries),
            patch("klean.hooks._call_claude_haiku", return_value="## 14:00 | main\n- Work") as mock_haiku,
            patch("klean.hooks._create_session_kb_entry"),
        ):
            _persist_session_log(tmp_path, "")
            # Verify KB entries were included in prompt
            prompt_arg = mock_haiku.call_args[0][0]
            assert "Knowledge captured this session" in prompt_arg
            assert "Auth uses weak hashing" in prompt_arg



class TestGetTodayKbEntries:
    """Tests for _get_today_kb_entries() function."""

    def test_returns_empty_when_server_unavailable(self, tmp_path):
        """Should return empty string when KB server is down."""
        from klean.hooks import _get_today_kb_entries

        with patch("klean.hooks._kb_send", return_value=None):
            result = _get_today_kb_entries(tmp_path)
            assert result == ""

    def test_filters_useful_types(self, tmp_path):
        """Should only include findings, warnings, solutions, patterns, lessons."""
        from klean.hooks import _get_today_kb_entries

        entries = [
            {"type": "finding", "title": "Auth weakness"},
            {"type": "commit", "title": "feat: add auth"},
            {"type": "warning", "title": "SQL injection risk"},
            {"type": "session", "title": "Session: 2026-02-08"},
            {"type": "solution", "title": "Use parameterized queries"},
        ]
        resp = {"status": "ok", "entries": entries}

        with patch("klean.hooks._kb_send", return_value=resp):
            result = _get_today_kb_entries(tmp_path)
            assert "[finding] Auth weakness" in result
            assert "[warning] SQL injection risk" in result
            assert "[solution] Use parameterized queries" in result
            assert "commit" not in result
            assert "session" not in result.lower().split("\n")[0]  # No session type

    def test_limits_to_15_entries(self, tmp_path):
        """Should cap output at 15 entries."""
        from klean.hooks import _get_today_kb_entries

        entries = [{"type": "finding", "title": f"Finding {i}"} for i in range(20)]
        resp = {"status": "ok", "entries": entries}

        with patch("klean.hooks._kb_send", return_value=resp):
            result = _get_today_kb_entries(tmp_path)
            lines = [ln for ln in result.split("\n") if ln.strip()]
            assert len(lines) == 15


class TestCreateSessionKbEntry:
    """Tests for _create_session_kb_entry() function."""

    def test_creates_entry(self, tmp_path):
        """Should create a KB session entry with correct fields and related_to path."""
        from klean.hooks import _create_session_kb_entry

        # First call: search returns no existing entry
        # Second call: add the entry
        search_resp = {"status": "ok", "results": []}
        add_resp = {"status": "ok"}

        with patch("klean.hooks._kb_send", side_effect=[search_resp, add_resp]) as mock_send:
            _create_session_kb_entry(tmp_path, "main", "## 14:00 | main\n- Did X\n- Did Y\n- Commits: abc123")
            assert mock_send.call_count == 2
            add_call = mock_send.call_args_list[1]
            entry = add_call[0][1]["entry"]
            assert entry["type"] == "session"
            assert "main" in entry["title"]
            assert "Did X" in entry["insight"]
            # Verify graph link to full session log
            assert len(entry["related_to"]) == 1
            assert "session-log-" in entry["related_to"][0]
            assert str(tmp_path) in entry["related_to"][0]

    def test_skips_when_already_exists(self, tmp_path):
        """Should skip creation if session entry for today exists."""
        from klean.hooks import _create_session_kb_entry

        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        source = f"session-log:{today}"

        search_resp = {"status": "ok", "results": [{"source": source, "title": "Existing"}]}

        with patch("klean.hooks._kb_send", return_value=search_resp) as mock_send:
            _create_session_kb_entry(tmp_path, "main", "## 14:00 | main\n- Work")
            # Should only call search, not add
            assert mock_send.call_count == 1

    def test_handles_server_unavailable(self, tmp_path):
        """Should not crash when KB server is down."""
        from klean.hooks import _create_session_kb_entry

        with patch("klean.hooks._kb_send", return_value=None):
            # Should not raise
            _create_session_kb_entry(tmp_path, "main", "## 14:00 | main\n- Work")

class TestReadLatestSessionLog:
    """Tests for _read_latest_session_log() function."""

    def test_returns_empty_when_no_serena_dir(self, tmp_path):
        """Should return empty when .serena/memories/ doesn't exist."""
        from klean.hooks import _read_latest_session_log

        result = _read_latest_session_log(tmp_path)
        assert result == ""

    def test_returns_empty_when_no_logs(self, tmp_path):
        """Should return empty when no session-log files exist."""
        from klean.hooks import _read_latest_session_log

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        result = _read_latest_session_log(tmp_path)
        assert result == ""

    def test_returns_most_recent_log(self, tmp_path):
        """Should return the most recent session log by date."""
        from klean.hooks import _read_latest_session_log

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        (memory_dir / "session-log-2026-02-06.md").write_text("# Old log")
        (memory_dir / "session-log-2026-02-07.md").write_text("# Recent log")

        result = _read_latest_session_log(tmp_path)
        assert "Recent log" in result
        assert "Old log" not in result


class TestPreCompact:
    """Tests for pre_compact() hook function."""

    def test_exits_on_manual_trigger(self):
        """Should exit immediately on manual compact trigger."""
        from klean.hooks import pre_compact

        with (
            patch("klean.hooks._read_input", return_value={"trigger": "manual"}),
            pytest.raises(SystemExit) as exc_info,
        ):
            pre_compact()
        assert exc_info.value.code == 0

    def test_exits_when_no_project_root(self):
        """Should exit when no project root found."""
        from klean.hooks import pre_compact

        with (
            patch("klean.hooks._read_input", return_value={
                "trigger": "auto", "transcript_path": "/tmp/test.jsonl"
            }),
            patch("klean.hooks.find_project_root", return_value=None),
            pytest.raises(SystemExit) as exc_info,
        ):
            pre_compact()
        assert exc_info.value.code == 0

    def test_calls_persist_on_auto(self, tmp_path):
        """Should call _persist_session_log on auto trigger."""
        from klean.hooks import pre_compact

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        with (
            patch("klean.hooks._read_input", return_value={
                "trigger": "auto", "transcript_path": "/tmp/test.jsonl"
            }),
            patch("klean.hooks.find_project_root", return_value=tmp_path),
            patch("klean.hooks._persist_session_log", return_value="ok") as mock_persist,
            pytest.raises(SystemExit),
        ):
            pre_compact()
        mock_persist.assert_called_once_with(tmp_path, "/tmp/test.jsonl")


# =============================================================================
# Get KB Context Tests
# =============================================================================


class TestGetKbContext:
    """Tests for _get_kb_context() function."""

    def test_returns_serena_prompt_when_server_down(self, tmp_path):
        """Should return Serena prompt when KB server not running."""
        from klean.hooks import _get_kb_context

        with patch("klean.hooks._is_kb_server_running", return_value=False):
            result = _get_kb_context(tmp_path)
            assert "mcp__serena__read_memory" in result

    def test_returns_serena_prompt_when_no_entries(self, tmp_path):
        """Should return Serena prompt when no entries."""
        from klean.hooks import _get_kb_context

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": []}),
        ):
            result = _get_kb_context(tmp_path)
            assert "mcp__serena__read_memory" in result

    def test_includes_session_log(self, tmp_path):
        """Should show [SESSION] section when session log file exists."""
        from klean.hooks import _get_kb_context

        # Create session log file
        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)
        log_file = memory_dir / "session-log-2026-02-07.md"
        log_file.write_text(
            "# Session Log: 2026-02-07\n\n"
            "## 14:00 - 15:30 | main\n"
            "- Fixed JWT race condition\n"
            "- Status: in-progress\n"
            "- Left: integration tests"
        )

        entries = [
            {
                "id": "f1",
                "type": "finding",
                "title": "Found perf issue",
                "keywords": ["perf"],
            },
        ]

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _get_kb_context(tmp_path)
            assert "[SESSION]" in result
            assert "14:00 - 15:30" in result
            assert "JWT race condition" in result

    def test_groups_warnings_compact(self, tmp_path):
        """Should show compact warning count with top titles."""
        from klean.hooks import _get_kb_context

        entries = [
            {"id": f"w{i}", "type": "warning", "priority": "high", "title": f"Warning {i}",
             "keywords": []}
            for i in range(4)
        ]
        entries.append(
            {"id": "f1", "type": "finding", "title": "Test", "keywords": ["test"]}
        )

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _get_kb_context(tmp_path)
            assert "[!] WARNINGS (4)" in result
            assert "+2 more" in result

    def test_excludes_journals_from_recent(self, tmp_path):
        """Should not include journal or session entries in RECENT section."""
        from klean.hooks import _get_kb_context

        entries = [
            {"id": "j1", "type": "journal", "title": "Session started", "keywords": []},
            {"id": "s1", "type": "session", "title": "Session summary: 2026-02-07",
             "insight": "test", "keywords": []},
            {"id": "f1", "type": "finding", "title": "Real finding", "keywords": ["test"]},
        ]

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _get_kb_context(tmp_path)
            assert "[KB] RECENT" in result
            assert "Real finding" in result


# =============================================================================
# Progressive Disclosure Tests
# =============================================================================


class TestHandleFindKnowledgeCompact:
    """Tests for _handle_find_knowledge() compact output."""

    def test_returns_compact_format_with_ids(self, tmp_path):
        """Should return compact index with entry IDs, no insight text."""
        from klean.hooks import _handle_find_knowledge

        project = tmp_path / "project"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        search_results = [
            {
                "id": "abc12345-6789-0000-0000-000000000000",
                "title": "Auth refactor",
                "type": "solution",
                "date": "2026-02-07",
                "score": 0.85,
                "insight": "Long insight text that should not appear in compact output",
            },
        ]

        with (
            patch("klean.hooks.find_project_root", return_value=project),
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"results": search_results}),
            patch("klean.hooks._update_usage"),
        ):
            result = _handle_find_knowledge("auth")

            assert "[id:abc12345]" in result
            assert "Auth refactor" in result
            assert "0.85" in result
            # Insight text should NOT be in output
            assert "Long insight text" not in result
            assert "FindKnowledgeDetail" in result

    def test_no_branch_in_compact_output(self, tmp_path):
        """Should not include branch in compact output."""
        from klean.hooks import _handle_find_knowledge

        project = tmp_path / "project"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        search_results = [
            {
                "id": "abc12345-0000-0000-0000-000000000000",
                "title": "Test",
                "type": "finding",
                "date": "2026-02-07",
                "branch": "feature/auth",
                "score": 0.90,
            },
        ]

        with (
            patch("klean.hooks.find_project_root", return_value=project),
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"results": search_results}),
            patch("klean.hooks._update_usage"),
        ):
            result = _handle_find_knowledge("test")
            assert "feature/auth" not in result


class TestHandleFindKnowledgeDetail:
    """Tests for _handle_find_knowledge_detail() function."""

    def test_returns_no_project_when_not_found(self):
        """Should return error when no project found."""
        from klean.hooks import _handle_find_knowledge_detail

        with patch("klean.hooks.find_project_root", return_value=None):
            result = _handle_find_knowledge_detail("abc123")
            assert "No project found" in result

    def test_returns_error_when_server_down(self, tmp_path):
        """Should return error when KB server not running."""
        from klean.hooks import _handle_find_knowledge_detail

        with (
            patch("klean.hooks.find_project_root", return_value=tmp_path),
            patch("klean.hooks._is_kb_server_running", return_value=False),
        ):
            result = _handle_find_knowledge_detail("abc123")
            assert "not running" in result

    def test_fetches_full_entry_by_uuid(self, tmp_path):
        """Should fetch and format full entry by UUID."""
        from klean.hooks import _handle_find_knowledge_detail

        full_id = "abc12345-6789-0123-4567-890123456789"
        entry = {
            "id": full_id,
            "title": "Auth refactor completed",
            "type": "solution",
            "priority": "high",
            "date": "2026-02-07",
            "branch": "main",
            "insight": "Refactored auth to use JWT tokens for better scalability.",
            "keywords": ["auth", "jwt", "refactor"],
            "source": "commit:abc123",
        }

        with (
            patch("klean.hooks.find_project_root", return_value=tmp_path),
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"status": "ok", "entry": entry}),
        ):
            result = _handle_find_knowledge_detail(full_id)

            assert "Auth refactor completed" in result
            assert "solution" in result
            assert "high" in result
            assert "JWT tokens" in result
            assert "auth, jwt, refactor" in result
            assert "commit:abc123" in result
            assert full_id in result

    def test_resolves_short_id_prefix(self, tmp_path):
        """Should resolve short ID prefix by scanning recent entries."""
        from klean.hooks import _handle_find_knowledge_detail

        entries = [
            {
                "id": "abc12345-full-uuid-here-000000000000",
                "title": "Matched entry",
                "type": "finding",
                "priority": "medium",
                "date": "2026-02-07",
                "insight": "This is the matched entry",
                "keywords": ["test"],
            },
            {
                "id": "def67890-full-uuid-here-000000000000",
                "title": "Other entry",
                "type": "solution",
            },
        ]

        with (
            patch("klean.hooks.find_project_root", return_value=tmp_path),
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _handle_find_knowledge_detail("abc12345")

            assert "Matched entry" in result
            assert "This is the matched entry" in result

    def test_returns_not_found_for_bad_prefix(self, tmp_path):
        """Should return error when no entry matches the prefix."""
        from klean.hooks import _handle_find_knowledge_detail

        with (
            patch("klean.hooks.find_project_root", return_value=tmp_path),
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": []}),
        ):
            result = _handle_find_knowledge_detail("zzz99999")
            assert "No entry found" in result


class TestPromptHandlerFindKnowledgeDetail:
    """Tests for FindKnowledgeDetail keyword in prompt_handler()."""

    def test_dispatches_findknowledgedetail(self, tmp_path, capsys):
        """Should dispatch FindKnowledgeDetail keyword to handler."""
        from klean.hooks import prompt_handler

        input_data = {"prompt": "FindKnowledgeDetail abc12345"}

        with (
            patch("sys.stdin", StringIO(json.dumps(input_data))),
            patch("klean.hooks.find_project_root", return_value=tmp_path),
            patch("klean.hooks._is_kb_server_running", return_value=False),
        ):
            with pytest.raises(SystemExit) as exc_info:
                prompt_handler()
            assert exc_info.value.code == 0

    def test_exits_zero_on_empty_id(self):
        """Should exit 0 when FindKnowledgeDetail has no ID."""
        from klean.hooks import prompt_handler

        input_data = {"prompt": "FindKnowledgeDetail "}

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with pytest.raises(SystemExit) as exc_info:
                prompt_handler()
            assert exc_info.value.code == 0
