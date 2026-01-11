"""Tests for klean.smol.multi_config module.

Tests cover:
- AgentConfig dataclass
- get_default_model function
- get_models function
- get_3_agent_config function
- get_thorough_agent_config function
"""

from unittest.mock import patch

# =============================================================================
# AgentConfig Tests
# =============================================================================


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_creates_config_with_required_fields(self):
        """Should create config with all required fields."""
        from klean.smol.multi_config import AgentConfig

        config = AgentConfig(
            name="test",
            model="test-model",
            tools=["tool1", "tool2"],
            max_steps=5,
            description="Test agent",
        )

        assert config.name == "test"
        assert config.model == "test-model"
        assert config.tools == ["tool1", "tool2"]
        assert config.max_steps == 5
        assert config.description == "Test agent"

    def test_default_planning_interval(self):
        """Should default planning_interval to 3."""
        from klean.smol.multi_config import AgentConfig

        config = AgentConfig(name="test", model="model", tools=[], max_steps=5, description="desc")

        assert config.planning_interval == 3

    def test_custom_planning_interval(self):
        """Should accept custom planning_interval."""
        from klean.smol.multi_config import AgentConfig

        config = AgentConfig(
            name="test",
            model="model",
            tools=[],
            max_steps=5,
            description="desc",
            planning_interval=5,
        )

        assert config.planning_interval == 5


# =============================================================================
# Get Default Model Tests
# =============================================================================


class TestGetDefaultModel:
    """Tests for get_default_model()."""

    def test_returns_string(self):
        """Should return a model name string."""
        from klean.smol.multi_config import get_default_model

        with patch("klean.smol.multi_config.get_model", return_value="test-model"):
            result = get_default_model()

            assert isinstance(result, str)

    def test_uses_discovery(self):
        """Should use model discovery from LiteLLM."""
        from klean.smol.multi_config import get_default_model

        with patch("klean.smol.multi_config.get_model", return_value="discovered-model"):
            result = get_default_model()

            assert result == "discovered-model"

    def test_returns_fallback_when_no_models(self):
        """Should return fallback when no models available."""
        from klean.smol.multi_config import get_default_model

        with patch("klean.smol.multi_config.get_model", return_value=None):
            result = get_default_model()

            # Should return a fallback model
            assert isinstance(result, str)
            assert len(result) > 0


# =============================================================================
# Get Models Tests
# =============================================================================


class TestGetModels:
    """Tests for get_models()."""

    def test_returns_dict(self):
        """Should return dict of model assignments."""
        from klean.smol.multi_config import get_models

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_models()

            assert isinstance(result, dict)

    def test_includes_all_roles(self):
        """Should include models for all agent roles."""
        from klean.smol.multi_config import get_models

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_models()

            # Should have entries for key roles
            assert "manager" in result
            assert "analyzer" in result
            assert "file-scout" in result


# =============================================================================
# Get 3-Agent Config Tests
# =============================================================================


class TestGet3AgentConfig:
    """Tests for get_3_agent_config()."""

    def test_returns_dict_of_agent_configs(self):
        """Should return dict mapping names to AgentConfig."""
        from klean.smol.multi_config import AgentConfig, get_3_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_3_agent_config()

            assert isinstance(result, dict)
            for _name, config in result.items():
                assert isinstance(config, AgentConfig)

    def test_includes_manager(self):
        """Should include manager agent."""
        from klean.smol.multi_config import get_3_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_3_agent_config()

            assert "manager" in result
            assert result["manager"].name == "manager"

    def test_includes_file_scout(self):
        """Should include file_scout agent."""
        from klean.smol.multi_config import get_3_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_3_agent_config()

            assert "file_scout" in result
            # File scout should have file reading tools
            assert "read_file" in result["file_scout"].tools

    def test_includes_analyzer(self):
        """Should include analyzer agent."""
        from klean.smol.multi_config import get_3_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_3_agent_config()

            assert "analyzer" in result

    def test_returns_exactly_3_agents(self):
        """Should return exactly 3 agents."""
        from klean.smol.multi_config import get_3_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_3_agent_config()

            assert len(result) == 3


# =============================================================================
# Get Thorough Agent Config Tests
# =============================================================================


class TestGetThoroughAgentConfig:
    """Tests for get_thorough_agent_config()."""

    def test_returns_dict_of_agent_configs(self):
        """Should return dict mapping names to AgentConfig."""
        from klean.smol.multi_config import AgentConfig, get_thorough_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_thorough_agent_config()

            assert isinstance(result, dict)
            for _name, config in result.items():
                assert isinstance(config, AgentConfig)

    def test_includes_manager(self):
        """Should include manager agent."""
        from klean.smol.multi_config import get_thorough_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_thorough_agent_config()

            assert "manager" in result

    def test_returns_more_agents_than_3_config(self):
        """Should return more agents than 3-agent config (currently 5)."""
        from klean.smol.multi_config import get_thorough_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_thorough_agent_config()

            # Thorough config has 5 agents: manager, file_scout, code_analyzer, security_auditor, synthesizer
            assert len(result) == 5

    def test_includes_security_agent(self):
        """Should include security-focused agent in thorough config."""
        from klean.smol.multi_config import get_thorough_agent_config

        with patch("klean.smol.multi_config.get_model", return_value="test"):
            result = get_thorough_agent_config()

            # 4-agent config should have a security specialist
            agent_names = list(result.keys())
            has_security = any("security" in name.lower() for name in agent_names)
            assert has_security, f"Expected security agent in {agent_names}"
