# Review System - Detailed Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REVIEW SYSTEM ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────────────────┐  │
│  │   Claude    │────►│    Hooks     │────►│  Background Scripts         │  │
│  │  (Native)   │     │ (settings)   │     │  (parallel-deep-review.sh)  │  │
│  └─────────────┘     └──────────────┘     └─────────────────────────────┘  │
│        │                                              │                     │
│        │                                              ▼                     │
│        │                                   ┌─────────────────────┐          │
│        │                                   │   LiteLLM Proxy     │          │
│        │                                   │   localhost:4000    │          │
│        │                                   └─────────────────────┘          │
│        │                                              │                     │
│        ▼                                              ▼                     │
│  ┌─────────────┐                          ┌─────────────────────┐          │
│  │   Serena    │                          │   Local Models      │          │
│  │    MCP      │                          │  qwen/deepseek/glm  │          │
│  └─────────────┘                          └─────────────────────┘          │
│        │                                              │                     │
│        ▼                                              ▼                     │
│  ┌─────────────┐                          ┌─────────────────────┐          │
│  │  Memories   │                          │  /tmp/claude-reviews │          │
│  │ .serena/    │                          │  (results)          │          │
│  └─────────────┘                          └─────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. Claude Code CLI
```bash
claude --version
```

### 2. LiteLLM Proxy
```bash
pip install litellm
# Config: ~/.config/litellm/nanogpt.yaml
start-nano-proxy  # alias to start
```

### 3. Serena MCP Server
```bash
# Configured in ~/.claude/mcp.json
# Activate project: mcp__serena__activate_project
```

### 4. Bash Aliases (~/.bashrc)
```bash
alias start-nano-proxy='litellm --config ~/.config/litellm/nanogpt.yaml &'
alias use-nano='cp ~/.claude/settings-nanogpt.json ~/.claude/settings.json'
alias use-native='cp ~/.claude/settings-native.json ~/.claude/settings.json'
```

---

## Configuration Files

### ~/.claude/settings.json (Main Config)
```json
{
  "alwaysThinkingEnabled": true,
  "model": "haiku",
  "includeCoAuthoredBy": false,
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/async-dispatch.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/post-commit-docs.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### ~/.config/litellm/nanogpt.yaml (LiteLLM Config)
```yaml
model_list:
  - model_name: coding-qwen
    litellm_params:
      model: openai/qwen-coder
      api_base: https://api.nano-gpt.com/v1

  - model_name: architecture-deepseek
    litellm_params:
      model: openai/deepseek-chat
      api_base: https://api.nano-gpt.com/v1

  - model_name: tools-glm
    litellm_params:
      model: openai/glm-4-flash
      api_base: https://api.nano-gpt.com/v1
