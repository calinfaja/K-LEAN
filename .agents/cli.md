# K-LEAN CLI Reference

## Command Overview

| Command | Purpose | Speed |
|---------|---------|-------|
| `k-lean doctor` | Validate config (.env, subscription, services) | ~3s |
| `k-lean doctor -f` | Auto-fix issues | ~5s |
| `k-lean status` | Show installed components & services | ~2s |
| `k-lean models` | List available models | ~1s |
| `k-lean models --health` | Check model health | ~60s |
| `k-lean models --test` | Test each model with latency | Slow |
| `k-lean start` | Start LiteLLM proxy | ~3s |
| `k-lean stop` | Stop services | ~1s |
| `k-lean install` | Install components | Varies |
| `k-lean uninstall` | Remove components | ~5s |
| `k-lean sync` | Sync package data (dev) | ~2s |
| `k-lean test` | Run test suite | ~10s |
| `k-lean test-model` | Test specific model | ~5s |
| `k-lean version` | Show version info | Instant |
| `k-lean debug` | Live monitoring dashboard | Continuous |

## User Mental Model

```
"Is my SYSTEM configured?" → k-lean doctor
"What's RUNNING now?"      → k-lean status
"Are my MODELS working?"   → k-lean models --health
```

## Command Details

### doctor

Validates configuration and services.

```bash
k-lean doctor           # Check everything
k-lean doctor --auto-fix  # Fix issues automatically
k-lean doctor -f        # Short form
```

**Checks performed:**
- .env file exists with NANOGPT_API_KEY
- NANOGPT_API_BASE configured (auto-detects subscription vs pay-per-use)
- NanoGPT subscription status + remaining quota
- LiteLLM proxy running
- Knowledge server running
- Hardcoded API keys (security check)

### status

Shows installed components and running services.

```bash
k-lean status
```

**Output includes:**
- Scripts count (symlinked status)
- KLN commands (9)
- SuperClaude availability (optional)
- Hooks (5)
- Factory Droids (8)
- Knowledge DB (per-project status + entry count)
- LiteLLM Proxy (model count + provider)
- Factory CLI version

### models

Lists and tests available LLM models.

```bash
k-lean models           # List all models
k-lean models --health  # Check health (calls each model)
k-lean models --test    # Full latency test
```

### start / stop

Controls K-LEAN services.

```bash
k-lean start                    # Start LiteLLM (default)
k-lean start -s knowledge       # Start Knowledge server
k-lean start -s all             # Start both services
k-lean start -p 4001            # Custom port
k-lean stop                     # Stop for current project
k-lean stop --all-projects      # Stop all KB servers
k-lean stop -s litellm          # Stop specific service
```

### install / uninstall

Manages K-LEAN components.

```bash
k-lean install                    # Full installation
k-lean install --component scripts  # Specific component
k-lean install --dev              # Dev mode (symlinks)

k-lean uninstall                  # Remove all
k-lean uninstall --yes            # Skip confirmation
```

**Components:** all, scripts, commands, hooks, droids, config, core, knowledge

### sync

Syncs data files (development tool).

```bash
k-lean sync           # Sync all data
k-lean sync --check   # Verify sync status (CI mode)
k-lean sync --clean   # Remove stale files
```

### test

Runs comprehensive test suite.

```bash
k-lean test
```

**Tests across 8 categories:**
1. Installation Structure
2. Scripts Executable
3. KLN Commands
4. Hooks
5. LiteLLM Service
6. Knowledge System
7. Nano Profile
8. Factory Droids

**Exit code:** 0 = all pass, 1 = failures (CI-friendly)

### debug

Live monitoring dashboard.

```bash
k-lean debug              # Full dashboard
k-lean debug --compact    # Minimal output (for hooks)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error / test failures |
| 2 | Configuration error |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `KLEAN_KB_PYTHON` | Override Python path |
| `KLEAN_SCRIPTS_DIR` | Override scripts location |
| `KLEAN_SOCKET_DIR` | Override socket directory |
| `KLEAN_CONFIG_DIR` | Override config directory |

## Implementation

Main CLI: `src/klean/cli.py` (~2300 lines)

Uses:
- `click` for CLI framework
- `rich` for terminal output
- `httpx` for async HTTP

---
*See [knowledge-db.md](knowledge-db.md) for KB details*
