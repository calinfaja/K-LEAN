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

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS_DIR="$HOME/.claude/scripts"
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
        # Log to timeline
        TIMESTAMP=$(date '+%m-%d %H:%M')
        echo "$TIMESTAMP | commit | $COMMIT_HASH: $COMMIT_MSG" >> "$TIMELINE_FILE"

        # Extract facts from commit (async)
        if [ -x "$SCRIPTS_DIR/fact-extract.sh" ]; then
            # Get commit diff for fact extraction
            DIFF=$(cd "$PROJECT_DIR" && git show --stat HEAD 2>/dev/null | head -20)

            # Run fact extraction in background
            (
                echo "Commit: $COMMIT_MSG

Changes:
$DIFF" | "$SCRIPTS_DIR/fact-extract.sh" - commit "$COMMIT_MSG" "$PROJECT_DIR" 2>/dev/null
            ) &
        fi

        # Output confirmation
        echo "{\"systemMessage\": \"📝 Commit logged to timeline: $COMMIT_HASH\"}"
    fi
fi

#------------------------------------------------------------------------------
# GIT PUSH DETECTION (Optional logging)
#------------------------------------------------------------------------------
if echo "$COMMAND" | grep -qE "git push"; then
    TIMESTAMP=$(date '+%m-%d %H:%M')
    BRANCH=$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null)
    echo "$TIMESTAMP | push | Pushed $BRANCH to remote" >> "$TIMELINE_FILE"
fi

# Continue normally
exit 0
