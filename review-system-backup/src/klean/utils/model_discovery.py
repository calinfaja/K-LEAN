"""Model discovery utilities for Agent SDK droids.

This module provides utilities to discover available models from LiteLLM
and select appropriate models for different droid types.
"""

import json
from typing import Dict, List, Optional


def get_available_models() -> List[str]:
    """Get list of available models from LiteLLM proxy.

    Checks if LiteLLM is running at localhost:4000 and returns available models.
    Falls back to empty list if LiteLLM is unavailable.

    Returns:
        List of model IDs available on LiteLLM (e.g., ['qwen3-coder', 'deepseek-v3-thinking'])
    """
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=2)
        data = json.loads(response.read().decode())

        if isinstance(data, dict) and "data" in data:
            return [model.get("id") for model in data["data"] if "id" in model]

        return []
    except Exception:
        return []


def get_model_for_task(task_type: str) -> Optional[str]:
    """Select best available model for a specific task type.

    Model selection strategy:
    - code_quality: qwen3-coder (best for code analysis)
    - architecture: deepseek-v3-thinking (best for design analysis)
    - security: qwen3-coder (best for security issues)
    - performance: deepseek-v3-thinking (best for performance analysis)
    - general: First available model

    Args:
        task_type: Type of task (code_quality, architecture, security, performance, general)

    Returns:
        Model ID to use, or None if no models available
    """
    available = get_available_models()

    if not available:
        return None

    # Define preferred models for each task type
    preferences = {
        "code_quality": ["qwen3-coder", "glm-4.6-thinking", "hermes-4-70b"],
        "architecture": ["deepseek-v3-thinking", "qwen3-coder", "kimi-k2-thinking"],
        "security": ["qwen3-coder", "deepseek-v3-thinking", "glm-4.6-thinking"],
        "performance": ["deepseek-v3-thinking", "qwen3-coder", "hermes-4-70b"],
        "general": available,  # Use first available for general tasks
    }

    # Get preferred models for this task type
    preferred = preferences.get(task_type, available)

    # Return first preferred model that's available
    for model in preferred:
        if model in available:
            return model

    # Fallback to any available model
    return available[0] if available else None


def is_litellm_available() -> bool:
    """Check if LiteLLM proxy is available and running.

    Returns:
        True if LiteLLM is available at localhost:4000, False otherwise
    """
    return len(get_available_models()) > 0


def get_model_info() -> Dict[str, any]:
    """Get comprehensive model information from LiteLLM.

    Returns:
        Dict with keys:
            - available: bool (is LiteLLM running)
            - models: List[str] (available model IDs)
            - recommended: Dict[str, str] (recommended model for each task type)
    """
    available = get_available_models()
    is_available = len(available) > 0

    recommendations = {}
    if is_available:
        for task_type in ["code_quality", "architecture", "security", "performance"]:
            model = get_model_for_task(task_type)
            if model:
                recommendations[task_type] = model

    return {
        "available": is_available,
        "models": available,
        "recommended": recommendations,
    }
