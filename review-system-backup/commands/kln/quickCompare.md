---
name: quickCompare
description: "Run 3 models in PARALLEL and compare reviews"
allowed-tools: Bash, Read, Grep
argument-hint: "[focus] — runs qwen, deepseek, glm in parallel"
---

# Quick Compare

Run the consensus-review script with 3 models in parallel:

```bash
~/.claude/scripts/consensus-review.sh "[FOCUS]" "$(pwd)"
```

**Arguments:** $ARGUMENTS (this is the focus/topic for review)

The script:
1. Health-checks models (qwen, deepseek, glm)
2. Runs healthy models in parallel
3. Returns results from each

Display the script output to the user.
