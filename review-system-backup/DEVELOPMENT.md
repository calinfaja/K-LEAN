# K-LEAN Development Guide

> Minimal reference for developers and AI agents maintaining this project.

## AI Agent Quick Start

**If you're Claude Code or another AI starting fresh:**

1. **Read this file first** - It has everything you need
2. **Understand the dual-source model** - Root dirs are canonical, `src/klean/data/` is synced copy
3. **Before ANY release:** Run `k-lean sync --check` - it must pass
4. **After changing files in root dirs:** Run `k-lean sync`
5. **Follow Release Workflow exactly** - Each step has verification

**Key files to understand:**
- `src/klean/cli.py` - All CLI commands (1950+ lines)
- `src/klean/data/core/klean_core.py` - Review/model logic
- `pyproject.toml` - Package configuration

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

## Release Workflow (Complete Checklist)

Follow these steps exactly. Each step has a verification.

### Step 1: Sync Package Data
```bash
k-lean sync --clean      # Sync + remove stale files
k-lean sync --check      # MUST show "Package is in sync"
```
**Verify:** Exit code 0, message shows "in sync"

### Step 2: Run Tests
```bash
k-lean status            # All components should show OK
k-lean doctor            # Should find no issues (or fix with -f)
```
**Verify:** No errors, all components green

### Step 3: Test Installation (Clean)
```bash
# Test in temporary venv
python -m venv /tmp/test-klean
source /tmp/test-klean/bin/activate
pip install -e .
k-lean install -y
k-lean status
deactivate
rm -rf /tmp/test-klean
```
**Verify:** Install succeeds, status shows all OK

### Step 4: Update Version (3 files - MUST match)
```bash
# Check current version
cat VERSION
grep 'version = ' pyproject.toml
grep '__version__' src/klean/__init__.py
```

Edit these 3 files with the NEW version (e.g., 1.0.1):
1. `VERSION` - Just the version string
2. `pyproject.toml` - Line: `version = "1.0.1"`
3. `src/klean/__init__.py` - Line: `__version__ = "1.0.1"`

**Verify:** All 3 show same version:
```bash
cat VERSION && grep 'version = ' pyproject.toml && grep '__version__' src/klean/__init__.py
```

### Step 5: Commit Release
```bash
git add -A
git status               # Review changes
git commit -m "Release v1.0.1"
git tag -a v1.0.1 -m "Release v1.0.1"
```
**Verify:** `git log --oneline -1` shows release commit

### Step 6: Build Package
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Build
pip install build
python -m build
```
**Verify:** `ls dist/` shows both `.whl` and `.tar.gz` files

### Step 7: Test Built Package
```bash
python -m venv /tmp/test-release
source /tmp/test-release/bin/activate
pip install dist/*.whl
k-lean --version         # Should show new version
k-lean status
deactivate
rm -rf /tmp/test-release
```
**Verify:** Version correct, status OK

### Step 8: Upload to PyPI
```bash
pip install twine
twine check dist/*       # Validate package
twine upload dist/*      # Upload (needs PyPI credentials)
```
**Verify:** No errors, package visible on pypi.org

### Step 9: Push to Git
```bash
git push origin main
git push origin v1.0.1   # Push tag
```
**Verify:** GitHub shows new tag/release

### Quick Release (After You Know the Process)
```bash
# One-liner checklist
k-lean sync --clean && k-lean sync --check && k-lean doctor && \
  echo "Ready for release - update VERSION, pyproject.toml, __init__.py"
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
