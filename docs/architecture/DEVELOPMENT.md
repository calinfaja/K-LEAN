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
| curl | Any | Health checks |

### Optional

| Tool | Purpose |
|------|---------|
| ShellCheck | Shell script linting |
| Black | Python formatting |
| Ruff | Python linting |

### Installation Check

```bash
python3 --version    # Python 3.9+
pipx --version       # pipx installed
git --version        # Git available
curl --version       # curl available
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
kln --version       # Should show 1.0.0b3
kln doctor          # Check configuration
kln test            # Run test suite
```

### Development Install

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
│   ├── smol/               # SmolKLN agent framework
│   └── data/               # Installable assets
│       ├── scripts/        # Shell & Python scripts
│       ├── commands/kln/   # Slash commands (.md)
│       ├── hooks/          # Claude Code hooks
│       ├── agents/         # SmolKLN agent definitions
│       ├── core/           # Review engine & prompts
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

# 3. Run tests
kln test

# 4. If editing data/ files, sync
kln sync

# 5. Validate everything
kln doctor -f

# 6. Commit with conventional commit message
git add -A
git commit -m "feat: add new review mode"
```

### Sync Command (Important!)

After editing files in `src/klean/data/`, sync updates to installation:

```bash
kln sync           # Sync data files to ~/.claude/
kln sync --check   # Check without syncing (CI mode)
kln sync --clean   # Remove stale files
```

**When to sync:**
- Added/modified scripts in `data/scripts/`
- Added/modified commands in `data/commands/`
- Added/modified hooks in `data/hooks/`
- Added/modified agents in `data/agents/`

### Live Debugging

```bash
kln debug              # Full dashboard
kln debug --compact    # Minimal (for hooks)
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

### Shell Style

#### General Rules

| Rule | Value |
|------|-------|
| Linter | ShellCheck |
| Shebang | `#!/usr/bin/env bash` |
| Safety | `set -euo pipefail` (scripts only, not hooks) |

#### Naming Conventions

```bash
# Scripts: kebab-case
quick-review.sh
knowledge-query.sh

# Functions: snake_case
get_agent_system_prompt() {
    # ...
}

# Exported variables: UPPER_SNAKE_CASE
export KB_PYTHON="..."

# Local variables: lower_snake_case
local model_name="$1"
```

#### Path Handling (Critical!)

**Always use kb-root.sh for paths:**

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true

# Good - uses variables from kb-root.sh
"$KB_PYTHON" "$KB_SCRIPTS_DIR/knowledge_db.py"

# Bad - hardcoded paths (NEVER DO THIS)
/home/user/.venvs/knowledge-db/bin/python
~/.claude/scripts/knowledge_db.py
```

#### Thinking Model Response Handling

Models may return content in different fields:

```bash
# Always check both response formats
content=$(echo "$response" | jq -r '.choices[0].message.content // empty')
if [ -z "$content" ]; then
    content=$(echo "$response" | jq -r '.choices[0].message.reasoning_content // empty')
fi
```

#### Error Handling

```bash
# Check command exists
if ! command -v curl &>/dev/null; then
    echo "Error: curl required" >&2
    exit 1
fi

# Check file exists
if [ ! -f "$config_file" ]; then
    log_debug "Config not found, using defaults"
fi

# Use log_debug for debugging
log_debug "Processing model: $model_name"
```

### Commit Messages

Follow conventional commits:

```
feat: add new droid for database review
fix: handle empty response from thinking models
docs: update architecture diagram
refactor: extract common path logic to kb-root.sh
test: add integration test for KB server
chore: update dependencies
```

### Code Review Checklist

Before committing:

- [ ] No hardcoded paths (`grep -r "/home/" src/`)
- [ ] No embedded secrets (`grep -r "api_key" src/`)
- [ ] Shell scripts source kb-root.sh
- [ ] Thinking model responses handled (both formats)
- [ ] Error handling present
- [ ] `kln test` passes
- [ ] `ruff check src/` passes

---

## Testing

### Running Tests

```bash
kln test              # Run full test suite (27 tests)
kln doctor            # Validate configuration
kln models --health   # Check model availability
```

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Installation Structure | 4 | Directory structure, files exist |
| Scripts Executable | 4 | Scripts have +x permission |
| KLN Commands | 9 | Slash commands work |
| Hooks | 3 | Hook scripts execute |
| LiteLLM Service | 1 | Proxy responds |
| Knowledge System | 2 | KB operations work |
| Nano Profile | 3 | Claude-nano works |
| SmolKLN Agents | 1 | Agent framework |

### Test Output Example

```
K-LEAN Test Suite
=================
Running 27 tests...

