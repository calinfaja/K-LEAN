#!/usr/bin/env python3
"""Unit tests for LLMClient class.

Tests the core LLMClient functionality:
- Model discovery via urllib
- Model prefix handling
- Sync/async completion
- Telemetry configuration
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from klean_core import LLMClient


class TestModelDiscovery(unittest.TestCase):
    """Test 1: Model Discovery via urllib."""

    @patch('urllib.request.urlopen')
    def test_discover_models_success(self, mock_urlopen):
        """Should parse models from LiteLLM /models endpoint."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": [
                {"id": "qwen3-coder"},
                {"id": "deepseek-r1"},
                {"id": "kimi-k2"}
            ]
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = lambda s, *args: None
        mock_urlopen.return_value = mock_response

        client = LLMClient()
        models = client.discover_models()

        self.assertEqual(models, ["qwen3-coder", "deepseek-r1", "kimi-k2"])
        mock_urlopen.assert_called_once()

    @patch('urllib.request.urlopen')
    def test_discover_models_empty(self, mock_urlopen):
        """Should handle empty model list."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"data": []}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = lambda s, *args: None
        mock_urlopen.return_value = mock_response

        client = LLMClient()
        models = client.discover_models()

        self.assertEqual(models, [])

    @patch('urllib.request.urlopen')
    def test_discover_models_network_error(self, mock_urlopen):
        """Should return empty list on network error."""
        mock_urlopen.side_effect = Exception("Connection refused")

        client = LLMClient()
        models = client.discover_models()

        self.assertEqual(models, [])


class TestModelPrefix(unittest.TestCase):
    """Test 2: Model prefix handling for proxy routing."""

    def test_adds_openai_prefix(self):
        """Should add openai/ prefix for proxy routing."""
        client = LLMClient()
        result = client._proxy_model("qwen3-coder")
        self.assertEqual(result, "openai/qwen3-coder")

    def test_preserves_existing_prefix(self):
        """Should not double-prefix models."""
        client = LLMClient()
        result = client._proxy_model("openai/gpt-4")
        self.assertEqual(result, "openai/gpt-4")

    def test_handles_empty_model(self):
        """Should handle empty model name."""
        client = LLMClient()
        result = client._proxy_model("")
        self.assertEqual(result, "openai/")


class TestSyncCompletion(unittest.TestCase):
    """Test 3: Sync completion via litellm."""

    @patch('litellm.completion')
    def test_completion_returns_content(self, mock_completion):
        """Should extract content from litellm response."""
        # Mock litellm response
        mock_message = MagicMock()
        mock_message.content = "Test response content"
        mock_message.reasoning_content = None

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.__iter__ = lambda s: iter([("prompt_tokens", 10), ("completion_tokens", 20)])
        mock_response.model = "qwen3-coder"

        mock_completion.return_value = mock_response

        client = LLMClient()
        result = client.completion("qwen3-coder", [{"role": "user", "content": "Hello"}])

        self.assertEqual(result["content"], "Test response content")
        self.assertIn("model", result)

    @patch('litellm.completion')
    def test_completion_uses_proxy_model(self, mock_completion):
        """Should add openai/ prefix when calling litellm."""
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.model = "openai/test-model"
        mock_completion.return_value = mock_response

        client = LLMClient()
        client.completion("test-model", [{"role": "user", "content": "Hi"}])

        # Check that openai/ prefix was added
        call_args = mock_completion.call_args
        self.assertTrue(call_args.kwargs["model"].startswith("openai/"))


class TestReasoningContent(unittest.TestCase):
    """Test 5: Reasoning content extraction for thinking models."""

    @patch('litellm.completion')
    def test_extracts_reasoning_content(self, mock_completion):
        """Should extract reasoning_content from thinking models."""
        mock_message = MagicMock()
        mock_message.content = "Final answer"
        mock_message.reasoning_content = "Let me think step by step..."

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.model = "deepseek-r1"

        mock_completion.return_value = mock_response

        client = LLMClient()
        result = client.completion("deepseek-r1", [{"role": "user", "content": "Think about this"}])

        self.assertEqual(result["content"], "Final answer")
        self.assertEqual(result["reasoning_content"], "Let me think step by step...")

    @patch('litellm.completion')
    def test_handles_missing_reasoning_content(self, mock_completion):
        """Should handle models without reasoning_content."""
        mock_message = MagicMock(spec=['content'])  # No reasoning_content attribute
        mock_message.content = "Regular response"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.model = "gpt-4"

        mock_completion.return_value = mock_response

        client = LLMClient()
        result = client.completion("gpt-4", [{"role": "user", "content": "Hello"}])

        self.assertEqual(result["content"], "Regular response")
        self.assertIsNone(result["reasoning_content"])


class TestTelemetrySetup(unittest.TestCase):
    """Test 6: Telemetry configuration."""

    def test_enable_telemetry_sets_env(self):
        """Should set PHOENIX_PROJECT_NAME environment variable."""
        client = LLMClient()

        # Clear any existing value
        if "PHOENIX_PROJECT_NAME" in os.environ:
            del os.environ["PHOENIX_PROJECT_NAME"]

        client.enable_telemetry("test-project")

        self.assertEqual(os.environ.get("PHOENIX_PROJECT_NAME"), "test-project")

    @patch('litellm.callbacks', [])
    def test_enable_telemetry_sets_callback(self):
        """Should add arize_phoenix to litellm callbacks."""
        import litellm
        litellm.callbacks = []

        client = LLMClient()
        client.enable_telemetry("test-project")

        self.assertIn("arize_phoenix", litellm.callbacks)


if __name__ == "__main__":
    unittest.main(verbosity=2)
