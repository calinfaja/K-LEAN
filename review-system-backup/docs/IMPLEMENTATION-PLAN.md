# K-LEAN Enhancement Implementation Plan

**Date**: 2025-12-15
**Features**: Context Monitor, Post-Edit Quality, /kln:remember, MCP Funnel

---

## Feature Overview

| # | Feature | Purpose | Files to Create/Modify |
|---|---------|---------|----------------------|
| 1 | Context Monitor Hook | Warn at 85%/95% context usage | `hooks/context-monitor.sh` |
| 2 | Post-Edit Quality Hook | Auto-format/lint on file save | `hooks/post-edit-quality.sh` |
| 3 | /kln:remember Command | End-of-session comprehensive save | `commands/kln/remember.md` |
| 4 | MCP Funnel Config | Filter tools to reduce context | `.mcp-funnel.json` |

---

## SaveThis vs /kln:remember - Key Differences

| Aspect | SaveThis | /kln:remember |
|--------|----------|---------------|
| **When** | During session (anytime) | End of session (before /clear) |
| **Scope** | Single insight/lesson | Entire session learnings |
| **Granularity** | One fact at a time | Multiple structured categories |
| **Use Case** | "Bookmark this insight now" | "Summarize everything I learned" |
| **Trigger** | Manual inline | Manual end-of-session |
| **Output** | Single KB entry | Multiple KB entries + Serena memory |

**Workflow:**
```
During session:  SaveThis "Quick insight" --type lesson
                 SaveThis "Found bug pattern" --type finding
                 ... work continues ...

End of session:  /kln:remember  (comprehensive review)
                 /clear or /compact
```

---

## 1. Context Monitor Hook

### Purpose
Prevent lost work by warning when context window is filling up.

### Implementation

**File**: `~/.claude/hooks/context-monitor.sh`

```bash
#!/bin/bash
#
# Context Monitor Hook - PostToolUse (All Tools)
# Warns at 85% and 95% context usage
#
# Since Claude doesn't expose context % directly, we estimate
# based on tool call count in the session.
#

INPUT=$(cat)

# Session tracking file (per-terminal session)
SESSION_FILE="/tmp/claude-context-monitor-$$"
PARENT_SESSION="/tmp/claude-context-monitor-$PPID"

# Use parent PID for consistency across tool calls
if [ -f "$PARENT_SESSION" ]; then
    SESSION_FILE="$PARENT_SESSION"
fi

# Read or initialize counter
if [ -f "$SESSION_FILE" ]; then
    COUNT=$(cat "$SESSION_FILE")
else
    COUNT=0
fi

# Increment counter
COUNT=$((COUNT + 1))
echo "$COUNT" > "$SESSION_FILE"

# Thresholds (based on typical session patterns)
# ~100 tool calls ≈ 200k context for complex operations
WARN_THRESHOLD=60   # ~85% estimate
CRITICAL_THRESHOLD=80  # ~95% estimate

if [ "$COUNT" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "{\"systemMessage\": \"🚨 CRITICAL: ~${COUNT} tool calls. Context likely near limit!\\n→ Run /compact to compress context\\n→ Or /kln:remember then /clear to save & reset\"}"
elif [ "$COUNT" -ge "$WARN_THRESHOLD" ]; then
    echo "{\"systemMessage\": \"⚠️ Context Monitor: ~${COUNT} tool calls (~85% estimate).\\n→ Consider /compact soon or plan for /clear\"}"
fi

exit 0
```

### Settings.json Addition
```json
{
  "PostToolUse": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "~/.claude/hooks/context-monitor.sh",
          "timeout": 5
        }
      ]
    }
  ]
}
```

### Testing
```bash
# Test the script directly
echo '{"tool_name": "Read"}' | ~/.claude/hooks/context-monitor.sh

# Verify counter file created
cat /tmp/claude-context-monitor-*

# Test threshold warnings (manually set counter)
echo "65" > /tmp/claude-context-monitor-$$
echo '{"tool_name": "Read"}' | ~/.claude/hooks/context-monitor.sh
# Should show warning

echo "85" > /tmp/claude-context-monitor-$$
echo '{"tool_name": "Read"}' | ~/.claude/hooks/context-monitor.sh
# Should show critical warning
```

---

## 2. Post-Edit Quality Hook

### Purpose
Auto-format and lint files after Claude edits them.

### Implementation

**File**: `~/.claude/hooks/post-edit-quality.sh`

