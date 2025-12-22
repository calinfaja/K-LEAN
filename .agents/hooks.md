# K-LEAN Hooks System

## Overview

K-LEAN integrates with Claude Code via **5 hooks** that trigger on specific events.

## Available Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | SessionStart | Auto-start LiteLLM + per-project KB |
| `user-prompt-handler.sh` | UserPromptSubmit | Keyword detection (7 keywords) |
| `post-bash-handler.sh` | PostToolUse (Bash) | Git events → timeline + fact extraction |
| `post-web-handler.sh` | PostToolUse (Web*) | Auto-capture web content to KB |
| `async-review.sh` | UserPromptSubmit | Background async reviews |

## Hook Triggers

### session-start.sh

**Trigger:** Claude Code session starts

**Actions:**
1. Start LiteLLM proxy (if not running)
2. Start per-project KB server
3. Show configuration warnings

### user-prompt-handler.sh

**Trigger:** User submits a prompt

**Keywords detected:**

| Keyword | Action |
|---------|--------|
| `SaveThis: <text>` | Capture insight to KB |
| `SaveInfo: <text>` | Smart save with LLM evaluation |
| `FindKnowledge: <query>` | Search KB |
| `InitKB` | Initialize project KB |
| `asyncReview` | Background quick review |
| `asyncDeepReview` | Background deep review |
| `asyncConsensus` | Background consensus review |

### post-bash-handler.sh

**Trigger:** After any Bash command

**Detects:**
- `git commit` → Log to timeline + extract facts
- `git push` → Log to timeline
- Other git operations

### post-web-handler.sh

**Trigger:** After WebFetch/WebSearch/Tavily tools

**Action:** Smart capture of web content to KB

## Hook Development

### File Location

```
src/klean/data/hooks/
├── session-start.sh
├── user-prompt-handler.sh
├── post-bash-handler.sh
├── post-web-handler.sh
└── async-review.sh
```

### Hook Structure

```bash
#!/usr/bin/env bash

# Source path utilities (with fallback)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../scripts/kb-root.sh" 2>/dev/null || {
    # Inline fallbacks if kb-root.sh not found
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
}

# Hook logic here...

# Exit codes:
# 0 = success, continue
# 1 = error (logged)
# 2 = block operation (with stderr message to Claude)
```

### Important Rules

1. **No blocking operations** - Hooks run synchronously
2. **Handle errors gracefully** - Hooks run silently
3. **Use inline fallbacks** - In case kb-root.sh missing
4. **Check exit codes** - For proper error reporting

## Registration

Hooks are registered in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": ["~/.claude/hooks/session-start.sh"]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": ["~/.claude/hooks/user-prompt-handler.sh"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["~/.claude/hooks/post-bash-handler.sh"]
      },
      {
        "matcher": "^(WebFetch|WebSearch|mcp__tavily)",
        "hooks": ["~/.claude/hooks/post-web-handler.sh"]
      }
    ]
  }
}
```

## Debugging Hooks

```bash
# Live monitoring
k-lean debug

# Compact mode (shows hook output)
k-lean debug --compact

# Manual test
~/.claude/hooks/session-start.sh
echo $?  # Check exit code
```

## Exit Code Behavior

| Code | Behavior |
|------|----------|
| 0 | Success, continue |
| 1 | Error (logged, operation continues) |
| 2 | **Block operation** (stderr shown to Claude) |

### Blocking Example

```bash
# Block dangerous commands
if [[ "$command" =~ "rm -rf /" ]]; then
    echo "Blocked: Dangerous command" >&2
    exit 2
fi
```

## Comparison with Best Practices

| Feature | K-LEAN | Community Best Practice |
|---------|--------|------------------------|
| PreToolUse (security) | ❌ | ✅ Block dangerous commands |
| Stop hook (completion) | ❌ | ✅ Notifications/TTS |
| Exit code 2 blocking | Partial | ✅ stderr to Claude |
| Web auto-capture | ✅ Unique | ❌ Not common |
| KB integration | ✅ Unique | ❌ Simple logging only |

## Future Improvements

1. Add `pre-tool-handler.sh` for security blocking
2. Consistent JSON output: `{"decision": "block", "reason": "..."}`
3. Stop hook for session completion notifications

---
*See [litellm.md](litellm.md) for model configuration*
