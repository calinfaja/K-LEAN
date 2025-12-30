#!/usr/bin/env bash
#
# Session Helper - Provides consistent output directories for all review scripts
#
# Usage: source this file, then use:
#   $KLN_BASE_DIR - base output directory (.claude/kln in project root)
#   get_output_dir "commandName" - get command-specific output dir
#   generate_filename "model" "focus" - generate timestamped filename
#
# Output structure:
#   <project_root>/.claude/kln/
#   ├── quickReview/
#   │   └── 2024-12-09_14-30-25_qwen_security.md
#   ├── quickCompare/
#   │   └── 2024-12-09_16-00-00_consensus.md
#   └── agentExecute/
#       └── 2024-12-09_18-00-00_qwen_security-auditor.txt

# Find git root (project root)
# Walks up directory tree looking for .git directory
# Falls back to current directory if not in a git repo
# Args: $1 - starting directory (default: pwd)
find_project_root() {
    local dir="${1:-$(pwd)}"

    # Handle permission errors gracefully
    if [ ! -r "$dir" ]; then
        echo "$(pwd)"
        return 1
    fi

    while [ "$dir" != "/" ]; do
        # Check if we can read the directory
        if [ ! -r "$dir" ]; then
            break
        fi
        if [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done

    # Fallback to current directory if not in git repo
    echo "$(pwd)"
    return 0
}

# Get the base KLN output directory
# Args: $1 - working directory (default: pwd)
# Returns: path to .claude/kln in project root
get_kln_base_dir() {
    local work_dir="${1:-$(pwd)}"
    local project_root
    project_root=$(find_project_root "$work_dir")
    echo "$project_root/.claude/kln"
}

# Get command-specific output directory (creates if needed)
# Args: $1 - command name (e.g., "quickReview", "agentExecute")
#       $2 - working directory (default: pwd)
# Returns: path to command-specific output directory
get_output_dir() {
    local cmd_name="$1"
    local work_dir="${2:-$(pwd)}"
    local base_dir
    base_dir=$(get_kln_base_dir "$work_dir")
    local output_dir="$base_dir/$cmd_name"
    mkdir -p "$output_dir" 2>/dev/null || {
        # Fallback to /tmp if project dir not writable
        output_dir="/tmp/claude-reviews/$cmd_name"
        mkdir -p "$output_dir"
    }
    echo "$output_dir"
}

# Generate a filename with timestamp, model, and focus
# Args: $1 - model name (e.g., "qwen", "deepseek")
#       $2 - focus/prompt description
#       $3 - file extension (default: .md)
# Returns: filename like "2024-12-09_14-30-25_qwen_security-review.md"
# Note: Focus is sanitized to 30 chars max to keep filenames reasonable
generate_filename() {
    local model="$1"
    local focus="$2"
    local ext="${3:-.md}"
    local timestamp
    timestamp=$(date '+%Y-%m-%d_%H-%M-%S')

    # Sanitize focus: replace spaces with dashes, remove special chars
    # Limit to 30 characters to keep filenames manageable on all filesystems
    local safe_focus
    safe_focus=$(echo "$focus" | tr ' ' '-' | tr -cd '[:alnum:]-_' | head -c 30)

    # Default to "review" if focus is empty after sanitization
    [ -z "$safe_focus" ] && safe_focus="review"

    echo "${timestamp}_${model}_${safe_focus}${ext}"
}

# Legacy compatibility: set SESSION_DIR to a temp location
# (for scripts that haven't migrated to KLN_BASE_DIR yet)
# These will be deprecated in a future version
SESSION_ID=$(date +%Y-%m-%d-%H%M%S)

# Use /tmp with fallback - check writability first
if [ -w "/tmp" ]; then
    SESSION_DIR="/tmp/claude-reviews/$SESSION_ID"
else
    SESSION_DIR="${TMPDIR:-/var/tmp}/claude-reviews/$SESSION_ID"
fi
mkdir -p "$SESSION_DIR" 2>/dev/null || true

# Initialize base directory for current working directory
KLN_BASE_DIR=$(get_kln_base_dir "$(pwd)")
mkdir -p "$KLN_BASE_DIR" 2>/dev/null || true

# Export for use in scripts
export SESSION_ID
export SESSION_DIR
export KLN_BASE_DIR
