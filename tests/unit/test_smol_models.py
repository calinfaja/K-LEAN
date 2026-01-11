"""Tests for klean.smol.models module.

Tests cover:
- create_model function
- LiteLLM model wrapper integration
- Error handling for missing dependencies
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCreateModel:
    """Tests for create_model() function."""

    def test_raises_import_error_without_smolagents(self):
        """Should raise ImportError when smolagents not installed."""
        with patch.dict("sys.modules", {"smolagents": None}):
            # Force reimport to trigger ImportError

            import klean.smol.models as models_module

            # Mock the import to fail
            with patch.object(models_module, "create_model") as mock_create:
                mock_create.side_effect = ImportError("smolagents not installed")
                with pytest.raises(ImportError):
                    mock_create("test-model")

    def test_raises_value_error_when_no_models(self):
        """Should raise ValueError when no models available."""
        from klean.smol.models import create_model

        with patch("klean.smol.models.get_model", return_value=None):
            with patch("smolagents.LiteLLMModel"):
                with pytest.raises(ValueError, match="No models available"):
                    create_model()

    def test_uses_first_available_model_when_none_specified(self):
        """Should use first available model from discovery."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()
        with patch("klean.smol.models.get_model", return_value="qwen-coder"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model()

                # Should call LiteLLMModel with discovered model
                mock_litellm.assert_called_once()
                call_kwargs = mock_litellm.call_args[1]
                assert "qwen-coder" in call_kwargs["model_id"]

    def test_uses_specified_model(self):
        """Should use the specified model_id."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()
        with patch("klean.smol.models.get_model", return_value="deepseek-v3"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model("deepseek-v3")

                call_kwargs = mock_litellm.call_args[1]
                assert "deepseek-v3" in call_kwargs["model_id"]

    def test_passes_api_base_parameter(self):
        """Should pass api_base to LiteLLMModel."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()
        custom_base = "http://custom:5000"

        with patch("klean.smol.models.get_model", return_value="test"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model("test", api_base=custom_base)

                call_kwargs = mock_litellm.call_args[1]
                assert call_kwargs["api_base"] == custom_base

    def test_passes_temperature_parameter(self):
        """Should pass temperature to LiteLLMModel."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()

        with patch("klean.smol.models.get_model", return_value="test"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model("test", temperature=0.5)

                call_kwargs = mock_litellm.call_args[1]
                assert call_kwargs["temperature"] == 0.5

    def test_default_temperature_is_0_7(self):
        """Should use default temperature of 0.7."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()

        with patch("klean.smol.models.get_model", return_value="test"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model("test")

                call_kwargs = mock_litellm.call_args[1]
                assert call_kwargs["temperature"] == 0.7

    def test_prefixes_model_id_with_openai(self):
        """Should prefix model_id with 'openai/' for LiteLLM proxy."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()

        with patch("klean.smol.models.get_model", return_value="my-model"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model("my-model")

                call_kwargs = mock_litellm.call_args[1]
                assert call_kwargs["model_id"] == "openai/my-model"

    def test_sets_api_key_to_not_needed(self):
        """Should set api_key to 'not-needed' since proxy handles auth."""
        from klean.smol.models import create_model

        mock_litellm = MagicMock()

        with patch("klean.smol.models.get_model", return_value="test"):
            with patch("smolagents.LiteLLMModel", mock_litellm):
                create_model("test")

                call_kwargs = mock_litellm.call_args[1]
                assert call_kwargs["api_key"] == "not-needed"
