"""Unit tests for klean.smol.loader module.

Tests agent file parsing and loading:
- YAML frontmatter parsing
- Tool list extraction
- Model resolution (inherit/auto)
- Agent discovery

ANTI-FALSE-POSITIVE MEASURES:
1. Verify parsed values match expected types and content
2. Test file existence checks with actual filesystem
3. Test edge cases (no frontmatter, empty tools)
4. Verify source_path is preserved correctly
"""

from pathlib import Path
from unittest.mock import patch

import pytest

# Import module under test
from klean.smol.loader import (
    Agent,
    AgentConfig,
    list_available_agents,
    load_agent,
    parse_agent_file,
)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_tools_populated(self):
        """Should use default tools when not specified."""
        # Act
        config = AgentConfig(name="test", description="Test agent")

        # Assert
        assert isinstance(config.tools, list), "Tools should be a list"
        assert len(config.tools) == 3, "Should have 3 default tools"
        assert "knowledge_search" in config.tools
        assert "read_file" in config.tools
        assert "search_files" in config.tools

    def test_tools_none_becomes_default(self):
        """Should convert None tools to default list."""
        # Act
        config = AgentConfig(name="test", description="Test", tools=None)

        # Assert - __post_init__ should set default tools
        assert config.tools is not None, "Tools should not be None"
        assert len(config.tools) == 3, "Should have default tools"

    def test_custom_tools_preserved(self):
        """Should preserve custom tools list."""
        # Arrange
        custom_tools = ["grep", "web_search"]

        # Act
        config = AgentConfig(name="test", description="Test", tools=custom_tools)

        # Assert
        assert config.tools == custom_tools, "Should preserve custom tools"
        assert len(config.tools) == 2, "Should have exactly 2 tools"


class TestParseAgentFile:
    """Tests for parse_agent_file() function."""

    @patch('klean.smol.loader.get_model')
    def test_parses_yaml_frontmatter(self, mock_get_model, temp_agents_dir):
        """Should extract YAML frontmatter from agent file."""
        # Arrange
        mock_get_model.return_value = "default-model"
        agent_path = temp_agents_dir / "security-auditor.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert - verify parsed config
        assert agent.config.name == "security-auditor"
        assert agent.config.description == "Security audit specialist"
        assert agent.config.model == "deepseek-r1"

    @patch('klean.smol.loader.get_model')
    def test_extracts_tools_list(self, mock_get_model, temp_agents_dir):
        """Should parse tools list from frontmatter."""
        # Arrange
        mock_get_model.return_value = "default-model"
        agent_path = temp_agents_dir / "security-auditor.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert
        assert isinstance(agent.config.tools, list)
        assert "knowledge_search" in agent.config.tools
        assert "read_file" in agent.config.tools
        assert "grep" in agent.config.tools

    @patch('klean.smol.loader.get_model')
    def test_extracts_system_prompt(self, mock_get_model, temp_agents_dir):
        """Should extract markdown content as system prompt."""
        # Arrange
        mock_get_model.return_value = "default-model"
        agent_path = temp_agents_dir / "security-auditor.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert - verify system prompt content
        assert "Security Auditor" in agent.system_prompt
        assert "SQL injection" in agent.system_prompt
        assert agent.system_prompt.startswith("#")

    @patch('klean.smol.loader.get_model')
    def test_handles_no_frontmatter(self, mock_get_model, temp_agents_dir):
        """Should use defaults when no YAML frontmatter present."""
        # Arrange
        mock_get_model.return_value = "fallback-model"
        agent_path = temp_agents_dir / "no-frontmatter.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert - name from filename, default tools
        assert agent.config.name == "no-frontmatter"
        assert agent.config.description == ""
        assert len(agent.config.tools) == 3  # Default tools
        assert agent.config.model == "fallback-model"

    @patch('klean.smol.loader.get_model')
    def test_resolves_inherit_model(self, mock_get_model, temp_agents_dir):
        """Should resolve 'inherit' model to first available."""
        # Arrange
        mock_get_model.return_value = "discovered-model"
        agent_path = temp_agents_dir / "inherit-model.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert - model should be resolved from get_model()
        assert agent.config.model == "discovered-model"
        mock_get_model.assert_called_once()

    @patch('klean.smol.loader.get_model')
    def test_resolves_empty_model(self, mock_get_model, temp_agents_dir):
        """Should resolve empty model to first available."""
        # Arrange
        mock_get_model.return_value = "first-available"
        agent_path = temp_agents_dir / "simple-reviewer.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert
        assert agent.config.model == "first-available"
        mock_get_model.assert_called_once()

    @patch('klean.smol.loader.get_model')
    def test_preserves_source_path(self, mock_get_model, temp_agents_dir):
        """Should preserve source file path in Agent."""
        # Arrange
        mock_get_model.return_value = "model"
        agent_path = temp_agents_dir / "security-auditor.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert
        assert agent.source_path == agent_path
        assert agent.source_path.exists()

    @patch('klean.smol.loader.get_model')
    def test_fallback_to_auto_when_no_model_available(self, mock_get_model, temp_agents_dir):
        """Should fallback to 'auto' when get_model() returns None."""
        # Arrange
        mock_get_model.return_value = None  # No models available
        agent_path = temp_agents_dir / "simple-reviewer.md"

        # Act
        agent = parse_agent_file(agent_path)

        # Assert
        assert agent.config.model == "auto"


