"""Tests for klean.config_generator module.

Tests cover:
- LiteLLM config generation
- Model merging without duplicates
- Adding/removing models from config
- YAML parsing and generation
- Environment file generation
"""

import pytest

# =============================================================================
# Generate LiteLLM Config Tests
# =============================================================================


class TestGenerateLiteLLMConfig:
    """Tests for generate_litellm_config()."""

    def test_generates_valid_yaml(self):
        """Should generate valid YAML string."""
        from klean.config_generator import generate_litellm_config

        models = [
            {"model_name": "gpt-4", "model_id": "openai/gpt-4"},
        ]

        result = generate_litellm_config(models)

        assert isinstance(result, str)
        assert "model_list:" in result
        assert "gpt-4" in result

    def test_includes_litellm_settings(self):
        """Should include litellm_settings with drop_params."""
        from klean.config_generator import generate_litellm_config

        models = [{"model_name": "test", "model_id": "openrouter/test/test"}]
        result = generate_litellm_config(models)

        assert "litellm_settings:" in result
        assert "drop_params:" in result

    def test_separates_thinking_models(self):
        """Should put thinking models after standard models."""
        from klean.config_generator import generate_litellm_config

        models = [
            {"model_name": "deepseek-thinking", "model_id": "openai/deepseek-thinking"},
            {"model_name": "gpt-4", "model_id": "openrouter/openai/gpt-4"},
        ]

        result = generate_litellm_config(models)

        # Standard model should appear before thinking model
        gpt_pos = result.find("gpt-4")
        thinking_pos = result.find("deepseek-thinking")
        assert gpt_pos < thinking_pos

    def test_handles_empty_list(self):
        """Should handle empty model list."""
        from klean.config_generator import generate_litellm_config

        result = generate_litellm_config([])

        assert "model_list:" in result


# =============================================================================
# Create Model Entry Tests
# =============================================================================


class TestCreateModelEntry:
    """Tests for _create_model_entry()."""

    def test_creates_entry_with_litellm_params(self):
        """Should create entry with litellm_params structure."""
        from klean.config_generator import _create_model_entry

        model = {"model_name": "test-model", "model_id": "openai/gpt-4"}
        entry = _create_model_entry(model)

        assert entry["model_name"] == "test-model"
        assert "litellm_params" in entry
        assert entry["litellm_params"]["model"] == "openai/gpt-4"

    def test_sets_api_key_env_var(self):
        """Should set api_key to environment variable reference."""
        from klean.config_generator import _create_model_entry

        model = {"model_name": "test", "model_id": "openrouter/test"}
        entry = _create_model_entry(model)

        assert "api_key" in entry["litellm_params"]


# =============================================================================
# Merge Models Tests
# =============================================================================


class TestMergeModelsIntoConfig:
    """Tests for merge_models_into_config()."""

    def test_adds_new_models(self):
        """Should add models that don't exist."""
        from klean.config_generator import merge_models_into_config

        existing = {"model_list": []}
        new_models = [{"model_name": "new-model", "model_id": "test/new"}]

        result = merge_models_into_config(existing, new_models)

        assert len(result["model_list"]) == 1

    def test_skips_duplicates(self):
        """Should not add models that already exist."""
        from klean.config_generator import merge_models_into_config

        existing = {"model_list": [{"model_name": "existing", "litellm_params": {"model": "test"}}]}
        new_models = [{"model_name": "existing", "model_id": "test/existing"}]

        result = merge_models_into_config(existing, new_models)

        # Should still have only 1 model
        assert len(result["model_list"]) == 1

    def test_preserves_existing_models(self):
        """Should preserve existing models in config."""
        from klean.config_generator import merge_models_into_config

        existing = {"model_list": [{"model_name": "old", "litellm_params": {"model": "test/old"}}]}
        new_models = [{"model_name": "new", "model_id": "test/new"}]

        result = merge_models_into_config(existing, new_models)

        model_names = [m.get("model_name") for m in result["model_list"]]
        assert "old" in model_names
        assert "new" in model_names


# =============================================================================
# Add Model Tests
# =============================================================================


class TestAddModelToConfig:
    """Tests for add_model_to_config()."""

    def test_adds_model_to_existing_config(self, tmp_path):
        """Should add model to existing config file."""
        from klean.config_generator import add_model_to_config

        # Create initial config
        config_path = tmp_path / "config.yaml"
        config_path.write_text("model_list: []\n")

        result = add_model_to_config(
            config_path, "openrouter/anthropic/claude-3.5-sonnet", "openrouter"
        )

        assert result is True
        content = config_path.read_text()
        assert "claude-3.5-sonnet" in content

    def test_returns_false_for_duplicate(self, tmp_path):
        """Should return False if model already exists."""
        from klean.config_generator import add_model_to_config

        # Create config with existing model
        # Note: extract_model_name converts dots to hyphens
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""model_list:
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: openrouter/anthropic/claude-3.5-sonnet
      api_key: os.environ/OPENROUTER_API_KEY
