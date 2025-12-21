#!/bin/bash
#
# K-LEAN PostToolUse (Bash) Hook Handler
# Triggered after Bash tool executions
#
# Handles:
#   - Git commit detection → Timeline logging + fact extraction
#   - Post-commit documentation
#

# Read JSON input from stdin
INPUT=$(cat)

# Extract the command that was executed
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
OUTPUT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null)

# Exit if no command
if [ -z "$COMMAND" ] || [ "$COMMAND" = "null" ]; then
    exit 0
fi

# Get project directory and source kb-root.sh if available
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
if [ -f "$_SCRIPTS_DIR/kb-root.sh" ]; then
    source "$_SCRIPTS_DIR/kb-root.sh"
    SCRIPTS_DIR="$KB_SCRIPTS_DIR"
    PYTHON_BIN="${KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
else
    SCRIPTS_DIR="$_SCRIPTS_DIR"
    PYTHON_BIN="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
fi
KNOWLEDGE_DIR="$PROJECT_DIR/.knowledge-db"
TIMELINE_FILE="$KNOWLEDGE_DIR/timeline.txt"

# Ensure knowledge directory exists
mkdir -p "$KNOWLEDGE_DIR"

#------------------------------------------------------------------------------
# GIT COMMIT DETECTION
#------------------------------------------------------------------------------
if echo "$COMMAND" | grep -qE "git commit|git merge|git rebase"; then

    # Get the commit hash and message
    COMMIT_HASH=$(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null)
    COMMIT_MSG=$(cd "$PROJECT_DIR" && git log -1 --format="%s" 2>/dev/null)

    if [ -n "$COMMIT_HASH" ] && [ -n "$COMMIT_MSG" ]; then
        # Log to timeline with error check
        TIMESTAMP=$(date '+%m-%d %H:%M')
        if echo "$TIMESTAMP | commit | $COMMIT_HASH: $COMMIT_MSG" >> "$TIMELINE_FILE" 2>/dev/null; then
            # Output confirmation
            echo "{\"systemMessage\": \"📝 Commit logged to timeline: $COMMIT_HASH\"}"
        else
            echo "{\"systemMessage\": \"⚠️ Could not write to timeline: $TIMELINE_FILE\"}"
        fi

        # Emit event (Phase 4) - log errors instead of discarding
        if [ -f "$SCRIPTS_DIR/knowledge-events.py" ]; then
            "$PYTHON_BIN" "$SCRIPTS_DIR/knowledge-events.py" emit "knowledge:commit" "{\"hash\": \"$COMMIT_HASH\", \"message\": \"$COMMIT_MSG\"}" 2>> /tmp/klean-errors.log &
        fi

        # Extract facts from commit (async) - log errors instead of discarding
        if [ -x "$SCRIPTS_DIR/fact-extract.sh" ]; then
            # Get commit diff for fact extraction
            DIFF=$(cd "$PROJECT_DIR" && git show --stat HEAD 2>/dev/null | head -20)

            # Run fact extraction in background
            (
                echo "Commit: $COMMIT_MSG

Changes:
$DIFF" | "$SCRIPTS_DIR/fact-extract.sh" - commit "$COMMIT_MSG" "$PROJECT_DIR" 2>> /tmp/klean-errors.log
            ) &
        fi
    fi
fi

#------------------------------------------------------------------------------
# GIT PUSH DETECTION (Optional logging)
#------------------------------------------------------------------------------
if echo "$COMMAND" | grep -qE "git push"; then
    TIMESTAMP=$(date '+%m-%d %H:%M')
    BRANCH=$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null)
    if ! echo "$TIMESTAMP | push | Pushed $BRANCH to remote" >> "$TIMELINE_FILE" 2>/dev/null; then
        echo "{\"systemMessage\": \"⚠️ Could not log push to timeline\"}"
    fi
fi

# Continue normally
exit 0
