"""
K-LEAN LiteLLM Config Generator

Generates config.yaml and .env files for LiteLLM with smart merging.
Supports multiple providers without overwriting existing keys.
"""

from pathlib import Path
from typing import Optional

import yaml

from klean.model_utils import extract_model_name, is_thinking_model, parse_model_id


def generate_litellm_config(models: list[dict]) -> str:
    """Generate litellm config.yaml content.

    Args:
        models: List of model dicts with model_name and model_id

    Returns:
        YAML string content for config.yaml
    """
    config = {
        "litellm_settings": {
            "drop_params": True,
        },
        "model_list": [],
    }

    # Separate models by type (thinking vs standard)
    standard_models = []
    thinking_models = []

    for model in models:
        if "thinking" in model["model_name"].lower():
            thinking_models.append(model)
        else:
            standard_models.append(model)

    # Add standard models first
    for model in standard_models:
        model_entry = _create_model_entry(model)
        config["model_list"].append(model_entry)

    # Add thinking models at the end (with comment section)
    if thinking_models:
        for model in thinking_models:
            model_entry = _create_model_entry(model)
            config["model_list"].append(model_entry)

    return _yaml_to_string(config)


def _create_model_entry(model: dict) -> dict:
    """Create a single model entry for config.yaml.

    Args:
        model: Dict with model_name and model_id

    Returns:
        Model entry dict
    """
    model_id = model["model_id"]
    model_name = model["model_name"]

    # Determine provider and API setup
    if model_id.startswith("openrouter/"):
        return {
            "model_name": model_name,
            "litellm_params": {
                "model": model_id,
                "api_key": "os.environ/OPENROUTER_API_KEY",
            },
        }
    elif model_id.startswith("openai/"):
        # NanoGPT models
        entry = {
            "model_name": model_name,
            "litellm_params": {
                "model": model_id,
                "api_key": "os.environ/NANOGPT_API_KEY",
            },
        }
        # Use thinking endpoint for thinking models
        if "thinking" in model_name.lower():
            entry["litellm_params"]["api_base"] = "os.environ/NANOGPT_THINKING_API_BASE"
        else:
            entry["litellm_params"]["api_base"] = "os.environ/NANOGPT_API_BASE"
        return entry
    else:
        # Generic case
        return {
            "model_name": model_name,
            "litellm_params": {
                "model": model_id,
            },
        }


def _yaml_to_string(config: dict) -> str:
    """Convert config dict to YAML string with comments.

    Args:
        config: Configuration dict

    Returns:
        YAML formatted string
    """
    yaml_str = "# K-LEAN LiteLLM Configuration\n"
    yaml_str += "# ============================\n"
    yaml_str += "#\n"
    yaml_str += "# ENDPOINT RULES:\n"
    yaml_str += "#   *-thinking models -> NANOGPT_THINKING_API_BASE\n"
    yaml_str += "#   all other models  -> NANOGPT_API_BASE or OPENROUTER_API_BASE\n"
    yaml_str += "#\n"
    yaml_str += "# No quotes around os.environ/ values!\n"
    yaml_str += "\n"

    # Add settings
    yaml_str += "litellm_settings:\n"
    yaml_str += "  drop_params: true\n"
    yaml_str += "\n"

    # Add model list with sections
    openrouter_models = []
    nanogpt_standard = []
    nanogpt_thinking = []

    for model in config.get("model_list", []):
        if "model_name" not in model:
            continue

        model_id = model["litellm_params"]["model"]
        if model_id.startswith("openrouter/"):
            openrouter_models.append(model)
        elif "thinking" in model["model_name"].lower():
            nanogpt_thinking.append(model)
        else:
            nanogpt_standard.append(model)

    # If no models, use empty list syntax to avoid YAML parsing as None
    if not openrouter_models and not nanogpt_standard and not nanogpt_thinking:
        yaml_str += "model_list: []\n"
        return yaml_str

    yaml_str += "model_list:\n"

    # OpenRouter section
    if openrouter_models:
        yaml_str += "  # ===================\n"
        yaml_str += "  # OPENROUTER MODELS\n"
        yaml_str += "  # ===================\n"
        for model in openrouter_models:
            yaml_str += _model_to_yaml(model)

    # NanoGPT standard section
    if nanogpt_standard:
        yaml_str += "  # ===================\n"
        yaml_str += "  # NANOGPT STANDARD MODELS\n"
        yaml_str += "  # ===================\n"
        for model in nanogpt_standard:
            yaml_str += _model_to_yaml(model)

    # NanoGPT thinking section
    if nanogpt_thinking:
        yaml_str += "  # ===================\n"
        yaml_str += "  # NANOGPT THINKING MODELS (advanced)\n"
        yaml_str += "  # ===================\n"
        for model in nanogpt_thinking:
            yaml_str += _model_to_yaml(model)

    return yaml_str


