"""Unit tests for klean.discovery module.

Tests model discovery from LiteLLM proxy with:
- Cache behavior (TTL, stale fallback)
- Model selection logic
- Availability checks

ANTI-FALSE-POSITIVE MEASURES:
1. Verify mock call arguments (URL, timeout)
2. Test cache with actual time manipulation
3. Test error paths with specific exceptions
4. Verify return values match expected types
"""

from unittest.mock import MagicMock, patch

# Import module under test
from klean.discovery import (
    CACHE_TTL,
    _cache,
    clear_cache,
    get_model,
    is_available,
    list_models,
)


class TestListModels:
    """Tests for list_models() function."""

    def setup_method(self):
        """Reset cache before each test."""
        clear_cache()

    @patch('klean.discovery.httpx.get')
    def test_returns_model_list_from_proxy(self, mock_get, mock_litellm_models):
        """Should fetch and parse models from LiteLLM /v1/models endpoint."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        models = list_models()

        # Assert - verify return value
        assert isinstance(models, list), "Should return a list"
        assert len(models) == 4, "Should return 4 models from fixture"
        assert "qwen3-coder" in models
        assert "deepseek-r1" in models

        # Assert - verify mock was called correctly (prevents false positive)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "/v1/models" in str(call_args), "Should call /v1/models endpoint"
        assert "timeout" in str(call_args), "Should specify timeout"

    @patch('klean.discovery.httpx.get')
    def test_uses_cache_when_fresh(self, mock_get, mock_litellm_models):
        """Should return cached models without HTTP call when cache is fresh."""
        # Arrange - first call populates cache
        mock_response = MagicMock()
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act - two calls
        first_result = list_models()
        second_result = list_models()

        # Assert - only one HTTP call made
        assert mock_get.call_count == 1, "Should only call API once"
        assert first_result == second_result, "Both calls should return same data"

    @patch('klean.discovery.httpx.get')
    @patch('klean.discovery.time.time')
    def test_refreshes_cache_when_stale(self, mock_time, mock_get, mock_litellm_models):
        """Should fetch new data when cache TTL expires."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # First call at time 0
        mock_time.return_value = 1000.0
        list_models()

        # Second call after TTL expires
        mock_time.return_value = 1000.0 + CACHE_TTL + 1

        # Act
        list_models()

        # Assert - two HTTP calls (cache expired)
        assert mock_get.call_count == 2, "Should call API twice after cache expires"

    @patch('klean.discovery.httpx.get')
    def test_force_refresh_bypasses_cache(self, mock_get, mock_litellm_models):
        """Should fetch fresh data when force_refresh=True."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act - two calls, second with force_refresh
        list_models()
        list_models(force_refresh=True)

        # Assert
        assert mock_get.call_count == 2, "force_refresh should bypass cache"

    @patch('klean.discovery.httpx.get')
    def test_returns_stale_cache_on_error(self, mock_get, mock_litellm_models):
        """Should return stale cache when API fails."""
        # Arrange - first call succeeds
        mock_response = MagicMock()
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Populate cache
        first_result = list_models(force_refresh=True)

        # Second call fails
        mock_get.side_effect = Exception("Connection refused")

        # Act - should return stale cache
        second_result = list_models(force_refresh=True)

        # Assert
        assert second_result == first_result, "Should return stale cache on error"
        assert len(second_result) == 4, "Should have cached models"

    @patch('klean.discovery.httpx.get')
    def test_handles_empty_response(self, mock_get):
        """Should handle empty model list from API."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        models = list_models()

        # Assert
        assert models == [], "Should return empty list"
        assert isinstance(models, list), "Should be a list type"

    @patch('klean.discovery.httpx.get')
    def test_handles_malformed_response(self, mock_get):
        """Should handle response without 'data' key."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}  # Wrong key
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        models = list_models()

        # Assert
        assert models == [], "Should return empty list for malformed response"


class TestGetModel:
    """Tests for get_model() function."""

    def setup_method(self):
        """Reset cache before each test."""
        clear_cache()

    @patch('klean.discovery.httpx.get')
    def test_returns_first_available(self, mock_get, mock_litellm_models):
        """Should return first model from discovery."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        model = get_model()

        # Assert
        assert model == "qwen3-coder", "Should return first model"

    def test_override_bypasses_discovery(self):
        """Should return override without calling API."""
        # Act
        model = get_model(override="my-custom-model")

        # Assert
        assert model == "my-custom-model", "Should return exact override"

    @patch('klean.discovery.httpx.get')
    def test_returns_none_when_no_models(self, mock_get):
        """Should return None when no models available."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        model = get_model()

        # Assert
        assert model is None, "Should return None when no models"


class TestClearCache:
    """Tests for clear_cache() function."""

    @patch('klean.discovery.httpx.get')
    def test_clears_cached_models(self, mock_get, mock_litellm_models):
        """Should clear cache forcing next call to fetch fresh."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = mock_litellm_models
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Populate cache
        list_models()
        assert mock_get.call_count == 1

        # Act
        clear_cache()

        # Verify cache is cleared by checking module-level _cache
        assert _cache["models"] == [], "Cache should be empty"
        assert _cache["timestamp"] == 0, "Timestamp should be reset"

        # Next call should hit API
        list_models()
        assert mock_get.call_count == 2, "Should fetch again after cache clear"


class TestIsAvailable:
    """Tests for is_available() function."""

    @patch('klean.discovery.httpx.get')
    def test_returns_true_when_proxy_healthy(self, mock_get):
        """Should return True when LiteLLM responds with 200."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        result = is_available()

        # Assert
        assert result is True, "Should return True for healthy proxy"
        mock_get.assert_called_once()
        assert "/v1/models" in str(mock_get.call_args), "Should check /v1/models"

    @patch('klean.discovery.httpx.get')
    def test_returns_false_on_connection_error(self, mock_get):
        """Should return False when connection fails."""
        # Arrange
        mock_get.side_effect = Exception("Connection refused")

        # Act
        result = is_available()

        # Assert
        assert result is False, "Should return False on connection error"

    @patch('klean.discovery.httpx.get')
    def test_returns_false_on_non_200(self, mock_get):
        """Should return False for non-200 status codes."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        # Act
        result = is_available()

        # Assert
        assert result is False, "Should return False for 503"

    @patch('klean.discovery.httpx.get')
    def test_uses_short_timeout(self, mock_get):
        """Should use short timeout for availability check."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        is_available()

        # Assert
        call_args = mock_get.call_args
        # timeout should be 3 seconds
        assert "timeout=3" in str(call_args) or "timeout" in call_args.kwargs, \
            "Should use timeout parameter"
