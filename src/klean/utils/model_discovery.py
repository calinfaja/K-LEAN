"""Model discovery utilities for K-LEAN.

Discovers models from LiteLLM and provides task-based selection.
"""

import json
import os
from typing import Dict, List, Optional, Any

# Minimal model metadata (tier, speed tok/s, primary use)
MODEL_DEFAULTS = {
    "qwen3-coder":        {"tier": "elite",     "speed": 35, "use": "coding"},
    "devstral-2":         {"tier": "elite",     "speed": 32, "use": "coding"},
    "deepseek-r1":        {"tier": "reasoning", "speed": 15, "use": "architecture"},
    "deepseek-v3-thinking": {"tier": "reasoning", "speed": 20, "use": "architecture"},
    "glm-4.6-thinking":   {"tier": "reasoning", "speed": 11, "use": "standards"},
    "kimi-k2":            {"tier": "agent",     "speed": 28, "use": "agents"},
    "kimi-k2-thinking":   {"tier": "agent",     "speed": 20, "use": "agents"},
    "llama-4-scout":      {"tier": "speed",     "speed": 47, "use": "fast"},
    "llama-4-maverick":   {"tier": "context",   "speed": 28, "use": "large-repos"},
    "minimax-m2":         {"tier": "specialist", "speed": 23, "use": "research"},
    "hermes-4-70b":       {"tier": "specialist", "speed": 20, "use": "scripting"},
    "qwen3-235b":         {"tier": "value",     "speed": 16, "use": "general"},
}

# Task -> preferred models mapping
TASK_MODELS = {
    "coding":       ["qwen3-coder", "devstral-2", "llama-4-scout"],
    "architecture": ["deepseek-v3-thinking", "deepseek-r1", "glm-4.6-thinking"],
    "reasoning":    ["deepseek-r1", "deepseek-v3-thinking", "glm-4.6-thinking"],
    "security":     ["qwen3-coder", "glm-4.6-thinking", "deepseek-v3-thinking"],
    "agent":        ["kimi-k2", "kimi-k2-thinking", "qwen3-coder"],
    "fast":         ["llama-4-scout", "kimi-k2", "qwen3-coder"],
    "context":      ["llama-4-maverick", "llama-4-scout", "minimax-m2"],
    "scripting":    ["hermes-4-70b", "qwen3-coder", "llama-4-scout"],
    "general":      ["qwen3-coder", "llama-4-scout", "deepseek-v3-thinking"],
}


def get_available_models() -> List[str]:
    """Get available models from LiteLLM proxy."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:4000/models")
        response = urllib.request.urlopen(req, timeout=2)
        data = json.loads(response.read().decode())
        if isinstance(data, dict) and "data" in data:
            return [m.get("id") for m in data["data"] if "id" in m]
    except Exception:
        pass
    return []


def get_model_metadata() -> Dict[str, Dict[str, Any]]:
    """Get model metadata from config or defaults."""
    metadata = {}

    # Try loading from config
    config_path = os.path.expanduser("~/.config/litellm/config.yaml")
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            for model in config.get("model_list", []):
                name = model.get("model_name")
                info = model.get("model_info", {})
                if name:
                    metadata[name] = info
        except Exception:
            pass

    # Merge with defaults
    for name, defaults in MODEL_DEFAULTS.items():
        if name not in metadata:
            metadata[name] = defaults

    return metadata


def get_model_for_task(task: str) -> Optional[str]:
    """Select best model for a task type."""
    available = get_available_models()
    if not available:
        return None

    preferred = TASK_MODELS.get(task, available)
    for model in preferred:
        if model in available:
            return model

    return available[0] if available else None


def is_litellm_available() -> bool:
    """Check if LiteLLM is running."""
    return len(get_available_models()) > 0


def get_model_info() -> Dict[str, Any]:
    """Get summary of available models."""
    available = get_available_models()
    metadata = get_model_metadata()

    return {
        "available": len(available) > 0,
        "models": available,
        "metadata": {m: metadata.get(m, {}) for m in available},
    }
