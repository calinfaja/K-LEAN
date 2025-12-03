#!/bin/bash
#
# sync-check.sh - Verify Claude config is synced with backup
#
# Usage:
#   sync-check.sh              # Check only
#   sync-check.sh --sync       # Check and sync differences to backup
#   sync-check.sh --scripts    # Check scripts only
#   sync-check.sh --commands   # Check commands only
#   sync-check.sh --config     # Check config only
#

CLAUDE_DIR="$HOME/.claude"
BACKUP_DIR="$HOME/claudeAgentic/review-system-backup"

SYNC_MODE=false
CHECK_SCRIPTS=true
CHECK_COMMANDS=true
CHECK_CONFIG=true

# Parse args
for arg in "$@"; do
    case $arg in
        --sync) SYNC_MODE=true ;;
        --scripts) CHECK_COMMANDS=false; CHECK_CONFIG=false ;;
        --commands) CHECK_SCRIPTS=false; CHECK_CONFIG=false ;;
        --config) CHECK_SCRIPTS=false; CHECK_COMMANDS=false ;;
    esac
done

TOTAL_DIFFS=0
TOTAL_SYNCED=0

# Helper function to check files
check_file() {
    local SRC="$1"
    local DST="$2"
    local NAME="$3"

    if [ ! -f "$SRC" ]; then
        echo "⚠️  $NAME - missing from source"
        return 2
    fi

    if [ ! -f "$DST" ]; then
        echo "❌ $NAME - missing from backup"
        if $SYNC_MODE; then
            mkdir -p "$(dirname "$DST")"
            cp "$SRC" "$DST"
            echo "   → copied to backup"
        fi
        return 1
    fi

    if diff -q "$SRC" "$DST" >/dev/null 2>&1; then
        echo "✅ $NAME"
        return 0
    else
        echo "❌ $NAME - differs"
        if $SYNC_MODE; then
            cp "$SRC" "$DST"
            echo "   → synced to backup"
        fi
        return 1
    fi
}

#=== SCRIPTS ===
if $CHECK_SCRIPTS; then
    echo "=== Scripts ==="
    SCRIPTS=(
        "knowledge_db.py"
        "knowledge-search.py"
        "knowledge-extract.sh"
        "goodjob-dispatch.sh"
        "auto-capture-hook.sh"
        "quick-review.sh"
        "second-opinion.sh"
        "consensus-review.sh"
        "deep-review.sh"
        "parallel-deep-review.sh"
        "litellm-review.sh"
        "async-dispatch.sh"
        "health-check.sh"
        "test-system.sh"
        "start-litellm.sh"
        "session-helper.sh"
        "post-commit-docs.sh"
        "sync-check.sh"
    )

    for f in "${SCRIPTS[@]}"; do
        check_file "$CLAUDE_DIR/scripts/$f" "$BACKUP_DIR/scripts/$f" "$f"
        case $? in
            0) ((TOTAL_SYNCED++)) ;;
            1) ((TOTAL_DIFFS++)) ;;
        esac
    done
    echo ""
fi

#=== COMMANDS (Slash Commands) ===
if $CHECK_COMMANDS; then
    echo "=== Slash Commands ==="

    # Get all .md files from source commands/sc/
    if [ -d "$CLAUDE_DIR/commands/sc" ]; then
        for f in "$CLAUDE_DIR/commands/sc"/*.md; do
            [ -f "$f" ] || continue
            NAME=$(basename "$f")
            check_file "$f" "$BACKUP_DIR/commands/$NAME" "sc/$NAME"
            case $? in
                0) ((TOTAL_SYNCED++)) ;;
                1) ((TOTAL_DIFFS++)) ;;
            esac
        done
    fi
    echo ""
fi

#=== CONFIG ===
if $CHECK_CONFIG; then
    echo "=== Config ==="

    check_file "$CLAUDE_DIR/settings.json" "$BACKUP_DIR/config/settings.json" "settings.json"
    case $? in
        0) ((TOTAL_SYNCED++)) ;;
        1) ((TOTAL_DIFFS++)) ;;
    esac

    # CLAUDE.md
    check_file "$CLAUDE_DIR/CLAUDE.md" "$BACKUP_DIR/CLAUDE.md" "CLAUDE.md"
    case $? in
        0) ((TOTAL_SYNCED++)) ;;
        1) ((TOTAL_DIFFS++)) ;;
    esac
    echo ""
fi

#=== SUMMARY ===
echo "==============================="
echo "Summary: $TOTAL_SYNCED synced, $TOTAL_DIFFS differ"

if [ $TOTAL_DIFFS -gt 0 ] && ! $SYNC_MODE; then
    echo ""
    echo "Run with --sync to copy differences to backup"
fi

exit $TOTAL_DIFFS
