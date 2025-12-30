#!/usr/bin/env bash
#
# Post-Commit Documentation Hook
# After git commit: Reviews Serena memories, updates them, creates documentation
# Uses headless Claude with full MCP access (including Serena)
#

# Source kb-root.sh for unified paths
SCRIPT_DIR="$(dirname "$0")"
if [ -f "$SCRIPT_DIR/kb-root.sh" ]; then
    source "$SCRIPT_DIR/kb-root.sh"
else
    KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
fi

OUTPUT_DIR="${TMPDIR:-/tmp}/claude-reviews"
mkdir -p "$OUTPUT_DIR"

# Read JSON input from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Check if this was a git commit
if echo "$COMMAND" | grep -qE "git commit|git merge"; then
    WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    TIMESTAMP=$(date +%s)

    # Get commit info
    COMMIT_MSG=$(cd "$WORK_DIR" && git log -1 --pretty=%B 2>/dev/null | head -1)
    COMMIT_HASH=$(cd "$WORK_DIR" && git log -1 --pretty=%h 2>/dev/null)
    CHANGED_FILES=$(cd "$WORK_DIR" && git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null)
    DIFF_STAT=$(cd "$WORK_DIR" && git show --stat HEAD 2>/dev/null | tail -20)

    RESULT_FILE="$OUTPUT_DIR/post-commit-docs-$TIMESTAMP.txt"
    LOG_FILE="$OUTPUT_DIR/post-commit-docs-$TIMESTAMP.log"

    # Run documentation agent in background with full MCP access
    (
        cd "$WORK_DIR"

        PROMPT="You are a documentation agent triggered by a git commit.

COMMIT INFO:
- Hash: $COMMIT_HASH
- Message: $COMMIT_MSG
- Changed files:
$CHANGED_FILES

- Diff stats:
$DIFF_STAT

YOUR TASKS:

1. **List Serena memories** using mcp__serena__list_memories
   - See what documentation/memories already exist

2. **Read relevant memories** that might need updating based on changed files
   - Architecture docs if structure changed
   - API docs if interfaces changed
   - Lessons learned if patterns discovered

3. **Update or create memories** as needed:
   - Update existing memories with new info from this commit
   - Create new memories if this commit introduces new patterns/components
   - Use mcp__serena__write_memory or mcp__serena__edit_memory

4. **Create/update session documentation**:
   - Write a memory named 'commit-log-$(date +%Y-%m-%d).md' with:
     - Commit summary
     - What changed and why
     - Any lessons learned (PATTERN/GOTCHA/TIP format)
     - Links to related memories

Be concise. Focus on what's useful for future development sessions.
Output a summary of what you updated."

        # Run headless Claude with full MCP access
        claude --print "$PROMPT" 2>&1

    ) > "$RESULT_FILE" 2>&1 &

    # Auto-extract facts from commit (Tier 2)
    # Build commit info for extraction
    COMMIT_INFO="Commit: $COMMIT_HASH
Message: $COMMIT_MSG

Changed Files:
$CHANGED_FILES

Diff Stats:
$DIFF_STAT"

    "$KB_SCRIPTS_DIR/fact-extract.sh" "$COMMIT_INFO" "commit" "$COMMIT_MSG" "$WORK_DIR" &

    # Log to timeline (direct, not via fact-extract since that's async)
    TIMELINE_FILE="$WORK_DIR/.knowledge-db/timeline.txt"
    if [ -d "$WORK_DIR/.knowledge-db" ] || [ -d "$WORK_DIR/.serena" ]; then
        mkdir -p "$WORK_DIR/.knowledge-db"
        echo "$(date '+%m-%d %H:%M') | commit | $COMMIT_HASH: $COMMIT_MSG" >> "$TIMELINE_FILE"
    fi

    echo " Post-commit Serena documentation started. Results: $RESULT_FILE"
    echo "📚 Auto-extracting facts from commit..."
fi

exit 0
