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

### Step 2: Get NanoGPT API Key

1. Go to https://nano-gpt.com
2. Create account and get API key
3. The installer will prompt for this

### Step 3: Run Installer

```bash
./install.sh --full
```

### Step 4: Start LiteLLM

```bash
~/.claude/scripts/start-litellm.sh
```

### Step 5: Verify

```bash
./test.sh
healthcheck
```

## Troubleshooting

### LiteLLM not starting
```bash
lsof -i :4000
litellm --config ~/.config/litellm/nanogpt.yaml --debug
```

### Knowledge DB errors
```bash
~/.venvs/knowledge-db/bin/pip install --upgrade txtai
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
