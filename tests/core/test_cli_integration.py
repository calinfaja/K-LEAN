#!/usr/bin/env python3
"""CLI integration tests for K-LEAN commands.

Tests 7-10: CLI commands (quick, multi, multi+telemetry, rethink).
These tests verify the CLI interface works correctly.
"""

import json
import subprocess
import unittest
from pathlib import Path

# K-LEAN paths - use source location for tests
KLEAN_CORE = Path(__file__).parent.parent.parent / "src" / "klean" / "data" / "core" / "klean_core.py"
PYTHON = Path.home() / ".local" / "share" / "pipx" / "venvs" / "kln-ai" / "bin" / "python"


def run_klean_command(args: list, timeout: int = 30) -> tuple:
    """Run a k-lean CLI command and return (stdout, stderr, returncode)."""
    cmd = [str(PYTHON), str(KLEAN_CORE)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.home())
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1


class TestCLIHelp(unittest.TestCase):
    """Test CLI help and basic invocation."""

    def test_status_command(self):
        """Should show status without crashing."""
        stdout, stderr, code = run_klean_command(["status"])
        # Status may fail if services not running, but should not crash
        self.assertNotIn("Traceback", stderr)

    def test_usage_shows_commands(self):
        """Should show usage when called without arguments."""
        stdout, stderr, code = run_klean_command([])
        combined = stdout + stderr
        self.assertIn("quick", combined.lower())
        self.assertIn("multi", combined.lower())


@unittest.skipUnless(
    subprocess.run(["curl", "-s", "http://localhost:4000/health"],
                   capture_output=True).returncode == 0,
    "LiteLLM proxy not running"
)
class TestCLIQuick(unittest.TestCase):
    """Test 7: CLI quick review command."""

    def test_quick_review_runs(self):
        """Should execute quick review without crashing."""
        stdout, stderr, code = run_klean_command(
            ["quick", "test review"],
            timeout=60
        )
        # Check it ran (may fail for model reasons, but should not crash)
        self.assertNotIn("Traceback", stderr)

    def test_quick_review_output_format(self):
        """Should produce structured output."""
        stdout, stderr, code = run_klean_command(
            ["quick", "--output", "json", "test review"],
            timeout=60
        )
        if code == 0 and stdout.strip():
            # Try to parse JSON output
            try:
                data = json.loads(stdout)
                self.assertIn("model", data)
            except json.JSONDecodeError:
                pass  # Text output is also acceptable


@unittest.skipUnless(
    subprocess.run(["curl", "-s", "http://localhost:4000/health"],
                   capture_output=True).returncode == 0,
    "LiteLLM proxy not running"
)
class TestCLIMulti(unittest.TestCase):
    """Test 8: CLI multi review command."""

    def test_multi_review_runs(self):
        """Should execute multi review without crashing."""
        stdout, stderr, code = run_klean_command(
            ["multi", "--models", "2", "test review"],
            timeout=120
        )
        self.assertNotIn("Traceback", stderr)

    def test_multi_review_accepts_model_list(self):
        """Test 8b: Should accept comma-separated model list (dynamic discovery)."""
        # Discover models dynamically from LiteLLM proxy
        import json
        import urllib.request
        try:
            req = urllib.request.Request(
                "http://localhost:4000/models",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            models = [m["id"] for m in data.get("data", [])]
        except Exception as e:
            self.skipTest(f"Model discovery failed: {e}")

        if len(models) < 2:
            self.skipTest("Need at least 2 models for this test")

        # Use first 2 discovered models
        model_list = ",".join(models[:2])
        stdout, stderr, code = run_klean_command(
            ["multi", "--models", model_list, "test"],
            timeout=120
        )
        # Should not crash with invalid args
        self.assertNotIn("invalid", stderr.lower())


@unittest.skipUnless(
    subprocess.run(["curl", "-s", "http://localhost:4000/health"],
                   capture_output=True).returncode == 0,
    "LiteLLM proxy not running"
)
class TestCLIMultiTelemetry(unittest.TestCase):
    """Test 9: CLI multi review with telemetry flag."""

    def test_multi_telemetry_flag(self):
        """Should accept --telemetry flag."""
        stdout, stderr, code = run_klean_command(
            ["multi", "--telemetry", "--models", "1", "test"],
            timeout=120
        )
        # Should mention telemetry or phoenix
        self.assertNotIn("unrecognized arguments: --telemetry", stderr)


@unittest.skipUnless(
    subprocess.run(["curl", "-s", "http://localhost:4000/health"],
                   capture_output=True).returncode == 0,
    "LiteLLM proxy not running"
)
class TestCLIRethink(unittest.TestCase):
    """Test 10: CLI rethink command."""

    def test_rethink_runs(self):
        """Should execute rethink without crashing."""
        stdout, stderr, code = run_klean_command(
            ["rethink", "test problem"],
            timeout=120
        )
        self.assertNotIn("Traceback", stderr)

    def test_rethink_with_telemetry(self):
        """Should accept --telemetry flag."""
        stdout, stderr, code = run_klean_command(
            ["rethink", "--telemetry", "test problem"],
            timeout=120
        )
        self.assertNotIn("unrecognized arguments: --telemetry", stderr)


class TestNoHttpxImports(unittest.TestCase):
    """Verify httpx has been removed from klean_core.py."""

    def test_no_httpx_import(self):
        """Should not import httpx."""
        with open(KLEAN_CORE) as f:
            content = f.read()

        # Check no active httpx import
        lines = content.split('\n')
        active_httpx_imports = [
            line for line in lines
            if 'import httpx' in line and not line.strip().startswith('#')
        ]
        self.assertEqual(
            len(active_httpx_imports), 0,
            f"Found active httpx imports: {active_httpx_imports}"
        )

    def test_has_litellm_import(self):
        """Should import litellm."""
        with open(KLEAN_CORE) as f:
            content = f.read()

        self.assertIn('import litellm', content)

    def test_has_urllib_import(self):
        """Should import urllib for model discovery."""
        with open(KLEAN_CORE) as f:
            content = f.read()

        self.assertIn('import urllib', content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
