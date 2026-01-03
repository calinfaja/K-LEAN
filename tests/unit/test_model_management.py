"""Tests for model management (model add, model remove commands)."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from klean.cli import main
from klean.model_utils import extract_model_name, is_thinking_model, parse_model_id


class TestModelUtils:
    """Tests for model utility functions."""

    def test_extract_model_name_openrouter(self):
        """Test extracting model name from OpenRouter ID."""
        result = extract_model_name("openrouter/kwaipilot/kat-coder-pro:free")
        assert result == "kat-coder-pro"

    def test_extract_model_name_nanogpt(self):
        """Test extracting model name from NanoGPT ID."""
        result = extract_model_name("openai/Qwen/Qwen2.5-Coder-32B-Instruct")
        # Should extract meaningful part (converts to lowercase, removes size info)
        assert "qwen" in result.lower()
        assert len(result) > 3, "Model name should not be too abbreviated"

    def test_extract_model_name_simple(self):
        """Test extracting model name from simple ID."""
        result = extract_model_name("anthropic/claude-3.5-sonnet")
        assert "claude" in result
        assert "sonnet" in result

    def test_extract_model_name_with_version(self):
        """Test extracting model name with version numbers."""
        result = extract_model_name("openai/Qwen/Qwen2.5-Coder")
        # Should replace dots with dashes
        assert "." not in result
        assert "-" in result

    def test_parse_model_id_openrouter(self):
        """Test parsing OpenRouter model ID."""
        provider, full_id = parse_model_id("openrouter/anthropic/claude-3.5-sonnet")
        assert provider == "openrouter"
        assert full_id == "openrouter/anthropic/claude-3.5-sonnet"

    def test_parse_model_id_nanogpt(self):
        """Test parsing NanoGPT (OpenAI) model ID."""
        provider, full_id = parse_model_id("openai/Qwen/Qwen2.5-Coder-32B-Instruct")
        assert provider == "nanogpt"
        assert full_id == "openai/Qwen/Qwen2.5-Coder-32B-Instruct"

    def test_parse_model_id_unknown(self):
        """Test parsing unknown provider ID."""
        provider, full_id = parse_model_id("unknown/model")
        assert provider == "unknown"

    def test_is_thinking_model_true(self):
        """Test thinking model detection."""
        assert is_thinking_model("deepseek-r1-thinking")
        assert is_thinking_model("glm-4.6-thinking")
        assert is_thinking_model("kimi-k2-thinking")

    def test_is_thinking_model_false(self):
        """Test non-thinking model detection."""
        assert not is_thinking_model("claude-3.5-sonnet")
        assert not is_thinking_model("qwen-coder")
        assert not is_thinking_model("deepseek-v3")


class TestAddModelCommand:
    """Tests for kln model add command."""

    def test_add_model_command_exists(self):
        """Test that kln model add command exists."""
        runner = CliRunner()
        result = runner.invoke(main, ["model", "add", "--help"])
        assert result.exit_code == 0
        assert "Add individual model" in result.output

    def test_add_model_no_config(self):
        """Test add-model fails when config doesn't exist."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "litellm"

            with patch("klean.cli.CONFIG_DIR", config_dir):
                result = runner.invoke(
                    main,
                    ["model", "add", "--provider", "openrouter", "anthropic/claude-3.5-sonnet"]
                )

                assert result.exit_code != 0
                assert "config.yaml not found" in result.output

    def test_add_model_openrouter(self):
        """Test adding OpenRouter model."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "litellm"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create initial config
            config_yaml = """litellm_settings:
  drop_params: true

model_list:
  - model_name: test-model
    litellm_params:
      model: openai/test
      api_key: os.environ/NANOGPT_API_KEY
"""
            (config_dir / "config.yaml").write_text(config_yaml)

            with patch("klean.cli.CONFIG_DIR", config_dir):
                result = runner.invoke(
                    main,
                    ["model", "add", "--provider", "openrouter", "anthropic/claude-3.5-sonnet"]
                )

                assert result.exit_code == 0
                assert "Added model" in result.output

                # Verify model was added
                config_content = (config_dir / "config.yaml").read_text()
                assert "claude-3.5-sonnet" in config_content
                assert "openrouter/anthropic" in config_content


class TestRemoveModelCommand:
    """Tests for kln model remove command."""

    def test_remove_model_command_exists(self):
        """Test that kln model remove command exists."""
        runner = CliRunner()
        result = runner.invoke(main, ["model", "remove", "--help"])
        assert result.exit_code == 0
        assert "Remove model" in result.output

    def test_remove_model_no_config(self):
        """Test remove-model fails when config doesn't exist."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "litellm"

            with patch("klean.cli.CONFIG_DIR", config_dir):
                result = runner.invoke(
                    main,
                    ["model", "remove", "nonexistent-model"]
                )

                assert result.exit_code != 0
                assert "config.yaml not found" in result.output

    def test_remove_model_not_found(self):
        """Test remove-model when model doesn't exist."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "litellm"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create config with one model
            config_yaml = """litellm_settings:
  drop_params: true

model_list:
  - model_name: test-model
    litellm_params:
      model: openai/test
      api_key: os.environ/NANOGPT_API_KEY
"""
            (config_dir / "config.yaml").write_text(config_yaml)

            with patch("klean.cli.CONFIG_DIR", config_dir):
                result = runner.invoke(
                    main,
                    ["model", "remove", "nonexistent-model"]
                )

                assert result.exit_code == 0
                assert "not found" in result.output
                assert "Available models:" in result.output

    def test_remove_model_success(self):
        """Test successfully removing a model."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "litellm"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create config with two models
            config_yaml = """litellm_settings:
  drop_params: true

model_list:
  - model_name: test-model-1
    litellm_params:
      model: openai/test1
      api_key: os.environ/NANOGPT_API_KEY
  - model_name: test-model-2
    litellm_params:
      model: openai/test2
      api_key: os.environ/NANOGPT_API_KEY
"""
            (config_dir / "config.yaml").write_text(config_yaml)

            with patch("klean.cli.CONFIG_DIR", config_dir):
                result = runner.invoke(
                    main,
                    ["model", "remove", "test-model-1"]
                )

                assert result.exit_code == 0
                assert "Removed model" in result.output

                # Verify model was removed
                config_content = (config_dir / "config.yaml").read_text()
                assert "test-model-1" not in config_content
                assert "test-model-2" in config_content


class TestAddAndRemoveIntegration:
    """Integration tests for add and remove operations."""

    def test_add_then_remove_model(self):
        """Test adding then removing a model."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "litellm"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create initial config
            config_yaml = """litellm_settings:
  drop_params: true

model_list: []
"""
            (config_dir / "config.yaml").write_text(config_yaml)

            with patch("klean.cli.CONFIG_DIR", config_dir):
                # Add model
                result1 = runner.invoke(
                    main,
                    ["model", "add", "--provider", "openrouter", "anthropic/claude-3.5-sonnet"]
                )
                assert result1.exit_code == 0

                # Remove model
                result2 = runner.invoke(
                    main,
                    ["model", "remove", "claude-3.5-sonnet"]
                )
                assert result2.exit_code == 0

                # Verify model list is empty
                config_content = (config_dir / "config.yaml").read_text()
                assert "claude-3.5-sonnet" not in config_content
