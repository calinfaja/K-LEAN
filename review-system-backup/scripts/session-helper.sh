#!/bin/bash
#
# Session Helper - Provides consistent output directories for all review scripts
#
# Usage: source this file, then use:
#   $KLN_OUTPUT_DIR - base output directory (.claude/kln in project root)
#   get_output_dir "commandName" - get command-specific output dir
#
# Output structure:
#   <project_root>/.claude/kln/
#   ├── quickReview/
#   │   └── 2024-12-09_14-30-25_qwen_security.md
#   ├── quickCompare/
#   │   └── 2024-12-09_16-00-00_consensus.md
#   ├── deepInspect/
#   │   └── 2024-12-09_17-00-00_qwen_audit.md
#   └── asyncDeepAudit/
#       └── 2024-12-09_18-00-00_parallel.md

# Find git root (project root)
find_project_root() {
    local dir="${1:-$(pwd)}"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    # Fallback to current directory if not in git repo
    echo "$(pwd)"
}

# Get the base KLN output directory
get_kln_base_dir() {
    local work_dir="${1:-$(pwd)}"
    local project_root=$(find_project_root "$work_dir")
    echo "$project_root/.claude/kln"
}

# Get command-specific output directory (creates if needed)
# Usage: get_output_dir "quickReview" [working_dir]
get_output_dir() {
    local cmd_name="$1"
    local work_dir="${2:-$(pwd)}"
    local base_dir=$(get_kln_base_dir "$work_dir")
    local output_dir="$base_dir/$cmd_name"
    mkdir -p "$output_dir"
    echo "$output_dir"
}

# Generate a filename with timestamp, model, and focus
# Usage: generate_filename "qwen" "security review"
generate_filename() {
    local model="$1"
    local focus="$2"
    local ext="${3:-.md}"
    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    # Sanitize focus: replace spaces with dashes, remove special chars, limit length
    local safe_focus=$(echo "$focus" | tr ' ' '-' | tr -cd '[:alnum:]-_' | head -c 30)
    [ -z "$safe_focus" ] && safe_focus="review"
    echo "${timestamp}_${model}_${safe_focus}${ext}"
}

# Legacy compatibility: set SESSION_DIR to a temp location
# (for scripts that haven't migrated yet)
SESSION_ID=$(date +%Y-%m-%d-%H%M%S)
SESSION_DIR="/tmp/claude-reviews/$SESSION_ID"
mkdir -p "$SESSION_DIR"

# Export base directory (can be overridden by passing work_dir)
KLN_BASE_DIR=$(get_kln_base_dir)
mkdir -p "$KLN_BASE_DIR"

# Export for use in scripts
export SESSION_ID
export SESSION_DIR
export KLN_BASE_DIR
