# K-LEAN LiteLLM Integration

## Overview

K-LEAN uses **LiteLLM proxy** to route requests to multiple LLM providers.

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude    │    │     LiteLLM      │    │    NanoGPT      │
│   Code      │◄──►│  localhost:4000  │◄──►│   12 models     │
│  (scripts)  │    │                  │    ├─────────────────┤
└─────────────┘    │  /chat/completions│    │   OpenRouter    │
                   │  /v1/models       │    │   6 models      │
                   └──────────────────┘    └─────────────────┘
```

## Providers

| Provider | Models | Config File |
|----------|--------|-------------|
| NanoGPT | 12 | `~/.config/litellm/config.yaml` |
| OpenRouter | 6 | `~/.config/litellm/openrouter.yaml` |

### NanoGPT Models

```yaml
# Sample models (via subscription)
- coding-qwen      # Qwen 2.5 Coder
- agent-kimi       # Kimi K2 (thinking)
- tools-glm        # GLM-4 Plus
- deepseek         # DeepSeek R1 (thinking)
- hermes-4-scout   # Hermes 4 Scout
- minimax          # MiniMax-01 (thinking)
```

### Thinking Models

These models return `reasoning_content` instead of `content`:
- DeepSeek R1
- GLM-4
- Kimi K2
- MiniMax-01

## Configuration

### File Locations

```
~/.config/litellm/
├── config.yaml      # NanoGPT models
├── openrouter.yaml  # OpenRouter models
└── .env             # API keys (chmod 600)
```

### Environment Variables

```bash
# Required
NANOGPT_API_KEY=your-api-key

# Auto-detected (subscription vs pay-per-use)
NANOGPT_API_BASE=https://nano-gpt.com/api/subscription/v1
# or
NANOGPT_API_BASE=https://nano-gpt.com/api/v1
```

### Config Syntax

```yaml
model_list:
  - model_name: coding-qwen
    litellm_params:
      model: openai/Qwen/Qwen2.5-Coder-32B-Instruct
      api_key: os.environ/NANOGPT_API_KEY  # NO quotes!
      api_base: os.environ/NANOGPT_API_BASE
```

**Critical:** `os.environ/KEY` must NOT be quoted. This is a common mistake:
```yaml
# Wrong - breaks env var substitution
api_key: "os.environ/NANOGPT_API_KEY"

# Correct
api_key: os.environ/NANOGPT_API_KEY
```

## Setup

### Initial Setup

```bash
~/.claude/scripts/setup-litellm.sh
```

**Wizard steps:**
1. Choose provider (NanoGPT/OpenRouter)
2. Enter API key
3. Auto-detect subscription status
4. Generate config files

### Starting LiteLLM

```bash
k-lean start              # Start proxy
k-lean start --background # Start in background
```

### Checking Status

```bash
k-lean doctor       # Validate config + subscription
k-lean models       # List available models
k-lean models --health  # Check model health
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `setup-litellm.sh` | Interactive setup wizard |
| `start-litellm.sh` | Start proxy with validation |
| `health-check.sh` | Full health check |
| `health-check-model.sh` | Single model health |
| `get-models.sh` | List models from /v1/models |
| `get-healthy-models.sh` | Filter healthy models |
| `validate-model.sh` | Verify model exists |

## Health Checking

### Model Health

```bash
~/.claude/scripts/health-check-model.sh coding-qwen
```

**Tests:** POST to `/chat/completions` with simple prompt

### Full System Health

```bash
~/.claude/scripts/health-check.sh
```

**Checks:**
1. LiteLLM proxy responding
2. Each model reachable
3. Response format correct

## Dynamic Model Discovery

Scripts use dynamic discovery, not hardcoded lists:

```bash
# Get available models
models=$(curl -s http://localhost:4000/v1/models | jq -r '.data[].id')

# Filter healthy
healthy=$(~/.claude/scripts/get-healthy-models.sh)
```

## Troubleshooting

### "Invalid session" Error

```bash
k-lean doctor --auto-fix
# Auto-detects subscription vs pay-per-use endpoint
```

### Proxy Not Starting

```bash
# Check if already running
lsof -i :4000

# Check logs
cat ~/.claude/k-lean/logs/litellm.log
```

### Models Unhealthy

```bash
k-lean models --health
# Shows which models are down

# Common causes:
# - NanoGPT subscription expired
# - Model temporarily unavailable
# - Rate limiting
```

### Config Validation

`k-lean doctor` checks for:
- Missing .env file
- Quoted `os.environ/` (breaks substitution)
- Missing NANOGPT_API_BASE
- Invalid subscription

## Implementation

Main scripts:
- `src/klean/data/scripts/setup-litellm.sh`
- `src/klean/data/scripts/start-litellm.sh`
- `src/klean/data/scripts/health-check.sh`

CLI integration: `src/klean/cli.py` (doctor, models commands)

---
*Back to [AGENTS.md](../AGENTS.md) for overview*