def _model_to_yaml(model: dict) -> str:
    """Convert a model entry to YAML string.

    Args:
        model: Model entry dict

    Returns:
        YAML formatted model entry
    """
    yaml_str = "  - model_name: " + model["model_name"] + "\n"
    yaml_str += "    litellm_params:\n"

    params = model["litellm_params"]
    yaml_str += f"      model: {params['model']}\n"

    if "api_base" in params:
        yaml_str += f"      api_base: {params['api_base']}\n"

    yaml_str += f"      api_key: {params['api_key']}\n"

    return yaml_str


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load existing .env file.

    Args:
        env_path: Path to .env file

    Returns:
        Dict of environment variables
    """
    env_vars = {}
    if env_path.exists():
        content = env_path.read_text()
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def generate_env_file(providers: dict[str, str], existing_env: Optional[dict] = None) -> str:
    """Generate .env file content, preserving existing keys.

    Args:
        providers: Dict mapping provider names to API keys
                  e.g., {"openrouter": "sk-or-...", "nanogpt": "sk-nano-..."}
        existing_env: Existing environment variables to merge

    Returns:
        .env file content as string
    """
    env_vars = existing_env or {}

    # Add/update provider keys
    if "openrouter" in providers:
        env_vars["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
        env_vars["OPENROUTER_API_KEY"] = providers["openrouter"]

    if "nanogpt" in providers:
        env_vars["NANOGPT_API_BASE"] = "https://nano-gpt.com/api/subscription/v1"
        env_vars["NANOGPT_THINKING_API_BASE"] = "https://nano-gpt.com/api/v1thinking"
        env_vars["NANOGPT_API_KEY"] = providers["nanogpt"]

    # Build .env content
    content = "# K-LEAN LiteLLM Environment Variables\n"
    content += "# Generated by kln setup\n"
    content += "\n"

    # Add variables in order
    for key in sorted(env_vars.keys()):
        content += f"{key}={env_vars[key]}\n"

    return content


def load_config_yaml(config_path: Path) -> dict:
    """Load existing config.yaml file.

    Args:
        config_path: Path to config.yaml

    Returns:
        Parsed YAML dict, or empty structure if file doesn't exist
    """
    if not config_path.exists():
        return {"litellm_settings": {"drop_params": True}, "model_list": []}

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return data or {"litellm_settings": {"drop_params": True}, "model_list": []}
    except Exception:
        return {"litellm_settings": {"drop_params": True}, "model_list": []}


def merge_models_into_config(existing_config: dict, new_models: list[dict]) -> dict:
    """Merge new models into existing config without duplicates.

    Args:
        existing_config: Current config dict
        new_models: List of new models to add

    Returns:
        Updated config dict with merged models
    """
    existing_names: set[str] = {
        model.get("model_name")
        for model in existing_config.get("model_list", [])
        if isinstance(model, dict) and "model_name" in model
    }

    # Add only new models (transform them first)
    for model in new_models:
        if model.get("model_name") not in existing_names:
            # Transform model to have litellm_params structure
            model_entry = _create_model_entry(model)
            existing_config["model_list"].append(model_entry)

    return existing_config


def add_model_to_config(config_path: Path, full_model_id: str, provider: str) -> bool:
    """Add a single model to existing config.yaml.

    Args:
        config_path: Path to config.yaml
        full_model_id: Full model ID like "openrouter/anthropic/claude-3.5-sonnet"
        provider: Provider name ("openrouter" or "nanogpt")

    Returns:
        True if successful, False if model already exists

    Raises:
        ValueError: If provider is invalid
    """
    if provider not in ("openrouter", "nanogpt"):
        raise ValueError(f"Invalid provider: {provider}")

    # Parse and validate model ID
    parsed_provider, validated_id = parse_model_id(full_model_id)
    if parsed_provider == "unknown":
        # User provided ID without provider prefix, prepend it
        validated_id = f"{provider}/{full_model_id}"

    # Load existing config
    config = load_config_yaml(config_path)

    # Check if model already exists
    existing_names = {
        m.get("model_name") for m in config.get("model_list", []) if isinstance(m, dict)
    }

    model_name = extract_model_name(validated_id)
    if model_name in existing_names:
        return False  # Already exists

    # Create model entry
    model_entry = _create_model_entry(
        {
            "model_name": model_name,
            "model_id": validated_id,
        }
    )

    config["model_list"].append(model_entry)

    # Write back to file
    config_path.write_text(_yaml_to_string_dict(config))
    return True


def remove_model_from_config(config_path: Path, model_name: str) -> bool:
    """Remove a model from config.yaml.

    Args:
        config_path: Path to config.yaml
        model_name: Short model name to remove

    Returns:
        True if removed, False if model not found
    """
    config = load_config_yaml(config_path)

    original_count = len(config.get("model_list", []))

    # Filter out the model
    config["model_list"] = [
        m
        for m in config.get("model_list", [])
        if not isinstance(m, dict) or m.get("model_name") != model_name
    ]

    if len(config["model_list"]) == original_count:
        return False  # Model not found

    # Write back to file
    config_path.write_text(_yaml_to_string_dict(config))
    return True


def list_models_in_config(config_path: Path) -> list[dict]:
    """List all models in current config.

    Args:
        config_path: Path to config.yaml

    Returns:
        List of model dicts with model_name and model_id
    """
    config = load_config_yaml(config_path)
    models = []

    for model in config.get("model_list", []):
        if isinstance(model, dict) and "model_name" in model:
            model_id = model.get("litellm_params", {}).get("model", "unknown")
            models.append(
                {
                    "model_name": model["model_name"],
                    "model_id": model_id,
                    "is_thinking": is_thinking_model(model["model_name"]),
                }
            )

    return models


def _yaml_to_string_dict(config: dict) -> str:
    """Convert config dict to YAML string (reuse existing logic).

    This is the internal version that accepts a dict instead of extracting from config.
    """
    return _yaml_to_string(config)
