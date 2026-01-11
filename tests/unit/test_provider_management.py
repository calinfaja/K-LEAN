"""Tests for provider management functionality."""

import pytest
from click.testing import CliRunner

from klean.cli import _get_configured_providers, _load_existing_env, main


class TestProviderCommands:
    """Test provider subcommand functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def temp_config(self, monkeypatch, tmp_path):
        """Create temporary config directory."""
        config_dir = tmp_path / ".config" / "litellm"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Mock CONFIG_DIR
        import klean.cli

        monkeypatch.setattr(klean.cli, "CONFIG_DIR", config_dir)

        return config_dir

    def test_provider_list_empty(self, cli_runner, temp_config):
        """Test listing providers when none configured."""
        result = cli_runner.invoke(main, ["provider", "list"])
        assert result.exit_code == 0
        assert "No providers configured" in result.output

    def test_provider_add_nanogpt(self, cli_runner, temp_config):
        """Test adding NanoGPT provider."""
        result = cli_runner.invoke(
            main,
            ["provider", "add", "nanogpt", "--api-key", "sk-nano-test123"],
            input="y\n",  # Confirm model installation
        )
        assert result.exit_code == 0
        assert "Configured NANOGPT API key" in result.output

        # Verify .env was created
        env_file = temp_config / ".env"
        assert env_file.exists()
        content = env_file.read_text()
        assert "NANOGPT_API_KEY=sk-nano-test123" in content

    def test_provider_add_openrouter(self, cli_runner, temp_config):
        """Test adding OpenRouter provider."""
        result = cli_runner.invoke(
            main,
            ["provider", "add", "openrouter", "--api-key", "sk-or-test456"],
            input="y\n",  # Confirm model installation
        )
        assert result.exit_code == 0
        assert "Configured OPENROUTER API key" in result.output

        env_file = temp_config / ".env"
        content = env_file.read_text()
        assert "OPENROUTER_API_KEY=sk-or-test456" in content
        assert "OPENROUTER_API_BASE" in content

    def test_provider_add_preserves_existing(self, cli_runner, temp_config):
        """Test that adding provider preserves existing ones."""
        # Add NanoGPT first
        result1 = cli_runner.invoke(
            main,
            ["provider", "add", "nanogpt", "--api-key", "sk-nano-original"],
            input="y\n",  # Confirm model installation
        )
        assert result1.exit_code == 0

        # Add OpenRouter
        result2 = cli_runner.invoke(
            main,
            ["provider", "add", "openrouter", "--api-key", "sk-or-new"],
            input="y\n",  # Confirm model installation
        )
        assert result2.exit_code == 0

        # Verify both are present
        env_file = temp_config / ".env"
        content = env_file.read_text()
        assert "NANOGPT_API_KEY=sk-nano-original" in content
        assert "OPENROUTER_API_KEY=sk-or-new" in content

    def test_provider_set_key(self, cli_runner, temp_config):
        """Test updating an existing provider's API key."""
        # Add NanoGPT
        cli_runner.invoke(main, ["provider", "add", "nanogpt", "--api-key", "sk-nano-old"])

        # Update key
        result = cli_runner.invoke(main, ["provider", "set-key", "nanogpt", "--key", "sk-nano-new"])
        assert result.exit_code == 0
        assert "Updated NANOGPT API key" in result.output

        # Verify new key is in place
        env_file = temp_config / ".env"
        content = env_file.read_text()
        assert "NANOGPT_API_KEY=sk-nano-new" in content
        assert "sk-nano-old" not in content

    def test_provider_remove(self, cli_runner, temp_config):
        """Test removing a provider."""
        # Add both providers
        cli_runner.invoke(main, ["provider", "add", "nanogpt", "--api-key", "sk-nano-test"])
        cli_runner.invoke(main, ["provider", "add", "openrouter", "--api-key", "sk-or-test"])

        # Remove NanoGPT
        result = cli_runner.invoke(main, ["provider", "remove", "nanogpt"], input="y\n")
        assert result.exit_code == 0
        assert "Removed NANOGPT configuration" in result.output

        # Verify NanoGPT is gone but OpenRouter remains
        env_file = temp_config / ".env"
        content = env_file.read_text()
        assert "NANOGPT_API_KEY" not in content
        assert "OPENROUTER_API_KEY=sk-or-test" in content

    def test_load_existing_env(self, temp_config):
        """Test loading existing .env file."""
        # Create .env file
        env_file = temp_config / ".env"
        env_file.write_text(
            "NANOGPT_API_KEY=sk-nano-123\n"
            "OPENROUTER_API_KEY=sk-or-456\n"
            "# This is a comment\n"
            "SOME_OTHER_VAR=value\n"
        )

        import unittest.mock

        import klean.cli

        with unittest.mock.patch.object(klean.cli, "CONFIG_DIR", temp_config):
            env_vars = _load_existing_env()

        assert env_vars["NANOGPT_API_KEY"] == "sk-nano-123"
        assert env_vars["OPENROUTER_API_KEY"] == "sk-or-456"
        assert env_vars["SOME_OTHER_VAR"] == "value"

    def test_get_configured_providers(self, temp_config):
        """Test getting list of configured providers."""
        # Create .env with both providers
        env_file = temp_config / ".env"
        env_file.write_text("NANOGPT_API_KEY=sk-nano-123\nOPENROUTER_API_KEY=sk-or-456\n")

        import unittest.mock

        import klean.cli

        with unittest.mock.patch.object(klean.cli, "CONFIG_DIR", temp_config):
            providers = _get_configured_providers()

        assert "nanogpt" in providers
        assert "openrouter" in providers
        assert providers["nanogpt"]["configured"] is True
        assert providers["openrouter"]["configured"] is True


class TestProviderHelperFunctions:
    """Test internal provider helper functions."""

    def test_load_existing_env_empty(self, tmp_path, monkeypatch):
        """Test loading when .env doesn't exist."""
        config_dir = tmp_path / ".config" / "litellm"
        config_dir.mkdir(parents=True)

        import klean.cli

        monkeypatch.setattr(klean.cli, "CONFIG_DIR", config_dir)

        env_vars = _load_existing_env()
        assert env_vars == {}

    def test_load_existing_env_with_errors(self, tmp_path, monkeypatch):
        """Test loading .env with malformed lines (graceful handling)."""
        config_dir = tmp_path / ".config" / "litellm"
        config_dir.mkdir(parents=True)
        env_file = config_dir / ".env"
        env_file.write_text(
            "VALID_KEY=value\nINVALID_LINE_NO_EQUALS\nANOTHER_VALID=another_value\n"
        )

        import klean.cli

        monkeypatch.setattr(klean.cli, "CONFIG_DIR", config_dir)

        env_vars = _load_existing_env()
        # Should load the valid lines and skip invalid ones
        assert "VALID_KEY" in env_vars
        assert "ANOTHER_VALID" in env_vars
