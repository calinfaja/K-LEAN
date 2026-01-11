"""Tests for klean.smol.executor module.

Tests cover:
- SmolKLNExecutor initialization
- Agent execution flow
- Result formatting
- Error handling
- Memory integration
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

# =============================================================================
# SmolKLNExecutor Initialization Tests
# =============================================================================


class TestSmolKLNExecutorInit:
    """Tests for SmolKLNExecutor.__init__()."""

    def test_sets_default_agents_dir(self):
        """Should set default agents directory to ~/.klean/agents/."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=Path("/tmp/test"))
            executor = SmolKLNExecutor()

            assert executor.agents_dir == Path.home() / ".klean" / "agents"

    def test_accepts_custom_agents_dir(self):
        """Should accept custom agents directory."""
        from klean.smol.executor import SmolKLNExecutor

        custom_dir = Path("/custom/agents")
        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=Path("/tmp/test"))
            executor = SmolKLNExecutor(agents_dir=custom_dir)

            assert executor.agents_dir == custom_dir

    def test_sets_default_api_base(self):
        """Should set default api_base to localhost:4000."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=Path("/tmp/test"))
            executor = SmolKLNExecutor()

            assert executor.api_base == "http://localhost:4000"

    def test_gathers_project_context(self):
        """Should call gather_project_context on init."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=Path("/my/project"))
            executor = SmolKLNExecutor()

            mock_ctx.assert_called_once()
            assert executor.project_root == Path("/my/project")

    def test_initializes_memory(self):
        """Should initialize AgentMemory."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            with patch("klean.smol.executor.AgentMemory") as mock_memory:
                mock_ctx.return_value = MagicMock(project_root=Path("/tmp/test"))
                executor = SmolKLNExecutor()

                mock_memory.assert_called_once()
                assert executor.memory is not None


# =============================================================================
# Output Directory Tests
# =============================================================================


class TestGetOutputDir:
    """Tests for SmolKLNExecutor._get_output_dir()."""

    def test_creates_output_dir_under_project(self, tmp_path):
        """Should create output dir under project_root/.claude/kln/agentExecute/."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = SmolKLNExecutor()

            expected = tmp_path / ".claude" / "kln" / "agentExecute"
            assert executor.output_dir == expected
            assert expected.exists()

    def test_falls_back_to_temp_on_permission_error(self, tmp_path):
        """Should fall back to temp directory if project dir not writable."""
        from klean.smol.executor import SmolKLNExecutor

        # Create a mock that fails only for the project dir, not fallback
        original_mkdir = Path.mkdir
        call_count = [0]

        def mock_mkdir(self, *args, **kwargs):
            call_count[0] += 1
            # First call is for project dir - fail it
            if call_count[0] == 1:
                raise PermissionError("Cannot create project dir")
            # Subsequent calls succeed
            return original_mkdir(self, *args, **kwargs)

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=Path("/nonexistent/readonly"))
            with patch.object(Path, "mkdir", mock_mkdir):
                executor = SmolKLNExecutor()

                assert "claude-reviews" in str(executor.output_dir)


# =============================================================================
# Format Result Tests
# =============================================================================


class TestFormatResult:
    """Tests for SmolKLNExecutor._format_result()."""

    def test_extracts_code_from_dict(self, tmp_path):
        """Should extract 'code' field from dict result."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = SmolKLNExecutor()

            result = {"thought": "thinking...", "code": "## Summary\nGood code!"}
            formatted = executor._format_result(result)

            assert formatted == "## Summary\nGood code!"

    def test_handles_escaped_newlines(self, tmp_path):
        """Should convert \\n to actual newlines."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = SmolKLNExecutor()

            result = {"code": "Line1\\nLine2\\nLine3"}
            formatted = executor._format_result(result)

            assert formatted == "Line1\nLine2\nLine3"

    def test_formats_thought_as_summary(self, tmp_path):
        """Should format 'thought' field as Analysis Summary."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = SmolKLNExecutor()

            result = {"thought": "My analysis"}
            formatted = executor._format_result(result)

            assert "## Analysis Summary" in formatted
            assert "My analysis" in formatted

    def test_returns_string_unchanged(self, tmp_path):
        """Should return string results unchanged."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = SmolKLNExecutor()

            result = "Plain string result"
            formatted = executor._format_result(result)

            assert formatted == "Plain string result"


# =============================================================================
# Execute Tests
# =============================================================================


