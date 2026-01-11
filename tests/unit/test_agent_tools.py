"""Tests for klean.tools module - Agent tools.

Tests cover:
- grep_codebase tool
- read_file tool
- search_knowledge tool
- run_tests tool
- Tool decorator
"""

import asyncio
from unittest.mock import MagicMock, patch

# =============================================================================
# Tool Decorator Tests
# =============================================================================


class TestToolDecorator:
    """Tests for the @tool decorator."""

    def test_marks_function_as_tool(self):
        """Should mark function with _is_tool attribute."""
        from klean.tools import tool

        @tool("test_tool", "A test tool")
        def my_func():
            pass

        assert hasattr(my_func, "_is_tool")
        assert my_func._is_tool is True

    def test_sets_tool_name(self):
        """Should set _tool_name attribute."""
        from klean.tools import tool

        @tool("my_tool", "Description")
        def my_func():
            pass

        assert my_func._tool_name == "my_tool"

    def test_sets_tool_description(self):
        """Should set _tool_description attribute."""
        from klean.tools import tool

        @tool("name", "My tool description")
        def my_func():
            pass

        assert my_func._tool_description == "My tool description"

    def test_accepts_optional_schema(self):
        """Should accept optional schema dict."""
        from klean.tools import tool

        schema = {"type": "object", "properties": {"x": {"type": "string"}}}

        @tool("name", "desc", schema=schema)
        def my_func():
            pass

        assert my_func._tool_schema == schema


# =============================================================================
# Grep Tool Tests
# =============================================================================


class TestGrepCodebase:
    """Tests for grep_codebase() tool."""

    def test_returns_structured_result(self):
        """Should return dict with matches, count, files_with_matches."""
        from klean.tools.grep_tool import grep_codebase

        result = asyncio.run(grep_codebase("test_pattern"))

        assert isinstance(result, dict)
        assert "matches" in result
        assert "count" in result

    def test_accepts_glob_pattern(self):
        """Should accept glob_pattern parameter."""
        from klean.tools.grep_tool import grep_codebase

        # Should not raise
        result = asyncio.run(grep_codebase("pattern", glob_pattern="*.py"))

        assert isinstance(result, dict)

    def test_accepts_file_type(self):
        """Should accept file_type parameter."""
        from klean.tools.grep_tool import grep_codebase

        result = asyncio.run(grep_codebase("pattern", file_type="py"))

        assert isinstance(result, dict)

    def test_handles_exceptions(self):
        """Should catch exceptions and return error dict."""
        from klean.tools.grep_tool import grep_codebase

        # Passing invalid path type should be handled
        result = asyncio.run(grep_codebase("pattern", path="/nonexistent/path"))

        assert isinstance(result, dict)


# =============================================================================
# Read File Tool Tests
# =============================================================================


class TestReadFile:
    """Tests for read_file() tool."""

    def test_reads_existing_file(self, tmp_path):
        """Should read and return file contents."""
        from klean.tools.read_tool import read_file

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!\nLine 2")

        result = asyncio.run(read_file(str(test_file)))

        assert result["content"] == "Hello, World!\nLine 2"
        assert result["lines"] == 2
        assert "path" in result

    def test_returns_error_for_missing_file(self):
        """Should return error dict for nonexistent file."""
        from klean.tools.read_tool import read_file

        result = asyncio.run(read_file("/nonexistent/file.txt"))

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_returns_error_for_directory(self, tmp_path):
        """Should return error when path is a directory."""
        from klean.tools.read_tool import read_file

        result = asyncio.run(read_file(str(tmp_path)))

        assert "error" in result
        assert "not a file" in result["error"].lower()

    def test_respects_line_limit(self, tmp_path):
        """Should limit lines when requested."""
        from klean.tools.read_tool import read_file

        # Create file with many lines
        test_file = tmp_path / "many_lines.txt"
        test_file.write_text("\n".join(f"Line {i}" for i in range(100)))

        result = asyncio.run(read_file(str(test_file), lines=10))

        assert result["lines"] == 10
        assert result["truncated"] is True

    def test_respects_offset(self, tmp_path):
        """Should start from offset when specified."""
        from klean.tools.read_tool import read_file

        test_file = tmp_path / "offset.txt"
        test_file.write_text("Line 0\nLine 1\nLine 2\nLine 3\nLine 4")

        result = asyncio.run(read_file(str(test_file), offset=2, lines=2))

        assert "Line 2" in result["content"]
        assert "Line 0" not in result["content"]


