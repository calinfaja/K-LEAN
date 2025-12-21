"""Base classes for K-LEAN droids.

This module provides abstract base classes and implementations for both
bash-based and Agent SDK-based droids, enabling a consistent interface
for different types of code analysis agents.
"""

import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseDroid(ABC):
    """Abstract base class for all droids.

    A droid is an autonomous agent that performs code analysis tasks.
    Droids can be implemented using bash scripts or the Agent SDK.
    """

    def __init__(self, name: str, description: str, droid_type: str = "bash"):
        """Initialize a droid.

        Args:
            name: Unique identifier for this droid
            description: Human-readable description of what the droid does
            droid_type: Type of droid ("bash" or "sdk")
        """
        self.name = name
        self.description = description
        self.droid_type = droid_type

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute the droid and return results.

        Returns:
            Dict containing:
                - output: str (the analysis results)
                - format: str ("markdown" or "json")
                - droid: str (the droid name)
                - [other optional fields depending on implementation]
        """
        pass

    @abstractmethod
    async def get_help(self) -> str:
        """Return help text for this droid."""
        pass


class BashDroid(BaseDroid):
    """Wrapper for bash-based droids (backward compatible).

    This class wraps bash scripts to provide a consistent interface with
    SDK-based droids. It enables backward compatibility with existing
    bash-based droid implementations.
    """

    def __init__(self, name: str, script_path: str, description: str):
        """Initialize a bash droid.

        Args:
            name: Unique identifier for this droid
            script_path: Path to the bash script
            description: Human-readable description
        """
        super().__init__(name, description, droid_type="bash")
        self.script_path = Path(script_path)

    async def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute bash script and return markdown output.

        Args:
            *args: Positional arguments to pass to the script
            **kwargs: Keyword arguments (ignored for bash execution)

        Returns:
            Dict with output, format, returncode, and droid name
        """
        try:
            cmd = [str(self.script_path)] + list(args)
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )

            return {
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "format": "markdown",
                "returncode": result.returncode,
                "droid": self.name,
            }
        except subprocess.TimeoutExpired:
            return {
                "output": f"Error: Script timeout after 300 seconds",
                "format": "markdown",
                "returncode": 124,
                "droid": self.name,
            }
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "format": "markdown",
                "returncode": 1,
                "droid": self.name,
            }

    async def get_help(self) -> str:
        """Return description as help text."""
        return self.description


class SDKDroid(BaseDroid):
    """Base class for Agent SDK-based droids.

    This class provides the foundation for droids that use the Claude Agent SDK
    for more advanced analysis capabilities, including:
    - Multi-turn conversations with Claude
    - Session context preservation
    - Custom tool integration
    - Structured JSON output
    """

    def __init__(
        self,
        name: str,
        description: str,
        model: str = "claude-opus-4-5-20251101",
    ):
        """Initialize an SDK droid.

        Args:
            name: Unique identifier for this droid
            description: Human-readable description
            model: Claude model to use (default: Opus 4.5)
        """
        super().__init__(name, description, droid_type="sdk")
        self.model = model
        self.client = None

    async def _initialize_client(self):
        """Lazy-initialize Anthropic client.

        This method is called before the first execution to initialize
        the client. It can connect to either the native Anthropic API
        or a LiteLLM proxy at localhost:4000.

        Raises:
            RuntimeError: If Agent SDK is not installed
            ConnectionError: If unable to connect to Claude
        """
        if self.client is not None:
            return

        try:
            # Import here to avoid requiring Agent SDK if not needed
            from anthropic import Anthropic

            # Check if LiteLLM proxy is available
            try:
                import urllib.request

                req = urllib.request.Request("http://localhost:4000/models")
                urllib.request.urlopen(req, timeout=2)
                # LiteLLM is available, use it
                self.client = Anthropic(
                    base_url="http://localhost:4000",
                    api_key="dummy",  # LiteLLM doesn't validate
                )
            except Exception:
                # Fall back to native Anthropic API
                self.client = Anthropic()

        except ImportError:
            raise RuntimeError(
                "Agent SDK not installed. "
                "Install with: pipx install k-lean[agent-sdk]"
            )

    async def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute via Agent SDK (subclasses override with specific logic).

        Subclasses must implement this method with their specific
        multi-turn analysis logic.

        Raises:
            NotImplementedError: This method must be overridden
        """
        raise NotImplementedError(
            f"Droid '{self.name}' must implement execute() method"
        )

    async def get_help(self) -> str:
        """Return description as help text."""
        return self.description
