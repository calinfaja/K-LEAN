#!/usr/bin/env bash
# K-LEAN Updater
# Pull latest changes and reinstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

VERSION=$(get_version)

print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║           K-LEAN Updater v$VERSION                          ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
}

main() {
    print_banner

    cd "$SCRIPT_DIR"

    # Check for updates
    log_info "Checking for updates..."
    git fetch origin 2>/dev/null || {
        log_error "Failed to fetch updates"
        exit 1
    }

    local LOCAL=$(git rev-parse HEAD)
    local REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master)

    if [ "$LOCAL" = "$REMOTE" ]; then
        log_success "Already up to date (v$VERSION)"
        exit 0
    fi

    # Pull updates
    log_info "Pulling updates..."
    git pull --rebase origin main 2>/dev/null || git pull --rebase origin master

    # Get new version
    NEW_VERSION=$(get_version)
    log_success "Updated from v$VERSION to v$NEW_VERSION"

    # Reinstall
    log_info "Reinstalling..."
    "$SCRIPT_DIR/install.sh" --full

    log_success "Update complete!"
}

main "$@"
