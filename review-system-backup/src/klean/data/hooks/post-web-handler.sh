#!/bin/bash
#
# K-LEAN PostToolUse (WebFetch/WebSearch/Tavily) Hook Handler
# Smart capture - uses AI to evaluate before saving to knowledge DB
#
# Triggered after:
#   - WebFetch tool calls
#   - WebSearch tool calls
#   - mcp__tavily__tavily-search tool calls
#   - mcp__tavily__tavily-extract tool calls
#
# Dispatches to smart-web-capture.sh for AI evaluation (runs in background)
# Only saves content that scores >= 0.7 relevance
#

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)

# Exit if no tool name
if [ -z "$TOOL_NAME" ] || [ "$TOOL_NAME" = "null" ]; then
    exit 0
fi

# Get project directory and source kb-root.sh if available
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
if [ -f "$_SCRIPTS_DIR/kb-root.sh" ]; then
    source "$_SCRIPTS_DIR/kb-root.sh"
    SCRIPTS_DIR="$KB_SCRIPTS_DIR"
else
    SCRIPTS_DIR="$_SCRIPTS_DIR"
fi
SMART_CAPTURE="$SCRIPTS_DIR/smart-web-capture.sh"

# Check if smart capture is available
if [ ! -x "$SMART_CAPTURE" ]; then
    # One-time warning per session (avoid spam on every web call)
    if [ ! -f /tmp/klean-webcapture-warned ]; then
        echo "{\"systemMessage\": \"ℹ️ Web auto-capture disabled (smart-web-capture.sh not found)\"}"
        touch /tmp/klean-webcapture-warned
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# WEBFETCH - Smart capture URL content
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "WebFetch" ]; then
    URL=$(echo "$INPUT" | jq -r '.tool_input.url // ""' 2>/dev/null)
    PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 3000)

    if [ -n "$URL" ] && [ "$URL" != "null" ] && [ -n "$RESULT" ]; then
        # Dispatch to smart capture in background
        "$SMART_CAPTURE" "$RESULT" "$URL" "$PROMPT" "webfetch" "$PROJECT_DIR" &
    fi
fi

#------------------------------------------------------------------------------
# WEBSEARCH - Smart capture search results
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "WebSearch" ]; then
    QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // ""' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 3000)

    if [ -n "$QUERY" ] && [ "$QUERY" != "null" ] && [ -n "$RESULT" ]; then
        # Dispatch to smart capture in background (no URL for searches)
        "$SMART_CAPTURE" "$RESULT" "" "$QUERY" "websearch" "$PROJECT_DIR" &
    fi
fi

#------------------------------------------------------------------------------
# TAVILY SEARCH - Smart capture Tavily search results
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "mcp__tavily__tavily-search" ]; then
    QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // ""' 2>/dev/null)
    TOPIC=$(echo "$INPUT" | jq -r '.tool_input.topic // "general"' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 4000)

    if [ -n "$QUERY" ] && [ "$QUERY" != "null" ] && [ -n "$RESULT" ]; then
        # Include topic in query context
        QUERY_WITH_TOPIC="$QUERY (topic: $TOPIC)"
        "$SMART_CAPTURE" "$RESULT" "" "$QUERY_WITH_TOPIC" "tavily-search" "$PROJECT_DIR" &
    fi
fi

#------------------------------------------------------------------------------
# TAVILY EXTRACT - Smart capture Tavily URL extraction
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "mcp__tavily__tavily-extract" ]; then
    # Tavily extract takes an array of URLs
    URLS=$(echo "$INPUT" | jq -r '.tool_input.urls // [] | join(", ")' 2>/dev/null)
    FIRST_URL=$(echo "$URLS" | cut -d',' -f1 | xargs)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 4000)

    if [ -n "$FIRST_URL" ] && [ "$FIRST_URL" != "null" ] && [ -n "$RESULT" ]; then
        "$SMART_CAPTURE" "$RESULT" "$FIRST_URL" "Extracted content from: $URLS" "tavily-extract" "$PROJECT_DIR" &
    fi
fi

# Always exit 0 - never block tool execution
exit 0