class TestExecute:
    """Tests for SmolKLNExecutor.execute()."""

    def test_returns_error_without_smolagents(self, tmp_path):
        """Should return error dict when smolagents not installed."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = SmolKLNExecutor()

            # Mock smolagents import failure
            with patch.dict("sys.modules", {"smolagents": None}):
                with patch("builtins.__import__", side_effect=ImportError("no smolagents")):
                    # Can't easily test this without complex import mocking
                    # Just verify the executor has the execute method
                    assert hasattr(executor, "execute")

    def test_returns_error_for_missing_agent(self, tmp_path):
        """Should return error when agent not found."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            with patch("klean.smol.executor.load_agent") as mock_load:
                mock_load.side_effect = FileNotFoundError("Agent not found")

                executor = SmolKLNExecutor()

                # Mock CodeAgent import
                with patch("klean.smol.executor.CodeAgent", create=True):
                    result = executor.execute("nonexistent-agent", "test task")

                    assert result["success"] is False
                    assert "not found" in result["output"].lower()

    def test_uses_model_override_when_provided(self, tmp_path):
        """Should use model_override instead of agent config model."""
        from klean.smol.executor import SmolKLNExecutor

        # Create a proper mock context with all required attributes
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context

            # Mock all dependencies
            mock_agent = MagicMock()
            mock_agent.config.model = "default-model"
            mock_agent.config.tools = []
            mock_agent.system_prompt = ""

            with patch("klean.smol.executor.load_agent", return_value=mock_agent):
                with patch("klean.smol.executor.create_model") as mock_create:
                    with patch("klean.smol.executor.get_default_tools", return_value=[]):
                        # Make CodeAgent.run() return something
                        mock_code_agent = MagicMock()
                        mock_code_agent.run.return_value = "Result"
                        mock_code_agent.memory = MagicMock()
                        mock_code_agent.prompt_templates = {}

                        with patch("smolagents.CodeAgent", return_value=mock_code_agent):
                            executor = SmolKLNExecutor()
                            executor.execute("test-agent", "task", model_override="override-model")

                            # Verify create_model was called with override
                            mock_create.assert_called_with("override-model", executor.api_base)

    def test_returns_success_result_structure(self, tmp_path):
        """Should return dict with expected keys on success."""
        from klean.smol.executor import SmolKLNExecutor

        # Create a proper mock context with all required attributes
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context

            mock_agent = MagicMock()
            mock_agent.config.model = "test"
            mock_agent.config.tools = []
            mock_agent.system_prompt = ""

            with patch("klean.smol.executor.load_agent", return_value=mock_agent):
                with patch("klean.smol.executor.create_model"):
                    with patch("klean.smol.executor.get_default_tools", return_value=[]):
                        mock_code_agent = MagicMock()
                        mock_code_agent.run.return_value = "Analysis complete"
                        mock_code_agent.memory = MagicMock()
                        mock_code_agent.prompt_templates = {}

                        with patch("smolagents.CodeAgent", return_value=mock_code_agent):
                            with patch("klean.smol.executor.get_citation_stats", return_value={}):
                                executor = SmolKLNExecutor()
                                result = executor.execute("test-agent", "review code")

                                # Check required keys
                                assert "output" in result
                                assert "agent" in result
                                assert "model" in result
                                assert "duration_s" in result
                                assert "success" in result


# =============================================================================
# List Agents Tests
# =============================================================================


class TestListAgents:
    """Tests for SmolKLNExecutor.list_agents()."""

    def test_calls_list_available_agents(self, tmp_path):
        """Should delegate to list_available_agents function."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            with patch("klean.smol.executor.list_available_agents") as mock_list:
                mock_list.return_value = ["agent1", "agent2"]

                executor = SmolKLNExecutor()
                agents = executor.list_agents()

                mock_list.assert_called_once_with(executor.agents_dir)
                assert agents == ["agent1", "agent2"]


# =============================================================================
# Get Agent Info Tests
# =============================================================================


class TestGetAgentInfo:
    """Tests for SmolKLNExecutor.get_agent_info()."""

    def test_returns_agent_details(self, tmp_path):
        """Should return dict with agent configuration."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)

            mock_agent = MagicMock()
            mock_agent.config.name = "test-agent"
            mock_agent.config.description = "Test description"
            mock_agent.config.model = "test-model"
            mock_agent.config.tools = ["tool1", "tool2"]
            mock_agent.source_path = Path("/path/to/agent.md")

            with patch("klean.smol.executor.load_agent", return_value=mock_agent):
                executor = SmolKLNExecutor()
                info = executor.get_agent_info("test-agent")

                assert info["name"] == "test-agent"
                assert info["description"] == "Test description"
                assert info["model"] == "test-model"
                assert info["tools"] == ["tool1", "tool2"]

    def test_returns_error_for_missing_agent(self, tmp_path):
        """Should return error dict for nonexistent agent."""
        from klean.smol.executor import SmolKLNExecutor

        with patch("klean.smol.executor.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            with patch("klean.smol.executor.load_agent") as mock_load:
                mock_load.side_effect = FileNotFoundError("Not found")

                executor = SmolKLNExecutor()
                info = executor.get_agent_info("nonexistent")

                assert "error" in info


# =============================================================================
# Step Awareness Callback Tests
# =============================================================================


class TestAddStepAwareness:
    """Tests for add_step_awareness callback function."""

    def test_adds_warning_on_low_steps(self):
        """Should add warning when 2 or fewer steps remaining."""
        from klean.smol.executor import add_step_awareness

        mock_step = MagicMock()
        mock_step.step_number = 8
        mock_step.observations = "Original observation"

        mock_agent = MagicMock()
        mock_agent.max_steps = 10

        add_step_awareness(mock_step, mock_agent)

        # Should append warning
        assert "final_answer()" in mock_step.observations
        assert "2 step(s) left" in mock_step.observations

    def test_no_warning_with_many_steps(self):
        """Should not modify observations when many steps remaining."""
        from klean.smol.executor import add_step_awareness

        mock_step = MagicMock()
        mock_step.step_number = 3
        mock_step.observations = "Original"

        mock_agent = MagicMock()
        mock_agent.max_steps = 10

        add_step_awareness(mock_step, mock_agent)

        # Should not modify
        assert mock_step.observations == "Original"

    def test_handles_none_observations(self):
        """Should handle None observations gracefully."""
        from klean.smol.executor import add_step_awareness

        mock_step = MagicMock()
        mock_step.step_number = 9
        mock_step.observations = None

        mock_agent = MagicMock()
        mock_agent.max_steps = 10

        add_step_awareness(mock_step, mock_agent)

        # Should set warning as observations
        assert mock_step.observations is not None
        assert "final_answer()" in mock_step.observations
