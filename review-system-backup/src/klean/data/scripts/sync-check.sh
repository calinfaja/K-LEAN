#!/bin/bash
# sync-check.sh - Verify and manage K-LEAN symlinks and file sync
#
# Usage:
#   sync-check.sh              # Check all components
#   sync-check.sh --sync       # Sync installed changes → repo (backup)
#   sync-check.sh --fix        # Fix broken symlinks (reinstall from repo)
#   sync-check.sh --orphans    # Find files in installed not tracked in repo
#   sync-check.sh --clean      # Remove orphaned files
#   sync-check.sh --verbose    # Show detailed output

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/common.sh" 2>/dev/null || {
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
    log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
}

REPO_DIR="$SCRIPT_DIR"
CLAUDE_DIR="$HOME/.claude"
FACTORY_DIR="$HOME/.factory"
CONFIG_DIR="$HOME/.config/litellm"

# Modes
MODE_CHECK=true
MODE_SYNC=false
MODE_FIX=false
MODE_ORPHANS=false
MODE_CLEAN=false
VERBOSE=false

# Counters
TOTAL_OK=0
TOTAL_WARN=0
TOTAL_ERROR=0
ORPHANS=()

# Parse args
for arg in "$@"; do
    case $arg in
        --sync) MODE_SYNC=true; MODE_CHECK=false ;;
        --fix) MODE_FIX=true; MODE_CHECK=false ;;
        --orphans) MODE_ORPHANS=true; MODE_CHECK=false ;;
        --clean) MODE_CLEAN=true; MODE_ORPHANS=true; MODE_CHECK=false ;;
        --verbose|-v) VERBOSE=true ;;
        --help|-h)
            echo "Usage: sync-check.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --sync      Sync installed changes to repo (backup your edits)"
            echo "  --fix       Fix broken symlinks (reinstall from repo)"
            echo "  --orphans   Find files in installed not tracked in repo"
            echo "  --clean     Remove orphaned files"
            echo "  --verbose   Show detailed output"
            exit 0
            ;;
    esac
done

# Check if file/dir exists and is properly symlinked
check_symlink() {
    local INSTALLED="$1"
    local REPO="$2"
    local NAME="$3"

    if [ ! -e "$REPO" ]; then
        log_error "$NAME - missing from repo"
        ((TOTAL_ERROR++))
        return 1
    fi

    if [ -L "$INSTALLED" ]; then
        local TARGET=$(readlink -f "$INSTALLED" 2>/dev/null || echo "broken")
        local EXPECTED=$(readlink -f "$REPO" 2>/dev/null)
        if [ "$TARGET" = "$EXPECTED" ]; then
            $VERBOSE && log_success "$NAME (symlinked)"
            ((TOTAL_OK++))
            return 0
        else
            log_warn "$NAME - symlink points to wrong target"
            $VERBOSE && echo "   Expected: $EXPECTED"
            $VERBOSE && echo "   Got: $TARGET"
            ((TOTAL_WARN++))
            return 2
        fi
    elif [ -e "$INSTALLED" ]; then
        # File exists but not a symlink (copied)
        if diff -q "$INSTALLED" "$REPO" >/dev/null 2>&1; then
            $VERBOSE && log_success "$NAME (copied, in sync)"
            ((TOTAL_OK++))
            return 0
        else
            log_warn "$NAME - differs from repo"
            ((TOTAL_WARN++))
            return 2
        fi
    else
        log_error "$NAME - not installed"
        ((TOTAL_ERROR++))
        return 1
    fi
}

# Sync file from installed to repo
sync_to_repo() {
    local INSTALLED="$1"
    local REPO="$2"
    local NAME="$3"

    if [ -L "$INSTALLED" ]; then
        log_info "$NAME - is symlink, no sync needed"
        return 0
    fi

    if [ -f "$INSTALLED" ] && [ -f "$REPO" ]; then
        if ! diff -q "$INSTALLED" "$REPO" >/dev/null 2>&1; then
            cp "$INSTALLED" "$REPO"
            log_success "$NAME - synced to repo"
            return 0
        fi
    fi
    return 1
}

