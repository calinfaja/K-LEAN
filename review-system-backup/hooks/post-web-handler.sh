#!/bin/bash
#
# K-LEAN PostToolUse (WebFetch/WebSearch/Tavily) Hook Handler
# Auto-captures web findings to knowledge DB
#
# Triggered after:
#   - WebFetch tool calls
#   - WebSearch tool calls
#   - mcp__tavily__tavily-search tool calls
#   - mcp__tavily__tavily-extract tool calls
#

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS_DIR="$HOME/.claude/scripts"
KNOWLEDGE_DIR="$PROJECT_DIR/.knowledge-db"

# Ensure knowledge directory exists
mkdir -p "$KNOWLEDGE_DIR"

#------------------------------------------------------------------------------
# WEBFETCH - Auto-capture URL content
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "WebFetch" ]; then
    URL=$(echo "$INPUT" | jq -r '.tool_input.url // ""' 2>/dev/null)
    PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 2000)

    if [ -n "$URL" ] && [ "$URL" != "null" ]; then
        # Create knowledge entry
        TITLE=$(echo "$URL" | sed 's|https\?://||' | cut -d'/' -f1)
        TIMESTAMP=$(date -Iseconds)

        ENTRY=$(jq -n \
            --arg title "Web: $TITLE" \
            --arg summary "${RESULT:0:500}" \
            --arg url "$URL" \
            --arg type "web" \
            --arg date "$TIMESTAMP" \
            --arg prompt "$PROMPT" \
            '{
                title: $title,
                summary: $summary,
                type: $type,
                url: $url,
                source: "auto-capture",
                found_date: $date,
                search_context: $prompt,
                relevance_score: 0.7,
                auto_extracted: true
            }')

        echo "$ENTRY" >> "$KNOWLEDGE_DIR/entries.jsonl"

        # Log to timeline
        TIMELINE_FILE="$KNOWLEDGE_DIR/timeline.txt"
        TIMESTAMP_SHORT=$(date '+%m-%d %H:%M')
        echo "$TIMESTAMP_SHORT | web | Captured: $URL" >> "$TIMELINE_FILE"
    fi
fi

#------------------------------------------------------------------------------
# WEBSEARCH - Auto-capture search results
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "WebSearch" ]; then
    QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // ""' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 3000)

    if [ -n "$QUERY" ] && [ "$QUERY" != "null" ]; then
        # Create knowledge entry for search
        TIMESTAMP=$(date -Iseconds)

        ENTRY=$(jq -n \
            --arg title "Search: $QUERY" \
            --arg summary "${RESULT:0:1000}" \
            --arg query "$QUERY" \
            --arg type "search" \
            --arg date "$TIMESTAMP" \
            '{
                title: $title,
                summary: $summary,
                type: $type,
                search_query: $query,
                source: "auto-capture",
                found_date: $date,
                relevance_score: 0.6,
                auto_extracted: true
            }')

        echo "$ENTRY" >> "$KNOWLEDGE_DIR/entries.jsonl"

        # Log to timeline
        TIMELINE_FILE="$KNOWLEDGE_DIR/timeline.txt"
        TIMESTAMP_SHORT=$(date '+%m-%d %H:%M')
        echo "$TIMESTAMP_SHORT | search | Query: $QUERY" >> "$TIMELINE_FILE"
    fi
fi

#------------------------------------------------------------------------------
# TAVILY SEARCH - Auto-capture Tavily search results
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "mcp__tavily__tavily-search" ]; then
    QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // ""' 2>/dev/null)
    TOPIC=$(echo "$INPUT" | jq -r '.tool_input.topic // "general"' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 4000)

    if [ -n "$QUERY" ] && [ "$QUERY" != "null" ]; then
        TIMESTAMP=$(date -Iseconds)

        ENTRY=$(jq -n \
            --arg title "Tavily: $QUERY" \
            --arg summary "${RESULT:0:1500}" \
            --arg query "$QUERY" \
            --arg topic "$TOPIC" \
            --arg type "tavily-search" \
            --arg date "$TIMESTAMP" \
            '{
                title: $title,
                summary: $summary,
                type: $type,
                search_query: $query,
                search_topic: $topic,
                source: "tavily-auto",
                found_date: $date,
                relevance_score: 0.8,
                auto_extracted: true
            }')

        echo "$ENTRY" >> "$KNOWLEDGE_DIR/entries.jsonl"

        # Log to timeline
        TIMELINE_FILE="$KNOWLEDGE_DIR/timeline.txt"
        TIMESTAMP_SHORT=$(date '+%m-%d %H:%M')
        echo "$TIMESTAMP_SHORT | tavily | Search: $QUERY ($TOPIC)" >> "$TIMELINE_FILE"
    fi
fi

#------------------------------------------------------------------------------
# TAVILY EXTRACT - Auto-capture Tavily URL extraction
#------------------------------------------------------------------------------
if [ "$TOOL_NAME" = "mcp__tavily__tavily-extract" ]; then
    # Tavily extract takes an array of URLs
    URLS=$(echo "$INPUT" | jq -r '.tool_input.urls // [] | join(", ")' 2>/dev/null)
    RESULT=$(echo "$INPUT" | jq -r '.tool_output // .output // ""' 2>/dev/null | head -c 4000)

    if [ -n "$URLS" ] && [ "$URLS" != "null" ] && [ "$URLS" != "" ]; then
        TIMESTAMP=$(date -Iseconds)
        FIRST_URL=$(echo "$URLS" | cut -d',' -f1 | xargs)
        TITLE=$(echo "$FIRST_URL" | sed 's|https\?://||' | cut -d'/' -f1)

        ENTRY=$(jq -n \
            --arg title "Tavily Extract: $TITLE" \
            --arg summary "${RESULT:0:1500}" \
            --arg urls "$URLS" \
            --arg type "tavily-extract" \
            --arg date "$TIMESTAMP" \
            '{
                title: $title,
                summary: $summary,
                type: $type,
                urls: $urls,
                source: "tavily-auto",
                found_date: $date,
                relevance_score: 0.85,
                auto_extracted: true
            }')

        echo "$ENTRY" >> "$KNOWLEDGE_DIR/entries.jsonl"

        # Log to timeline
        TIMELINE_FILE="$KNOWLEDGE_DIR/timeline.txt"
        TIMESTAMP_SHORT=$(date '+%m-%d %H:%M')
        echo "$TIMESTAMP_SHORT | tavily | Extract: $FIRST_URL" >> "$TIMELINE_FILE"
    fi
fi

# Continue normally
exit 0
