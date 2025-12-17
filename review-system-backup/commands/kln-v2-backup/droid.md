---
name: droid
description: "Fast deep review with Factory Droid - agentic tools, parallel execution"
allowed-tools: Bash, Read
argument-hint: "[model] [focus] — models: qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking, kimi-k2-thinking, minimax-m2, hermes-4-70b"
---

# Factory Droid Review

Run a deep code review using Factory Droid with your LiteLLM models.

**Arguments:** $ARGUMENTS

Parse $ARGUMENTS:
- First word = model (default: qwen3-coder)
- Rest = focus/prompt for the review

## Execution

```bash
~/.claude/scripts/droid-review.sh "$ARGUMENTS" "$(pwd)"
```

Display the output to the user. Factory Droid has built-in agentic capabilities:
- File reading and navigation
- Code search (ripgrep)
- Symbol analysis
- Parallel execution

This is faster than headless Claude (~30s-1min vs 3-5min).
