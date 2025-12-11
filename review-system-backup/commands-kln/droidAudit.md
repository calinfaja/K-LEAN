---
name: droidAudit
description: "Run 3 Factory Droids in PARALLEL for comprehensive audit"
allowed-tools: Bash, Read
argument-hint: "[focus] — runs qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking in parallel"
---

# Factory Droid Parallel Audit

Run 3 Factory Droid reviews in parallel for comprehensive code analysis.

**Arguments:** $ARGUMENTS (focus/prompt for all reviews)

Default focus if not specified: "Comprehensive code review for bugs, security, architecture, and best practices"

## Execution

```bash
~/.claude/scripts/parallel-droid-review.sh "$ARGUMENTS" "$(pwd)"
```

This launches 3 parallel droid reviews:
1. **qwen3-coder** - Code quality and bugs
2. **deepseek-v3-thinking** - Architecture and design
3. **glm-4.6-thinking** - Standards and security

Results are saved to `/tmp/droid-audit-*` and displayed when all complete.

Much faster than headless Claude parallel reviews (~1-2min vs 10-15min).
