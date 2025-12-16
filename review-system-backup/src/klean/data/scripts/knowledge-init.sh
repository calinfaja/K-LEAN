#!/bin/bash
#
# Knowledge Init - Auto-initialize knowledge-db for current project
#
# Called automatically by hooks or manually.
# Creates .knowledge-db/ in the nearest git root or current directory.
#
# Usage:
#   knowledge-init.sh           # Auto-detect and initialize
#   knowledge-init.sh /path     # Initialize specific path
#   knowledge-init.sh --check   # Just check, don't create
#

TARGET="${1:-}"
CHECK_ONLY=false

if [ "$TARGET" = "--check" ]; then
    CHECK_ONLY=true
    TARGET=""
fi

# Find git root (best indicator of project)
find_git_root() {
    local dir="${1:-$(pwd)}"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo ""
}

# Find existing knowledge-db
find_knowledge_root() {
    local dir="${1:-$(pwd)}"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.knowledge-db" ] || [ -d "$dir/.serena" ] || [ -d "$dir/.claude" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo ""
}

# Determine project root
if [ -n "$TARGET" ]; then
    PROJECT_ROOT="$TARGET"
else
    # First check if knowledge-db already exists
    EXISTING=$(find_knowledge_root)
    if [ -n "$EXISTING" ]; then
        if [ "$CHECK_ONLY" = true ]; then
            echo "exists:$EXISTING/.knowledge-db"
        fi
        exit 0  # Already initialized
    fi

    # Find git root as project indicator
    GIT_ROOT=$(find_git_root)
    if [ -n "$GIT_ROOT" ]; then
        PROJECT_ROOT="$GIT_ROOT"
    else
        # Fallback to current directory
        PROJECT_ROOT="$(pwd)"
    fi
fi

if [ "$CHECK_ONLY" = true ]; then
    echo "would-create:$PROJECT_ROOT/.knowledge-db"
    exit 0
fi

# Create knowledge-db structure
KB_DIR="$PROJECT_ROOT/.knowledge-db"
if [ ! -d "$KB_DIR" ]; then
    mkdir -p "$KB_DIR"

    # Initialize empty timeline
    touch "$KB_DIR/timeline.txt"

    # Add to .gitignore if git repo
    if [ -d "$PROJECT_ROOT/.git" ]; then
        GITIGNORE="$PROJECT_ROOT/.gitignore"
        if [ -f "$GITIGNORE" ]; then
            if ! grep -q "^\.knowledge-db/$" "$GITIGNORE" 2>/dev/null; then
                echo "" >> "$GITIGNORE"
                echo "# K-LEAN knowledge database (local)" >> "$GITIGNORE"
                echo ".knowledge-db/" >> "$GITIGNORE"
            fi
        else
            echo "# K-LEAN knowledge database (local)" > "$GITIGNORE"
            echo ".knowledge-db/" >> "$GITIGNORE"
        fi
    fi

    echo "📚 Initialized knowledge-db at: $KB_DIR"
else
    echo "📚 Knowledge-db already exists: $KB_DIR"
fi
