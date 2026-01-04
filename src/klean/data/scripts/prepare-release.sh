#!/usr/bin/env bash
# prepare-release.sh - Verify K-LEAN is ready for PyPI release
#
# Validates version consistency and data directory contents.
# All source files already live in src/klean/data/ (no copying needed).
#
# Usage:
#   ./src/klean/data/scripts/prepare-release.sh         # Verify release
#   ./src/klean/data/scripts/prepare-release.sh --help  # Show help

set -euo pipefail

# Find repo root (where pyproject.toml is)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && while [ ! -f pyproject.toml ] && [ "$(pwd)" != "/" ]; do cd ..; done && pwd)"
DATA_DIR="$REPO_ROOT/src/klean/data"

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

# Get version from pyproject.toml (single source of truth)
get_version() {
    grep '^version' "$REPO_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2
}

# Verify release is ready
check_release() {
    log_info "Checking release readiness..."
    echo ""

    local errors=0

    # Check VERSION
    local version=$(get_version)
    if [[ -z "$version" || "$version" == "0.0.0" ]]; then
        log_error "Version not found in pyproject.toml"
        ((errors++))
    else
        log_success "VERSION: $version"
    fi

    # Check __init__.py version matches
    local init_version=$(grep '__version__ = ' "$REPO_ROOT/src/klean/__init__.py" | head -1 | cut -d'"' -f2)
    if [[ "$init_version" != "$version" ]]; then
        log_error "__init__.py version ($init_version) != pyproject.toml ($version)"
        ((errors++))
    else
        log_success "__init__.py version matches"
    fi

    # Check data directories have content
    for dir in scripts commands/kln hooks agents; do
        if [ -d "$DATA_DIR/$dir" ] && [ "$(ls -1 "$DATA_DIR/$dir" 2>/dev/null | wc -l)" -gt 0 ]; then
            local count=$(ls -1 "$DATA_DIR/$dir" 2>/dev/null | wc -l)
            log_success "data/$dir: $count files"
        else
            log_error "data/$dir empty or missing"
            ((errors++))
        fi
    done

    # Check MANIFEST.in
    if [ -f "$REPO_ROOT/MANIFEST.in" ]; then
        log_success "MANIFEST.in exists"
    else
        log_warn "MANIFEST.in missing (recommended for sdist)"
    fi

    # Check README
    if [ -f "$REPO_ROOT/README.md" ]; then
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
        echo "  python -m build"
        echo "  twine check dist/*"
        echo ""
        echo "Or use GitHub Actions:"
        echo "  Actions > Publish to PyPI > Run workflow"
        return 0
    else
        log_error "Release has $errors error(s) - fix before building"
        return 1
    fi
}

# Print usage
usage() {
    echo "Usage: $0 [--help]"
    echo ""
    echo "Verify K-LEAN is ready for PyPI release."
    echo ""
    echo "Checks:"
    echo "  - Version in pyproject.toml and __init__.py match"
    echo "  - Required data directories have content"
    echo "  - MANIFEST.in and README.md exist"
    echo ""
    echo "Note: All source files already live in src/klean/data/"
    echo "      No copying is needed - just run this to validate."
}

# Main
case "${1:-}" in
    --help|-h)
        usage
        ;;
    ""|--check)
        check_release
        ;;
    *)
        log_error "Unknown option: $1"
        usage
        exit 1
        ;;
esac
