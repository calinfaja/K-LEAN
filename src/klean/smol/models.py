"""LiteLLM model wrapper for Smolagents.

This module is INDEPENDENT - no imports from src/klean/droids/.
"""

from typing import Optional


# Model name mappings (short name -> LiteLLM model ID)
MODEL_ALIASES = {
    "qwen": "qwen3-coder",
    "deepseek": "deepseek-v3-thinking",
    "glm": "glm-4.6-thinking",
    "kimi": "kimi-k2-thinking",
    "minimax": "minimax-m2",
    "hermes": "hermes-4-70b",
}

# Role -> Best model mapping
ROLE_MODELS = {
    "security-auditor": "glm-4.6-thinking",
    "debugger": "qwen3-coder",
    "code-reviewer": "qwen3-coder",
    "orchestrator": "deepseek-v3-thinking",
    "architect": "deepseek-v3-thinking",
    "performance-engineer": "deepseek-v3-thinking",
    "arm-cortex-expert": "qwen3-coder",
    "c-pro": "qwen3-coder",
    "rust-expert": "qwen3-coder",
}


def resolve_model_name(model: str) -> str:
    """Resolve model alias to full LiteLLM model ID."""
    return MODEL_ALIASES.get(model, model)


def get_model_for_role(role: str) -> str:
    """Get the best model for a given agent role."""
    return ROLE_MODELS.get(role, "qwen3-coder")


def create_model(
    model_id: str,
    api_base: str = "http://localhost:4000",
    temperature: float = 0.7,
):
    """Create a LiteLLM model for Smolagents.

    Args:
        model_id: Model name (e.g., "qwen3-coder" or "glm")
        api_base: LiteLLM proxy URL
        temperature: Sampling temperature

    Returns:
        Configured LiteLLMModel instance
    """
    try:
        from smolagents import LiteLLMModel
    except ImportError:
        raise ImportError(
            "smolagents not installed. Install with: pip install smolagents[litellm]"
        )

    resolved_model = resolve_model_name(model_id)

    return LiteLLMModel(
        model_id=f"openai/{resolved_model}",
        api_base=api_base,
        api_key="not-needed",  # LiteLLM proxy handles auth
        temperature=temperature,
    )