class TestListAvailableAgents:
    """Tests for list_available_agents() function."""

    def test_lists_md_files(self, temp_agents_dir):
        """Should list all .md files as agent names."""
        # Act
        agents = list_available_agents(agents_dir=temp_agents_dir)

        # Assert
        assert isinstance(agents, list)
        assert len(agents) == 4  # 4 agent files in fixture
        assert "security-auditor" in agents
        assert "simple-reviewer" in agents
        assert "no-frontmatter" in agents
        assert "inherit-model" in agents

    def test_returns_empty_for_missing_dir(self, tmp_path):
        """Should return empty list when directory doesn't exist."""
        # Arrange
        nonexistent = tmp_path / "nonexistent"

        # Act
        agents = list_available_agents(agents_dir=nonexistent)

        # Assert
        assert agents == []
        assert isinstance(agents, list)

    def test_returns_empty_for_empty_dir(self, tmp_path):
        """Should return empty list for directory with no .md files."""
        # Arrange
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Act
        agents = list_available_agents(agents_dir=empty_dir)

        # Assert
        assert agents == []


class TestLoadAgent:
    """Tests for load_agent() function."""

    @patch('klean.smol.loader.get_model')
    def test_loads_existing_agent(self, mock_get_model, temp_agents_dir):
        """Should load and parse existing agent by name."""
        # Arrange
        mock_get_model.return_value = "model"

        # Act
        agent = load_agent("security-auditor", agents_dir=temp_agents_dir)

        # Assert
        assert isinstance(agent, Agent)
        assert agent.config.name == "security-auditor"
        assert agent.source_path.name == "security-auditor.md"

    def test_raises_for_missing_agent(self, temp_agents_dir):
        """Should raise FileNotFoundError for non-existent agent."""
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            load_agent("nonexistent-agent", agents_dir=temp_agents_dir)

        # Verify error message contains agent name
        assert "nonexistent-agent" in str(exc_info.value)

    @patch('klean.smol.loader.get_model')
    def test_returns_agent_instance(self, mock_get_model, temp_agents_dir):
        """Should return proper Agent instance with all fields."""
        # Arrange
        mock_get_model.return_value = "test-model"

        # Act
        agent = load_agent("simple-reviewer", agents_dir=temp_agents_dir)

        # Assert - verify all Agent fields
        assert hasattr(agent, 'config')
        assert hasattr(agent, 'system_prompt')
        assert hasattr(agent, 'source_path')
        assert isinstance(agent.config, AgentConfig)
        assert isinstance(agent.system_prompt, str)
        assert isinstance(agent.source_path, Path)

