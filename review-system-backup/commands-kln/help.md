---
name: help
description: List all /kln: custom commands and their functionality
allowed-tools: Read, Glob
argument-hint: ""
---

# /kln:help - Custom Commands Reference

## Triggers
- Command discovery for custom review/knowledge framework
- Documentation requests for /kln: namespace

## Behavioral Flow
1. **Display**: Present complete list of /kln: commands
2. **Complete**: End after displaying information

---

Here is a complete list of all custom `/kln:` commands in your review & knowledge framework.

## Review Commands

| Command | Description | Models | Time |
|---------|-------------|--------|------|
| `/kln:review <model> <focus>` | Quick code review via LiteLLM | 1 | ~30s |
| `/kln:secondOpinion <model> <question>` | Get independent opinion with full context | 1 | ~1min |
| `/kln:consensus <focus>` | 3-model parallel review comparison | 3 | ~1min |
| `/kln:deepReview <model> <focus>` | Thorough review with tool access | 1 | ~3min |
| `/kln:parallelDeepReview <focus>` | 3 headless Claude instances with tools | 3 | ~5min |

## Async Commands (Background Execution)

| Command | Description | Output Location |
|---------|-------------|-----------------|
| `/kln:asyncReview <model> <focus>` | Background single-model review | `/tmp/claude-reviews/{session}/` |
| `/kln:asyncSecondOpinion <model> <question>` | Background opinion | `/tmp/claude-reviews/{session}/` |
| `/kln:asyncConsensus <focus>` | Background 3-model consensus | `/tmp/claude-reviews/{session}/` |
| `/kln:asyncDeepReview <focus>` | Background deep review (3 models) | `/tmp/claude-reviews/{session}/` |

## Documentation Commands

| Command | Description |
|---------|-------------|
| `/kln:createReviewDoc <title>` | Create session review documentation |
| `/kln:asyncReviewDoc <title>` | Create doc in background |
| `/kln:backgroundReviewDoc <title>` | Spawn doc creation in subagent |

---

## Model Aliases

### Reliable for Deep Reviews (Tool Use)
| Alias | LiteLLM Model | Specialty |
|-------|---------------|-----------|
| `qwen` | `coding-qwen` | Code quality, bugs, memory safety |
| `kimi` | `agent-kimi` | Architecture, planning |
| `glm` | `tools-glm` | Standards compliance, MISRA |

### Quick Reviews Only (No Tools)
| Alias | LiteLLM Model | Notes |
|-------|---------------|-------|
| `deepseek` | `architecture-deepseek` | ⚠️ Empty output in tool mode |
| `minimax` | `research-minimax` | ⚠️ Timeouts common |
| `hermes` | `scripting-hermes` | ⚠️ May hallucinate |

---

## Knowledge Keywords (Type in Prompt)

| Keyword | Action |
|---------|--------|
| `GoodJob <url>` | Capture knowledge from URL |
| `GoodJob <url> <focus>` | Capture with specific focus |
| `SaveThis <description>` | Save a lesson learned |
| `FindKnowledge <query>` | Search knowledge database |

---

## Quick Examples

```bash
# Quick single-model review
/kln:review qwen security vulnerabilities

# Get architecture opinion (use kimi for reliable tool use)
/kln:secondOpinion kimi "Is this design scalable?"

# 3-model consensus (uses qwen, kimi, glm)
/kln:consensus code quality

# Deep review with tools (qwen recommended)
/kln:deepReview qwen "memory safety audit"

# Background deep review (continue working)
/kln:asyncDeepReview performance audit

# Capture knowledge
GoodJob https://docs.example.com focus on authentication
```

---

## Related

- `/sc:help` - SuperClaude framework commands
- `healthcheck` - Check all 6 models health
- `~/.claude/scripts/sync-check.sh` - Verify scripts synced

---

**Note:** Review outputs are saved to `/tmp/claude-reviews/{session-id}/`
