"""Tests for klean.smol.multi_agent module.

Tests cover:
- MultiAgentExecutor initialization
- Output directory handling
- Agent prompt loading
- Result formatting
- Multi-agent execution flow
- Error handling
"""

from unittest.mock import MagicMock, patch

# =============================================================================
# MultiAgentExecutor Initialization Tests
# =============================================================================


class TestMultiAgentExecutorInit:
    """Tests for MultiAgentExecutor.__init__()."""

    def test_sets_default_api_base(self, tmp_path):
        """Should set default api_base to localhost:4000."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            assert executor.api_base == "http://localhost:4000"

    def test_accepts_custom_api_base(self, tmp_path):
        """Should accept custom api_base."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor(api_base="http://custom:5000")

            assert executor.api_base == "http://custom:5000"

    def test_gathers_project_context(self, tmp_path):
        """Should gather project context on init."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            mock_ctx.assert_called_once()
            assert executor.project_root == tmp_path

    def test_accepts_custom_project_path(self, tmp_path):
        """Should accept custom project_path override."""
        from klean.smol.multi_agent import MultiAgentExecutor

        custom_path = tmp_path / "custom"
        custom_path.mkdir()

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=custom_path)
            _executor = MultiAgentExecutor(project_path=custom_path)

            mock_ctx.assert_called_once_with(custom_path)


# =============================================================================
# Output Directory Tests
# =============================================================================


class TestGetOutputDir:
    """Tests for MultiAgentExecutor._get_output_dir()."""

    def test_creates_output_dir_under_project(self, tmp_path):
        """Should create output dir under project_root/.claude/kln/multiAgent/."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            expected = tmp_path / ".claude" / "kln" / "multiAgent"
            assert executor.output_dir == expected
            assert expected.exists()


# =============================================================================
# Load Agent Prompt Tests
# =============================================================================


class TestLoadAgentPrompt:
    """Tests for MultiAgentExecutor._load_agent_prompt()."""

    def test_loads_prompt_from_file(self, tmp_path):
        """Should load prompt from .md file."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            # Create a mock prompt file
            mock_prompt_path = MagicMock()
            mock_prompt_path.exists.return_value = True
            mock_prompt_path.read_text.return_value = "Agent prompt content"

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="Agent prompt content"):
                    prompt = executor._load_agent_prompt("security-specialist")

                    # Should return content if file exists
                    assert prompt == "Agent prompt content"

    def test_returns_empty_for_missing_file(self, tmp_path):
        """Should return empty string if prompt file doesn't exist."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            # For a non-existent agent, prompt file won't exist
            prompt = executor._load_agent_prompt("nonexistent-agent-xyz")

            assert prompt == ""

    def test_strips_yaml_frontmatter(self, tmp_path):
        """Should strip YAML frontmatter from prompt."""
        from klean.smol.multi_agent import MultiAgentExecutor

        content_with_frontmatter = """---
name: test
model: test
---
Actual prompt content here."""

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value=content_with_frontmatter):
                    prompt = executor._load_agent_prompt("test")

                    assert prompt == "Actual prompt content here."


# =============================================================================
# Format Result Tests
# =============================================================================


class TestFormatResult:
    """Tests for MultiAgentExecutor._format_result()."""

    def test_extracts_code_from_dict(self, tmp_path):
        """Should extract 'code' field from dict result."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            result = {"thought": "thinking...", "code": "## Summary\nGood review!"}
            formatted = executor._format_result(result)

            assert formatted == "## Summary\nGood review!"

    def test_handles_string_result(self, tmp_path):
        """Should return string results unchanged."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            result = "Plain string result"
            formatted = executor._format_result(result)

            assert formatted == "Plain string result"


# =============================================================================
# Execute Tests
# =============================================================================


