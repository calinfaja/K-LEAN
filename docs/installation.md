# Installation

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Claude Code | 2.0+ | `claude --version` |
| pipx | any | `pipx --version` |
| git | any | `git --version` |

## Install

```bash
# 1. Install K-LEAN
pipx install kln-ai

# 2. Initialize (installs components + configures provider)
kln init

# 3. Verify
kln doctor
```

**From source (development):**
```bash
git clone https://github.com/calinfaja/k-lean.git
cd k-lean
pipx install -e .
kln install
```

## Configure LiteLLM

Provider configuration is included in `kln init`. To add providers later:

```bash
kln provider add nanogpt --api-key $KEY
kln provider add openrouter --api-key $KEY
```

**Providers:**
- **NanoGPT**: https://nano-gpt.com (8 recommended models)
- **OpenRouter**: https://openrouter.ai (3 recommended models)

**Config files:**
```
~/.config/litellm/
├── config.yaml    # Model definitions
└── .env           # API keys (chmod 600)
```

## Start Services

```bash
kln start              # LiteLLM proxy only
kln start -s all       # LiteLLM + Knowledge server
kln start --telemetry  # Also start Phoenix telemetry server
```

## Optional: Agent Telemetry

Install Phoenix for SmolKLN agent tracing:

```bash
pipx inject kln-ai 'kln-ai[telemetry]'
```

This installs:
- `arize-phoenix` - Local OpenTelemetry collector with web UI
- `openinference-instrumentation-smolagents` - Auto-instrumentation for smolagents

**Usage:**
```bash
kln start --telemetry                 # Start Phoenix on :6006
kln-smol security-auditor "audit" -t     # Run agent with tracing
```

View traces at `http://localhost:6006`

## Verify

```bash
kln status             # Component status
kln model list --health  # Model health
```

## Uninstall

```bash
kln uninstall
pipx uninstall kln-ai
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| LiteLLM not starting | `lsof -i :4000` (check port) |
| Models unhealthy | Check API key in `~/.config/litellm/.env` |
| Config errors | `kln doctor -f` (auto-fix) |
