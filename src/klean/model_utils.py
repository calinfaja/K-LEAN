"""K-LEAN Model Utilities

Utilities for model name generation, parsing, and validation.
"""

import re


def extract_model_name(full_model_id: str) -> str:
    """Auto-generate short model name from full model ID.

    Args:
        full_model_id: Full model ID like "openrouter/kwaipilot/kat-coder-pro:free"
                      or "openai/Qwen/Qwen2.5-Coder-32B-Instruct"

    Returns:
        Short model name for config like "kat-coder-pro" or "qwen2-5-coder"

    Examples:
        >>> extract_model_name("openrouter/kwaipilot/kat-coder-pro:free")
        'kat-coder-pro'
        >>> extract_model_name("openai/Qwen/Qwen2.5-Coder-32B-Instruct")
        'qwen2-5-coder'
        >>> extract_model_name("anthropic/claude-3.5-sonnet")
        'claude-3.5-sonnet'
    """
    # Remove provider prefix if present (openrouter/, openai/)
    if "/" in full_model_id:
        parts = full_model_id.split("/")
        # Take the last non-empty part
        model_part = parts[-1]
    else:
        model_part = full_model_id

    # Remove suffix like ":free"
    if ":" in model_part:
        model_part = model_part.split(":")[0]

    # Convert to lowercase and replace underscores with hyphens
    model_name = model_part.lower().replace("_", "-")

    # Shorten extremely long names by removing size suffixes
    # e.g., "qwen2-5-coder-32b-instruct" -> "qwen2-5-coder"
    model_name = re.sub(r"-(32b|70b|120b|instruct|chat)$", "", model_name)

    # Clean up dots in version numbers: "2.5" -> "2-5"
    model_name = model_name.replace(".", "-")

    # Limit length to 50 chars
    model_name = model_name[:50]

    return model_name


def parse_model_id(full_model_id: str) -> tuple[str, str]:
    """Parse full model ID to determine provider.

    Args:
        full_model_id: Full model ID like "openrouter/..." or "openai/..."

    Returns:
        Tuple of (provider, full_model_id)
        Provider is one of: 'openrouter', 'nanogpt', 'unknown'

    Examples:
        >>> parse_model_id("openrouter/anthropic/claude-3.5-sonnet")
        ('openrouter', 'openrouter/anthropic/claude-3.5-sonnet')
        >>> parse_model_id("openai/Qwen/Qwen2.5-Coder")
        ('nanogpt', 'openai/Qwen/Qwen2.5-Coder')
    """
    if full_model_id.startswith("openrouter/"):
        return ("openrouter", full_model_id)
    elif full_model_id.startswith("openai/"):
        return ("nanogpt", full_model_id)
    else:
        return ("unknown", full_model_id)


def is_thinking_model(model_name: str) -> bool:
    """Check if a model is a thinking/reasoning model.

    Args:
        model_name: Model name to check

    Returns:
        True if model is a thinking model, False otherwise
    """
    thinking_keywords = [
        "thinking",
        "reasoning",
        "reflection",
        "r1",
        "deepseek-r1",
    ]
    model_lower = model_name.lower()
    return any(keyword in model_lower for keyword in thinking_keywords)
