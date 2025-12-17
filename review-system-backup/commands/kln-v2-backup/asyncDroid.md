---
name: asyncDroid
description: "Run Factory Droid review in background subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[model] [focus] — Runs in background, returns summary when done"
---

# Async Factory Droid Review

Launch a background subagent to run Factory Droid review while you continue working.

**Arguments:** $ARGUMENTS

Parse $ARGUMENTS:
- First word = model (default: qwen3-coder)
- Rest = focus/prompt for the review

## Available Models
- qwen3-coder (default)
- deepseek-v3-thinking
- glm-4.6-thinking
- kimi-k2-thinking
- minimax-m2
- hermes-4-70b

## Execution

Use the Task tool with `run_in_background: true` to spawn a subagent:

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: "Run this command and return the complete output: ~/.claude/scripts/droid-review.sh '$ARGUMENTS' '$(pwd)'"
```

Tell the user: "Factory Droid review started in background with [model]. Use AgentOutputTool to check results when ready."
