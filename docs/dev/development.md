# K-LEAN Developer Guide

Guide for contributing to K-LEAN development.

---

## Development Setup

### 1. Clone and Install (Dev Mode)

```bash
git clone https://github.com/calinfaja/k-lean.git
cd k-lean

# Install with symlinks (dev mode)
./install.sh --full
# Or: pipx install -e . && k-lean install --dev
```

Dev mode creates symlinks from `~/.claude/` to the repo. Changes take effect immediately.

### 2. Verify Setup

```bash
k-lean status                    # Check components
./scripts/sync-check.sh          # Verify symlinks
./test.sh                        # Run tests
```

---

## Project Structure

```
k-lean/
├── src/klean/                   # Python package
│   ├── __init__.py              # Version, paths
│   ├── cli.py                   # k-lean CLI
│   ├── data/                    # Package data (for PyPI builds)
│   ├── agents/                  # Claude Agent SDK agents
│   ├── droids/                  # Droid base classes
│   ├── knowledge/               # Knowledge DB integration
│   ├── tools/                   # Agent tools
│   └── utils/                   # Utilities
│
├── scripts/                     # Shell/Python scripts → ~/.claude/scripts/
├── commands-kln/                # Slash commands → ~/.claude/commands/kln/
├── hooks/                       # Event hooks → ~/.claude/hooks/
├── droids/                      # Factory Droids → ~/.factory/droids/
├── config/                      # Configs → ~/.config/litellm/, ~/.claude/
│   ├── CLAUDE.md
│   └── litellm/
├── lib/                         # Shared bash libs → ~/.claude/lib/
│
├── install.sh                   # Main installer
├── test.sh                      # Test suite
├── update.sh                    # Updater
├── settings.json                # Claude settings template
├── pyproject.toml               # Python package config
├── MANIFEST.in                  # sdist manifest
├── VERSION                      # Version file
├── README.md                    # Quick start
└── DOCS.md                      # Full documentation
```

---

## Workflow

### Adding a New Script

1. Create script in `scripts/`:
   ```bash
   touch scripts/my-script.sh
   chmod +x scripts/my-script.sh
   ```

2. Reinstall symlinks:
   ```bash
   ./scripts/sync-check.sh --fix
   ```

3. Verify:
   ```bash
   ./scripts/sync-check.sh
   ls -la ~/.claude/scripts/my-script.sh
   ```

### Adding a New Command

1. Create command in `commands-kln/`:
   ```bash
   cat > commands-kln/myCommand.md << 'EOF'
   # /kln:myCommand
   Description of command...
   EOF
   ```

2. Reinstall:
   ```bash
   ./scripts/sync-check.sh --fix
   ```

3. Test in Claude:
   ```
   /kln:myCommand
   ```

### Adding a New Hook

1. Create hook in `hooks/`:
   ```bash
   touch hooks/my-hook.sh
   chmod +x hooks/my-hook.sh
   ```

2. Register in `settings.json`:
   ```json
   "PostToolUse": [
     {
       "matcher": "MyTool",
       "hooks": [{"type": "command", "command": "~/.claude/hooks/my-hook.sh"}]
     }
   ]
   ```

3. Sync settings:
   ```bash
   ./scripts/sync-check.sh --sync
   ```

### Adding a New Droid

1. Create droid in `droids/`:
   ```markdown
   # Droid Name

   ## Role
   Description...

   ## Capabilities
   - Capability 1
   - Capability 2
   ```

2. Reinstall:
   ```bash
   ./scripts/sync-check.sh --fix
   ```

---

## Sync System

K-LEAN uses symlinks for development. The `sync-check.sh` script manages synchronization:

```bash
# Check all components
./scripts/sync-check.sh

# Verbose output
./scripts/sync-check.sh --verbose

# Fix broken/missing symlinks
./scripts/sync-check.sh --fix

# Backup local changes to repo
./scripts/sync-check.sh --sync

# Find files in installed not in repo
./scripts/sync-check.sh --orphans

# Remove orphaned files
./scripts/sync-check.sh --clean
```

### Synced Components

| Source | Destination |
|--------|-------------|
| `scripts/*.sh`, `scripts/*.py` | `~/.claude/scripts/` |
| `commands-kln/*.md` | `~/.claude/commands/kln/` |
| `hooks/*.sh` | `~/.claude/hooks/` |
| `droids/*.md` | `~/.factory/droids/` |
| `config/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `config/litellm/*.yaml` | `~/.config/litellm/` |
| `lib/*.sh` | `~/.claude/lib/` |

---

## Testing

### Run All Tests

```bash
./test.sh
```

### Test Specific Components

```bash
# Test LiteLLM
curl http://localhost:4000/v1/models

# Test model
k-lean test-model qwen3-coder

# Test knowledge DB
~/.claude/scripts/knowledge-query.sh "test"

# Test sync
./scripts/sync-check.sh
```

---

## Release Process

### 1. Update Version

Edit these files (all must match):
- `VERSION`
- `pyproject.toml` → `version = "X.Y.Z"`
- `src/klean/__init__.py` → `__version__ = "X.Y.Z"`

### 2. Prepare Release

```bash
# Populate data/ for PyPI
./scripts/prepare-release.sh

# Verify release
./scripts/prepare-release.sh --check
```

### 3. Build

```bash
pip install build
python -m build
```

### 4. Upload to PyPI

```bash
pip install twine
twine upload dist/*
```

### 5. Clean

```bash
./scripts/prepare-release.sh --clean
rm -rf dist/ build/ *.egg-info
```

---

## Code Style

- **Shell:** Use `shellcheck`, follow Google style
- **Python:** Black, Ruff, type hints
- **Markdown:** ATX headings, fenced code blocks

### Pre-commit

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Common Patterns

### Script Header

```bash
#!/bin/bash
# script-name.sh - Brief description
#
# Usage: script-name.sh [options]

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
```

### Python Script Header

```python
#!/usr/bin/env python3
"""Module description."""

import sys
from pathlib import Path
```

### Command Structure

```markdown
# /kln:commandName [args] — Brief description

## Description
What this command does.

## Usage
/kln:commandName arg1 arg2

## Examples
Example usage...
```

---

## Debugging

### Enable Debug Output

```bash
# Bash scripts
set -x

# LiteLLM
litellm --debug

# Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs

```bash
# LiteLLM logs
tail -f /tmp/litellm.log

# Knowledge server
tail -f ~/.klean/logs/knowledge-server.log
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Symlink broken | `sync-check.sh --fix` |
| Script not executable | `chmod +x script.sh` |
| LiteLLM not starting | Check port 4000, API keys |
| Knowledge DB slow | Start server daemon |

---

## Contact

- **Issues:** https://github.com/calinfaja/k-lean/issues
- **Author:** Calin Faja
