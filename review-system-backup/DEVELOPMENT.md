# K-LEAN Development Guide

> Minimal reference for developers and AI agents maintaining this project.

## Project Structure

```
k-lean/
├── src/klean/              # Python package (pip installable)
│   ├── cli.py              # Main CLI (~1950 lines) - k-lean commands
│   ├── __init__.py         # Version, path constants
│   └── data/               # Package data (synced from root)
│       ├── core/           # klean_core.py + prompts (review logic)
│       ├── scripts/        # Shell/Python scripts
│       ├── hooks/          # Claude Code hooks
│       ├── commands/kln/   # Slash commands (/kln:*)
│       ├── droids/         # Droid specialist prompts
│       └── config/         # Configuration files
│
├── scripts/                # CANONICAL source for scripts
├── hooks/                  # CANONICAL source for hooks
├── commands/kln/           # CANONICAL source for /kln: commands
├── droids/                 # CANONICAL source for droids
├── config/                 # CANONICAL source for config
├── lib/                    # Shared shell libraries
│
├── install.sh              # Shell-based installer
├── pyproject.toml          # Python package config
└── tests/                  # Test suite
```

## Key Principle: Dual Source

| Location | Purpose | Installed By |
|----------|---------|--------------|
| Root dirs (scripts/, hooks/, etc.) | Development, install.sh | `install.sh`, `k-lean install --dev` |
| src/klean/data/ | PyPI package | `pip install k-lean`, `k-lean install` |

**Keep them in sync:** `k-lean sync`

## Essential Commands

```bash
# Development
k-lean sync              # Sync root → package data
k-lean sync --check      # Verify sync (CI)
k-lean sync --clean      # Remove stale files first

# Installation
k-lean install --dev     # Dev mode (symlinks)
k-lean install           # Production (copies)
k-lean install -c core   # Install specific component

# Testing
k-lean status            # Check installation
k-lean doctor -f         # Diagnose + auto-fix
k-lean test              # Run test suite

# Services
k-lean start             # Start LiteLLM proxy
k-lean stop              # Stop services
k-lean models            # List available models
```

## Release Workflow

```bash
# 1. Ensure sync
k-lean sync --clean
k-lean sync --check      # Must pass

# 2. Update version (3 places)
#    - VERSION
#    - pyproject.toml
#    - src/klean/__init__.py

# 3. Build
pip install build
python -m build

# 4. Upload
pip install twine
twine upload dist/*
```

## File Responsibilities

| File | What It Does |
|------|--------------|
| `cli.py` | All k-lean CLI commands |
| `klean_core.py` | Review logic, model resolution, LiteLLM calls |
| `install.sh` | Shell-based installation (alternative to pip) |
| `session-start.sh` | Hook: auto-start services |
| `user-prompt-handler.sh` | Hook: keyword detection (InitKB, SaveThis, etc.) |
| `post-bash-handler.sh` | Hook: git commit detection, timeline |
| `post-web-handler.sh` | Hook: auto-capture web content |

## Common Tasks

### Add a new script
1. Create in `scripts/`
2. Run `k-lean sync`
3. Test with `k-lean install --dev`

### Add a new /kln: command
1. Create `commands/kln/name.md`
2. Run `k-lean sync`
3. Restart Claude Code to load

### Modify klean_core.py
1. Edit `src/klean/data/core/klean_core.py`
2. Run `k-lean install -c core` to update ~/.claude/k-lean/

### Add CLI command
1. Edit `src/klean/cli.py`
2. Add `@main.command()` decorated function
3. Test with `k-lean <command>`

## Don't Do

| Don't | Why | Do Instead |
|-------|-----|------------|
| Edit src/klean/data/scripts/ directly | Gets overwritten by sync | Edit scripts/ then sync |
| Forget k-lean sync before release | Package will be stale | Always sync --check before build |
| Delete commands/sc/ | Symlinked to ~/.claude | It's SuperClaude (external) |
| Hardcode ~/.claude paths in Python | Breaks different installs | Use CLAUDE_DIR from __init__.py |

## Dependencies

**Required:**
- Python 3.9+
- click, rich, pyyaml, httpx

**Optional:**
- txtai, sentence-transformers (knowledge DB)
- LiteLLM proxy (multi-model reviews)

## Testing Checklist

- [ ] `k-lean sync --check` passes
- [ ] `k-lean install --dev -y` succeeds
- [ ] `k-lean status` shows all green
- [ ] `/kln:status` works in Claude Code
- [ ] `k-lean doctor` finds no issues

## Architecture Notes

- **Hooks** run on Claude Code events (session start, tool use, etc.)
- **Scripts** are called by hooks or directly
- **klean_core.py** handles LiteLLM communication for reviews
- **Knowledge DB** uses txtai for semantic search per-project
- **Slash commands** are markdown files auto-discovered by Claude Code
