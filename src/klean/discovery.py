"""Model discovery for K-LEAN.

Central module for discovering models from LiteLLM proxy.
Single source of truth - no hardcoded model names.

Usage:
    from klean.discovery import list_models, get_model

    models = list_models()           # All available models
    model = get_model()              # First available (default)
    model = get_model("my-model")    # Explicit override
"""

import time
from typing import Optional

import httpx

# LiteLLM proxy endpoint
LITELLM_ENDPOINT = "http://localhost:4000"

# Cache with TTL
_cache: dict = {"models": [], "timestamp": 0}
CACHE_TTL = 300  # 5 minutes


def list_models(force_refresh: bool = False) -> list[str]:
    """Get all available models from LiteLLM.

    Uses TTL cache (5 min) for performance. Auto-refreshes when stale.

    Args:
        force_refresh: Bypass cache and fetch fresh

    Returns:
        List of model IDs (e.g., ["claude-sonnet", "gpt-4o"])
    """
    now = time.time()

    # Return cached if fresh
    if not force_refresh and _cache["models"] and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["models"]

    # Fetch fresh from LiteLLM
    try:
        resp = httpx.get(f"{LITELLM_ENDPOINT}/v1/models", timeout=5)
        resp.raise_for_status()
        models = [m["id"] for m in resp.json().get("data", [])]
        _cache["models"] = models
        _cache["timestamp"] = now
        return models
    except Exception:
        # Return stale cache on error (better than nothing)
        return _cache["models"]


def get_model(override: str = None) -> Optional[str]:
    """Get model to use.

    Simple logic: explicit override wins, otherwise first available.

    Args:
        override: Explicit model name (bypasses discovery)

    Returns:
        Model name or None if no models available
    """
    if override:
        return override
    models = list_models()
    return models[0] if models else None


def clear_cache():
    """Clear model cache.

    Call after LiteLLM restart to pick up new models immediately.
    """
    _cache["models"] = []
    _cache["timestamp"] = 0


def is_available() -> bool:
    """Check if LiteLLM proxy is available.

    Uses /v1/models endpoint (more reliable than /health).
    """
    try:
        resp = httpx.get(f"{LITELLM_ENDPOINT}/v1/models", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
