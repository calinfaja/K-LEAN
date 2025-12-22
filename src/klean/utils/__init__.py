"""K-LEAN Utilities - Helper functions for agents and tools.

This module provides utility functions for model discovery, caching, and other
support functionality for SmolKLN agents.
"""

from .model_discovery import (
    get_available_models,
    get_model_for_task,
    is_litellm_available,
    get_model_info,
)

__all__ = [
    "get_available_models",
    "get_model_for_task",
    "is_litellm_available",
    "get_model_info",
]