""")

        result = add_model_to_config(
            config_path, "openrouter/anthropic/claude-3.5-sonnet", "openrouter"
        )

        assert result is False

    def test_raises_for_invalid_provider(self, tmp_path):
        """Should raise ValueError for invalid provider."""
        from klean.config_generator import add_model_to_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("model_list: []\n")

        with pytest.raises(ValueError, match="Invalid provider"):
            add_model_to_config(config_path, "test/model", "invalid_provider")


# =============================================================================
# Remove Model Tests
# =============================================================================


class TestRemoveModelFromConfig:
    """Tests for remove_model_from_config()."""

    def test_removes_existing_model(self, tmp_path):
        """Should remove model from config."""
        from klean.config_generator import remove_model_from_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("""model_list:
  - model_name: model-to-remove
    litellm_params:
      model: openrouter/test/model
      api_key: os.environ/OPENROUTER_API_KEY
  - model_name: keep-this
    litellm_params:
      model: openrouter/test/keep
      api_key: os.environ/OPENROUTER_API_KEY
""")

        result = remove_model_from_config(config_path, "model-to-remove")

        assert result is True
        content = config_path.read_text()
        assert "model-to-remove" not in content
        assert "keep-this" in content

    def test_returns_false_for_nonexistent(self, tmp_path):
        """Should return False if model doesn't exist."""
        from klean.config_generator import remove_model_from_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("model_list: []\n")

        result = remove_model_from_config(config_path, "nonexistent")

        assert result is False


# =============================================================================
# List Models Tests
# =============================================================================


class TestListModelsInConfig:
    """Tests for list_models_in_config()."""

    def test_lists_all_models(self, tmp_path):
        """Should list all model dicts with names and IDs."""
        from klean.config_generator import list_models_in_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("""model_list:
  - model_name: model-1
    litellm_params:
      model: test/1
  - model_name: model-2
    litellm_params:
      model: test/2
""")

        result = list_models_in_config(config_path)

        assert len(result) == 2
        model_names = [m["model_name"] for m in result]
        assert "model-1" in model_names
        assert "model-2" in model_names

    def test_returns_empty_for_no_models(self, tmp_path):
        """Should return empty list if no models."""
        from klean.config_generator import list_models_in_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("model_list: []\n")

        result = list_models_in_config(config_path)

        assert result == []


# =============================================================================
# Load Config Tests
# =============================================================================


class TestLoadConfigYaml:
    """Tests for load_config_yaml()."""

    def test_loads_valid_yaml(self, tmp_path):
        """Should load and parse valid YAML."""
        from klean.config_generator import load_config_yaml

        config_path = tmp_path / "config.yaml"
        config_path.write_text("""model_list:
  - model_name: test
""")

        result = load_config_yaml(config_path)

        assert "model_list" in result
        assert len(result["model_list"]) == 1

    def test_creates_default_for_missing_file(self, tmp_path):
        """Should return default config if file doesn't exist."""
        from klean.config_generator import load_config_yaml

        config_path = tmp_path / "nonexistent.yaml"

        result = load_config_yaml(config_path)

        assert "model_list" in result
        assert result["model_list"] == []


# =============================================================================
# Environment File Tests
# =============================================================================


class TestGenerateEnvFile:
    """Tests for generate_env_file()."""

    def test_generates_env_content(self):
        """Should generate .env file content."""
        from klean.config_generator import generate_env_file

        providers = {"openrouter": "or-key-123", "nanogpt": "nano-key-456"}
        result = generate_env_file(providers)

        assert "OPENROUTER_API_KEY=or-key-123" in result
        assert "NANOGPT_API_KEY=nano-key-456" in result

    def test_handles_empty_providers(self):
        """Should handle empty providers dict."""
        from klean.config_generator import generate_env_file

        result = generate_env_file({})

        # Should still generate valid content with header
        assert isinstance(result, str)
        assert "K-LEAN" in result


class TestLoadEnvFile:
    """Tests for load_env_file()."""

    def test_loads_existing_env(self, tmp_path):
        """Should load existing .env file."""
        from klean.config_generator import load_env_file

        env_path = tmp_path / ".env"
        env_path.write_text("OPENROUTER_API_KEY=test-key\n")

        result = load_env_file(env_path)

        assert result.get("OPENROUTER_API_KEY") == "test-key"

    def test_returns_empty_for_missing(self, tmp_path):
        """Should return empty dict if file doesn't exist."""
        from klean.config_generator import load_env_file

        env_path = tmp_path / "nonexistent.env"

        result = load_env_file(env_path)

        assert result == {}
