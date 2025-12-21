# K-LEAN Development Guide

## Prerequisites

- Python 3.9+
- pipx (recommended) or pip
- Git
- curl (for health checks)

## Development Setup

```bash
# Clone repository
git clone https://github.com/calinfaja/K-LEAN-Companion.git
cd K-LEAN-Companion

# Install in editable mode
pipx install -e .

# Verify installation
k-lean --version    # Should show 1.0.0-beta
k-lean doctor       # Check configuration
k-lean test         # Run 27 tests
```

## Project Layout

```
K-LEAN-Companion/
├── src/klean/           # Main package
│   ├── cli.py           # CLI entry point
│   └── data/            # Installable assets
├── config/              # Config templates
├── docs/                # Documentation
├── tests/               # Test suite
├── .agents/             # AI agent context (this folder)
├── AGENTS.md            # Universal AI instructions
├── CLAUDE.md            # Claude Code specific
└── pyproject.toml       # Package metadata
```

## Development Workflow

### Making Changes

1. **Edit source files** in `src/klean/`
2. **Test locally**: `k-lean test`
3. **Sync to package** (if editing data/): `k-lean sync`
4. **Commit**: Follow conventional commits

### Sync Command

After editing files in `src/klean/data/`, sync updates:

```bash
k-lean sync           # Sync data files
k-lean sync --check   # Check without syncing (CI mode)
k-lean sync --clean   # Remove stale files
```

### Testing

```bash
k-lean test           # Run all 27 tests
k-lean doctor         # Validate configuration
k-lean models --health  # Check model availability
```

**Test Categories:**
1. Installation Structure (4 tests)
2. Scripts Executable (4 tests)
3. KLN Commands (9 tests)
4. Hooks (3 tests)
5. LiteLLM Service (1 test)
6. Knowledge System (2 tests)
7. Nano Profile (3 tests)
8. Factory Droids (1 test)

## Release Checklist

```bash
# 1. Run full test suite
k-lean test

# 2. Check for issues
k-lean doctor

# 3. Verify sync
k-lean sync --check

# 4. Update version in:
#    - src/klean/__init__.py
#    - pyproject.toml
#    - src/klean/data/core/config.yaml

# 5. Commit and tag
git add -A
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

## Common Tasks

### Adding a New Script

1. Create script in `src/klean/data/scripts/`
2. Make executable: `chmod +x script.sh`
3. Source `kb-root.sh` for paths:
   ```bash
   #!/usr/bin/env bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true
   ```
4. Run `k-lean sync`

### Adding a New Command

1. Create `src/klean/data/commands/kln/command.md`
2. Follow existing command structure
3. Run `k-lean sync`

### Adding a New Hook

1. Create `src/klean/data/hooks/hook-name.sh`
2. Register in `~/.claude/settings.json`
3. Test with `k-lean debug`

### Adding a New Droid

1. Copy `src/klean/data/droids/TEMPLATE.md`
2. Customize for specialization
3. Register in `~/.factory/droids/`

## Debugging

### Live Monitoring

```bash
k-lean debug              # Full dashboard
k-lean debug --compact    # Minimal (for hooks)
```

### Log Locations

| Component | Log Path |
|-----------|----------|
| LiteLLM | `~/.claude/k-lean/logs/litellm.log` |
| Reviews | `~/.claude/reviews/` |
| KB Server | stdout (use debug mode) |

### Common Issues

| Issue | Solution |
|-------|----------|
| "Invalid session" | Run `k-lean doctor --auto-fix` |
| KB not starting | Check `~/.venvs/knowledge-db/` exists |
| Models unhealthy | Verify NanoGPT subscription |
| Symlinks broken | Reinstall: `pipx install -e . --force` |

---
*See [coding-conventions.md](coding-conventions.md) for style guide*
