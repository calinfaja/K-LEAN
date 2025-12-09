# K-LEAN Installation Guide

Complete setup guide for the K-LEAN Multi-Model Code Review and Knowledge Capture System.

## Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Claude Code | Latest | `claude --version` |
| Python | 3.9+ | `python3 --version` |
| Git | Any | `git --version` |
| curl | Any | `curl --version` |

## Quick Install

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/claudeAgentic.git
cd claudeAgentic/review-system-backup

# 2. Run installer
./install.sh --full

# 3. Verify
./test.sh
```

## Detailed Installation

### Step 1: Install LiteLLM

```bash
pipx install litellm
```

### Step 2: Run Installer

```bash
./install.sh --full
```

The installer will:
- Install scripts, commands, and hooks
- Setup knowledge database system
- Create nano profile
- Configure LiteLLM (optional interactive wizard)

### Step 3: Configure LiteLLM Provider

The installer runs an interactive setup wizard:

```
Select your provider:
  1) NanoGPT (recommended, 6 models)
  2) OpenRouter (diverse model selection)
  3) Skip setup (use existing config)
```

**Provider Options:**

| Provider | API Key | Cost | Setup |
|----------|---------|------|-------|
| **NanoGPT** | $0.50/1M tokens | Lowest | https://nano-gpt.com |
| **OpenRouter** | $0-10/month | Low-Mid | https://openrouter.ai |

### Step 4: Start LiteLLM

```bash
~/.claude/scripts/litellm-start.sh
```

Or manually:
```bash
source ~/.config/litellm/.env && litellm --config ~/.config/litellm/config.yaml
```

### Step 5: Setup Profile Aliases

Add to `~/.bashrc`:

```bash
# K-LEAN Profile System
alias claude-nano='CLAUDE_CONFIG_DIR=~/.claude-nano claude'
alias claude-status='if [ -n "$CLAUDE_CONFIG_DIR" ]; then echo "Profile: nano ($CLAUDE_CONFIG_DIR)"; else echo "Profile: native (~/.claude/)"; fi'
```

Then reload: `source ~/.bashrc`

### Step 6: Verify Installation

```bash
./test.sh        # Should show 18 tests passed
healthcheck      # Check all models
claude-status    # Should show "Profile: native"
```

## Profile System

K-LEAN uses two profiles:

| Command | Profile | Config Directory | API |
|---------|---------|------------------|-----|
| `claude` | Native | `~/.claude/` | Anthropic |
| `claude-nano` | NanoGPT | `~/.claude-nano/` | LiteLLM proxy |

Both can run **simultaneously** in different terminals!

```bash
# Terminal 1: Native Claude
claude

# Terminal 2: NanoGPT Claude (parallel!)
claude-nano
```

## Knowledge Server

The installer configures the knowledge server to auto-start on terminal open. This keeps txtai embeddings in memory for fast searches (~30ms vs ~17s cold start).

```bash
# Check if running
ls -la /tmp/knowledge-server.sock

# Manual start (if needed)
cd ~/claudeAgentic && ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-server.py start &

# Test fast search
~/.claude/scripts/knowledge-query.sh "authentication"
```

## Testing Models

Test the deep audit system with each LiteLLM model:

```bash
# Test with default 3 reliable models (qwen, kimi, glm)
~/.claude/scripts/test-deep-audit.sh

# Test all 6 models
~/.claude/scripts/test-deep-audit.sh --all

# Test single model
~/.claude/scripts/test-deep-audit.sh --model glm

# Test specific commit range
~/.claude/scripts/test-deep-audit.sh --compare HEAD~3 HEAD

# Run all tests in parallel
~/.claude/scripts/test-deep-audit.sh --all --parallel
```

**Options:**
| Option | Description |
|--------|-------------|
| `--all` | Test all 6 models (default: 3 reliable) |
| `--model NAME` | Test single model (qwen/deepseek/kimi/glm/minimax/hermes) |
| `--parallel` | Run tests simultaneously |
| `--timeout N` | Set timeout in seconds (default: 300) |
| `--compare A B` | Compare specific commits |
| `--unsafe` | Disable audit mode (NOT RECOMMENDED) |

## Audit Mode (Safe Automation)

All review scripts run in **audit mode** by default:
- Uses `--dangerously-skip-permissions` for fast execution
- Restricted to read-only tools via `permissions` in settings.json
- Full research capabilities (Grep, Read, WebSearch, Tavily, Serena search)
- No write access (Edit, Write, git commit/push blocked)

**Security:**
```
ALLOWED: Read, Glob, Grep, WebSearch, WebFetch, git read ops, MCP search tools
DENIED:  Write, Edit, rm, mv, git commit/push, any destructive operations
```

This provides safe, fast automated reviews without permission prompts.

**Output:**
- Results saved to `/tmp/deep-audit-test-YYYYMMDD-HHMMSS/`
- Generates `comparison-report.md` with performance summary

## Troubleshooting

### LiteLLM not starting
```bash
# Check if port 4000 is in use
lsof -i :4000

# Start with debug output
source ~/.config/litellm/.env && litellm --config ~/.config/litellm/config.yaml --debug
```

### Reconfigure LiteLLM provider
```bash
# Run setup wizard again
~/.claude/scripts/setup-litellm.sh

# Or choose provider directly
~/.claude/scripts/setup-litellm.sh nanogpt
~/.claude/scripts/setup-litellm.sh openrouter
~/.claude/scripts/setup-litellm.sh ollama
```

### Knowledge DB errors
```bash
~/.venvs/knowledge-db/bin/pip install --upgrade txtai sentence-transformers python-toon
```

### TOON adapter errors
```bash
# Verify TOON is installed
~/.venvs/knowledge-db/bin/pip show python-toon

# Test TOON adapter
~/.claude/scripts/test-toon-adapter.sh
```

### Models not showing in healthcheck
```bash
# Verify LiteLLM is running
curl http://localhost:4000/v1/models

# Check config file
cat ~/.config/litellm/config.yaml

# Verify .env file has API keys
cat ~/.config/litellm/.env
```

## Updating

```bash
./update.sh
```

## Uninstalling

```bash
./install.sh --uninstall
```

Backups preserved in ~/.claude/backups/
