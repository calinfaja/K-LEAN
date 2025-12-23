# Installation

> **Note:** K-LEAN is in beta. Install from source until PyPI release.

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Claude Code | 2.0+ | `claude --version` |
| pipx | any | `pipx --version` |
| git | any | `git --version` |

## Install

```bash
# 1. Clone repository
git clone https://github.com/calinfaja/k-lean.git
cd k-lean

# 2. Install K-LEAN
pipx install .

# 3. Install components (symlinks scripts, commands, hooks)
k-lean install

# 4. Verify
k-lean doctor
```

**After PyPI release:** `pipx install k-lean`

## Configure LiteLLM

```bash
# Interactive setup wizard
k-lean setup
```

**Providers:**
- **NanoGPT**: https://nano-gpt.com (12 models, subscription)
- **OpenRouter**: https://openrouter.ai (6 models, pay-per-use)

**Config files:**
```
~/.config/litellm/
├── config.yaml    # Model definitions
└── .env           # API keys (chmod 600)
```

## Start Services

```bash
k-lean start              # LiteLLM proxy only
k-lean start -s all       # LiteLLM + Knowledge server
k-lean start --telemetry  # Also start Phoenix telemetry server
```

## Optional: Agent Telemetry

Install Phoenix for SmolKLN agent tracing:

```bash
pipx inject k-lean 'k-lean[telemetry]'
```

This installs:
- `arize-phoenix` - Local OpenTelemetry collector with web UI
- `openinference-instrumentation-smolagents` - Auto-instrumentation for smolagents

**Usage:**
```bash
k-lean start --telemetry                      # Start Phoenix on :6006
smol-kln.py security-auditor "audit" -t       # Run agent with tracing
```

View traces at `http://localhost:6006`

## Verify

```bash
k-lean status             # Component status
k-lean models --health    # Model health
healthcheck               # In Claude (tests all models)
```

## Uninstall

```bash
k-lean uninstall
pipx uninstall k-lean
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| LiteLLM not starting | `lsof -i :4000` (check port) |
| Models unhealthy | Check API key in `~/.config/litellm/.env` |
| Config errors | `k-lean doctor -f` (auto-fix) |

See [.agents/troubleshooting.md](../.agents/troubleshooting.md) for detailed diagnostics.
