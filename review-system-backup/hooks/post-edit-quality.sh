#!/bin/bash
#
# K-LEAN Post-Edit Quality Hook
# Auto-formats and lints files after Claude edits them
#
# Supports:
#   - Python: ruff format + check
#   - Shell: shellcheck
#   - JavaScript/TypeScript: prettier (if available)
#   - JSON: jq formatting
#
# Runs on: Edit, Write tool completions
#

INPUT=$(cat)

# Extract file path from tool output
# Try multiple possible JSON paths
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // ""' 2>/dev/null)

# Skip if no file path or file doesn't exist
if [ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ]; then
    exit 0
fi

if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Get file extension and name
EXT="${FILE_PATH##*.}"
FILENAME=$(basename "$FILE_PATH")

# Skip certain files/patterns
case "$FILENAME" in
    *.min.js|*.min.css|package-lock.json|yarn.lock|*.lock)
        exit 0
        ;;
esac

# Process by file type
case "$EXT" in
    py)
        # Python: ruff format + check
        if command -v ruff &>/dev/null; then
            # Format the file (in-place, silent)
            ruff format "$FILE_PATH" 2>/dev/null

            # Check for issues (show first 3)
            ISSUES=$(ruff check "$FILE_PATH" --output-format=concise 2>&1 | grep -v "^All checks passed" | head -3)
            if [ -n "$ISSUES" ] && [ "$ISSUES" != "" ]; then
                # Escape for JSON
                ISSUES_ESC=$(echo "$ISSUES" | jq -Rs . | sed 's/^"//;s/"$//')
                echo "{\"systemMessage\": \"🐍 Ruff ($FILENAME):\\n$ISSUES_ESC\"}"
            fi
        fi
        ;;

    sh|bash)
        # Shell: shellcheck
        if command -v shellcheck &>/dev/null; then
            ISSUES=$(shellcheck -f gcc "$FILE_PATH" 2>&1 | head -3)
            if [ -n "$ISSUES" ] && [ "$ISSUES" != "" ]; then
                ISSUES_ESC=$(echo "$ISSUES" | jq -Rs . | sed 's/^"//;s/"$//')
                echo "{\"systemMessage\": \"🐚 ShellCheck ($FILENAME):\\n$ISSUES_ESC\"}"
            fi
        fi
        ;;

    js|ts|jsx|tsx)
        # JavaScript/TypeScript: prettier format (if available)
        if command -v prettier &>/dev/null; then
            prettier --write "$FILE_PATH" 2>/dev/null
        fi
        ;;

    json)
        # JSON: validate and format with jq
        if command -v jq &>/dev/null; then
            TEMP=$(mktemp)
            if jq '.' "$FILE_PATH" > "$TEMP" 2>/dev/null; then
                # Only update if jq succeeded (valid JSON)
                mv "$TEMP" "$FILE_PATH"
            else
                rm -f "$TEMP"
                echo "{\"systemMessage\": \"⚠️ JSON ($FILENAME): Invalid JSON syntax\"}"
            fi
        fi
        ;;

    yaml|yml)
        # YAML: just validate (no auto-format to preserve style)
        if command -v python3 &>/dev/null; then
            RESULT=$(python3 -c "import yaml; yaml.safe_load(open('$FILE_PATH'))" 2>&1)
            if [ $? -ne 0 ]; then
                echo "{\"systemMessage\": \"⚠️ YAML ($FILENAME): Invalid syntax\"}"
            fi
        fi
        ;;

    md|markdown)
        # Markdown: skip formatting (preserve author style)
        ;;

    *)
        # Unknown extension: skip
        ;;
esac

# Always exit 0 - never block tool execution
exit 0