[OK] Installation structure valid
[OK] Scripts executable
[OK] KLN commands installed
[OK] Hooks configured
[OK] LiteLLM proxy responding
[OK] Knowledge DB operational
[OK] Nano profile functional
[OK] SmolKLN agents available

27/27 tests passed
```

---

## Common Tasks

### Adding a New Script

1. Create script in `src/klean/data/scripts/`:

```bash
#!/usr/bin/env bash
# my-new-script.sh - Description of what it does

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true

set -euo pipefail

# Your script logic here
echo "Hello from my-new-script"
```

2. Make executable and sync:

```bash
chmod +x src/klean/data/scripts/my-new-script.sh
kln sync
```

3. Test:

```bash
~/.claude/scripts/my-new-script.sh
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
kln sync
```

### Adding a New Hook

1. Create `src/klean/data/hooks/my-hook.sh`:

```bash
#!/usr/bin/env bash
# Hook: Runs on specific events
# Note: Do NOT use set -euo pipefail in hooks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../scripts/kb-root.sh" 2>/dev/null || true

# Hook logic here (must be non-blocking)
```

2. Register in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": ["~/.claude/hooks/my-hook.sh"]
  }
}
```

### Adding a New SmolKLN Agent

1. Copy template:

```bash
cp src/klean/data/agents/TEMPLATE.md src/klean/data/agents/my-agent.md
```

2. Customize the agent definition

3. Sync and test:

```bash
kln sync
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
| `kln models --health` | Check model health |

### Issue: LiteLLM Proxy Not Running

**Symptoms:**
- `ERROR: LiteLLM proxy not running on localhost:4000`
- Reviews fail immediately

**Diagnosis:**
```bash
curl -s http://localhost:4000/models
lsof -i :4000
```

**Fixes:**
```bash
kln start                           # Start proxy
~/.claude/scripts/start-litellm.sh     # Direct script
```

### Issue: No Healthy Models

**Symptoms:**
- `ERROR: No healthy models available`
- All models fail health check

**Diagnosis:**
```bash
~/.claude/scripts/health-check.sh
~/.claude/scripts/get-models.sh
```

**Fixes:**
```bash
# Check API key
cat ~/.config/litellm/.env

# Re-run setup wizard
kln setup

# Verify NanoGPT subscription
kln doctor
```

### Issue: Knowledge Server Slow

**Symptoms:**
- Queries take ~17s instead of ~30ms
- `FindKnowledge` timeouts

**Diagnosis:**
```bash
ls -la /tmp/kb-*.sock              # Check socket exists
source ~/.claude/scripts/kb-root.sh
is_kb_server_running               # Check server status
```

**Fixes:**
```bash
kln start -s knowledge          # Start KB server
rm /tmp/kb-*.sock                  # Clean stale socket
~/.claude/scripts/knowledge-server.py start
```

### Issue: Python Environment Problems

**Symptoms:**
- `ERROR: K-LEAN Python not executable`
- Knowledge DB operations fail

**Diagnosis:**
```bash
ls -la ~/.venvs/knowledge-db/bin/python
~/.venvs/knowledge-db/bin/python --version
```

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

**Diagnosis:**
```bash
kln doctor
cat ~/.config/litellm/config.yaml | grep os.environ
```

**Fix:** Remove quotes from `os.environ/KEY`:

```yaml
# Wrong
api_key: "os.environ/NANOGPT_API_KEY"

# Correct
api_key: os.environ/NANOGPT_API_KEY
```

### Issue: Review Output Not Saved

**Symptoms:**
- Reviews complete but no file saved
- Can't find review history

**Diagnosis:**
```bash
ls -la .claude/kln/
ls -la /tmp/claude-reviews/
```

**Fix:** Ensure you're in a git repository (required for `find_project_root`).

### Issue: Symlinks Broken

**Symptoms:**
- Commands not found
- Scripts point to wrong locations

**Fix:**
```bash
pipx install -e . --force
kln sync --clean
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
pytest tests/ -v --ignore=tests/core/

# 2. Check configuration
kln doctor

# 3. Lint code
ruff check src/ --select=F,E722

# 4. Verify sync
kln sync --check

# 5. Verify release readiness
./src/klean/data/scripts/prepare-release.sh --check
```

### Release Process

#### Step 1: Update Version

```bash
# Edit both files with new version
vim pyproject.toml                    # version = "1.0.0b2"
vim src/klean/__init__.py             # __version__ = "1.0.0b2"

# Verify they match
./src/klean/data/scripts/prepare-release.sh --check

# Commit
git add -A
git commit -m "chore: bump version to 1.0.0b2"
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
tag      -> Create git tag (v1.0.0b2)
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
