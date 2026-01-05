"""LiteLLM model wrapper for Smolagents.

Model discovery and LiteLLM integration for SmolKLN.
Uses central discovery module - no hardcoded model names.
"""

import warnings

# Suppress Pydantic serialization warnings from smolagents/LiteLLM
# These occur when LiteLLM response fields don't match smolagents' Pydantic models
warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings",
    category=UserWarning,
    module="pydantic",
)

from klean.discovery import get_model  # noqa: E402


def create_model(
    model_id: str = None,
    api_base: str = "http://localhost:4000",
    temperature: float = 0.7,
):
    """Create a LiteLLM model for Smolagents.

    Args:
        model_id: Model name. If None, uses first available from LiteLLM.
        api_base: LiteLLM proxy URL
        temperature: Sampling temperature

    Returns:
        Configured LiteLLMModel instance

    Raises:
        ValueError: If no models available
        ImportError: If smolagents not installed
    """
    try:
        from smolagents import LiteLLMModel
    except ImportError as err:
        raise ImportError(
            "smolagents not installed. Install with: pipx inject kln-ai 'smolagents[litellm]'"
        ) from err

    # Use discovery: explicit model or first available
    resolved_model = get_model(model_id)
    if not resolved_model:
        raise ValueError("No models available. Check LiteLLM is running: kln status")

    return LiteLLMModel(
        model_id=f"openai/{resolved_model}",
        api_base=api_base,
        api_key="not-needed",  # LiteLLM proxy handles auth
        temperature=temperature,
    )
