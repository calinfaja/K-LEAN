# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

K-LEAN is a multi-model code review and knowledge capture system for Claude Code. It provides consensus reviews from multiple LLMs via LiteLLM proxy, a persistent per-project knowledge database with hybrid semantic search, and 8 specialist agents for domain-specific analysis.

**Package name:** `kln-ai` (PyPI)
**Entry points:** `kln` (main CLI), `kln-smol` (agent executor)

## Development Commands

```bash
# Install in editable mode
pipx install -e .

# Run tests
pytest tests/ -v

# Run single test
pytest tests/test_discovery.py -v
pytest tests/test_discovery.py::test_function_name -v

# Lint
ruff check src/
ruff check src/ --fix

# Format
black src/

# Sync data files to ~/.claude/ after editing data/*
kln admin sync

# Check installation health
kln doctor -f
```

## Architecture

### Core Flow

```
Claude Code
    |
    v
/kln:* commands (data/commands/kln/*.md)
    |
    +---> LiteLLM Proxy (localhost:4000) ---> NanoGPT/OpenRouter
    |
    +---> Knowledge DB (.knowledge-db/) - fastembed hybrid search
    |
    +---> SmolKLN Agents (src/klean/smol/) - smolagents framework
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/klean/cli.py` | Click CLI with subgroups: `model`, `provider`, `admin` |
| `src/klean/discovery.py` | Dynamic model discovery from LiteLLM proxy |
| `src/klean/config_generator.py` | LiteLLM config generation with non-destructive merging |
| `src/klean/smol/executor.py` | Single agent execution with tool use |
| `src/klean/smol/multi_agent.py` | Multi-agent orchestration and consensus |
| `src/klean/smol/loader.py` | Agent definition loading from markdown (YAML frontmatter + system prompt) |
| `src/klean/smol/models.py` | LiteLLM model wrapper with thinking model support |

### Data Directory Structure

`src/klean/data/` contains installable assets deployed to `~/.claude/`:

```
data/
├── scripts/        # Python scripts for knowledge DB
├── commands/kln/   # Slash commands (9 .md files)
├── agents/         # SmolKLN agent definitions (8 .md files)
└── config/         # Config templates
```

**Note:** Hooks are now Python entry points (`kln-hook-*`), not shell scripts.

### Cross-Platform Modules

| Module | Purpose |
|--------|---------|
| `src/klean/platform.py` | Cross-platform paths (platformdirs) and process management (psutil) |
| `src/klean/reviews.py` | Async code review with httpx (quick, consensus, second-opinion) |
| `src/klean/hooks.py` | Claude Code hook handlers (session, prompt, bash, web) |

### Knowledge DB

Per-project storage in `.knowledge-db/` using hybrid search:
- Dense embeddings: BAAI/bge-small-en-v1.5 via fastembed
- Sparse matching: BM42
- RRF fusion + cross-encoder reranking
- TCP server for fast queries (~30ms vs ~17s cold)

Core scripts: `data/scripts/knowledge_db.py`, `knowledge-server.py`, `knowledge-capture.py`

### Thinking Model Handling

Models may return content in different fields. Always check both:
```python
content = response.get("content") or response.get("reasoning_content")
```

The `reviews.py` module handles this automatically via `_extract_content()` which strips `<think>` tags.

## CLI Structure

```
kln
├── init                    # Interactive setup (provider selection + install)
├── install / uninstall     # Deploy/remove ~/.claude/ components
├── start / stop            # LiteLLM proxy management
├── status / doctor         # Health checks
├── multi                   # Multi-agent orchestrated review
├── model                   # Subgroup
│   ├── list [--health]
│   ├── add --provider <p> "<model>"
│   ├── remove "<model>"
│   └── test "<model>"
├── provider                # Subgroup
│   ├── list
│   ├── add <provider> --api-key <key>
│   ├── set-key <provider> --key <key>
│   └── remove <provider>
└── admin                   # Hidden subgroup
    ├── sync                # Sync data files
    ├── debug               # Live monitoring
    └── test                # Run test suite
```

## Release Process

Version is maintained in TWO files (must match):
1. `pyproject.toml` -> `version = "X.Y.Z"`
2. `src/klean/__init__.py` -> `__version__ = "X.Y.Z"`

```bash
# Verify release readiness
./src/klean/data/scripts/prepare-release.sh --check

# Build locally
python -m build
twine check dist/*
```

Releases are published via GitHub Actions workflow `.github/workflows/publish.yml`.

## Code Conventions

- Line length: 100 characters (ruff/black)
- Target Python: 3.9+
- Cross-platform: Use `klean.platform` for paths and process management
- Hooks: Python entry points (`kln-hook-*`), read JSON from stdin, output JSON to stdout
- IPC: TCP localhost (not Unix sockets) for cross-platform compatibility
- Commit style: conventional commits (`feat:`, `fix:`, `docs:`, etc.)