```

---

## Scripts Reference

### async-dispatch.sh
**Purpose:** UserPromptSubmit hook dispatcher
**Location:** `~/.claude/scripts/async-dispatch.sh`
**Triggers:** Prompts containing `asyncDeepReview`, `asyncConsensus`, `asyncReview`, `asyncSecondOpinion`
**Action:** Starts appropriate review script in background

### parallel-deep-review.sh
**Purpose:** Run 3 headless Claude instances with different LiteLLM models
**Location:** `~/.claude/scripts/parallel-deep-review.sh`
**Usage:** `./parallel-deep-review.sh "<focus>" <working_dir>`
**Models:** coding-qwen, architecture-deepseek, tools-glm
**Features:** Full tool access (Read, Grep, Bash, Serena)

### consensus-review.sh
**Purpose:** Run 3 parallel curl requests to LiteLLM
**Location:** `~/.claude/scripts/consensus-review.sh`
**Usage:** `./consensus-review.sh "<focus>" <working_dir>`
**Features:** Fast, no tool access, compares findings

### quick-review.sh
**Purpose:** Single model quick review via curl
**Location:** `~/.claude/scripts/quick-review.sh`
**Usage:** `./quick-review.sh <model> "<focus>" <working_dir>`

### second-opinion.sh
**Purpose:** Single model with comprehensive context
**Location:** `~/.claude/scripts/second-opinion.sh`
**Usage:** `./second-opinion.sh <model> "<question>" <working_dir>`

### post-commit-docs.sh
**Purpose:** PostToolUse hook - auto-documentation after commits
**Location:** `~/.claude/scripts/post-commit-docs.sh`
**Triggers:** After any `git commit` or `git merge`
**Action:** Spawns Claude to update Serena memories and create commit docs

---

## Hooks Explained

### UserPromptSubmit Hook
- **When:** Every time you submit a prompt
- **What:** `async-dispatch.sh` checks for keywords
- **Behavior:** If keyword found, starts background script; if not, does nothing
- **Note:** Does NOT support `matcher` - script handles keyword detection

### PostToolUse Hook
- **When:** After Bash tool completes
- **What:** `post-commit-docs.sh` checks if command was git commit
- **Behavior:** If git commit, spawns Claude to update Serena docs
- **Matcher:** `Bash` (only triggers for Bash tool)

---

## Model Specializations

| Model | Alias | Specialty | Best For |
|-------|-------|-----------|----------|
| coding-qwen | qwen | Code quality | Bugs, memory safety, buffer handling |
| architecture-deepseek | deepseek | Design | Architecture, coupling, modularity |
| tools-glm | glm | Compliance | MISRA, standards, best practices |

---

## Output Formats

### Review Output
```
## Grade: [A-F]
## Risk: [CRITICAL/HIGH/MEDIUM/LOW]
## Critical Issues
| File:Line | Issue | Evidence |
## Warnings
| File:Line | Issue |
## Verdict: [APPROVE/REQUEST_CHANGES]
```

### Consensus Output
```
## Consensus Summary
### HIGH CONFIDENCE (All 3 agree)
| Issue | Qwen | DeepSeek | GLM |
### MEDIUM CONFIDENCE (2/3 agree)
### LOW CONFIDENCE (1/3 found)
### Final Verdict
```

### Session Documentation (Serena)
```
# Session Review: [Title]
| Date | Project | Grade | Risk |
## Quality Assessment
## Lessons Learned
- [PATTERN] ...
- [GOTCHA] ...
- [TIP] ...
```

---

## Troubleshooting

### LiteLLM Not Responding
```bash
curl http://localhost:4000/health
start-nano-proxy
curl http://localhost:4000/models | jq '.data[].id'
```

### Hook Not Firing
```bash
# Check settings
cat ~/.claude/settings.json | jq '.hooks'

# Test script manually
echo '{"prompt":"asyncDeepReview test"}' | ~/.claude/scripts/async-dispatch.sh
```

### Serena Memory Errors
```bash
# Activate project first
mcp__serena__activate_project project: "your-project"
mcp__serena__list_memories
```

### Review Script Fails
```bash
# Check logs
cat /tmp/claude-reviews/*.log
ls -la /tmp/claude-reviews/
```

### Model Routing Issues
Ensure all three model overrides are set in parallel-deep-review.sh:
```bash
ANTHROPIC_DEFAULT_SONNET_MODEL
ANTHROPIC_DEFAULT_HAIKU_MODEL
ANTHROPIC_DEFAULT_OPUS_MODEL
```

---

## File Locations

| Type | Location |
|------|----------|
| Scripts | `~/.claude/scripts/` |
| Slash Commands | `~/.claude/commands/sc/` |
| Settings | `~/.claude/settings.json` |
| MCP Config | `~/.claude/mcp.json` |
| LiteLLM Config | `~/.config/litellm/nanogpt.yaml` |
| Review Results | `/tmp/claude-reviews/` |
| Serena Memories | `.serena/memories/` (in project) |
| Backups | `~/claudeAgentic/review-system-backup/` |
| Knowledge DB | `.knowledge-db/` (in project) |

---

## Knowledge System Integration

Review scripts automatically search the project's knowledge database and inject relevant prior knowledge into the system prompt.

**Integrated scripts:**
- `quick-review.sh` - Searches before review
- `second-opinion.sh` - Includes knowledge context
- `consensus-review.sh` - All 3 models get prior knowledge

**How it works:**
1. Script extracts focus/query from arguments
2. Searches knowledge DB with `--format inject`
3. Injects relevant entries (score > 0.3) into system prompt
4. Model receives prior knowledge during review

See [KNOWLEDGE_SYSTEM.md](KNOWLEDGE_SYSTEM.md) for full documentation.

---

## Version History

- **2025-12-03:** Knowledge System integration
  - Per-project semantic knowledge database (txtai)
  - Review scripts inject prior knowledge
  - Auto-capture hooks for WebFetch/WebSearch
  - Manual capture: GoodJob, SaveThis, FindKnowledge

- **2025-12-02:** Initial implementation
  - Hooks for async reviews (UserPromptSubmit)
  - Post-commit documentation (PostToolUse)
  - 3-tier review system
  - Serena MCP integration