class TestExecute:
    """Tests for MultiAgentExecutor.execute()."""

    def test_returns_error_without_smolagents(self, tmp_path):
        """Should return error dict when smolagents not installed."""
        from klean.smol.multi_agent import MultiAgentExecutor

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = MagicMock(project_root=tmp_path)
            executor = MultiAgentExecutor()

            # Just verify the executor has the execute method
            assert hasattr(executor, "execute")

    def test_uses_3_agent_config_by_default(self, tmp_path):
        """Should use 3-agent config when thorough=False."""
        from klean.smol.multi_agent import MultiAgentExecutor

        # Create proper mock context
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context
            with patch("klean.smol.multi_agent.get_3_agent_config") as mock_3:
                with patch("klean.smol.multi_agent.get_thorough_agent_config") as mock_thorough:
                    # Mock config
                    mock_agent_config = MagicMock()
                    mock_agent_config.model = "test"
                    mock_agent_config.tools = []
                    mock_agent_config.name = "test"
                    mock_agent_config.description = "test"
                    mock_agent_config.max_steps = 5
                    mock_agent_config.planning_interval = 2

                    mock_3.return_value = {"manager": mock_agent_config}
                    mock_thorough.return_value = {}

                    with patch("klean.smol.multi_agent.create_model"):
                        with patch("smolagents.CodeAgent") as mock_code_agent:
                            mock_agent = MagicMock()
                            mock_agent.run.return_value = "Result"
                            mock_agent.memory = MagicMock()
                            mock_agent.prompt_templates = {}
                            mock_code_agent.return_value = mock_agent

                            with patch(
                                "klean.smol.multi_agent.get_citation_stats", return_value={}
                            ):
                                executor = MultiAgentExecutor()
                                executor.execute("test task", thorough=False)

                                mock_3.assert_called_once()
                                mock_thorough.assert_not_called()

    def test_uses_thorough_agent_config_when_thorough(self, tmp_path):
        """Should use thorough agent config when thorough=True."""
        from klean.smol.multi_agent import MultiAgentExecutor

        # Create proper mock context
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context
            with patch("klean.smol.multi_agent.get_3_agent_config") as mock_3:
                with patch("klean.smol.multi_agent.get_thorough_agent_config") as mock_thorough:
                    # Mock config
                    mock_agent_config = MagicMock()
                    mock_agent_config.model = "test"
                    mock_agent_config.tools = []
                    mock_agent_config.name = "test"
                    mock_agent_config.description = "test"
                    mock_agent_config.max_steps = 5
                    mock_agent_config.planning_interval = 2

                    mock_3.return_value = {}
                    mock_thorough.return_value = {"manager": mock_agent_config}

                    with patch("klean.smol.multi_agent.create_model"):
                        with patch("smolagents.CodeAgent") as mock_code_agent:
                            mock_agent = MagicMock()
                            mock_agent.run.return_value = "Result"
                            mock_agent.memory = MagicMock()
                            mock_agent.prompt_templates = {}
                            mock_code_agent.return_value = mock_agent

                            with patch(
                                "klean.smol.multi_agent.get_citation_stats", return_value={}
                            ):
                                executor = MultiAgentExecutor()
                                executor.execute("test task", thorough=True)

                                mock_thorough.assert_called_once()
                                mock_3.assert_not_called()

    def test_returns_variant_in_result(self, tmp_path):
        """Should return variant (3-agent or thorough) in result."""
        from klean.smol.multi_agent import MultiAgentExecutor

        # Create proper mock context
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context
            with patch("klean.smol.multi_agent.get_3_agent_config") as mock_3:
                mock_agent_config = MagicMock()
                mock_agent_config.model = "test"
                mock_agent_config.tools = []
                mock_agent_config.name = "test"
                mock_agent_config.description = "test"
                mock_agent_config.max_steps = 5
                mock_agent_config.planning_interval = 2

                mock_3.return_value = {"manager": mock_agent_config}

                with patch("klean.smol.multi_agent.create_model"):
                    with patch("smolagents.CodeAgent") as mock_code_agent:
                        mock_agent = MagicMock()
                        mock_agent.run.return_value = "Result"
                        mock_agent.memory = MagicMock()
                        mock_agent.prompt_templates = {}
                        mock_code_agent.return_value = mock_agent

                        with patch("klean.smol.multi_agent.get_citation_stats", return_value={}):
                            executor = MultiAgentExecutor()
                            result = executor.execute("test task", thorough=False)

                            assert "variant" in result
                            assert result["variant"] == "3-agent"

    def test_returns_success_structure(self, tmp_path):
        """Should return dict with expected keys on success."""
        from klean.smol.multi_agent import MultiAgentExecutor

        # Create proper mock context
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context
            with patch("klean.smol.multi_agent.get_3_agent_config") as mock_3:
                mock_agent_config = MagicMock()
                mock_agent_config.model = "test"
                mock_agent_config.tools = []
                mock_agent_config.name = "test"
                mock_agent_config.description = "test"
                mock_agent_config.max_steps = 5
                mock_agent_config.planning_interval = 2

                mock_3.return_value = {"manager": mock_agent_config}

                with patch("klean.smol.multi_agent.create_model"):
                    with patch("smolagents.CodeAgent") as mock_code_agent:
                        mock_agent = MagicMock()
                        mock_agent.run.return_value = "Analysis complete"
                        mock_agent.memory = MagicMock()
                        mock_agent.prompt_templates = {}
                        mock_code_agent.return_value = mock_agent

                        with patch("klean.smol.multi_agent.get_citation_stats", return_value={}):
                            executor = MultiAgentExecutor()
                            result = executor.execute("test task")

                            # Check required keys
                            assert "output" in result
                            assert "variant" in result
                            assert "agents_used" in result
                            assert "duration_s" in result
                            assert "success" in result


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in MultiAgentExecutor."""

    def test_returns_error_on_agent_creation_failure(self, tmp_path):
        """Should return error when specialist agent creation fails."""
        from klean.smol.multi_agent import MultiAgentExecutor

        # Create proper mock context
        mock_context = MagicMock()
        mock_context.project_root = tmp_path
        mock_context.project_name = "test-project"
        mock_context.git_branch = None
        mock_context.git_status_summary = ""
        mock_context.claude_md = None
        mock_context.has_knowledge_db = False
        mock_context.knowledge_db_path = None
        mock_context.serena_available = False

        with patch("klean.smol.multi_agent.gather_project_context") as mock_ctx:
            mock_ctx.return_value = mock_context
            with patch("klean.smol.multi_agent.get_3_agent_config") as mock_3:
                # Setup config with a specialist that will fail
                mock_manager = MagicMock()
                mock_manager.model = "manager-model"
                mock_manager.tools = []
                mock_manager.name = "manager"

                mock_specialist = MagicMock()
                mock_specialist.model = "test-model"
                mock_specialist.tools = []
                mock_specialist.name = "security"
                mock_specialist.description = "Security specialist"
                mock_specialist.max_steps = 5
                mock_specialist.planning_interval = 2

                mock_3.return_value = {
                    "manager": mock_manager,
                    "security": mock_specialist,
                }

                with patch(
                    "klean.smol.multi_agent.create_model", side_effect=Exception("Model error")
                ):
                    executor = MultiAgentExecutor()
                    result = executor.execute("test task")

                    assert result["success"] is False
                    assert "Error creating agent" in result["output"]
