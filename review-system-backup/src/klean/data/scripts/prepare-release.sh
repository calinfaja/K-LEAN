#!/usr/bin/env bash
# prepare-release.sh - Prepare K-LEAN for PyPI release
#
# This script populates src/klean/data/ with all required files for
# a production pip/pipx install (non-editable).
#
# Usage:
#   ./scripts/prepare-release.sh          # Prepare for release
#   ./scripts/prepare-release.sh --clean  # Clean data directory
#   ./scripts/prepare-release.sh --check  # Verify release is ready

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$SCRIPT_DIR/src/klean/data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get version from VERSION file
get_version() {
    cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "0.0.0"
}

# Clean data directory
clean_data() {
    log_info "Cleaning $DATA_DIR..."
    rm -rf "$DATA_DIR"
    mkdir -p "$DATA_DIR"
    log_success "Data directory cleaned"
}

# Copy files to data directory
populate_data() {
    log_info "Populating data directory for release..."

    mkdir -p "$DATA_DIR"

    # Scripts
    log_info "Copying scripts..."
    mkdir -p "$DATA_DIR/scripts"
    cp "$SCRIPT_DIR/scripts"/*.sh "$DATA_DIR/scripts/" 2>/dev/null || true
    cp "$SCRIPT_DIR/scripts"/*.py "$DATA_DIR/scripts/" 2>/dev/null || true
    local script_count=$(ls -1 "$DATA_DIR/scripts" 2>/dev/null | wc -l)
    log_success "Copied $script_count scripts"

    # Commands (kln) - canonical source is commands/kln/
    log_info "Copying commands..."
    mkdir -p "$DATA_DIR/commands/kln"
    cp "$SCRIPT_DIR/commands/kln"/*.md "$DATA_DIR/commands/kln/" 2>/dev/null || true
    local cmd_count=$(ls -1 "$DATA_DIR/commands/kln" 2>/dev/null | wc -l)
    log_success "Copied $cmd_count commands"

    # Hooks
    log_info "Copying hooks..."
    mkdir -p "$DATA_DIR/hooks"
    cp "$SCRIPT_DIR/hooks"/*.sh "$DATA_DIR/hooks/" 2>/dev/null || true
    local hook_count=$(ls -1 "$DATA_DIR/hooks" 2>/dev/null | wc -l)
    log_success "Copied $hook_count hooks"

    # Droids
    log_info "Copying droids..."
    mkdir -p "$DATA_DIR/droids"
    cp "$SCRIPT_DIR/droids"/*.md "$DATA_DIR/droids/" 2>/dev/null || true
    local droid_count=$(ls -1 "$DATA_DIR/droids" 2>/dev/null | wc -l)
    log_success "Copied $droid_count droids"

    # Config
    log_info "Copying configuration..."
    mkdir -p "$DATA_DIR/config/litellm"
    cp "$SCRIPT_DIR/config/CLAUDE.md" "$DATA_DIR/config/" 2>/dev/null || true
    cp "$SCRIPT_DIR/config/litellm"/*.yaml "$DATA_DIR/config/litellm/" 2>/dev/null || true
    cp "$SCRIPT_DIR/config/litellm/.env.example" "$DATA_DIR/config/litellm/" 2>/dev/null || true
    log_success "Copied configuration files"

    # Lib
    log_info "Copying lib..."
    mkdir -p "$DATA_DIR/lib"
    cp "$SCRIPT_DIR/lib"/*.sh "$DATA_DIR/lib/" 2>/dev/null || true
    log_success "Copied lib files"

    # Make scripts executable
    chmod +x "$DATA_DIR/scripts"/*.sh 2>/dev/null || true
    chmod +x "$DATA_DIR/scripts"/*.py 2>/dev/null || true
    chmod +x "$DATA_DIR/hooks"/*.sh 2>/dev/null || true

    echo ""
    log_success "Data directory ready for release!"
}

# Verify release is ready
check_release() {
    log_info "Checking release readiness..."
    echo ""

    local errors=0

    # Check VERSION
    local version=$(get_version)
    if [[ "$version" == "0.0.0" ]]; then
        log_error "VERSION file missing or invalid"
        ((errors++))
    else
        log_success "VERSION: $version"
    fi

    # Check pyproject.toml version matches
    local pyproject_version=$(grep -oP 'version = "\K[^"]+' "$SCRIPT_DIR/pyproject.toml" 2>/dev/null || echo "")
    if [[ "$pyproject_version" != "$version" ]]; then
        log_warn "pyproject.toml version ($pyproject_version) != VERSION ($version)"
    else
        log_success "pyproject.toml version matches"
    fi

    # Check __init__.py version matches
    local init_version=$(grep -oP '__version__ = "\K[^"]+' "$SCRIPT_DIR/src/klean/__init__.py" 2>/dev/null || echo "")
    if [[ "$init_version" != "$version" ]]; then
        log_warn "__init__.py version ($init_version) != VERSION ($version)"
    else
        log_success "__init__.py version matches"
    fi

    # Check data directory
    if [ -d "$DATA_DIR/scripts" ] && [ "$(ls -1 "$DATA_DIR/scripts" 2>/dev/null | wc -l)" -gt 0 ]; then
        local count=$(ls -1 "$DATA_DIR/scripts" 2>/dev/null | wc -l)
        log_success "Data/scripts: $count files"
    else
        log_error "Data/scripts empty or missing"
        ((errors++))
    fi

    if [ -d "$DATA_DIR/commands/kln" ] && [ "$(ls -1 "$DATA_DIR/commands/kln" 2>/dev/null | wc -l)" -gt 0 ]; then
        local count=$(ls -1 "$DATA_DIR/commands/kln" 2>/dev/null | wc -l)
        log_success "Data/commands/kln: $count files"
    else
        log_error "Data/commands/kln empty or missing"
        ((errors++))
    fi

    if [ -d "$DATA_DIR/hooks" ] && [ "$(ls -1 "$DATA_DIR/hooks" 2>/dev/null | wc -l)" -gt 0 ]; then
        local count=$(ls -1 "$DATA_DIR/hooks" 2>/dev/null | wc -l)
        log_success "Data/hooks: $count files"
    else
        log_error "Data/hooks empty or missing"
        ((errors++))
    fi

    if [ -d "$DATA_DIR/droids" ] && [ "$(ls -1 "$DATA_DIR/droids" 2>/dev/null | wc -l)" -gt 0 ]; then
        local count=$(ls -1 "$DATA_DIR/droids" 2>/dev/null | wc -l)
        log_success "Data/droids: $count files"
    else
        log_error "Data/droids empty or missing"
        ((errors++))
    fi

    # Check MANIFEST.in
    if [ -f "$SCRIPT_DIR/MANIFEST.in" ]; then
        log_success "MANIFEST.in exists"
    else
        log_warn "MANIFEST.in missing (recommended for sdist)"
    fi

    # Check README
    if [ -f "$SCRIPT_DIR/README.md" ]; then
        log_success "README.md exists"
    else
        log_error "README.md missing"
        ((errors++))
    fi

    echo ""
    if [ $errors -eq 0 ]; then
        log_success "Release is ready!"
        echo ""
        echo "Build commands:"
        echo "  pip install build"
        echo "  python -m build"
        echo ""
        echo "Upload to PyPI:"
        echo "  pip install twine"
        echo "  twine upload dist/*"
        return 0
    else
        log_error "Release has $errors error(s) - fix before building"
        return 1
    fi
}

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Prepare K-LEAN for PyPI release by populating src/klean/data/"
    echo ""
    echo "Options:"
    echo "  (no args)   Populate data directory"
    echo "  --clean     Remove data directory contents"
    echo "  --check     Verify release is ready"
    echo "  --help      Show this help"
    echo ""
    echo "Workflow:"
    echo "  1. ./scripts/prepare-release.sh        # Populate data/"
    echo "  2. ./scripts/prepare-release.sh --check # Verify"
    echo "  3. python -m build                      # Build package"
    echo "  4. twine upload dist/*                  # Upload to PyPI"
}

# Main
case "${1:-}" in
    --clean)
        clean_data
        ;;
    --check)
        check_release
        ;;
    --help|-h)
        usage
        ;;
    "")
        populate_data
        ;;
    *)
        log_error "Unknown option: $1"
        usage
        exit 1
        ;;
esac
