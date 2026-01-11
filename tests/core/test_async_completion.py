#!/usr/bin/env python3
"""Async completion tests for LLMClient.

Test 4: Async completion via litellm.acompletion.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add klean data/core to path for klean_core module
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src",
        "klean",
        "data",
        "core",
    ),
)

from klean_core import LLMClient


def create_mock_response(content="Response", model="test-model", reasoning=None):
    """Helper to create a mock litellm response."""
    mock_message = MagicMock()
    mock_message.content = content
    mock_message.reasoning_content = reasoning

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = None
    mock_response.model = model
    return mock_response


class TestAsyncCompletion(unittest.TestCase):
    """Test 4: Async completion via litellm.acompletion."""

    @patch("klean_core.litellm.acompletion", new_callable=AsyncMock)
    def test_async_completion_returns_content(self, mock_acompletion):
        """Should extract content from async litellm response."""
        mock_acompletion.return_value = create_mock_response(
            content="Async response content", model="qwen3-coder"
        )

        client = LLMClient()

        # Run async method
        result = asyncio.run(
            client.acompletion("qwen3-coder", [{"role": "user", "content": "Hello async"}])
        )

        self.assertEqual(result["content"], "Async response content")
        self.assertIn("model", result)
        mock_acompletion.assert_called_once()

    @patch("klean_core.litellm.acompletion", new_callable=AsyncMock)
    def test_async_completion_uses_proxy_model(self, mock_acompletion):
        """Should add openai/ prefix for async calls."""
        mock_acompletion.return_value = create_mock_response(model="openai/test-model")

        client = LLMClient()
        asyncio.run(client.acompletion("test-model", [{"role": "user", "content": "Hi"}]))

        # Check that openai/ prefix was added
        call_args = mock_acompletion.call_args
        self.assertTrue(call_args.kwargs["model"].startswith("openai/"))

    @patch("klean_core.litellm.acompletion", new_callable=AsyncMock)
    def test_async_completion_extracts_reasoning(self, mock_acompletion):
        """Should extract reasoning_content from async thinking model response."""
        mock_acompletion.return_value = create_mock_response(
            content="Final answer", model="deepseek-r1", reasoning="Thinking process..."
        )

        client = LLMClient()
        result = asyncio.run(
            client.acompletion("deepseek-r1", [{"role": "user", "content": "Think about this"}])
        )

        self.assertEqual(result["content"], "Final answer")
        self.assertEqual(result["reasoning_content"], "Thinking process...")


class TestParallelAsyncCalls(unittest.TestCase):
    """Test parallel async completion for multi-model reviews."""

    @patch("klean_core.litellm.acompletion", new_callable=AsyncMock)
    def test_parallel_completions(self, mock_acompletion):
        """Should handle multiple parallel async calls."""
        call_count = 0

        async def mock_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            model = kwargs.get("model", "unknown")
            return create_mock_response(content=f"Response from {model}", model=model)

        mock_acompletion.side_effect = mock_side_effect

        client = LLMClient()

        async def run_parallel():
            tasks = [
                client.acompletion("model-1", [{"role": "user", "content": "Test 1"}]),
                client.acompletion("model-2", [{"role": "user", "content": "Test 2"}]),
                client.acompletion("model-3", [{"role": "user", "content": "Test 3"}]),
            ]
            return await asyncio.gather(*tasks)

        results = asyncio.run(run_parallel())

        self.assertEqual(len(results), 3)
        self.assertEqual(call_count, 3)
        # Verify each got a response
        for result in results:
            self.assertIn("content", result)
            self.assertIn("Response from", result["content"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