```bash
#!/bin/bash
#
# Post-Edit Quality Hook
# Auto-formats and lints files after editing
#
# Supports: Python (ruff), Shell (shellcheck), JS/TS (prettier)
#

INPUT=$(cat)

# Extract file path from Edit tool output
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // ""' 2>/dev/null)

# Skip if no file path
if [ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ] || [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"
FILENAME=$(basename "$FILE_PATH")
ISSUES=""

case "$EXT" in
    py)
        # Python: ruff format + check
        if command -v ruff &>/dev/null; then
            # Format silently
            ruff format "$FILE_PATH" 2>/dev/null

            # Check for issues
            ISSUES=$(ruff check "$FILE_PATH" --output-format=concise 2>&1 | head -3)
            if [ -n "$ISSUES" ] && [ "$ISSUES" != "" ]; then
                echo "{\"systemMessage\": \"🐍 Ruff ($FILENAME):\\n$ISSUES\"}"
            fi
        fi
        ;;

    sh|bash)
        # Shell: shellcheck
        if command -v shellcheck &>/dev/null; then
            ISSUES=$(shellcheck -f gcc "$FILE_PATH" 2>&1 | head -3)
            if [ -n "$ISSUES" ] && [ "$ISSUES" != "" ]; then
                echo "{\"systemMessage\": \"🐚 ShellCheck ($FILENAME):\\n$ISSUES\"}"
            fi
        fi
        ;;

    js|ts|jsx|tsx)
        # JavaScript/TypeScript: prettier (if available)
        if command -v prettier &>/dev/null; then
            prettier --write "$FILE_PATH" 2>/dev/null
        fi
        ;;

    json)
        # JSON: jq format
        if command -v jq &>/dev/null; then
            TEMP=$(mktemp)
            if jq '.' "$FILE_PATH" > "$TEMP" 2>/dev/null; then
                mv "$TEMP" "$FILE_PATH"
            else
                rm -f "$TEMP"
            fi
        fi
        ;;

    md)
        # Markdown: skip formatting, just validate
        ;;
esac

exit 0
```

### Settings.json Addition
```json
{
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "~/.claude/hooks/post-edit-quality.sh",
          "timeout": 10
        }
      ]
    }
  ]
}
```

### Testing
```bash
# Test Python file
echo 'def foo():pass' > /tmp/test.py
echo '{"tool_input": {"file_path": "/tmp/test.py"}}' | ~/.claude/hooks/post-edit-quality.sh
cat /tmp/test.py  # Should be formatted

# Test Shell file with issues
echo 'echo $foo' > /tmp/test.sh
echo '{"tool_input": {"file_path": "/tmp/test.sh"}}' | ~/.claude/hooks/post-edit-quality.sh
# Should show shellcheck warning about quoting
```

---

## 3. /kln:remember Command

### Purpose
End-of-session comprehensive save of all learnings before /clear.

### Implementation

**File**: `~/.claude/commands/kln/remember.md`

```markdown
# /kln:remember - Save Session Learnings

Comprehensive end-of-session knowledge capture before clearing context.

## Process

### Step 1: Assess What Was Done
Run these commands to understand the session:
- `git status` - See uncommitted changes
- `git diff --stat` - See what files changed
- `git log --oneline -5` - Recent commits

### Step 2: Identify Learnings by Category

Review the session and extract learnings in these categories:

#### Architecture & Design
- Pattern choices and WHY they were made
- System connections discovered
- Integration points identified

#### Implementation Details
- Key file locations (file:line format)
- Upstream/downstream dependencies
- Configuration requirements

#### Decisions & Trade-offs
- What was decided
- Alternatives considered
- Constraints that influenced choice

#### Gotchas & Warnings
- Problems encountered
- Solutions that worked
- Things to avoid

#### Testing Insights
- Test patterns that worked
- Edge cases discovered
- Test data requirements

### Step 3: Save Each Learning

For each significant learning, save to knowledge DB:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "<description>" \
    --type <lesson|finding|solution|pattern|warning|best-practice> \
    --tags "<relevant,tags>" \
    --priority <low|medium|high|critical>
```

**Type Guide:**
- `lesson` - General learning
- `finding` - Discovery during exploration
- `solution` - Working fix for a problem
- `pattern` - Reusable approach
- `warning` - Gotcha to avoid
- `best-practice` - Recommended approach

### Step 4: Save to Serena Memory (Cross-Session)

For critical architectural knowledge, also save to Serena memory:

```
Use mcp__serena__write_memory or mcp__serena__edit_memory to save:
- Architecture decisions
- Project patterns
- Critical gotchas
```

### Step 5: Confirm and Clear

