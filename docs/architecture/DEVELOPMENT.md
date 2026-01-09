# K-LEAN Development Guide

Complete reference for developing, testing, and troubleshooting K-LEAN.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Project Layout](#project-layout)
4. [Development Workflow](#development-workflow)
5. [Coding Conventions](#coding-conventions)
6. [Testing](#testing)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)
9. [Release Checklist](#release-checklist)

---

## Prerequisites

### Required

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Runtime |
| pipx | Latest | Isolated installation |
| Git | 2.x | Version control |

### Optional

| Tool | Purpose |
|------|---------|
| Black | Python formatting |
| Ruff | Python linting |

### Installation Check

```bash
python3 --version    # Python 3.9+
pipx --version       # pipx installed
git --version        # Git available
```

---

## Development Setup

### Quick Start

```bash
# Clone repository
git clone https://github.com/calinfaja/k-lean.git
cd k-lean

# Install in editable mode (recommended)
pipx install -e .

# Verify installation
kln --version       # Should show 1.0.0b6
kln doctor          # Check configuration
```

### Development Install with Symlinks

```bash
# Install editable + dev mode (symlinks data files)
pipx install -e . --force
kln install --dev

# This creates symlinks from ~/.claude/ to src/klean/data/
# Changes to data files are immediately reflected
```

### Development Install (pip)

```bash
# Install with dev tools
pip install -e ".[dev]"

# Or with all optional extras (telemetry, agent-sdk)
pip install -e ".[all,dev]"
```

---

## Project Layout

```
k-lean/
├── src/klean/              # Main package
│   ├── __init__.py         # Version
│   ├── cli.py              # CLI entry point (kln command)
│   ├── platform.py         # Cross-platform utilities (psutil, platformdirs)
│   ├── reviews.py          # Async review engine (httpx)
│   ├── hooks.py            # Hook entry points (4 functions)
│   ├── smol/               # SmolKLN agent framework
│   └── data/               # Installable assets
│       ├── scripts/        # Python scripts for knowledge DB
│       ├── commands/kln/   # Slash commands (.md)
│       ├── agents/         # SmolKLN agent definitions
│       └── config/         # Config templates
├── docs/                   # Documentation
│   └── architecture/       # Technical docs (this folder)
├── tests/                  # Test suite
├── CLAUDE.md               # Claude Code instructions
└── pyproject.toml          # Package metadata
```

---

## Development Workflow

### Daily Development Cycle

```bash
# 1. Make changes in src/klean/
vim src/klean/cli.py

# 2. Lint your changes
ruff check src/

# 3. If editing data/ files and NOT using --dev mode, sync
kln admin sync

# 4. Validate everything
kln doctor -f

# 5. Commit with conventional commit message
git add -A
git commit -m "feat: add new review mode"
```

### Sync Command (For non-dev installs)

After editing files in `src/klean/data/`, sync updates to installation:

```bash
kln admin sync           # Sync data files to ~/.claude/
kln admin sync --check   # Check without syncing (CI mode)
kln admin sync --clean   # Remove stale files
```

**Note:** If you installed with `kln install --dev`, syncing is not needed - symlinks update automatically.

### Live Debugging

```bash
kln admin debug            # Full dashboard
kln admin debug --compact  # Minimal output (for hooks)
```

---

## Coding Conventions

### Python Style

#### General Rules

| Rule | Tool | Setting |
|------|------|---------|
| Line length | Black/Ruff | 100 characters |
| Target version | Black/Ruff | Python 3.9 |
| Type hints | Manual | Required for public functions |
| Docstrings | Manual | Google style |

#### Naming Conventions

```python
# Classes: PascalCase
class ModelResolver:
    pass

# Functions/methods: snake_case
def get_healthy_models():
    pass

# Constants: UPPER_SNAKE_CASE
CLAUDE_DIR = Path.home() / ".claude"

# Private: leading underscore
def _parse_response():
    pass
```

#### Import Order

```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third party
import httpx
from rich.console import Console

# 3. Local
from klean import CLAUDE_DIR
```

#### Example Function

```python
def validate_model(model_name: str, timeout: int = 5) -> bool:
    """Check if a model responds to health checks.

    Args:
        model_name: The model identifier from LiteLLM.
        timeout: Request timeout in seconds.

    Returns:
        True if model responds successfully, False otherwise.

    Raises:
        ConnectionError: If LiteLLM proxy is unreachable.
    """
    try:
        response = httpx.post(
            "http://localhost:4000/chat/completions",
            json={"model": model_name, "messages": [{"role": "user", "content": "ping"}]},
            timeout=timeout,
        )
        return response.status_code == 200
    except httpx.ConnectError:
        raise ConnectionError("LiteLLM proxy not running")
```

### Cross-Platform Considerations

#### Use platform.py for paths

```python
from klean.platform import get_config_dir, get_runtime_dir

# Good - cross-platform
config_dir = get_config_dir()  # Windows: %APPDATA%\klean
runtime_dir = get_runtime_dir()  # Windows: %TEMP%\klean-{user}

# Bad - hardcoded paths (NEVER DO THIS)
config_dir = Path("/home/user/.config/litellm")
```

#### Use platform.py for process management

```python
from klean.platform import is_process_running, kill_process_tree, spawn_background

# Good - cross-platform
if is_process_running(pid):
    kill_process_tree(pid)

# Bad - Unix-only
os.kill(pid, 0)  # Doesn't work on Windows
```

### Thinking Model Response Handling

Some models return content in different fields:

```python
# Always check both response formats
content = response.get("content") or response.get("reasoning_content")

# The reviews.py module handles this automatically via _extract_content()
```

### Commit Messages

Follow conventional commits:

```
feat: add new droid for database review
fix: handle empty response from thinking models
docs: update architecture diagram
refactor: extract common path logic to platform.py
test: add integration test for KB server
chore: update dependencies
```

### Code Review Checklist

Before committing:

- [ ] No hardcoded paths (`grep -r "/home/" src/`)
- [ ] No embedded secrets (`grep -r "api_key" src/`)
- [ ] Cross-platform path handling (use platform.py)
- [ ] Thinking model responses handled (both formats)
- [ ] Error handling present
- [ ] `kln doctor` passes
- [ ] `ruff check src/` passes

---

## Testing

### Running Tests

```bash
python -m pytest tests/ -v
kln doctor            # Validate configuration
kln model list --health  # Check model availability
```

### Test Structure

```
tests/
├── unit/
│   ├── test_platform.py        # Cross-platform utilities
│   ├── test_hooks.py           # Hook entry points
│   ├── test_reviews.py         # Review engine
│   ├── test_knowledge_server.py # KB server
│   └── test_cli_integration.py # CLI commands
└── conftest.py                 # Shared fixtures
```

---

## Common Tasks

### Adding a New Script

1. Create script in `src/klean/data/scripts/`:

```python
#!/usr/bin/env python3
"""my-new-script.py - Description of what it does"""

import sys
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from kb_utils import find_project_root, get_server_port

def main():
    project = find_project_root()
    print(f"Project: {project}")

if __name__ == "__main__":
    main()
```

2. Make executable and sync:

```bash
chmod +x src/klean/data/scripts/my-new-script.py
kln admin sync  # If not using --dev mode
```

### Adding a New Command

1. Create `src/klean/data/commands/kln/mycommand.md`:

```markdown
# /kln:mycommand

Short description of what this command does.

## Usage

/kln:mycommand [options]

## Examples

/kln:mycommand --verbose
```

2. Sync:

```bash
kln admin sync
```

### Adding Hook Functionality

Hooks are Python entry points in `src/klean/hooks.py`. To add new functionality:

1. Edit `src/klean/hooks.py`:

```python
def prompt_handler() -> None:
    """Handle user prompts - add new keyword detection here."""
    data = _read_input()
    prompt = data.get("prompt", "")

    # Add your new keyword
    if "MyNewKeyword" in prompt:
        # Handle it
        result = handle_my_keyword(prompt)
        _output({"additionalContext": result})
        return
```

2. Test:

```bash
echo '{"prompt":"MyNewKeyword test"}' | kln-hook-prompt
```

### Adding a New SmolKLN Agent

1. Copy template:

```bash
cp src/klean/data/agents/TEMPLATE.md src/klean/data/agents/my-agent.md
```

2. Customize the agent definition

3. Sync and test:

```bash
kln admin sync
kln-smol my-agent "test task"
```

---

## Troubleshooting

### Diagnostic Commands

| Command | Purpose |
|---------|---------|
| `kln doctor` | Full system diagnostics |
| `kln doctor -f` | Diagnose + auto-fix |
| `kln status` | Component status |
| `kln model list --health` | Check model health |

### Issue: LiteLLM Proxy Not Running

**Symptoms:**
- `ERROR: LiteLLM proxy not running on localhost:4000`
- Reviews fail immediately

**Diagnosis:**
```bash
curl -s http://localhost:4000/models
```

**Fixes:**
```bash
kln start                # Start proxy
```

### Issue: No Healthy Models

**Symptoms:**
- `ERROR: No healthy models available`
- All models fail health check

**Fixes:**
```bash
# Check API key
cat ~/.config/litellm/.env

# Re-run setup wizard
kln init

# Verify NanoGPT subscription
kln doctor
```

### Issue: Knowledge Server Slow

**Symptoms:**
- Queries take ~17s instead of ~30ms
- `FindKnowledge` timeouts

**Diagnosis:**
```bash
kln status  # Check KB status
```

**Fixes:**
```bash
kln start -s knowledge   # Start KB server
```

### Issue: Python Environment Problems

**Symptoms:**
- `ERROR: K-LEAN Python not executable`
- Knowledge DB operations fail

**Fixes:**
```bash
kln install --component knowledge
# Or manually:
python3 -m venv ~/.venvs/knowledge-db
~/.venvs/knowledge-db/bin/pip install fastembed numpy
```

### Issue: Config Validation Errors

**Symptoms:**
- `os.environ` not substituting
- API key not found

**Fix:** Remove quotes from `os.environ/KEY`:

```yaml
# Wrong
api_key: "os.environ/NANOGPT_API_KEY"

# Correct
api_key: os.environ/NANOGPT_API_KEY
```

### Log Locations

| Component | Path |
|-----------|------|
| LiteLLM | `~/.klean/logs/litellm.log` |
| KB Server | `~/.klean/logs/kb-server.log` |
| Debug | `~/.klean/logs/debug.log` |
| Reviews | `/tmp/claude-reviews/` |
| Timeline | `.knowledge-db/timeline.txt` (per-project) |

### Quick Recovery

```bash
# Full restart
kln stop
kln start -s all

# Reset knowledge DB (per-project)
rm -rf .knowledge-db/
# Will auto-recreate on next /kln:learn or FindKnowledge

# Complete reinstall
kln uninstall
pipx uninstall kln-ai
pipx install kln-ai
kln install
```

---

## Release Checklist

### Package Info

- **Name**: `kln-ai` (k-lean and kln were taken on PyPI)
- **Install**: `pipx install kln-ai`
- **URL**: https://pypi.org/project/kln-ai/
- **Workflow**: `.github/workflows/publish.yml`

### Version Sources

Version is maintained in TWO files (CI validates they match):

1. `pyproject.toml` -> `version = "X.Y.Z"`
2. `src/klean/__init__.py` -> `__version__ = "X.Y.Z"`

No separate VERSION file - `prepare-release.sh` reads from pyproject.toml.

### Pre-Release

```bash
# 1. Run tests
python -m pytest tests/ -v

# 2. Check configuration
kln doctor

# 3. Lint code
ruff check src/ --select=F,E722

# 4. Verify sync
kln admin sync --check

# 5. Verify release readiness
./src/klean/data/scripts/prepare-release.sh --check
```

### Release Process

#### Step 1: Update Version

```bash
# Edit both files with new version
vim pyproject.toml                    # version = "1.0.0b7"
vim src/klean/__init__.py             # __version__ = "1.0.0b7"

# Verify they match
./src/klean/data/scripts/prepare-release.sh --check

# Commit
git add -A
git commit -m "chore: bump version to 1.0.0b7"
git push
```

**Version Format** (PEP 440):
```
1.0.0b1  <- beta
1.0.0    <- stable
1.0.1    <- patch
1.1.0    <- minor
```

#### Step 2: Run Publish Workflow

1. Go to: **Actions > Publish to PyPI > Run workflow**
2. Enter version (must match pyproject.toml)
3. Click **Run workflow**

#### Step 3: Workflow Runs (automatic)

```
verify   -> Check version matches pyproject.toml and __init__.py
test     -> Lint, pytest, sync check
publish  -> Build, twine check, upload to PyPI
verify   -> Check PyPI API, test install in fresh venv
tag      -> Create git tag (v1.0.0b7)
```

#### Step 4: Create GitHub Release

1. Go to Releases, select the new tag
2. Click "Generate release notes"
3. Publish

### Local Build (optional)

```bash
# Build locally before GitHub Actions
python -m build
twine check dist/*

# Test install
pipx install dist/*.whl --force
kln --version
```

### Troubleshooting

| Issue | Fix |
|-------|-----|
| Version mismatch | Update both pyproject.toml AND __init__.py |
| Auth failed | Check `PYPI_TOKEN` in GitHub Secrets |
| Version exists | PyPI rejects duplicates - bump version |
| sdist missing files | Check MANIFEST.in includes all needed files |

---

## Dependencies Reference

### Core (included in base install)

| Package | Purpose |
|---------|---------|
| click, rich | CLI framework |
| pyyaml, httpx | Config & HTTP |
| psutil, platformdirs | Cross-platform utilities |
| fastembed, numpy | Knowledge DB |
| smolagents[litellm] | SmolKLN agents |
| ddgs, markdownify, lizard | Agent tools |

### Optional Extras

| Extra | Packages | Purpose |
|-------|----------|---------|
| `[telemetry]` | arize-phoenix, opentelemetry | Agent tracing |
| `[agent-sdk]` | anthropic | Claude Agent SDK |
| `[dev]` | pytest, black, ruff | Development |

---

*Last updated: 2026-01*
