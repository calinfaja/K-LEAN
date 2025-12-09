---
name: deepInspect
description: "Thorough review with FULL TOOL ACCESS - spawns headless Claude with LiteLLM model"
allowed-tools: Bash, Read
argument-hint: "[model] [focus] — models: qwen, kimi, glm, hermes"
---

# Deep Inspect

Run the deep-review script with full tool access:

```bash
~/.claude/scripts/deep-review.sh "[MODEL]" "[FOCUS]" "$(pwd)"
```

**Arguments:** $ARGUMENTS

Parse $ARGUMENTS:
- First word = model (default: qwen)
- Rest = focus

This spawns a headless Claude instance that can read files, grep, and investigate the codebase.

Display the script output to the user.
