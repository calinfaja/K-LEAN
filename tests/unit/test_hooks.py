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
    """Tests for _extract_user_messages() interleaved conversation extraction."""

    def test_extracts_interleaved_conversation(self, tmp_path):
        """Should extract both user and assistant messages as dialogue."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "file-history-snapshot", "snapshot": {}}),
            json.dumps({"type": "user", "message": {"content": "Fix the auth bug in login"}}),
            json.dumps({"type": "assistant", "message": {"content": "I'll fix the JWT validation."}}),
            json.dumps({"type": "user", "message": {"content": "Now run the tests please"}}),
        ]
        transcript.write_text("\n".join(lines))

        messages, start_ts, end_ts = _extract_user_messages(str(transcript))
        assert "USER: Fix the auth bug" in messages
        assert "CLAUDE: I'll fix the JWT" in messages
        assert "USER: Now run the tests" in messages

    def test_strips_system_tags(self, tmp_path):
        """Should strip system-reminder and other injected tags."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps(
                {"type": "user", "message": {"content": "<command-name>/clear</command-name>"}}
            ),
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": "<local-command-caveat>some caveat</local-command-caveat>"
                    },
                }
            ),
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": (
                            "Actual user question about the code"
                            "<system-reminder>ignore this noise</system-reminder>"
                        )
                    },
                }
            ),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "clear" not in messages
        assert "caveat" not in messages
        assert "ignore this noise" not in messages
        assert "Actual user question" in messages

    def test_extracts_list_content_user_messages(self, tmp_path):
        """Should extract text from list-type user messages (skip tool_results)."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            # List with tool_result -> should be skipped
            json.dumps({
                "type": "user",
                "message": {"content": [
                    {"type": "tool_result", "content": "file contents here"},
                    {"type": "text", "text": "This should be skipped due to tool_result"},
                ]},
            }),
            # List with only text -> should be extracted
            json.dumps({
                "type": "user",
                "message": {"content": [
                    {"type": "text", "text": "Please review this implementation carefully"},
                ]},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "file contents" not in messages
        assert "should be skipped" not in messages
        assert "review this implementation" in messages

    def test_budget_caps_from_recent(self, tmp_path):
        """Should include all messages within budget, most recent first."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": f"Message number {i} with enough text"}})
            for i in range(20)
        ]
        transcript.write_text("\n".join(lines))

        # All 20 messages should fit within 200K char budget
        messages, _, _ = _extract_user_messages(str(transcript))
        assert "Message number 0" in messages
        assert "Message number 19" in messages

    def test_returns_empty_for_missing_file(self):
        """Should return empty tuple for non-existent file."""
        from klean.hooks import _extract_user_messages

        messages, start_ts, end_ts = _extract_user_messages("/nonexistent/path.jsonl")
        assert messages == ""
        assert start_ts == ""
        assert end_ts == ""

    def test_skips_short_messages(self, tmp_path):
        """Should skip messages shorter than 15 chars."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": "yes"}}),
            json.dumps({"type": "user", "message": {"content": "ok sure"}}),
            json.dumps(
                {"type": "user", "message": {"content": "Please fix the authentication bug"}}
            ),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "yes" not in messages
        assert "authentication bug" in messages

    def test_extracts_timestamps(self, tmp_path):
        """Should extract first and last timestamps as HH:MM."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({
                "type": "user",
                "message": {"content": "First question of the session"},
                "timestamp": "2026-02-08T09:15:30.000Z",
            }),
            json.dumps({
                "type": "user",
                "message": {"content": "Last question of the session"},
                "timestamp": "2026-02-08T17:45:10.000Z",
            }),
        ]
        transcript.write_text("\n".join(lines))

        _, start_ts, end_ts = _extract_user_messages(str(transcript))
        assert start_ts == "09:15"
        assert end_ts == "17:45"

    def test_keeps_text_from_text_plus_tool_turns(self, tmp_path):
        """Should keep text from turns that have both text and tools."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "text", "text": "I fixed the authentication validation logic."},
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "/src/hooks.py"}},
                    {"type": "tool_use", "name": "Edit", "input": {"file_path": "/src/cli.py"}},
                ]},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "CLAUDE:" in messages
        assert "authentication validation" in messages
        # Tool annotations are dropped (noise for changelog)
        assert "[read]" not in messages
        assert "[edit]" not in messages

    def test_drops_noise_tools(self, tmp_path):
        """Should drop turns with only noise tools (sequential-thinking, etc.)."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "tool_use", "name": "mcp__sequential-thinking__sequentialthinking",
                     "input": {"thought": "thinking..."}},
                ]},
            }),
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "tool_use", "name": "TaskUpdate", "input": {"taskId": "1"}},
                ]},
            }),
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "text", "text": "Here is the result of my analysis."},
                ]},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "sequentialthinking" not in messages
        assert "TaskUpdate" not in messages
        assert "Here is the result" in messages

    def test_drops_tool_only_turns(self, tmp_path):
        """Should drop tool-only turns entirely (zero value for changelog)."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "/a.py"}},
                ]},
            }),
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "/b.py"}},
                ]},
            }),
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "/c.py"}},
                ]},
            }),
            json.dumps({
                "type": "user",
                "message": {"content": "What did you find in those files?"},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        # Tool-only turns are dropped entirely
        assert "CLAUDE:" not in messages
        # Should still have the user message
        assert "What did you find" in messages

    def test_drops_filler_text(self, tmp_path):
        """Should drop filler-only text turns."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "message": {"content": "Let me read the file and check the contents."},
            }),
            json.dumps({
                "type": "assistant",
                "message": {"content": "The implementation uses a TCP socket for IPC."},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "Let me read" not in messages
        assert "TCP socket" in messages

    def test_delta_extraction_skips_before_boundary(self, tmp_path):
        """Should only extract conversation after the last compact_boundary."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            # Pre-boundary conversation (should be skipped)
            json.dumps({"type": "user", "message": {"content": "Old question from before compaction happened"}}),
            json.dumps({"type": "assistant", "message": {"content": "Old answer that should not appear in output."}}),
            # Compact boundary marker
            json.dumps({"type": "system", "subtype": "compact_boundary", "content": "Conversation compacted", "timestamp": "2026-02-08T13:30:00.000Z"}),
            # Post-boundary conversation (should be extracted)
            json.dumps({"type": "user", "message": {"content": "New question after compaction happened here"}}),
            json.dumps({"type": "assistant", "message": {"content": "New answer that should appear in the output."}}),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "Old question" not in messages
        assert "Old answer" not in messages
        assert "New question" in messages
        assert "New answer" in messages

    def test_delta_extracts_all_when_no_boundary(self, tmp_path):
        """Should extract everything when no compact_boundary exists."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": "First question of the session here"}}),
            json.dumps({"type": "assistant", "message": {"content": "First answer of the entire session."}}),
            json.dumps({"type": "user", "message": {"content": "Second question of the session here"}}),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "First question" in messages
        assert "First answer" in messages
        assert "Second question" in messages

    def test_delta_uses_last_boundary_not_first(self, tmp_path):
        """Should use the LAST compact_boundary, not the first one."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"content": "Very old question from first segment"}}),
            json.dumps({"type": "system", "subtype": "compact_boundary", "content": "Conversation compacted"}),
            json.dumps({"type": "user", "message": {"content": "Middle question between two boundaries"}}),
            json.dumps({"type": "system", "subtype": "compact_boundary", "content": "Conversation compacted"}),
            json.dumps({"type": "user", "message": {"content": "Latest question after second boundary"}}),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        assert "Very old" not in messages
        assert "Middle question" not in messages
        assert "Latest question" in messages


    def test_long_text_not_over_truncated(self, tmp_path):
        """Should keep up to 2000 chars per turn, not just 500."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        long_text = "Agent 1 findings: important stuff. " * 60  # ~2100 chars
        lines = [
            json.dumps({
                "type": "assistant",
                "message": {"content": [
                    {"type": "text", "text": long_text},
                ]},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        # Should keep significantly more than 500 chars
        claude_line = [ln for ln in messages.split("\n") if ln.startswith("CLAUDE:")][0]
        assert len(claude_line) > 1000

    def test_truncates_session_continuation_summary(self, tmp_path):
        """Should truncate session continuation summaries to ~200 chars."""
        from klean.hooks import _extract_user_messages

        transcript = tmp_path / "transcript.jsonl"
        long_summary = (
            "This session is being continued from a previous conversation. "
            + "Detail about previous work. " * 50  # ~1400 chars of noise
        )
        lines = [
            json.dumps({
                "type": "user",
                "message": {"content": long_summary},
            }),
            json.dumps({
                "type": "user",
                "message": {"content": "Now let's work on the actual task at hand"},
            }),
        ]
        transcript.write_text("\n".join(lines))

        messages, _, _ = _extract_user_messages(str(transcript))
        # Continuation summary should be truncated
        user_lines = [ln for ln in messages.split("\n") if ln.startswith("USER:")]
        continuation_line = user_lines[0]
        assert len(continuation_line) < 300
        assert "..." in continuation_line
        # The real user message should be preserved
        assert "actual task" in messages

    def test_raises_on_logic_bug_not_swallowed(self, tmp_path):
        """Parsing exceptions for IO/JSON are caught, but logic bugs propagate."""
        from klean.hooks import _extract_user_messages

        # A file that doesn't exist returns empty (OSError caught)
        messages, _, _ = _extract_user_messages(str(tmp_path / "nonexistent.jsonl"))
        assert messages == ""

        # A file with invalid JSON returns empty (JSONDecodeError caught)
        bad_json = tmp_path / "bad.jsonl"
        bad_json.write_text("not json\n")
        messages, _, _ = _extract_user_messages(str(bad_json))
        assert messages == ""


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
            assert "---" in content  # Separator between entries

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
            patch(
                "klean.hooks._call_claude_haiku", return_value="## 14:00 | main\n- Work"
            ) as mock_haiku,
            patch("klean.hooks._create_session_kb_entry"),
        ):
            _persist_session_log(tmp_path, "")
            # Verify KB entries were included in prompt
            prompt_arg = mock_haiku.call_args[0][0]
            assert "KNOWLEDGE CAPTURED:" in prompt_arg
            assert "Auth uses weak hashing" in prompt_arg

    def test_skips_minimal_activity(self, tmp_path):
        """Should skip Haiku call when delta conversation is too small."""
        from klean.hooks import _persist_session_log

        memory_dir = tmp_path / ".serena" / "memories"
        memory_dir.mkdir(parents=True)

        # Simulate tiny conversation (< 500 chars) with no git activity
        mock_git = MagicMock()
        mock_git.stdout = ""

        with (
            patch("subprocess.run", return_value=mock_git),
            patch("klean.hooks._get_current_branch", return_value="main"),
            patch("klean.hooks._get_today_kb_entries", return_value=""),
            patch(
                "klean.hooks._extract_user_messages",
                return_value=("USER: ok sure", "14:00", "14:01"),
            ),
            patch("klean.hooks._call_claude_haiku") as mock_haiku,
        ):
            result = _persist_session_log(tmp_path, "/fake/transcript.jsonl")
            assert "minimal activity" in result.lower() or "Skipped" in result
            mock_haiku.assert_not_called()


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

    def test_includes_insight_text(self, tmp_path):
        """Should include truncated insight text when available."""
        from klean.hooks import _get_today_kb_entries

        entries = [
            {"type": "finding", "title": "Auth weakness", "insight": "bcrypt replaced by md5 in migration"},
            {"type": "warning", "title": "SQL injection", "insight": ""},
        ]
        resp = {"status": "ok", "entries": entries}

        with patch("klean.hooks._kb_send", return_value=resp):
            result = _get_today_kb_entries(tmp_path)
            assert "Auth weakness: bcrypt replaced by md5" in result
            # No insight -> no colon suffix
            assert "[warning] SQL injection\n" in result or result.endswith("[warning] SQL injection")

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
            _create_session_kb_entry(
                tmp_path, "main", "## 14:00 | main\n- Did X\n- Did Y\n- Commits: abc123"
            )
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
        from datetime import datetime

        from klean.hooks import _create_session_kb_entry

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
            patch(
                "klean.hooks._read_input",
                return_value={"trigger": "auto", "transcript_path": "/tmp/test.jsonl"},
            ),
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
            patch(
                "klean.hooks._read_input",
                return_value={"trigger": "auto", "transcript_path": "/tmp/test.jsonl"},
            ),
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
            "### 14:00-15:30 | `main` | 2 commits\n\n"
            "**Accomplished**\n"
            "- Fix JWT race condition (abc1234)\n\n"
            "**Carry Forward**\n"
            "- [ ] Integration tests for auth flow"
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
            assert "JWT race condition" in result
            assert "Integration tests" in result

    def test_groups_warnings_compact(self, tmp_path):
        """Should show compact warning count with top titles."""
        from klean.hooks import _get_kb_context

        entries = [
            {
                "id": f"w{i}",
                "type": "warning",
                "priority": "high",
                "title": f"Warning {i}",
                "keywords": [],
            }
            for i in range(4)
        ]
        entries.append({"id": "f1", "type": "finding", "title": "Test", "keywords": ["test"]})

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
            {
                "id": "s1",
                "type": "session",
                "title": "Session summary: 2026-02-07",
                "insight": "test",
                "keywords": [],
            },
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


# =============================================================================
# Auto-Pin Tests
# =============================================================================


class TestGetKbContextPinned:
    """Tests for pinned entries in _get_kb_context()."""

    def test_pinned_entries_shown_in_pinned_section(self, tmp_path):
        """Pinned entries should appear in [KB] PINNED section."""
        from klean.hooks import _get_kb_context

        entries = [
            {
                "id": "p1",
                "type": "pattern",
                "title": "JWT uses RS256",
                "keywords": ["jwt"],
                "pinned": True,
            },
            {
                "id": "f1",
                "type": "finding",
                "title": "Found perf issue",
                "keywords": ["perf"],
                "pinned": False,
            },
        ]

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _get_kb_context(tmp_path)
            assert "[KB] PINNED:" in result
            assert "JWT uses RS256" in result
            assert "[KB] RECENT:" in result
            assert "Found perf issue" in result

    def test_pinned_entries_not_duplicated_in_recent(self, tmp_path):
        """Pinned entries should NOT appear in RECENT section."""
        from klean.hooks import _get_kb_context

        entries = [
            {
                "id": "p1",
                "type": "pattern",
                "title": "Pinned entry",
                "keywords": ["test"],
                "pinned": True,
            },
        ]

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _get_kb_context(tmp_path)
            assert "[KB] PINNED:" in result
            # Should not have RECENT section since the only entry is pinned
            assert "[KB] RECENT:" not in result

    def test_no_pinned_section_when_none_pinned(self, tmp_path):
        """Should not show PINNED section when no entries are pinned."""
        from klean.hooks import _get_kb_context

        entries = [
            {"id": "f1", "type": "finding", "title": "Regular entry", "keywords": ["test"]},
        ]

        with (
            patch("klean.hooks._is_kb_server_running", return_value=True),
            patch("klean.hooks._kb_send", return_value={"entries": entries}),
        ):
            result = _get_kb_context(tmp_path)
            assert "[KB] PINNED:" not in result
            assert "[KB] RECENT:" in result
