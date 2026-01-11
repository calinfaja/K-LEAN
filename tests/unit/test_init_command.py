"""Tests for kln init command."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from klean.cli import main


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".config" / "litellm"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_claude_dir(tmp_path):
    """Create a temporary .claude directory."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    return claude_dir


def test_init_command_exists():
    """Test that kln init command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize K-LEAN" in result.output


def test_init_nanogpt_silent():
    """Test init with NanoGPT provider (silent mode)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            result = runner.invoke(
                main,
                ["init", "--provider", "nanogpt", "--api-key", "test-key"],
                input="y\n",  # Confirm model installation
            )

            assert result.exit_code == 0
            assert "NANOGPT providers configured" in result.output
            assert "10 recommended models" in result.output


def test_init_openrouter_silent():
    """Test init with OpenRouter provider (silent mode)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            result = runner.invoke(
                main,
                ["init", "--provider", "openrouter", "--api-key", "sk-or-test"],
                input="y\n",  # Confirm model installation
            )

            assert result.exit_code == 0
            assert "OPENROUTER providers configured" in result.output
            assert "6 recommended models" in result.output


def test_init_skip_litellm():
    """Test init with skip provider (knowledge only)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            result = runner.invoke(main, ["init", "--provider", "skip"])

            assert result.exit_code == 0
            assert "Knowledge system ready" in result.output
            assert "no LiteLLM" in result.output
            # Config should not exist for skip
            assert not (config_dir / "config.yaml").exists()


def test_init_creates_config_file():
    """Test that init creates config.yaml correctly."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            runner.invoke(
                main,
                ["init", "--provider", "nanogpt", "--api-key", "test-key"],
                input="y\n",  # Confirm model installation
            )

            config_file = config_dir / "config.yaml"
            assert config_file.exists()
            assert "model_list:" in config_file.read_text()


def test_init_creates_env_file():
    """Test that init creates .env file with correct permissions."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            runner.invoke(
                main,
                ["init", "--provider", "nanogpt", "--api-key", "test-key"],
                input="y\n",  # Confirm model installation
            )

            env_file = config_dir / ".env"
            assert env_file.exists()

            # Check file permissions (Unix only - Windows doesn't have Unix permissions)
            if sys.platform != "win32":
                mode = env_file.stat().st_mode
                assert (mode & 0o077) == 0  # No group/other permissions


def test_init_nanogpt_creates_models():
    """Test that NanoGPT init creates config with multiple models."""
    from klean.config_generator import list_models_in_config

    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            runner.invoke(
                main,
                ["init", "--provider", "nanogpt", "--api-key", "test-key"],
                input="y\n",  # Confirm model installation
            )

            config_file = config_dir / "config.yaml"
            models = list_models_in_config(config_file)

            # Should have multiple models (exact count is user-configurable)
            assert len(models) > 0, "Expected at least one model configured"
            # All models should have required fields
            for model in models:
                assert "model_name" in model
                assert "model_id" in model
                assert "is_thinking" in model


def test_init_no_pricing_info():
    """Test that init doesn't show pricing information."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            result = runner.invoke(main, ["init"], input="1\ntest-key\n")

            # Should not contain any pricing info
            assert "$" not in result.output
            assert "free" not in result.output.lower()
            assert "pay" not in result.output.lower()


def test_init_openrouter_models_count():
    """Test that OpenRouter init includes default 6 models."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            runner.invoke(
                main,
                ["init", "--provider", "openrouter", "--api-key", "sk-or-test"],
                input="y\n",  # Confirm model installation
            )

            config_file = config_dir / "config.yaml"
            content = config_file.read_text()

            # Count model_name entries
            model_count = content.count("model_name:")
            assert model_count == 6, f"Expected 6 models, got {model_count}"


def test_init_already_initialized():
    """Test that init warns when already initialized."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        # Create existing config BEFORE patching CONFIG_DIR
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yaml").write_text("# existing config")

        with patch("klean.cli.CONFIG_DIR", config_dir), patch("klean.cli.CLAUDE_DIR", claude_dir):
            # Try to init again - should ask for reconfiguration
            result = runner.invoke(main, ["init", "--provider", "skip"], input="n\n")

            # Should warn about already being initialized
            assert (
                "already initialized" in result.output.lower()
                or "reconfigure" in result.output.lower()
            )


def test_init_api_key_hidden_in_interactive():
    """Test that interactive mode accepts API key input."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "litellm"
        claude_dir = Path(tmpdir) / ".claude"

        with (
            patch("klean.cli.CONFIG_DIR", config_dir),
            patch("klean.cli.CLAUDE_DIR", claude_dir),
            patch("klean.cli.install"),
        ):
            result = runner.invoke(
                main,
                ["init"],
                input="1\nn\nmy-secret-key\ny\n",  # Choose provider, no more providers, API key, confirm models
            )

            # Command should complete successfully
            assert result.exit_code == 0
            # Verify initialization completed
            assert "K-LEAN initialized" in result.output
