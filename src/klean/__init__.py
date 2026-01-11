"""
K-LEAN: Multi-model code review and knowledge capture system for Claude Code.

This package provides:
- CLI for installing/managing K-LEAN components
- Knowledge database with semantic search
- Integration with Claude Code slash commands and hooks
"""

__version__ = "1.0.0b7"
__author__ = "Calin Faja"

from pathlib import Path

# Package data directory (relative to this file when installed)
DATA_DIR = Path(__file__).parent / "data"

# Default paths
CLAUDE_DIR = Path.home() / ".claude"
VENV_DIR = Path.home() / ".venvs" / "knowledge-db"
CONFIG_DIR = Path.home() / ".config" / "litellm"
KLEAN_DIR = Path.home() / ".klean"
LOGS_DIR = KLEAN_DIR / "logs"
PIDS_DIR = KLEAN_DIR / "pids"
SMOL_AGENTS_DIR = KLEAN_DIR / "agents"  # SmolKLN agent prompts


def get_version() -> str:
    """Return the package version."""
    return __version__


def get_data_path() -> Path:
    """Return the path to package data files."""
    return DATA_DIR