After saving all learnings:
1. Verify saves: `FindKnowledge <topic>` to confirm entries exist
2. Clear context: `/clear` or `/compact`

## Example Session

```
/kln:remember

[Claude reviews session, identifies learnings]

Saving learnings...

1. Architecture: "Use hook system for auto-capture instead of manual"
   → knowledge-capture.py "Hook-based auto-capture..." --type pattern --tags hooks,automation

2. Gotcha: "Hooks must exit 0 even on error or Claude hangs"
   → knowledge-capture.py "Hooks must exit 0..." --type warning --tags hooks,gotcha --priority critical

3. Solution: "Use jq -Rs for JSON escaping in bash"
   → knowledge-capture.py "jq -Rs escapes..." --type solution --tags bash,json

Saved 3 learnings to knowledge DB.
Cross-session memory updated via Serena.

Ready to /clear when you are.
```

## Difference from SaveThis

| SaveThis | /kln:remember |
|----------|---------------|
| Single insight, inline | Full session review |
| During work | End of session |
| Quick capture | Comprehensive extraction |
| One entry | Multiple entries |
```

### Testing
```bash
# Verify command file exists
cat ~/.claude/commands/kln/remember.md

# Test knowledge-capture.py directly
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Test remember command" \
    --type lesson \
    --tags test,remember

# Verify entry saved
tail -1 .knowledge-db/entries.jsonl
```

---

## 4. MCP Funnel Configuration

### Purpose
Filter MCP tools to reduce context consumption from tool descriptions.

### Implementation

**Step 1: Install MCP Funnel**
```bash
npm install -g mcp-funnel
```

**Step 2: Create Config File**

**File**: `~/.mcp-funnel.json`

```json
{
  "version": "1.0",
  "defaultMode": "allowlist",
  "servers": {
    "serena": {
      "mode": "allowlist",
      "tools": [
        "find_symbol",
        "get_symbols_overview",
        "search_for_pattern",
        "find_referencing_symbols",
        "replace_symbol_body",
        "insert_after_symbol",
        "insert_before_symbol",
        "read_memory",
        "write_memory",
        "list_memories",
        "edit_memory",
        "list_dir",
        "find_file",
        "activate_project",
        "check_onboarding_performed"
      ]
    },
    "tavily": {
      "mode": "allowlist",
      "tools": [
        "tavily-search",
        "tavily-extract"
      ]
    },
    "context7": {
      "mode": "allowlist",
      "tools": [
        "resolve-library-id",
        "get-library-docs"
      ]
    },
    "sequential-thinking": {
      "mode": "allowlist",
      "tools": [
        "sequentialthinking"
      ]
    }
  }
}
```

**Step 3: Update MCP Configuration**

This requires updating the Claude Code MCP settings to route through funnel.
Note: MCP Funnel acts as a proxy - check its documentation for exact setup.

### Testing
```bash
# Verify mcp-funnel installed
npx mcp-funnel --version

# Verify config is valid JSON
jq '.' ~/.mcp-funnel.json
```

---

## Implementation Order

### Phase 1: Hooks (Do First)
1. Create `context-monitor.sh`
2. Create `post-edit-quality.sh`
3. Update `settings.json` with new hooks
4. Test hooks individually

### Phase 2: Remember Command
1. Create `commands/kln/remember.md`
2. Test command execution
3. Verify KB entries created

### Phase 3: MCP Funnel
1. Install mcp-funnel
2. Create config file
3. Test tool filtering

### Phase 4: Integration Testing
1. Full workflow test
2. Verify all hooks fire correctly
3. Test /kln:remember end-to-end

### Phase 5: Sync & Commit
1. Copy new files to backup location
2. Create commit with all changes
3. Push to remote

---

## File Locations Summary

```
~/.claude/
├── hooks/
│   ├── user-prompt-handler.sh    # Existing (SaveThis, etc.)
│   ├── post-bash-handler.sh      # Existing (git commits)
│   ├── post-web-handler.sh       # Existing (auto-capture)
│   ├── context-monitor.sh        # NEW
│   └── post-edit-quality.sh      # NEW
├── commands/kln/
│   ├── remember.md               # NEW
│   └── ... (existing commands)
├── settings.json                  # MODIFY (add hooks)
└── scripts/
    └── knowledge-capture.py       # Existing (used by remember)

~/.mcp-funnel.json                 # NEW (if using funnel)
```

---

## Rollback Plan

If issues occur:
1. Remove new hook entries from `settings.json`
2. Delete new hook files
3. Delete command file
4. Revert to previous commit

All changes are additive - existing functionality unchanged.