# Fix by creating symlink
fix_symlink() {
    local INSTALLED="$1"
    local REPO="$2"
    local NAME="$3"

    if [ ! -e "$REPO" ]; then
        log_error "$NAME - source missing in repo, cannot fix"
        return 1
    fi

    # Remove existing file/symlink
    rm -f "$INSTALLED" 2>/dev/null || true

    # Create parent directory if needed
    mkdir -p "$(dirname "$INSTALLED")"

    # Create symlink
    ln -sf "$REPO" "$INSTALLED"
    log_success "$NAME - symlink created"
    return 0
}

# Find orphaned files
find_orphans() {
    local INSTALLED_DIR="$1"
    local REPO_DIR="$2"
    local PATTERN="$3"

    if [ ! -d "$INSTALLED_DIR" ]; then
        return
    fi

    for f in "$INSTALLED_DIR"/$PATTERN; do
        [ -e "$f" ] || continue
        local NAME=$(basename "$f")
        local REPO_FILE="$REPO_DIR/$NAME"

        if [ ! -e "$REPO_FILE" ]; then
            ORPHANS+=("$f")
            log_warn "Orphan: $f"
        fi
    done
}

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              K-LEAN Sync Checker                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

#=== SCRIPTS ===
echo "=== Scripts (*.sh, *.py) ==="
for ext in sh py; do
    for f in "$REPO_DIR/scripts"/*.$ext; do
        [ -f "$f" ] || continue
        NAME=$(basename "$f")
        INSTALLED="$CLAUDE_DIR/scripts/$NAME"

        if $MODE_CHECK; then
            check_symlink "$INSTALLED" "$f" "$NAME" || true
        elif $MODE_SYNC; then
            sync_to_repo "$INSTALLED" "$f" "$NAME" || true
        elif $MODE_FIX; then
            fix_symlink "$INSTALLED" "$f" "$NAME" || true
        fi
    done
done

if $MODE_ORPHANS; then
    find_orphans "$CLAUDE_DIR/scripts" "$REPO_DIR/scripts" "*.sh" || true
    find_orphans "$CLAUDE_DIR/scripts" "$REPO_DIR/scripts" "*.py" || true
fi
echo ""

#=== COMMANDS ===
echo "=== Commands (/kln:) ==="
for f in "$REPO_DIR/commands-kln"/*.md; do
    [ -f "$f" ] || continue
    NAME=$(basename "$f")
    INSTALLED="$CLAUDE_DIR/commands/kln/$NAME"

    if $MODE_CHECK; then
        check_symlink "$INSTALLED" "$f" "kln/$NAME" || true
    elif $MODE_SYNC; then
        sync_to_repo "$INSTALLED" "$f" "kln/$NAME" || true
    elif $MODE_FIX; then
        fix_symlink "$INSTALLED" "$f" "kln/$NAME" || true
    fi
done

if $MODE_ORPHANS; then
    find_orphans "$CLAUDE_DIR/commands/kln" "$REPO_DIR/commands-kln" "*.md" || true
fi
echo ""

#=== HOOKS ===
echo "=== Hooks ==="
for f in "$REPO_DIR/hooks"/*.sh; do
    [ -f "$f" ] || continue
    NAME=$(basename "$f")
    INSTALLED="$CLAUDE_DIR/hooks/$NAME"

    if $MODE_CHECK; then
        check_symlink "$INSTALLED" "$f" "$NAME" || true
    elif $MODE_SYNC; then
        sync_to_repo "$INSTALLED" "$f" "$NAME" || true
    elif $MODE_FIX; then
        fix_symlink "$INSTALLED" "$f" "$NAME" || true
    fi
done

if $MODE_ORPHANS; then
    find_orphans "$CLAUDE_DIR/hooks" "$REPO_DIR/hooks" "*.sh" || true
fi
echo ""

#=== DROIDS ===
echo "=== Factory Droids ==="
for f in "$REPO_DIR/droids"/*.md; do
    [ -f "$f" ] || continue
    NAME=$(basename "$f")
    INSTALLED="$FACTORY_DIR/droids/$NAME"

    if $MODE_CHECK; then
        check_symlink "$INSTALLED" "$f" "$NAME" || true
    elif $MODE_SYNC; then
        sync_to_repo "$INSTALLED" "$f" "$NAME" || true
    elif $MODE_FIX; then
        fix_symlink "$INSTALLED" "$f" "$NAME" || true
    fi
done

if $MODE_ORPHANS; then
    find_orphans "$FACTORY_DIR/droids" "$REPO_DIR/droids" "*.md" || true
fi
echo ""

#=== CONFIG ===
echo "=== Configuration ==="

# CLAUDE.md
if $MODE_CHECK; then
    check_symlink "$CLAUDE_DIR/CLAUDE.md" "$REPO_DIR/config/CLAUDE.md" "CLAUDE.md" || true
elif $MODE_SYNC; then
    sync_to_repo "$CLAUDE_DIR/CLAUDE.md" "$REPO_DIR/config/CLAUDE.md" "CLAUDE.md" || true
elif $MODE_FIX; then
    fix_symlink "$CLAUDE_DIR/CLAUDE.md" "$REPO_DIR/config/CLAUDE.md" "CLAUDE.md" || true
fi

# settings.json (special: usually edited locally, sync TO repo)
if [ -f "$CLAUDE_DIR/settings.json" ]; then
    if $MODE_CHECK; then
        if diff -q "$CLAUDE_DIR/settings.json" "$REPO_DIR/settings.json" >/dev/null 2>&1; then
            $VERBOSE && log_success "settings.json (in sync)"
            ((TOTAL_OK++))
        else
            log_warn "settings.json - differs (run --sync to backup)"
            ((TOTAL_WARN++))
        fi
    elif $MODE_SYNC; then
        if ! diff -q "$CLAUDE_DIR/settings.json" "$REPO_DIR/settings.json" >/dev/null 2>&1; then
            cp "$CLAUDE_DIR/settings.json" "$REPO_DIR/settings.json"
            log_success "settings.json - synced to repo"
        fi
    fi
fi

# LiteLLM configs
for f in "$REPO_DIR/config/litellm"/*.yaml; do
    [ -f "$f" ] || continue
    NAME=$(basename "$f")
    INSTALLED="$CONFIG_DIR/$NAME"

    if $MODE_CHECK; then
        check_symlink "$INSTALLED" "$f" "litellm/$NAME" || true
    elif $MODE_FIX; then
        fix_symlink "$INSTALLED" "$f" "litellm/$NAME" || true
    fi
done

# lib/common.sh
if $MODE_CHECK; then
    check_symlink "$CLAUDE_DIR/lib/common.sh" "$REPO_DIR/lib/common.sh" "lib/common.sh" || true
elif $MODE_FIX; then
    mkdir -p "$CLAUDE_DIR/lib"
    fix_symlink "$CLAUDE_DIR/lib/common.sh" "$REPO_DIR/lib/common.sh" "lib/common.sh" || true
fi

echo ""

#=== CLEAN ORPHANS ===
if $MODE_CLEAN && [ ${#ORPHANS[@]} -gt 0 ]; then
    echo "=== Cleaning Orphans ==="
    for orphan in "${ORPHANS[@]}"; do
        rm -f "$orphan"
        log_success "Removed: $orphan"
    done
    echo ""
fi

#=== SUMMARY ===
echo "═══════════════════════════════════════════════════════════"
if $MODE_CHECK; then
    echo -e "Results: ${GREEN}$TOTAL_OK OK${NC}, ${YELLOW}$TOTAL_WARN warnings${NC}, ${RED}$TOTAL_ERROR errors${NC}"

    if [ $TOTAL_ERROR -gt 0 ]; then
        echo -e "\n${RED}Run 'sync-check.sh --fix' to repair broken symlinks${NC}"
    elif [ $TOTAL_WARN -gt 0 ]; then
        echo -e "\n${YELLOW}Run 'sync-check.sh --sync' to backup local changes to repo${NC}"
    else
        echo -e "\n${GREEN}All components in sync!${NC}"
    fi
fi

if $MODE_ORPHANS && [ ${#ORPHANS[@]} -gt 0 ]; then
    echo -e "\nFound ${#ORPHANS[@]} orphaned file(s)"
    if ! $MODE_CLEAN; then
        echo "Run 'sync-check.sh --clean' to remove them"
    fi
fi

echo "═══════════════════════════════════════════════════════════"

exit $TOTAL_ERROR
