---
name: quickReview
description: Fast code review via LiteLLM API with grades and risk assessment
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__write_memory, mcp__serena__read_memory, mcp__serena__list_memories
argument-hint: "[model] [focus] — models: qwen, deepseek, glm, minimax, kimi, hermes"
---

# Quick Review

Run the quick-review script with the provided arguments:

```bash
~/.claude/scripts/quick-review.sh "[MODEL]" "[FOCUS]" "$(pwd)"
```

**Arguments:** $ARGUMENTS

Parse $ARGUMENTS:
- First word = model (default: qwen)
- Rest = focus

Display the script output to the user.