# =============================================================================
# Search Knowledge Tool Tests
# =============================================================================


class TestSearchKnowledge:
    """Tests for search_knowledge() tool."""

    def test_returns_structured_result(self):
        """Should return dict with success, query, results."""
        from klean.tools.search_knowledge_tool import search_knowledge

        # Mock kb_utils to avoid needing actual server
        with patch.dict("sys.modules", {"kb_utils": MagicMock()}):
            result = asyncio.run(search_knowledge("test query"))

            assert isinstance(result, dict)
            assert "query" in result

    def test_handles_server_not_running(self):
        """Should return helpful error when server not running."""
        from klean.tools.search_knowledge_tool import search_knowledge

        # Call without mocking - it will fail naturally if server not running
        result = asyncio.run(search_knowledge("test"))

        assert isinstance(result, dict)
        # Should indicate failure when server not running
        assert "success" in result or "error" in result

    def test_accepts_limit_parameter(self):
        """Should accept limit parameter."""
        from klean.tools.search_knowledge_tool import search_knowledge

        # Should not raise
        result = asyncio.run(search_knowledge("query", limit=10))

        assert isinstance(result, dict)

    def test_accepts_min_score_parameter(self):
        """Should accept min_score parameter."""
        from klean.tools.search_knowledge_tool import search_knowledge

        result = asyncio.run(search_knowledge("query", min_score=0.5))

        assert isinstance(result, dict)


# =============================================================================
# Run Tests Tool Tests
# =============================================================================


class TestRunTests:
    """Tests for run_tests() tool."""

    def test_returns_structured_result(self):
        """Should return dict with passed, failed, skipped counts."""
        from klean.tools.testing_tool import run_tests

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="test_a PASSED\ntest_b PASSED\n", stderr=""
            )

            result = asyncio.run(run_tests())

            assert "passed" in result
            assert "failed" in result
            assert "skipped" in result
            assert "total" in result

    def test_parses_pytest_output(self):
        """Should parse pytest output for counts."""
        from klean.tools.testing_tool import run_tests

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="test_a PASSED\ntest_b PASSED\ntest_c FAILED\n", stderr=""
            )

            result = asyncio.run(run_tests())

            assert result["passed"] == 2
            assert result["failed"] == 1

    def test_handles_pytest_not_found(self):
        """Should return error when pytest not installed."""
        from klean.tools.testing_tool import run_tests

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = asyncio.run(run_tests())

            assert result["success"] is False
            assert "pytest not found" in result["error"]

    def test_handles_timeout(self):
        """Should handle test timeout."""
        import subprocess

        from klean.tools.testing_tool import run_tests

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 60)):
            result = asyncio.run(run_tests())

            assert result["success"] is False
            assert "timeout" in result["error"].lower()

    def test_accepts_pattern_filter(self):
        """Should accept pattern parameter."""
        from klean.tools.testing_tool import run_tests

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            asyncio.run(run_tests(pattern="test_security"))

            # Check that -k flag was used
            call_args = mock_run.call_args[0][0]
            assert "-k" in call_args
            assert "test_security" in call_args


# =============================================================================
# Tool Exports Tests
# =============================================================================


class TestToolExports:
    """Tests for klean.tools module exports."""

    def test_exports_all_tools(self):
        """Should export all tool functions."""
        from klean.tools import grep_codebase, read_file, run_tests, search_knowledge

        assert callable(grep_codebase)
        assert callable(read_file)
        assert callable(search_knowledge)
        assert callable(run_tests)

    def test_exports_tool_decorator(self):
        """Should export tool decorator."""
        from klean.tools import tool

        assert callable(tool)
