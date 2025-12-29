"""K-LEAN Utilities - Helper functions for agents and tools.

This module provides utility functions for model discovery and other
support functionality for SmolKLN agents.

Note: Model discovery is now centralized in klean.discovery module.
"""

from klean.discovery import get_model, is_available, list_models

# Re-export with legacy names for backwards compatibility
get_available_models = list_models
is_litellm_available = is_available

__all__ = [
    "get_available_models",
    "is_litellm_available",
    "list_models",
    "get_model",
]
