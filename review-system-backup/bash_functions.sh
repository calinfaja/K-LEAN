#!/bin/bash

# Claude Review System Functions

# Function to get the current git repository root
get_git_root() {
    git rev-parse --show-toplevel 2>/dev/null || echo "$PWD"
}

# Function to set up the SuperClaude project environment
setup_superclaude_env() {
    # Set the project root to the current git repository root
    export SUPERCLAUDE_PROJECT_ROOT="$(get_git_root)"

    # Set the LiteLLM settings directory
    export LITELLMS_DIR="$HOME/.claude-review"

    # Ensure the directory exists
    mkdir -p "$LITELLMS_DIR"

    # Create or update the settings.json file
    cat > "$LITELLMS_DIR/settings.json" << 'EOF'
{
    "project_root": "",
    "current_file": "",
    "session_id": ""
}
EOF

    echo "SuperClaude environment set up:"
    echo "  Project Root: $SUPERCLAUDE_PROJECT_ROOT"
    echo "  LiteLLM Settings Dir: $LITELLMS_DIR"
}

# Function to update the settings file with current context
update_claude_settings() {
    local project_root="${1:-$SUPERCLAUDE_PROJECT_ROOT}"
    local current_file="${2:-}"
    local session_id="${3:-$(date +%s)}"

    # Update the settings.json file
    cat > "$LITELLMS_DIR/settings.json" << EOF
{
    "project_root": "$project_root",
    "current_file": "$current_file",
    "session_id": "$session_id"
}
EOF
}

# Function to run a LiteLLM review
claude_review_run() {
    local model="${1:-sonnet}"
    local file_path="${2:-}"
    local focus="${3:-}"

    # Set up environment if not already done
    if [[ -z "$SUPERCLAUDE_PROJECT_ROOT" ]]; then
        setup_superclaude_env
    fi

    # Update settings with current context
    update_claude_settings "$(get_git_root)" "$file_path" "$(date +%s)"

    # Run the review script
    if [[ -n "$file_path" && -n "$focus" ]]; then
        "$HOME/.claude/scripts/litellm-review.sh" "$model" "$file_path" "$focus"
    elif [[ -n "$file_path" ]]; then
        "$HOME/.claude/scripts/litellm-review.sh" "$model" "$file_path"
    else
        "$HOME/.claude/scripts/litellm-review.sh" "$model"
    fi
}

# Function to run a parallel consensus review
claude_review_consensus() {
    local file_path="${1:-}"
    local focus="${2:-}"

    # Set up environment if not already done
    if [[ -z "$SUPERCLAUDE_PROJECT_ROOT" ]]; then
        setup_superclaude_env
    fi

    # Update settings with current context
    update_claude_settings "$(get_git_root)" "$file_path" "$(date +%s)"

    # Run the consensus script
    if [[ -n "$file_path" && -n "$focus" ]]; then
        "$HOME/.claude/scripts/litellm-review.sh" "consensus" "$file_path" "$focus"
    elif [[ -n "$file_path" ]]; then
        "$HOME/.claude/scripts/litellm-review.sh" "consensus" "$file_path"
    else
        "$HOME/.claude/scripts/litellm-review.sh" "consensus"
    fi
}

# Function to run a deep review with tool access
claude_review_deep() {
    local model="${1:-sonnet}"
    local file_path="${2:-}"
    local focus="${3:-}"

    # Set up environment if not already done
    if [[ -z "$SUPERCLAUDE_PROJECT_ROOT" ]]; then
        setup_superclaude_env
    fi

    # Update settings with current context
    update_claude_settings "$(get_git_root)" "$file_path" "$(date +%s)"

    # Run the deep review script
    if [[ -n "$file_path" && -n "$focus" ]]; then
        "$HOME/.claude/scripts/deep-review.sh" "$model" "$file_path" "$focus"
    elif [[ -n "$file_path" ]]; then
        "$HOME/.claude/scripts/deep-review.sh" "$model" "$file_path"
    else
        "$HOME/.claude/scripts/deep-review.sh" "$model"
    fi
}

# Function to run parallel deep reviews with tool access
claude_review_parallel_deep() {
    local file_path="${1:-}"
    local focus="${2:-}"

    # Set up environment if not already done
    if [[ -z "$SUPERCLAUDE_PROJECT_ROOT" ]]; then
        setup_superclaude_env
    fi

    # Update settings with current context
    update_claude_settings "$(get_git_root)" "$file_path" "$(date +%s)"

    # Run the parallel deep review script
    if [[ -n "$file_path" && -n "$focus" ]]; then
        "$HOME/.claude/scripts/parallel-deep-review.sh" "$file_path" "$focus"
    elif [[ -n "$file_path" ]]; then
        "$HOME/.claude/scripts/parallel-deep-review.sh" "$file_path"
    else
        "$HOME/.claude/scripts/parallel-deep-review.sh"
    fi
}

# Function to create a review document
claude_create_review_doc() {
    local session_title="${1:-"Code Review Session $(date +%Y-%m-%d_%H-%M-%S)"}"

    # Set up environment if not already done
    if [[ -z "$SUPERCLAUDE_PROJECT_ROOT" ]]; then
        setup_superclaude_env
    fi

    # Update settings with current context
    update_claude_settings "$(get_git_root)" "" "$(date +%s)"

    # Run SuperClaude with the createReviewDoc command
    superclaude /sc:createReviewDoc "$session_title"
}