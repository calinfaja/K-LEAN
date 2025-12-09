# Hooks System

Event-driven automation using Claude Code hooks for async reviews, knowledge capture, and post-commit documentation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       HOOKS SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  UserPromptSubmit Hook                                          │
│  └── Triggers BEFORE Claude processes user input                │
│      ├── Keyword detection (healthcheck, GoodJob, SaveThis)     │
│      ├── Async review dispatch (asyncDeepReview, etc.)          │
│      └── FindKnowledge queries                                  │
│                                                                  │
│  PostToolUse Hook (Bash)                                        │
│  └── Triggers AFTER Bash tool completes                         │
│      ├── Git commit detection → post-commit docs + timeline     │
│      └── Fact extraction from commit messages                   │
│                                                                  │
│  PostToolUse Hook (WebFetch/WebSearch)                          │
│  └── Triggers AFTER web tools complete                          │
│      └── Auto-capture to knowledge database                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Hook Location

```
~/.claude/hooks/
├── user-prompt-submit.js    # Keyword detection and dispatch
└── post-tool-use.sh         # Post-tool automation
```

## UserPromptSubmit Hook

Runs before Claude processes user input. Used for keyword detection and async dispatch.

### Configuration

```json
// ~/.claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": ["~/.claude/hooks/user-prompt-submit.js"]
      }
    ]
  }
}
```

### Keywords Handled

| Keyword | Action |
|---------|--------|
| `healthcheck` | Check all 6 model health |
| `GoodJob <url>` | Capture URL to knowledge DB |
| `SaveThis <text>` | Direct save to knowledge DB (no AI eval) |
| `SaveInfo <text>` | Smart save with Haiku evaluation (score ≥ 0.7) |
| `FindKnowledge <query>` | Search knowledge DB |
| `asyncDeepReview <focus>` | 3 models with tools (background) |
| `asyncConsensus <focus>` | 3 models quick review (background) |
| `asyncReview <model> <focus>` | Single model (background) |

### Example Hook Logic

```javascript
// user-prompt-submit.js
const input = process.env.USER_PROMPT;

if (input.startsWith('healthcheck')) {
  // Run health check script
  execSync('~/.claude/scripts/health-check.sh');
}

if (input.startsWith('GoodJob ')) {
  const url = input.replace('GoodJob ', '').split(' ')[0];
  execSync(`~/.claude/scripts/goodjob-dispatch.sh "${url}"`);
}

if (input.startsWith('FindKnowledge ')) {
  const query = input.replace('FindKnowledge ', '');
  execSync(`~/.claude/scripts/knowledge-query.sh "${query}"`);
}
```

## PostToolUse Hook (Bash)

Runs after Bash tool completes. Detects git commits for documentation and timeline logging.

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["~/.claude/hooks/post-tool-use.sh"]
      }
    ]
  }
}
```

### Git Commit Detection

When a `git commit` is detected:

1. **Extract commit info:** hash, message, files changed
2. **Log to timeline:** `MM-DD HH:MM | commit | <hash>: <message>`
3. **Extract facts:** Parse commit message for learnings
4. **Generate docs:** Optional post-commit documentation

```bash
# post-tool-use.sh (simplified)
if echo "$TOOL_OUTPUT" | grep -q "git commit"; then
  HASH=$(git rev-parse --short HEAD)
  MSG=$(git log -1 --format='%s')

  # Log to timeline
  echo "$(date '+%m-%d %H:%M') | commit | $HASH: $MSG" >> .knowledge-db/timeline.txt

  # Extract facts
  ~/.claude/scripts/fact-extract.sh "$MSG" "commit" "$MSG" "$(pwd)"
fi
```

## PostToolUse Hook (WebFetch/WebSearch)

Auto-captures knowledge from web research.

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "WebFetch|WebSearch",
        "hooks": ["~/.claude/hooks/post-tool-use.sh"]
      }
    ]
  }
}
```

### Auto-Capture Logic

```bash
# When WebFetch/WebSearch completes
if [ "$TOOL_NAME" = "WebFetch" ] || [ "$TOOL_NAME" = "WebSearch" ]; then
  # Extract URL and content
  URL=$(echo "$TOOL_INPUT" | jq -r '.url // .query')

  # Auto-capture to knowledge DB
  ~/.claude/scripts/auto-capture-hook.sh "$URL" "$TOOL_OUTPUT"
fi
```

## Hook Environment Variables

Available to hooks:

| Variable | Description |
|----------|-------------|
| `USER_PROMPT` | User's input text |
| `TOOL_NAME` | Name of tool that ran |
| `TOOL_INPUT` | Tool input parameters (JSON) |
| `TOOL_OUTPUT` | Tool output/result |
| `WORKING_DIR` | Current working directory |

## Creating Custom Hooks

### JavaScript Hook

```javascript
#!/usr/bin/env node
// ~/.claude/hooks/my-hook.js

const input = process.env.USER_PROMPT;
const { execSync } = require('child_process');

if (input.includes('my-keyword')) {
  const result = execSync('my-script.sh');
  console.log(result.toString());
}
```

### Shell Hook

```bash
#!/bin/bash
# ~/.claude/hooks/my-hook.sh

if [[ "$USER_PROMPT" == *"my-keyword"* ]]; then
  ~/.claude/scripts/my-script.sh
fi
```

### Make Executable

```bash
chmod +x ~/.claude/hooks/my-hook.js
chmod +x ~/.claude/hooks/my-hook.sh
```

## Hook Registration

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "my-pattern",
        "hooks": ["~/.claude/hooks/my-hook.sh"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "ToolName",
        "hooks": ["~/.claude/hooks/my-hook.sh"]
      }
    ]
  }
}
```

## Debugging Hooks

### Check Hook Output

Hooks output is visible in Claude's response. Add logging:

```bash
echo "HOOK DEBUG: Processing $USER_PROMPT" >&2
```

### Test Hook Manually

```bash
USER_PROMPT="healthcheck" ~/.claude/hooks/user-prompt-submit.js
```

### Common Issues

**Hook not triggering:**
- Check matcher regex matches input
- Verify hook file is executable
- Check hook path is correct in settings.json

**Hook errors:**
- Check stderr output in Claude response
- Verify all scripts called by hook exist
- Check environment variables are set

## Scripts Called by Hooks

| Script | Called By | Purpose |
|--------|-----------|---------|
| `health-check.sh` | UserPromptSubmit | Check model health |
| `goodjob-dispatch.sh` | UserPromptSubmit | Capture URLs |
| `knowledge-query.sh` | UserPromptSubmit | Search knowledge |
| `fact-extract.sh` | PostToolUse | Extract facts |
| `auto-capture-hook.sh` | PostToolUse | Auto-capture web |

## Best Practices

1. **Keep hooks fast** - Long-running hooks delay response
2. **Use async for heavy work** - Spawn background processes
3. **Handle errors gracefully** - Don't crash on edge cases
4. **Log for debugging** - But clean up in production
5. **Test hooks manually** - Before relying on them
