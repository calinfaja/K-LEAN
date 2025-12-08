# Installation Guide

Complete step-by-step guide to set up the Claude Agentic Workflow on a new Linux machine.

## Prerequisites

- Linux (Ubuntu/Debian recommended)
- Python 3.10+
- Node.js 18+ (for Claude Code)
- Git
- curl, jq (JSON processing)

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm curl jq bc
```

---

## Step 1: Install Claude Code CLI

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version

# Set up API key
export ANTHROPIC_API_KEY="your-api-key"
echo 'export ANTHROPIC_API_KEY="your-api-key"' >> ~/.bashrc
```

---

## Step 2: Install LiteLLM Proxy

```bash
# Install LiteLLM
pip install litellm

# Or with pipx (recommended for isolation)
pipx install litellm
```

---

## Step 3: Set Up NanoGPT Configuration

Create LiteLLM config for NanoGPT models:

```bash
mkdir -p ~/.config/litellm
```

Create `~/.config/litellm/nanogpt.yaml`:

```yaml
model_list:
  # Qwen 3 Coder - Code quality specialist
  - model_name: qwen3-coder
    litellm_params:
      model: openai/Qwen/Qwen3-Coder
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

  # DeepSeek V3 - Architecture specialist (thinking model)
  - model_name: deepseek-v3-thinking
    litellm_params:
      model: openai/deepseek-chat
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

  # GLM 4.6 - Standards specialist (thinking model)
  - model_name: glm-4.6-thinking
    litellm_params:
      model: openai/glm-z1-air
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

  # MiniMax M2 - Research specialist
  - model_name: minimax-m2
    litellm_params:
      model: openai/MiniMax-M2-Large
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

  # Kimi K2 - Agent specialist (thinking model)
  - model_name: kimi-k2-thinking
    litellm_params:
      model: openai/kimi-k2-0711-preview
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

  # Hermes 4 - Scripting specialist
  - model_name: hermes-4-70b
    litellm_params:
      model: openai/hermes-4-mini
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

general_settings:
  master_key: sk-1234
```

Set NanoGPT API key:

```bash
export NANOGPT_API_KEY="your-nanogpt-api-key"
echo 'export NANOGPT_API_KEY="your-nanogpt-api-key"' >> ~/.bashrc
```

---

## Step 4: Install Knowledge System (txtai)

```bash
# Create dedicated virtual environment
python3 -m venv ~/.venvs/knowledge-db

# Install txtai with SQLite backend
~/.venvs/knowledge-db/bin/pip install txtai[database,ann]

# Verify installation
~/.venvs/knowledge-db/bin/python -c "from txtai import Embeddings; print('txtai OK')"
```

---

## Step 5: Copy Scripts and Configuration

### Option A: From This Repository

```bash
# Clone the repository
git clone https://github.com/your-username/claudeAgentic.git ~/claudeAgentic

# Create Claude directories
mkdir -p ~/.claude/scripts
mkdir -p ~/.claude/commands/sc    # SuperClaude commands
mkdir -p ~/.claude/commands/kln   # Custom review commands
mkdir -p ~/.claude/templates

# Copy scripts
cp ~/claudeAgentic/review-system-backup/scripts/*.sh ~/.claude/scripts/
cp ~/claudeAgentic/review-system-backup/scripts/*.py ~/.claude/scripts/
chmod +x ~/.claude/scripts/*.sh

# Copy SuperClaude slash commands (/sc:)
cp ~/claudeAgentic/review-system-backup/commands/*.md ~/.claude/commands/sc/

# Copy custom review commands (/kln:)
cp ~/claudeAgentic/review-system-backup/commands-kln/*.md ~/.claude/commands/kln/

# Copy configuration
cp ~/claudeAgentic/review-system-backup/config/settings.json ~/.claude/settings.json

# Copy CLAUDE.md (system instructions)
cp ~/claudeAgentic/review-system-backup/CLAUDE.md ~/.claude/CLAUDE.md

# Copy templates
cp ~/claudeAgentic/review-system-backup/templates/* ~/.claude/templates/ 2>/dev/null || true
```

### Option B: Manual Setup

Create each directory and copy files manually from the backup folder.

---

## Step 6: Set Up Bash Aliases

Add to `~/.bashrc`:

```bash
# LiteLLM proxy
alias start-nano-proxy='~/.claude/scripts/start-litellm.sh'

# Health check
alias healthcheck='~/.claude/scripts/health-check.sh'

# Quick review shortcuts
alias qreview='~/.claude/scripts/quick-review.sh'
alias consensus='~/.claude/scripts/consensus-review.sh'

# Sync check
alias sync-check='~/.claude/scripts/sync-check.sh'
```

Reload:

```bash
source ~/.bashrc
```

---

## Step 7: Start LiteLLM Proxy

```bash
start-nano-proxy
```

Verify it's running:

```bash
curl http://localhost:4000/health
```

---

## Step 8: Verify Installation

Run the test script:

```bash
~/.claude/scripts/test-system.sh
```

Or manually test:

```bash
# Test health check
healthcheck

# Test knowledge system
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py stats

# Verify all scripts synced
sync-check
```

---

## Step 9: Initialize Project Knowledge DB (Per Project)

In each project directory:

```bash
# Create knowledge-db directory
mkdir -p .knowledge-db

# The system auto-detects projects by looking for:
# - .serena/
# - .claude/
# - .knowledge-db/
```

---

## Step 10: Optional - Serena MCP Server

If using Serena for project memories:

```bash
# Install Serena MCP (check latest instructions)
# Configure in ~/.claude/mcp.json:
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["serena-mcp", "--config", "/path/to/config.yml"]
    }
  }
}
```

---

## Directory Structure After Installation

```
~/.claude/
├── settings.json          # Main Claude configuration
├── CLAUDE.md              # System-wide instructions
├── mcp.json               # MCP servers config
├── scripts/
│   ├── knowledge_db.py    # Knowledge DB core
│   ├── knowledge-search.py
│   ├── knowledge-extract.sh
│   ├── goodjob-dispatch.sh
│   ├── auto-capture-hook.sh
│   ├── quick-review.sh
│   ├── second-opinion.sh
│   ├── consensus-review.sh
│   ├── deep-review.sh
│   ├── parallel-deep-review.sh
│   ├── async-dispatch.sh
│   ├── health-check.sh
│   ├── start-litellm.sh
│   ├── sync-check.sh
│   └── test-system.sh
├── commands/
│   ├── sc/                # SuperClaude commands (30)
│   │   ├── implement.md
│   │   ├── analyze.md
│   │   └── ... (30 commands)
│   └── kln/               # Custom review commands (12)
│       ├── review.md
│       ├── consensus.md
│       ├── deepReview.md
│       └── ... (12 commands)
└── templates/
    └── serena-knowledge-memory.md

~/.venvs/
└── knowledge-db/          # txtai virtual environment

~/.config/litellm/
└── nanogpt.yaml           # LiteLLM configuration

/tmp/claude-reviews/       # Review outputs (auto-created)
└── {session-id}/
    ├── quick-*.json
    ├── consensus-*.json
    └── deep-*.txt

/your-project/
├── .knowledge-db/         # Per-project knowledge
│   ├── index/
│   └── entries.jsonl
└── .serena/               # Serena memories (optional)
    └── memories/
```

---

## Quick Verification Commands

```bash
# Check LiteLLM proxy
curl http://localhost:4000/health

# Check all models
healthcheck

# Check scripts are in place
sync-check

# Check knowledge system
~/.venvs/knowledge-db/bin/python -c "from knowledge_db import KnowledgeDB; print('OK')"

# Run full system test
~/.claude/scripts/test-system.sh
```

---

## Troubleshooting

### LiteLLM won't start
```bash
# Check if port is in use
lsof -i :4000
# Kill existing process
pkill -f litellm
# Restart
start-nano-proxy
```

### Scripts permission denied
```bash
chmod +x ~/.claude/scripts/*.sh
```

### Knowledge DB import error
```bash
# Reinstall txtai
~/.venvs/knowledge-db/bin/pip install --force-reinstall txtai[database,ann]
```

### Hooks not firing
```bash
# Check settings.json has correct hook configuration
cat ~/.claude/settings.json | jq '.hooks'
```

---

## Updates

To update the system:

```bash
# Pull latest from repo
cd ~/claudeAgentic
git pull

# Sync scripts
~/.claude/scripts/sync-check.sh --sync
```
