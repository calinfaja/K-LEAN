"""Run tests tool for Agent SDK droids.

This tool allows droids to execute test suites and analyze results.
"""

import subprocess
from typing import Any, Optional

from ..tools import tool


@tool("run_tests", "Run tests and return results")
async def run_tests(
    path: str = "tests",
    pattern: Optional[str] = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Execute tests and return structured results.

    This tool enables droids to run test suites during analysis,
    understanding test coverage, identifying failing tests, etc.

    Args:
        path: Path to test directory or file (default: "tests")
        pattern: Optional pattern to filter tests (e.g., "test_security")
        verbose: Whether to include verbose output (default: False)

    Returns:
        Dict with test results:
            - success: Whether tests executed successfully
            - passed: Number of passing tests
            - failed: Number of failing tests
            - skipped: Number of skipped tests
            - total: Total tests run
            - details: Full test output
            - error: Error message if execution failed

    Example:
        result = await run_tests(
            path="tests",
            pattern="test_security"
        )
        if result["failed"] > 0:
            print(f"Found {result['failed']} failing security tests")
    """
    try:
        # Build pytest command
        cmd = ["pytest", path]

        if pattern:
            cmd.extend(["-k", pattern])

        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Parse pytest output for summary
        output = result.stdout + result.stderr

        # Extract counts from pytest output
        import re

        passed = len(re.findall(r" PASSED", output))
        failed = len(re.findall(r" FAILED", output))
        skipped = len(re.findall(r" SKIPPED", output))

        return {
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "details": output[-2000:] if len(output) > 2000 else output,  # Last 2000 chars
            "returncode": result.returncode,
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "pytest not found. Install with: pip install pytest",
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timeout (60 seconds)",
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
        }
