"""
K-LEAN Model Defaults and Configuration

Defines default model lists for each API provider.
Used by the setup wizard and model management commands.
"""

# OpenRouter default models (6)
OPENROUTER_DEFAULTS = [
    {
        "model_name": "gemini-3-flash",
        "model_id": "openrouter/google/gemini-3-flash-preview",
    },
    {
        "model_name": "gemini-2.5-flash",
        "model_id": "openrouter/google/gemini-2.5-flash",
    },
    {
        "model_name": "qwen3-coder-plus",
        "model_id": "openrouter/qwen/qwen3-coder-plus",
    },
    {
        "model_name": "deepseek-v3.2-speciale",
        "model_id": "openrouter/deepseek/deepseek-v3.2-speciale",
    },
    {
        "model_name": "gpt-5-mini",
        "model_id": "openrouter/openai/gpt-5-mini",
    },
    {
        "model_name": "gpt-5.1-codex-mini",
        "model_id": "openrouter/openai/gpt-5.1-codex-mini",
    },
]

# NanoGPT standard models (10 non-thinking)
NANOGPT_STANDARD = [
    {
        "model_name": "gpt-oss-120b",
        "model_id": "openai/openai/gpt-oss-120b",
    },
    {
        "model_name": "qwen3-coder",
        "model_id": "openai/qwen/qwen3-coder",
    },
    {
        "model_name": "llama-4-maverick",
        "model_id": "openai/meta-llama/llama-4-maverick",
    },
    {
        "model_name": "llama-4-scout",
        "model_id": "openai/meta-llama/llama-4-scout",
    },
    {
        "model_name": "mimo-v2-flash",
        "model_id": "openai/xiaomi/mimo-v2-flash",
    },
    {
        "model_name": "kimi-k2",
        "model_id": "openai/moonshotai/kimi-k2-instruct",
    },
    {
        "model_name": "glm-4.7",
        "model_id": "openai/zai-org/glm-4.7",
    },
    {
        "model_name": "deepseek-v3.2",
        "model_id": "openai/deepseek/deepseek-v3.2",
    },
    {
        "model_name": "deepseek-r1",
        "model_id": "openai/deepseek-ai/DeepSeek-R1-0528",
    },
    {
        "model_name": "devstral-2-123b",
        "model_id": "openai/mistralai/devstral-2-123b-instruct-2512",
    },
]

# NanoGPT thinking models (4 - optional)
NANOGPT_THINKING = [
    {
        "model_name": "kimi-k2-thinking",
        "model_id": "openai/moonshotai/kimi-k2-thinking",
    },
    {
        "model_name": "glm-4.7-thinking",
        "model_id": "openai/zai-org/glm-4.7:thinking",
    },
    {
        "model_name": "deepseek-v3.2-thinking",
        "model_id": "openai/deepseek/deepseek-v3.2:thinking",
    },
    {
        "model_name": "deepseek-r1-thinking",
        "model_id": "openai/deepseek-ai/DeepSeek-R1-0528",
    },
]

# Combined lists for convenience
NANOGPT_DEFAULTS = NANOGPT_STANDARD + NANOGPT_THINKING


def get_openrouter_models(include_all: bool = False) -> list:
    """Get OpenRouter models.

    Args:
        include_all: If True, returns all configured models (not implemented yet)

    Returns:
        List of OpenRouter default models
    """
    return OPENROUTER_DEFAULTS


def get_nanogpt_models(include_thinking: bool = False) -> list:
    """Get NanoGPT models.

    Args:
        include_thinking: If True, includes thinking models

    Returns:
        List of NanoGPT models
    """
    if include_thinking:
        return NANOGPT_DEFAULTS
    return NANOGPT_STANDARD
