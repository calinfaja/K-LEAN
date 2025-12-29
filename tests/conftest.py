"""Shared pytest fixtures for K-LEAN tests.

Provides reusable fixtures for:
- Temporary project directories
- Mock HTTP responses
- Mock subprocess results
- Sample agent files

IMPORTANT: These fixtures mock EXTERNAL dependencies only.
The code under test should execute normally.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional


# =============================================================================
# Temporary File System Fixtures
# =============================================================================

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory with .git and CLAUDE.md.

    Returns:
        Path to temporary project root
    """
    project = tmp_path / "test-project"
    project.mkdir()

    # Create .git directory (marks as git repo)
    (project / ".git").mkdir()

    # Create CLAUDE.md
    (project / "CLAUDE.md").write_text("""# Test Project

## Commands
- `/test` - Run tests

## Architecture
Simple test project for unit tests.
""")

    return project


@pytest.fixture
def temp_agents_dir(tmp_path):
    """Create temporary agents directory with sample agents.

    Returns:
        Path to agents directory
    """
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Create sample agent with full YAML frontmatter
    (agents_dir / "security-auditor.md").write_text("""---
name: security-auditor
description: Security audit specialist
model: deepseek-r1
tools:
  - knowledge_search
  - read_file
  - grep
---

# Security Auditor

You are a security auditor. Analyze code for vulnerabilities.

## Focus Areas
- SQL injection
- XSS
- Authentication flaws
""")

    # Agent with minimal frontmatter
    (agents_dir / "simple-reviewer.md").write_text("""---
name: simple-reviewer
description: Simple code reviewer
---

You review code for quality issues.
""")

    # Agent with no frontmatter
    (agents_dir / "no-frontmatter.md").write_text("""# Basic Agent

This agent has no YAML frontmatter.
It should use defaults.
""")

    # Agent with inherit model
    (agents_dir / "inherit-model.md").write_text("""---
name: inherit-agent
description: Uses inherited model
model: inherit
tools: ["read_file"]
---

Inherits model from LiteLLM discovery.
""")

    return agents_dir


@pytest.fixture
def temp_knowledge_db(tmp_path):
    """Create temporary knowledge DB directory structure.

    Returns:
        Path to .knowledge-db directory
    """
    kb_dir = tmp_path / ".knowledge-db"
    kb_dir.mkdir()

    # Create index marker (txtai uses this)
    (kb_dir / "index").mkdir()

    return kb_dir


# =============================================================================
# HTTP/Network Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_litellm_models():
    """Standard LiteLLM /models response.

    Returns:
        Dict matching LiteLLM API format
    """
    return {
        "data": [
            {"id": "qwen3-coder", "object": "model"},
            {"id": "deepseek-r1", "object": "model"},
            {"id": "kimi-k2", "object": "model"},
            {"id": "glm-4.6-thinking", "object": "model"},
        ]
    }


@pytest.fixture
def mock_httpx_get(mock_litellm_models):
    """Mock httpx.get for LiteLLM model discovery.

    Returns:
        Configured MagicMock for httpx.get
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_litellm_models
    mock_response.raise_for_status = MagicMock()

    mock_get = MagicMock(return_value=mock_response)
    return mock_get


@pytest.fixture
def mock_httpx_get_failure():
    """Mock httpx.get that raises connection error.

    Returns:
        MagicMock that raises exception
    """
    import httpx
    mock_get = MagicMock(side_effect=httpx.ConnectError("Connection refused"))
    return mock_get


# =============================================================================
# Subprocess Mock Fixtures
# =============================================================================

@dataclass
class MockCompletedProcess:
    """Mock subprocess.CompletedProcess for git commands."""
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


@pytest.fixture
def mock_git_toplevel(temp_project):
    """Mock subprocess.run for git rev-parse --show-toplevel.

    Returns:
        Function to create mock that returns project path
    """
    def create_mock(returncode=0, path=None):
        result = MockCompletedProcess(
            returncode=returncode,
            stdout=str(path or temp_project) + "\n",
            stderr=""
        )
        return MagicMock(return_value=result)

    return create_mock


@pytest.fixture
def mock_git_branch():
    """Mock subprocess.run for git branch --show-current.

    Returns:
        Function to create mock with specified branch
    """
    def create_mock(branch="main"):
        result = MockCompletedProcess(
            returncode=0,
            stdout=f"{branch}\n",
            stderr=""
        )
        return MagicMock(return_value=result)

    return create_mock


@pytest.fixture
def mock_git_status():
    """Mock subprocess.run for git status --short.

    Returns:
        Function to create mock with specified status
    """
    def create_mock(files_changed=0):
        if files_changed == 0:
            stdout = ""
        else:
            lines = [f" M file{i}.py" for i in range(files_changed)]
            stdout = "\n".join(lines)

        result = MockCompletedProcess(
            returncode=0,
            stdout=stdout,
            stderr=""
        )
        return MagicMock(return_value=result)

    return create_mock


# =============================================================================
# Agent Memory Mock Fixtures (for citation validation)
# =============================================================================

@pytest.fixture
def mock_agent_memory():
    """Mock smolagents memory with tool outputs containing file:line refs.

    Returns:
        Mock memory object with get_full_steps()
    """
    class MockStep:
        def __init__(self, observations):
            self.observations = observations

    class MockMemory:
        def __init__(self, outputs):
            self._outputs = outputs

        def get_full_steps(self):
            return [MockStep(o) for o in self._outputs]

    return MockMemory([
        "Found issue at src/auth.py:42: password = input()",
        "Vulnerability in src/login.py:15: SQL injection risk",
        "Pattern at utils/helper.py:100-110: unsafe deserialization",
    ])


@pytest.fixture
def mock_empty_agent_memory():
    """Mock agent memory with no tool outputs.

    Returns:
        Mock memory with empty steps
    """
    class MockMemory:
        def get_full_steps(self):
            return []

    return MockMemory()


# =============================================================================
# Time Control Fixtures
# =============================================================================

@pytest.fixture
def frozen_time():
    """Fixture to control time.time() for cache TTL testing.

    Returns:
        Function to set the current time
    """
    current_time = [time.time()]

    def set_time(t):
        current_time[0] = t

    def get_time():
        return current_time[0]

    return type('FrozenTime', (), {
        'set': set_time,
        'get': get_time,
        'advance': lambda seconds: set_time(current_time[0] + seconds)
    })()


# =============================================================================
# Assertion Helpers
# =============================================================================

def assert_mock_called_with_url(mock, expected_url_part):
    """Assert mock was called with URL containing expected part.

    Raises AssertionError with helpful message if not found.
    """
    calls = mock.call_args_list
    urls = [str(call) for call in calls]

    for call in calls:
        if expected_url_part in str(call):
            return

    raise AssertionError(
        f"Expected URL containing '{expected_url_part}' not found in calls: {urls}"
    )


def assert_file_contains(path: Path, expected: str):
    """Assert file exists and contains expected string."""
    assert path.exists(), f"File does not exist: {path}"
    content = path.read_text()
    assert expected in content, f"Expected '{expected}' not found in {path}"
