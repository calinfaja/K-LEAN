---
name: asyncDroidAudit
description: "Run 3 Factory Droids in PARALLEL in background subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[focus] — Runs qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking in background"
---

# Async Factory Droid Parallel Audit

Launch a background subagent to run 3 parallel Factory Droid reviews while you continue working.

**Arguments:** $ARGUMENTS (focus/prompt for all reviews)

## Execution

Use the Task tool with `run_in_background: true` to spawn a subagent:

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: "Run this command and return the complete output: ~/.claude/scripts/parallel-droid-review.sh '$ARGUMENTS' '$(pwd)'"
```

Tell the user: "Factory Droid parallel audit started in background (3 models). Use AgentOutputTool to check results when ready."
