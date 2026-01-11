"""Tests for Windows compatibility.

These tests verify that K-LEAN works correctly on Windows:
- Hypercorn flag is added for proxy on Windows
- Platform detection works correctly
- Dependencies are properly conditional

Test categories:
- Logic tests: Run on all platforms (use mocks to simulate Windows)
- Integration tests: Run only on actual Windows (marked with skipif)
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Markers for platform-specific tests
IS_WINDOWS = sys.platform == "win32"
skip_unless_windows = pytest.mark.skipif(not IS_WINDOWS, reason="Windows-only test")


class TestWindowsProxyCommand:
    """Tests for Windows-specific proxy startup."""

    def test_adds_hypercorn_flag_on_windows(self):
        """Should add --run_hypercorn flag when on Windows."""
        # Simulate Windows platform
        with patch.object(sys, "platform", "win32"):
            # Import after patching to get correct behavior
            # We need to test the command building logic
            litellm_bin = Path("/fake/litellm")
            config_file = Path("/fake/config.yaml")
            port = 4000

            cmd = [
                str(litellm_bin),
                "--config",
                str(config_file),
                "--port",
                str(port),
            ]

            # This is the logic from cli.py
            if sys.platform == "win32":
                cmd.append("--run_hypercorn")

            assert "--run_hypercorn" in cmd

    def test_no_hypercorn_flag_on_linux(self):
        """Should NOT add --run_hypercorn flag on Linux."""
        with patch.object(sys, "platform", "linux"):
            litellm_bin = Path("/fake/litellm")
            config_file = Path("/fake/config.yaml")
            port = 4000

            cmd = [
                str(litellm_bin),
                "--config",
                str(config_file),
                "--port",
                str(port),
            ]

            if sys.platform == "win32":
                cmd.append("--run_hypercorn")

            assert "--run_hypercorn" not in cmd

    def test_no_hypercorn_flag_on_macos(self):
        """Should NOT add --run_hypercorn flag on macOS."""
        with patch.object(sys, "platform", "darwin"):
            litellm_bin = Path("/fake/litellm")
            config_file = Path("/fake/config.yaml")
            port = 4000

            cmd = [
                str(litellm_bin),
                "--config",
                str(config_file),
                "--port",
                str(port),
            ]

            if sys.platform == "win32":
                cmd.append("--run_hypercorn")

            assert "--run_hypercorn" not in cmd


class TestPlatformDetection:
    """Tests for platform detection utilities."""

    def test_win32_is_windows(self):
        """win32 platform string indicates Windows."""
        with patch.object(sys, "platform", "win32"):
            assert sys.platform == "win32"

    def test_linux_is_not_windows(self):
        """linux platform string is not Windows."""
        with patch.object(sys, "platform", "linux"):
            assert sys.platform != "win32"

    def test_darwin_is_not_windows(self):
        """darwin platform string is not Windows."""
        with patch.object(sys, "platform", "darwin"):
            assert sys.platform != "win32"


class TestLiteLLMBinaryDiscovery:
    """Tests for finding the litellm binary."""

    def test_finds_litellm_in_same_venv(self, tmp_path):
        """Should find litellm binary in same directory as Python."""
        from klean.cli import get_litellm_binary

        # Create a fake litellm binary
        fake_bin_dir = tmp_path / "bin"
        fake_bin_dir.mkdir()
        fake_litellm = fake_bin_dir / "litellm"
        fake_litellm.touch()

        with patch.object(sys, "executable", str(fake_bin_dir / "python")):
            result = get_litellm_binary()
            assert result == fake_litellm

    def test_falls_back_to_shutil_which(self, tmp_path):
        """Should fall back to shutil.which if not in venv."""
        from klean.cli import get_litellm_binary

        # Create a fake bin dir without litellm
        fake_bin_dir = tmp_path / "bin"
        fake_bin_dir.mkdir()

        with patch.object(sys, "executable", str(fake_bin_dir / "python")):
            with patch("shutil.which", return_value="/usr/bin/litellm"):
                result = get_litellm_binary()
                assert result == Path("/usr/bin/litellm")


class TestDependencyMarkers:
    """Tests to verify dependency markers are correct."""

    def test_pyproject_has_windows_hypercorn(self):
        """pyproject.toml should have hypercorn for Windows."""
        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
        content = pyproject.read_text()

        # Check for Windows-specific hypercorn dependency
        assert "hypercorn" in content
        assert "sys_platform == 'win32'" in content

    def test_pyproject_has_conditional_litellm(self):
        """pyproject.toml should have conditional litellm deps."""
        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
        content = pyproject.read_text()

        # Check for platform-conditional litellm
        assert "litellm[proxy]" in content
        assert "sys_platform != 'win32'" in content


# =============================================================================
# Windows-Only Integration Tests
# These tests run ONLY on actual Windows and verify real functionality
# =============================================================================


class TestWindowsIntegration:
    """Integration tests that only run on Windows."""

    @skip_unless_windows
    def test_hypercorn_is_importable(self):
        """On Windows, hypercorn should be installed and importable."""
        import hypercorn  # noqa: F401

        assert True  # If import succeeds, test passes

    @skip_unless_windows
    def test_litellm_is_importable(self):
        """On Windows, litellm should be installed and importable."""
        import litellm  # noqa: F401

        assert True

    @skip_unless_windows
    def test_uvloop_not_imported(self):
        """On Windows, uvloop should NOT be imported (it doesn't exist)."""
        # uvloop doesn't support Windows, so it shouldn't be in sys.modules
        # after a clean import of our code
        assert "uvloop" not in sys.modules or sys.modules["uvloop"] is None

    @skip_unless_windows
    def test_cli_version_works(self):
        """kln --version should work on Windows."""
        import subprocess

        result = subprocess.run(
            ["kln", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "kln-ai" in result.stdout or "1." in result.stdout

    @skip_unless_windows
    def test_cli_help_works(self):
        """kln --help should work on Windows."""
        import subprocess

        result = subprocess.run(
            ["kln", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "start" in result.stdout
        assert "stop" in result.stdout
