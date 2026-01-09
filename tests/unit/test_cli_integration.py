"""Tests for CLI integration with cross-platform utilities.

Tests cover:
- Service start/stop using platform.spawn_background and kill_process_tree
- Hook entry points configuration
- Knowledge server TCP-based operations
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

# =============================================================================
# CLI Import Tests
# =============================================================================


class TestCLIImports:
    """Tests for CLI module imports."""

    def test_imports_platform_functions(self):
        """Should import platform functions correctly."""
        from klean.cli import (
            cleanup_stale_files,
            get_kb_pid_file,
            get_kb_port_file,
            get_runtime_dir,
            is_process_running,
            kill_process_tree,
            spawn_background,
        )

        # All should be callable
        assert callable(cleanup_stale_files)
        assert callable(get_kb_pid_file)
        assert callable(get_kb_port_file)
        assert callable(get_runtime_dir)
        assert callable(is_process_running)
        assert callable(kill_process_tree)
        assert callable(spawn_background)


# =============================================================================
# Hook Configuration Tests
# =============================================================================


class TestHooksConfig:
    """Tests for hooks configuration."""

    def test_hooks_use_entry_points(self):
        """Hooks config should use Python entry points."""
        from klean.cli import KLEAN_HOOKS_CONFIG

        # Check all hooks use kln-hook-* commands
        session_hooks = KLEAN_HOOKS_CONFIG.get("SessionStart", [])
        assert len(session_hooks) >= 2

        for hook_group in session_hooks:
            for hook in hook_group.get("hooks", []):
                assert "kln-hook-session" in hook.get("command", "")

        prompt_hooks = KLEAN_HOOKS_CONFIG.get("UserPromptSubmit", [])
        assert len(prompt_hooks) >= 1
        for hook_group in prompt_hooks:
            for hook in hook_group.get("hooks", []):
                assert "kln-hook-prompt" in hook.get("command", "")

        post_hooks = KLEAN_HOOKS_CONFIG.get("PostToolUse", [])
        assert len(post_hooks) >= 2
        bash_found = False
        web_found = False
        for hook_group in post_hooks:
            matcher = hook_group.get("matcher", "")
            for hook in hook_group.get("hooks", []):
                cmd = hook.get("command", "")
                if "Bash" in matcher and "kln-hook-bash" in cmd:
                    bash_found = True
                if "Web" in matcher and "kln-hook-web" in cmd:
                    web_found = True
        assert bash_found
        assert web_found

    def test_hooks_no_shell_scripts(self):
        """Hooks config should not reference .sh files."""
        from klean.cli import KLEAN_HOOKS_CONFIG

        for hook_type, hook_list in KLEAN_HOOKS_CONFIG.items():
            for hook_group in hook_list:
                for hook in hook_group.get("hooks", []):
                    cmd = hook.get("command", "")
                    assert ".sh" not in cmd, f"Shell script found in {hook_type}: {cmd}"


# =============================================================================
# Service Management Tests
# =============================================================================


class TestKnowledgeServerTCP:
    """Tests for TCP-based knowledge server operations."""

    def test_check_knowledge_server_uses_tcp(self, tmp_path):
        """check_knowledge_server should use TCP connection."""
        from klean.cli import check_knowledge_server

        # Create a fake project
        project = tmp_path / "project"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        with patch("klean.cli.find_project_root", return_value=project):
            with patch("klean.cli.get_kb_port_file") as mock_port_file:
                # No port file = not running
                mock_port_file.return_value = tmp_path / "nonexistent.port"
                result = check_knowledge_server(project)
                assert result is False

    def test_list_knowledge_servers_uses_runtime_dir(self):
        """list_knowledge_servers should use runtime directory."""
        from klean.cli import list_knowledge_servers

        with patch("klean.cli.get_runtime_dir") as mock_runtime:
            mock_dir = MagicMock()
            mock_dir.glob.return_value = []
            mock_runtime.return_value = mock_dir

            result = list_knowledge_servers()
            assert result == []
            mock_dir.glob.assert_called_with("kb-*.port")


class TestStartLiteLLM:
    """Tests for start_litellm function."""

    def test_uses_spawn_background(self, tmp_path):
        """start_litellm should use spawn_background."""
        from klean.cli import start_litellm

        # Mock all dependencies
        with patch("klean.cli.check_litellm", return_value=False):
            with patch("klean.cli.CONFIG_DIR", tmp_path):
                # Create required files
                (tmp_path / "config.yaml").write_text("model_list: []")
                (tmp_path / ".env").write_text("OPENAI_API_KEY=test")

                with patch("klean.cli.get_litellm_binary", return_value=Path("/usr/bin/litellm")):
                    with patch("klean.cli.ensure_klean_dirs"):
                        with patch("klean.cli.LOGS_DIR", tmp_path):
                            with patch("klean.cli.get_litellm_pid_file", return_value=tmp_path / "litellm.pid"):
                                with patch("klean.cli.spawn_background", return_value=12345) as mock_spawn:
                                    with patch("klean.cli.is_process_running", return_value=True):
                                        result = start_litellm(background=True, port=4000)

                                        # Should have called spawn_background
                                        assert mock_spawn.called
                                        # Should return True
                                        assert result is True


class TestStopLiteLLM:
    """Tests for stop_litellm function."""

    def test_uses_kill_process_tree(self, tmp_path):
        """stop_litellm should use kill_process_tree."""
        from klean.cli import stop_litellm

        pid_file = tmp_path / "litellm.pid"
        pid_file.write_text("12345")

        with patch("klean.cli.get_litellm_pid_file", return_value=pid_file):
            with patch("klean.cli.is_process_running", return_value=True):
                with patch("klean.cli.kill_process_tree") as mock_kill:
                    result = stop_litellm()

                    mock_kill.assert_called_once_with(12345, timeout=5.0)
                    assert result is True


class TestStopKnowledgeServer:
    """Tests for stop_knowledge_server function."""

    def test_uses_kill_process_tree(self, tmp_path):
        """stop_knowledge_server should use kill_process_tree."""
        from klean.cli import stop_knowledge_server

        project = tmp_path / "project"
        project.mkdir()

        pid_file = tmp_path / "kb.pid"
        pid_file.write_text("54321")

        port_file = tmp_path / "kb.port"
        port_file.write_text("14000")

        with patch("klean.cli.find_project_root", return_value=project):
            with patch("klean.cli.get_kb_pid_file", return_value=pid_file):
                with patch("klean.cli.get_kb_port_file", return_value=port_file):
                    with patch("klean.cli.is_process_running", return_value=True):
                        with patch("klean.cli.kill_process_tree") as mock_kill:
                            with patch("klean.cli.cleanup_stale_files"):
                                with patch("klean.cli.check_knowledge_server", return_value=False):
                                    result = stop_knowledge_server(project)

                                    mock_kill.assert_called_once_with(54321, timeout=5.0)
                                    assert result is True


class TestStartKnowledgeServer:
    """Tests for start_knowledge_server function."""

    def test_uses_spawn_background(self, tmp_path):
        """start_knowledge_server should use spawn_background."""
        from klean.cli import start_knowledge_server

        project = tmp_path / "project"
        project.mkdir()
        (project / ".knowledge-db").mkdir()

        with patch("klean.cli.find_project_root", return_value=project):
            with patch("klean.cli.check_knowledge_server", return_value=False):
                with patch("klean.cli.CLAUDE_DIR", tmp_path):
                    # Create fake script
                    scripts_dir = tmp_path / "scripts"
                    scripts_dir.mkdir()
                    (scripts_dir / "knowledge-server.py").write_text("# fake")

                    with patch("klean.cli.VENV_DIR", tmp_path / "venv"):
                        with patch("klean.cli.cleanup_stale_files"):
                            with patch("klean.cli.ensure_klean_dirs"):
                                with patch("klean.cli.LOGS_DIR", tmp_path):
                                    with patch("klean.cli.spawn_background", return_value=99999) as mock_spawn:
                                        with patch("klean.cli.get_kb_port_file") as mock_port:
                                            mock_port.return_value = tmp_path / "kb.port"
                                            with patch("klean.cli.is_process_running", return_value=True):
                                                result = start_knowledge_server(project, wait=False)

                                                assert mock_spawn.called
                                                assert result is True


# =============================================================================
# Merge Hooks Tests
# =============================================================================


class TestMergeKleanHooks:
    """Tests for merge_klean_hooks function."""

    def test_adds_hooks_to_empty_settings(self):
        """Should add all hooks to empty settings."""
        from klean.cli import merge_klean_hooks

        settings = {}
        updated, added = merge_klean_hooks(settings)

        assert "hooks" in updated
        assert len(added) > 0
        assert "SessionStart" in updated["hooks"]
        assert "UserPromptSubmit" in updated["hooks"]
        assert "PostToolUse" in updated["hooks"]

    def test_preserves_existing_hooks(self):
        """Should preserve existing user hooks."""
        from klean.cli import merge_klean_hooks

        settings = {
            "hooks": {
                "SessionStart": [
                    {"matcher": "custom", "hooks": [{"type": "command", "command": "my-hook"}]}
                ]
            }
        }

        updated, _added = merge_klean_hooks(settings)

        # Should still have custom hook
        session_hooks = updated["hooks"]["SessionStart"]
        custom_found = False
        for h in session_hooks:
            if h.get("matcher") == "custom":
                custom_found = True
                break
        assert custom_found


# =============================================================================
# CLI Command Tests
# =============================================================================


class TestCLICommands:
    """Tests for CLI commands via CliRunner."""

    def test_status_command_runs(self):
        """Status command should run without errors."""
        from klean.cli import main

        runner = CliRunner()
        with patch("klean.cli.check_litellm", return_value=False):
            with patch("klean.cli.list_knowledge_servers", return_value=[]):
                with patch("klean.cli.check_phoenix", return_value=False):
                    result = runner.invoke(main, ["status"])
                    # Should not crash (exit code 0 or 1 is OK)
                    assert result.exit_code in [0, 1]

    def test_help_command(self):
        """Help command should work."""
        from klean.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "K-LEAN" in result.output or "kln" in result.output
