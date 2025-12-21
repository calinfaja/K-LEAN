# Installation

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Claude Code | 2.0+ | `claude --version` |
| pipx | any | `pipx --version` |

## Install

```bash
# 1. Install K-LEAN
pipx install k-lean

# 2. Install components (symlinks scripts, commands, hooks)
k-lean install

# 3. Verify
k-lean doctor
```

## Configure LiteLLM

```bash
# Interactive setup wizard
~/.claude/scripts/setup-litellm.sh
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
```

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
